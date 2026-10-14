import unittest
from tester_spin.mechanics import classify_mechanics, mechanics_badge, merge_mechanics
class MechanicsTests(unittest.TestCase):
    def test_normal_spin_purchases_ante_and_plain_multiplier_are_not_particular(self):
        r={'discovered_modes':[{'kind':'SPIN'},{'kind':'PURCHASE'},{'kind':'ANTE_BET'},{'kind':'CHOICE_BRANCH','observed':True,'wire_command':'start'}],'multiplier':8}
        self.assertEqual(mechanics_badge(classify_mechanics(r)),'Sin datos')
    def test_remote_and_resolved_choices_are_detected(self):
        for game in [{'choices':{'selected':None,'available':['continue','collect']}},{'picker':{'options':[{'name':'Multiplier','value':2}], 'choices':[{'name':'Multiplier','option':0}]}}]:
            self.assertIn('Sí',mechanics_badge(classify_mechanics({'result':{'game':game}})))
    def test_progress_and_locked_symbols_are_indications_not_confirmed_accumulators(self):
        d=classify_mechanics({'game':{'progress':{'current':3,'next':4},'lockedTiles':[{'reel':1,'index':2}]}})
        self.assertTrue(mechanics_badge(d).startswith('Indicio'))
    def test_future_provider_can_use_shared_explicit_contract(self):
        r={'provider':'future','mechanics':{'schema':'tester-spin/mechanics/v1','items':[{'id':'accumulator','label':'Acumulador','status':'confirmed','source':'settings+rounds'}]}}
        self.assertEqual(mechanics_badge(classify_mechanics(r)),'Sí — Acumulador')
    def test_historical_positive_evidence_survives_a_short_unknown_run(self):
        old=classify_mechanics({'discovered_modes':[{'kind':'INDEXED_CHOICE','observed':True}]})
        self.assertIn('Elecciones',mechanics_badge(merge_mechanics(old,classify_mechanics({}))))
    def test_storage_keeps_older_confirmed_mechanic(self):
        import tempfile
        from pathlib import Path
        from tester_spin.storage import Storage
        from tester_spin.models import GameTestResult
        with tempfile.TemporaryDirectory() as tmp:
            storage = Storage(Path(tmp) / 'test.sqlite')
            for modes in [[{'kind': 'INDEXED_CHOICE', 'observed': True}], []]:
                storage.record_result(GameTestResult(provider='future', slug='x', game_name='X', game_url='', requested_spins=0, successful_spins=0, failed_spins=0, status='OK', discovered_modes=modes))
            self.assertEqual(mechanics_badge(storage.mechanics_history()['future::x']), 'Sí — Elecciones')

    def test_artifact_inspection_and_serialization(self):
        import tempfile, json
        from pathlib import Path
        from tester_spin.mechanics import run_mechanics
        from tester_spin.models import GameTestResult
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, 'spin-response.json').write_text(json.dumps({'game': {'choices': {'selected': None, 'available': ['continue', 'collect']}}}), encoding='utf-8')
            result = GameTestResult(provider='future', slug='x', game_name='X', game_url='', requested_spins=0, successful_spins=0, failed_spins=0, status='OK', run_dir=tmp)
            result.mechanics = run_mechanics(result.to_dict())
            self.assertEqual(mechanics_badge(result.to_dict()['mechanics']), 'Sí — Elecciones')

    def test_config_option_lists_do_not_prove_server_choice_state(self):
        self.assertEqual(mechanics_badge(classify_mechanics({'choices': {'available': ['a', 'b']}, 'progress': {'title': 'loading'}})), 'Sin datos')

    def test_malformed_optional_contract_is_ignored(self):
        self.assertEqual(mechanics_badge(classify_mechanics({'mechanics': {'schema':'tester-spin/mechanics/v1', 'items': None}, 'discovered_modes': 1})), 'Sin datos')
