import json,tempfile,unittest
from pathlib import Path
from tester_spin.models import GameTestResult,SpinAttempt
from tester_spin.providers.pragmatic_bonus_coverage import annotate_bonus_coverage

class BonusCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.result=GameTestResult(provider='pragmatic',slug='test',game_name='Test',game_url='https://example.invalid',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',run_dir=str(self.root))
    def tearDown(self):self.temp.cleanup()
    def add(self,*,number=1,selected='0',domain=None,signature='bonus:level0',source_hash='hash-a',terminal=True,proof='CONFIRMED',consecutive=2,response=None,subdir=''):
        directory=self.root/f'attempt-{number}'
        directory.mkdir(exist_ok=True)
        existing=next((a for a in self.result.attempts if a.number==number),None)
        if not existing:self.result.attempts.append(SpinAttempt(number=number,ok=True,terminal=terminal,mode_id='SPIN',artifact_dir=str(directory)))
        (directory/'return-to-base.json').write_text(json.dumps({'status':proof,'consecutive_base':consecutive}))
        target=directory/subdir;target.mkdir(parents=True,exist_ok=True)
        count=len(list(target.glob('*.bonus-selection.json')))
        stem=f'step-{count:03d}-bonus'
        (target/(stem+'.bonus-selection.json')).write_text(json.dumps({'domain':domain or ['0','1','2','3'],'selected':selected,'branch_signature':signature,'contract_sha256':source_hash,'contract_source':'https://example.invalid/build.js'}))
        (target/(stem+'.response.json')).write_text(json.dumps({'na':'cb'} if response is None else response))
    def rows(self):return [m for m in self.result.discovered_modes if m.get('kind')=='CHOICE_BRANCH']
    def test_only_selected_option_is_covered_and_other_choices_stay_pending(self):
        self.add();annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['covered_options'],['0'])
        self.assertEqual(self.rows()[0]['required_options'],['0','1','2','3'])
        self.assertEqual(self.result.status,'PARCIAL')
    def test_recursive_base_probes_contribute_with_parent_terminal_proof(self):
        self.add(subdir='return-to-base/probe-002',domain=['0'])
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['sample_counts'],{'0':1})
        self.assertEqual(self.result.status,'OK')
    def test_nonterminal_or_missing_two_confirmations_never_cover(self):
        self.add(terminal=False,consecutive=1)
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['covered_options'],[])
    def test_server_error_never_covers_selected_option(self):
        self.add(response={'frozen':'Internal server error','ext_code':'SystemError'})
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['covered_options'],[])
    def test_signature_and_source_hash_are_separate_branches(self):
        self.add(signature='bonus:level0',selected='0')
        self.add(signature='bonus:level1',selected='1')
        self.add(signature='bonus:level0',source_hash='hash-b',selected='2')
        annotate_bonus_coverage(self.result)
        self.assertEqual(len(self.rows()),3)
        self.assertEqual(sorted(row['covered_options'] for row in self.rows()),[['0'],['1'],['2']])
    def test_samples_count_independent_attempts_not_multiple_probes(self):
        self.result.samples_per_path=2
        self.add(domain=['0']);self.add(domain=['0'],subdir='return-to-base/probe-001')
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['sample_counts'],{'0':1})
        self.assertEqual(self.rows()[0]['covered_options'],[])
        self.add(number=2,domain=['0']);annotate_bonus_coverage(self.result)
        self.assertEqual(len(self.rows()),1)
        self.assertEqual(self.rows()[0]['sample_counts'],{'0':2})
        self.assertEqual(self.rows()[0]['covered_options'],['0'])
    def test_empty_response_and_selected_outside_domain_do_not_cover(self):
        self.add(response={});self.add(number=2,selected='9')
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['covered_options'],[])
    def test_cancelled_state_is_preserved(self):
        self.add();self.result.status='CANCELADO';annotate_bonus_coverage(self.result)
        self.assertEqual(self.result.status,'CANCELADO')

    def test_unknown_branch_is_not_explored_or_marked_complete(self):
        import threading
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        from tester_spin.providers.pragmatic_bonus_coverage import expand_observed_bonus_choices
        self.add(signature='unknown:wheel')
        provider=SimpleNamespace(base_bet=2,_test_mode_once=Mock(),_write_json=Mock())
        with patch('tester_spin.providers.pragmatic_modes.discover_modes',return_value=SimpleNamespace(enabled=lambda:[])):
            expand_observed_bonus_choices(provider,None,self.result,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda s:None)
        provider._test_mode_once.assert_not_called()
        self.assertEqual(self.result.status,'PARCIAL')
    def test_hidden_grid_structural_policy_preserves_real_domain(self):
        signature='PRAGMATIC:bonus-grid:bg_0:bgt=69:size=4:level=0'
        self.add(signature=signature,selected='2')
        path=next(Path(self.result.attempts[0].artifact_dir).glob('*.bonus-selection.json'))
        record=json.loads(path.read_text());record['coverage_policy']='hidden-position-structural/v1'
        path.write_text(json.dumps(record))
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['observed_position_domain'],['0','1','2','3'])
        self.assertEqual(self.rows()[0]['covered_options'],['0'])
        self.assertEqual(self.result.status,'OK')
        self.assertEqual(json.loads(path.read_text())['selected'],'2')

    def test_structural_policy_does_not_apply_to_menu_options(self):
        self.add(signature='PRAGMATIC:bonus-choice:bgt=69:choices=0,1,2,3')
        path=next(Path(self.result.attempts[0].artifact_dir).glob('*.bonus-selection.json'))
        record=json.loads(path.read_text());record['coverage_policy']='hidden-position-structural/v1'
        path.write_text(json.dumps(record))
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['covered_options'],['0'])
        self.assertEqual(self.result.status,'PARCIAL')

    def test_same_structural_handler_is_shared_across_origin_modes(self):
        from unittest.mock import patch
        signature='PRAGMATIC:bonus-grid:bg_0:bgt=69:size=4:level=0'
        self.add(signature=signature,selected='2')
        path=next(Path(self.result.attempts[0].artifact_dir).glob('*.bonus-selection.json'))
        record=json.loads(path.read_text());record['coverage_policy']='hidden-position-structural/v1'
        path.write_text(json.dumps(record))
        with patch('tester_spin.providers.pragmatic_bonus_coverage.selection_artifacts',return_value=[(path,'SPIN','bootstrap'),(path,'PURCHASE_1','attempt')]):
            annotate_bonus_coverage(self.result)
        self.assertEqual(len(self.rows()),2)
        self.assertTrue(all(row['covered_options']==['0'] for row in self.rows()))
        self.assertTrue(all(row['handler_sample_modes']==['PURCHASE_1'] for row in self.rows()))
        self.assertEqual(self.result.status,'OK')

    def test_structural_class_does_not_cover_invalid_index(self):
        signature='PRAGMATIC:bonus-grid:bg_0:bgt=69:size=4:level=0'
        self.add(signature=signature,selected='9')
        path=next(Path(self.result.attempts[0].artifact_dir).glob('*.bonus-selection.json'))
        record=json.loads(path.read_text());record['coverage_policy']='hidden-position-structural/v1'
        path.write_text(json.dumps(record))
        annotate_bonus_coverage(self.result)
        self.assertEqual(self.rows()[0]['covered_options'],[])
        self.assertEqual(self.result.status,'PARCIAL')

    def test_grid_histories_share_only_same_level_size_and_contract(self):
        self.add(number=1,signature='raw:history-a',selected='0',domain=['0','1'])
        self.add(number=2,signature='raw:history-b',selected='1',domain=['1','2'])
        signature='PRAGMATIC:bonus-grid:bg_0:bgt=69:size=14:level=1'
        for attempt in self.result.attempts:
            path=next(Path(attempt.artifact_dir).glob('*.bonus-selection.json'))
            row=json.loads(path.read_text());row['coverage_branch_signature']=signature
            path.write_text(json.dumps(row))
        annotate_bonus_coverage(self.result)
        self.assertEqual(len(self.rows()),1)
        self.assertEqual(self.rows()[0]['required_options'],['0','1','2'])
        self.assertEqual(self.rows()[0]['covered_options'],['0','1'])
        self.assertEqual(self.result.status,'PARCIAL')

    def test_observed_free_spin_choices_are_explored_automatically(self):
        import threading
        from types import SimpleNamespace
        from unittest.mock import Mock,patch
        from tester_spin.providers.pragmatic_bonus_coverage import expand_observed_bonus_choices
        signature='PRAGMATIC:bonus-choice:bgt=69:choices=0,1,2'
        self.add(signature=signature,domain=['0','1','2'])
        choices=iter(['1','2'])
        def execute(*args,**kwargs):
            self.add(number=kwargs['attempt_number'],selected=next(choices),signature=signature,domain=['0','1','2'])
            return self.result.attempts.pop()
        provider=SimpleNamespace(base_bet=2,_test_mode_once=Mock(side_effect=execute),_write_json=Mock())
        catalog=SimpleNamespace(enabled=lambda:[SimpleNamespace(id='SPIN')])
        with patch('tester_spin.providers.pragmatic_modes.discover_modes',return_value=catalog):
            expand_observed_bonus_choices(provider,None,self.result,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda s:None)
        self.assertEqual(provider._test_mode_once.call_count,2)
        self.assertEqual(self.rows()[0]['covered_options'],['0','1','2'])
        self.assertEqual(self.result.status,'OK')

    def test_nine_option_labeled_menu_receives_full_automatic_coverage(self):
        import threading
        from types import SimpleNamespace
        from unittest.mock import patch
        from tester_spin.providers.pragmatic_bonus_coverage import expand_observed_bonus_choices
        domain=list(map(str,range(9)))
        signature='PRAGMATIC:bonus-choice:bgt=69:choices=0,1,2,3,4,5,6,7,8:family=buy'
        self.add(signature=signature,domain=domain)
        choices=iter(domain[1:])
        def execute(*args,**kwargs):
            self.add(number=kwargs['attempt_number'],selected=next(choices),signature=signature,domain=domain)
            return self.result.attempts.pop()
        provider=SimpleNamespace(base_bet=2,_test_mode_once=execute,_write_json=lambda *args:None)
        catalog=SimpleNamespace(enabled=lambda:[SimpleNamespace(id='SPIN')])
        with patch('tester_spin.providers.pragmatic_modes.discover_modes',return_value=catalog):
            expand_observed_bonus_choices(provider,None,self.result,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda s:None)
        self.assertEqual(self.rows()[0]['covered_options'],domain)
        self.assertEqual(self.result.status,'OK')

    def test_catalog_metadata_reflects_final_expansion_result(self):
        import threading
        from unittest.mock import patch
        from tester_spin.models import Game
        from tester_spin.providers.pragmatic_hybrid import PragmaticProvider, _EndpointPragmaticProvider
        provider=PragmaticProvider(self.root)
        game=Game('pragmatic','test','Test','https://example.invalid')
        self.result.run_dir=None
        def expand(*args,**kwargs):
            self.result.requested_spins=3
            self.result.status='CANCELADO'
            return self.result
        with patch.object(_EndpointPragmaticProvider,'test_game',return_value=self.result), \
             patch('tester_spin.providers.pragmatic_reel_coverage.expand_reel_choices',side_effect=lambda p,g,r,**kw:r), \
             patch('tester_spin.providers.pragmatic_bonus_coverage.expand_observed_bonus_choices',side_effect=expand):
            provider.test_game(game,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda s:None)
        metadata=json.loads((provider.game_dir(game)/'game.json').read_text())['last_test']
        self.assertEqual(metadata['status'],'CANCELADO')
        self.assertEqual(metadata['requested_mode_attempts'],3)
