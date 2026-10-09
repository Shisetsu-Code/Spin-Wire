import json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import requests
from tester_spin.providers.pragmatic import PragmaticProvider
from tester_spin.providers.pragmatic_observed_transitions import automatic_fs_respin, bonus_choice

AUTO = {'na':'s','rs':'mc','rs_p':'0','rs_c':'1','rs_m':'1','tmb_win':'0.40','fs':'2','fsmax':'25'}
CHOICE = {'na':'b','g':'{bg_0:{ask:"0",bgid:"0",bgt:"69",ch_k:"fs_10_srw,fs_8_sew,fs_6_ssw",ch_v:"0,1,2",end:"0",rw:"0.00"}}'}

class ObservedTransitions(unittest.TestCase):
    def test_reward_overlay_does_not_hide_explicit_bonus_menu(self):
        state={'na':'b','g':'{R_G:{mo_tv:"150",mo_tw:"30.00",mo_wpos:"4"},bg_0:{ask:"0",bgid:"0",bgt:"69",ch_k:"fs_win,mb_win",ch_v:"201.00,-1.00",end:"0",rw:"0.00"},reels:{reel_set:"8",s:"12,4,6,2,17,9,9,12,3,3,5,9,11,4,4",sa:"6,3,7,12,5",sb:"8,5,12,5,12",sh:"3",st:"rect",sw:"5"}}'}
        choice=bonus_choice(state)
        self.assertIsNotNone(choice)
        self.assertEqual(choice['domain'],['0','1'])
        self.assertEqual(choice['fields'],{'ind':'0'})
        self.assertIsNone(bonus_choice({**state,'g':state['g'].replace('mo_tw:"30.00"','mo_tw:"NaN"')}))
        self.assertIsNone(bonus_choice({**state,'g':state['g'].replace('mo_tw:"30.00"','mo_tw:"30.00",ask:"0"')}))

    def test_reel_screen_may_also_contain_money_symbols(self):
        state={'na':'b','g':'{main:{s:"1,2",sa:"1",sb:"2",sh:"2",st:"rect",sw:"1",mo:"0,2",mo_t:"h,s"},bg_0:{ask:"0",bgid:"0",bgt:"69",ch_k:"n,y",ch_v:"0,1",end:"0",rw:"0.00"}}'}
        choice=bonus_choice(state)
        self.assertIsNotNone(choice)
        self.assertEqual(choice['domain'],['0','1'])
        self.assertIsNone(bonus_choice({**state,'g':state['g'].replace('mo_t:"h,s"','mo_t:"h,s",ask:"0"')}))

    def test_kraken_menu_selects_active_ask_table_not_flattened_choices(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_kraken2_segmented_har.json').read_text())
        state=fixture['steps'][-1]['response']
        choice=bonus_choice(state)
        self.assertIsNotNone(choice)
        self.assertEqual(choice['domain'],['0','1'])
        self.assertEqual(choice['fields'],{'ind':'0'})
        self.assertIn('ask=1',choice['branch_signature'])
        self.assertIsNone(bonus_choice({**state,'g':state['g'].replace('ask:"1"','ask:"4"')}))
        with self.assertRaises(ValueError):bonus_choice(state,override='3')
    def test_segmented_labeled_menus_reuse_active_table_for_gambling(self):
        state={'na':'b','g':'{gambling:{ask:"1",bgid:"0",bgt:"69",ch_h:"0~1",ch_k:"play,sm5s4-3,sp4s5-6;play,sp3s5-6",ch_v:"0,1,2;0,2",end:"0",level:"1",lifes:"1",rw:"0.00"}}'}
        choice=bonus_choice(state)
        self.assertIsNotNone(choice)
        self.assertEqual(choice['domain'],['0','1'])
        self.assertEqual(bonus_choice(state,override='1')['fields'],{'ind':'1'})
        self.assertIsNone(bonus_choice({**state,'g':state['g'].replace('0,1,2;0,2','0,1,2;0')}))
    def test_second_bonus_group_uses_observed_option_position(self):
        state={'na':'b','g':'{bg_0:{bgid:"0",bgt:"69",end:"1",rw:"0.00"},bg_1:{ask:"0",bgid:"1",bgt:"69",ch_k:"n,y",ch_v:"0,1",end:"0",rw:"0.00"}}'}
        self.assertEqual(bonus_choice(state)['fields'],{'ind':'0'})
        self.assertEqual(bonus_choice(state)['domain'],['0','1'])
        self.assertEqual(bonus_choice({**state,'g':state['g'].replace('ask:"0"','ask:"0",ch_h:"0~1"')})['domain'],['0','1'])
    def test_fruit_party_dynamic_cascade_uses_spin_without_reel_index(self):
        fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_fruit_party2_cascade_har.json').read_text())
        self.assertEqual(len(fixture['steps']),2)
        for step in fixture['steps']:
            self.assertEqual(step['request']['action'],'doSpin')
            self.assertNotIn('ind',step['request'])
            self.assertTrue(automatic_fs_respin(step['response']))
            self.assertFalse(automatic_fs_respin({**step['response'],'rs_more':'0'}))
            self.assertFalse(automatic_fs_respin({**step['response'],'trail':'sr~0,1'}))
    def test_preselected_bonus_enhancer_is_not_a_player_choice(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        state={'na':'b','g':'{bg_0:{ask:"0",bgid:"0",bgt:"69",ch_k:"0,1,2",ch_v:"0,1,2",end:"0",level:"0",lifes:"1",rw:"0.00",status:"0,1,0",wi:"1",wins:"0,0,0",wins_mask:"h,be,h"}}'}
        self.assertEqual(bonus_transition(state)['domain'], ['0', '2'])
        with self.assertRaises(ValueError):bonus_transition(state, override='1')
        malformed={'na':'b','g':'{bg_0:{ask:"0",bgid:"0",bgt:"69",ch_k:"0,1,2",ch_v:"0,1,2",end:"0",level:"1",lifes:"1",rw:"0.00",status:"1,1,0",ch_h:"0~0",wi:"0",wins:"0,1,0",wins_mask:"be,s,h"}}'}
        self.assertIsNone(bonus_transition(malformed))
    def test_incomplete_f_choice_is_rejected_without_exception(self):
        state={'na':'b','g':'{f:{ask:"0",bgid:"0",bgt:"69",ch_k:"f1,f2",ch_v:"1,2",end:"0",rw:"0.00"}}'}
        self.assertIsNone(bonus_choice(state))
    def test_wheel_continuation_has_no_index_or_choice_coverage(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        state={'na':'b','g':'{wheel:{bgid:"0",bgt:"69",end:"0",rw:"0.00",whms:"fs,fs;mul,mul",whnwi:"0,1",whsc:"0",whvs:"8,10;1,2",whws:"1,1;1,1"}}'}
        selection=bonus_transition(state)
        self.assertEqual(selection['fields'],{})
        self.assertEqual(selection['domain'],[])
        self.assertIsNone(bonus_transition({**state,'g':state['g'].replace('whnwi:"0,1"','whnwi:"0,2"')}))
        with self.assertRaises(ValueError):bonus_transition(state,override=0)
    def test_chilli_har_three_respin_sequence_returns_to_base(self):
        from tester_spin.provider_return_checks import pragmatic_check
        fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_chilli_respin_har.json').read_text(encoding='utf-8-sig'))
        self.assertTrue(automatic_fs_respin(fixture['steps'][0]['response']))
        with tempfile.TemporaryDirectory() as tmp:
            provider=PragmaticProvider(Path(tmp))
            responses=[step['response'] for step in fixture['steps']]*2
            provider._post_and_store=lambda *args,**kwargs:(200,b'',responses.pop(0),{})
            proof=pragmatic_check(provider,SimpleNamespace(reel_contract=None),{'na':'s'},{'symbol':'demo'},Path(tmp),1)
            self.assertEqual(proof['status'],'CONFIRMED')
    def test_completed_ordinary_cascade_is_a_base_round(self):
        from tester_spin.provider_return_checks import pragmatic_check
        with tempfile.TemporaryDirectory() as tmp:
            provider=PragmaticProvider(Path(tmp))
            base={k:v for k,v in AUTO.items() if k not in {'fs','fsmax'}}
            responses=[base,{'na':'c','rs_t':'1'},{'na':'s'}]*2
            provider._post_and_store=lambda *args,**kwargs:(200,b'',responses.pop(0),{})
            proof=pragmatic_check(provider,SimpleNamespace(reel_contract=None),{'na':'s'},{'symbol':'demo'},Path(tmp),1)
            self.assertEqual(proof['status'],'CONFIRMED')
            self.assertTrue(all(p['base'] for p in proof['probes']))

    def test_minimal_bonus_uses_observed_zero_index(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        state=json.loads((Path(__file__).parent/'fixtures/pragmatic_minimal_bonus_har.json').read_text())['before']
        self.assertEqual(bonus_transition(state)['fields'],{'ind':'0'})
        self.assertIsNone(bonus_transition({**state,'g':state['g'].replace('69','70')}))

    def test_minimal_reward_counter_collect_uses_observed_index(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_fury_collect_har.json').read_text())
        selection=bonus_transition(fixture['before'])
        self.assertIsNotNone(selection)
        self.assertEqual(selection['fields'],{'ind':fixture['request']['ind']})
        self.assertEqual(selection['selection_policy'],'observed_continuation')
        self.assertIsNone(bonus_transition(fixture['after']))
        for extra in ['rw_c:"1"','rw_c:"0",ask:"0"']:
            self.assertIsNone(bonus_transition({**fixture['before'],'g':fixture['before']['g'].replace('rw_c:"0"',extra)}))
        menu={**fixture['before'],'g':fixture['before']['g'].replace('rw_c:"0"','rw_c:"0",ask:"0",ch_k:"collect,gamble",ch_v:"0,1"')}
        self.assertEqual(bonus_transition(menu)['domain'],['0','1'])

    def test_minimal_continuation_namespaces_share_wire_contract(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_fury_collect_har.json').read_text())
        for family in ['bg','pc','pl','flat']:
            with self.subTest(family=family):
                state={**fixture['before'],'g':fixture['before']['g'].replace('bg_0:',family+':')}
                self.assertIsNotNone(bonus_transition(state))
                self.assertEqual(bonus_transition(state)['fields'],{'ind':'0'})
                self.assertIsNone(bonus_transition({**state,'g':state['g'].replace('rw_c:"0"','rw_c:"0",lifes:"3",level:"0"')}))

    def test_grid_rejects_unknown_revealed_mask(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        state=json.loads((Path(__file__).parent/'fixtures/pragmatic_pick_grid_har.json').read_text())['steps'][1]['before']
        self.assertIsNone(bonus_transition({**state,'g':state['g'].replace(',s,',',unknown,')}))

    def test_observed_grid_only_selects_hidden_positions(self):
        from tester_spin.providers.pragmatic_observed_transitions import bonus_transition
        fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_pick_grid_har.json').read_text())
        selected=[]
        for step in fixture['steps']:
            index=step['request']['ind']
            selection=bonus_transition(step['before'],override=index)
            self.assertEqual(selection['fields'],{'ind':index})
            self.assertFalse(set(selected)&set(selection['domain']))
            selected.append(index)
        self.assertIsNone(bonus_transition(fixture['steps'][-1]['after']))
        with self.assertRaises(ValueError):bonus_transition(fixture['steps'][1]['before'],override='6')
        first=fixture['steps'][0]['before']
        for changed in [first['g'].replace('level:"0"','level:"999999999999"'),first['g'].replace('bgt:"69"','bgt:"70"'),first['g'].replace('wins_mask:"h,','wins_mask:"s,')]:
            self.assertIsNone(bonus_transition({**first,'g':changed}))
    def test_auto_respin_is_not_inferred_from_rs_alone(self):
        self.assertTrue(automatic_fs_respin(AUTO))
        self.assertTrue(automatic_fs_respin({k:v for k,v in AUTO.items() if k not in {'fs','fsmax'}}))
        self.assertTrue(automatic_fs_respin({**AUTO,'rs_p':'2'}))
        self.assertTrue(automatic_fs_respin({**AUTO,'rs_p':'3'}))
        self.assertFalse(automatic_fs_respin({**AUTO,'rs_p':'-1'}))
        for changed in ({'rs':'mc'}, {**AUTO,'trail':'sr~2'}, {**AUTO,'fs':'0'}, {**AUTO,'rs_m':'2'}):
            self.assertFalse(automatic_fs_respin(changed))

    def test_automatic_cascade_accepts_grouped_currency_not_malformed_numbers(self):
        for value in ['1,200.00','12,345,678.90']:
            self.assertTrue(automatic_fs_respin({**AUTO,'tmb_win':value}))
        for value in ['12,00.00','1,2','-1,200.00','NaN']:
            self.assertFalse(automatic_fs_respin({**AUTO,'tmb_win':value}))

    def test_bonus_uses_server_choices_and_rejects_unknown_shapes(self):
        choice=bonus_choice(CHOICE)
        self.assertEqual(choice['fields'], {'ind':'0'})
        self.assertEqual(choice['domain'], ['0','1','2'])
        self.assertEqual(bonus_choice(CHOICE,override='1')['fields'], {'ind':'1'})
        self.assertIsNone(bonus_choice({'na':'b'}))
        self.assertIsNone(bonus_choice({**CHOICE,'g':CHOICE['g'].replace('69','70')}))
        with self.assertRaises(ValueError): bonus_choice(CHOICE,override='9')

    def test_f_family_sends_option_index_not_reward_value(self):
        response={'na':'b','g':'{f:{ask:"0",bgid:"0",bgt:"69",ch_k:"fm,f20,f15,f13,f10,f8,f6",ch_v:"0,2,3,5,8,10,15",end:"0",level:"0",lifes:"1",rw:"0.00"}}'}
        selection=bonus_choice(response,override='1')
        self.assertEqual(selection['fields'],{'ind':'1'})
        self.assertEqual(selection['domain'],list(map(str,range(7))))
        self.assertIsNone(bonus_choice({**response,'g':response['g'].replace('level:"0"','level:"1"')}))

    def test_live_wire_uses_observed_transitions_without_guessing(self):
        grid=json.loads((Path(__file__).parent/'fixtures/pragmatic_pick_grid_har.json').read_text())['steps'][0]['before']
        minimal={'na':'b','g':'{bg_0:{bgid:"0",bgt:"69",end:"0",rw:"0.00"}}'}
        for previous, action, expected in [(AUTO,'doSpin',None),(CHOICE,'doBonus','ind=0'),(grid,'doBonus','ind=0'),(minimal,'doBonus','ind=0')]:
            with tempfile.TemporaryDirectory() as tmp:
                response=requests.Response();response.status_code=200;response._content=b'na=s'
                response.request=requests.Request('POST','https://example.invalid').prepare()
                boot=SimpleNamespace(session=Mock(post=Mock(return_value=response)),endpoint='https://example.invalid',current_response=previous,calibration_response={},symbol='test')
                provider=PragmaticProvider(Path(tmp))
                provider._resolve_reel_contract=Mock(side_effect=AssertionError('automatic response must not request a reel contract'))
                provider._resolve_bonus_contract=Mock(side_effect=AssertionError('observed choice must not request a simple-pick contract'))
                provider._post_and_store(boot,{'action':action},Path(tmp),step=1,label='observed',timeout_s=1)
                sent=boot.session.post.call_args.kwargs['data']
                if expected: self.assertIn(expected,sent)
                else: self.assertNotIn('ind=',sent)

    def test_free_spin_choice_collects_with_do_collect_not_bonus_collect(self):
        from tester_spin.providers.pragmatic_har_states import PragmaticProvider as StateProvider
        from tester_spin.models import Game
        with tempfile.TemporaryDirectory() as tmp:
            provider=StateProvider(Path(tmp))
            boot=SimpleNamespace(session=Mock(),calibration_response={},init_response={},spin_template={},mgckey='demo',endpoint='https://example.invalid')
            provider._http_bootstrap=Mock(return_value=boot)
            provider._write_http_bootstrap=Mock()
            provider._feature_active=lambda state: bool(state.get('fs'))
            responses=[CHOICE,{'na':'s','fs':'1','fsmax':'10'},{'na':'c'},{'na':'s'}]
            actions=[]
            def post(bootstrap,fields,*args,**kwargs):
                actions.append(fields['action']);return 200,b'',responses.pop(0),{}
            provider._post_and_store=post
            mode=SimpleNamespace(id='PURCHASE_1',kind='PURCHASE',provider_bl=0,provider_pur=0)
            catalog=SimpleNamespace(base_bet=2,base_coin=.1,base_scale=20)
            result=provider._test_mode_once(Game('pragmatic','demo','Demo','https://example.invalid'),symbol='demo',cver=None,mode=mode,catalog=catalog,attempt_number=1,repetition=1,run_root=Path(tmp),timeout_s=1)
            self.assertEqual(actions,['doSpin','doBonus','doSpin','doCollect'])
            self.assertTrue(result.terminal)

    def test_normal_cascade_round_counts_as_return_to_base(self):
        from tester_spin.provider_return_checks import pragmatic_check
        with tempfile.TemporaryDirectory() as tmp:
            provider=PragmaticProvider(Path(tmp))
            provider._feature_active=lambda data: bool(data.get('rs') or data.get('fs'))
            base={k:v for k,v in AUTO.items() if k not in {'fs','fsmax'}}
            responses=[base,{'na':'c','rs_t':'1'},{'na':'s'}]*2
            provider._post_and_store=lambda *args,**kwargs:(200,b'',responses.pop(0),{})
            boot=SimpleNamespace(reel_contract={'schema':'pragmatic/manual-reel-selection/v1','trail_key':'trail','status_key':'sr'})
            proof=pragmatic_check(provider,boot,{'na':'s'},{'symbol':'demo','mgckey':'demo'},Path(tmp),1)
            self.assertEqual(proof['status'],'CONFIRMED')
            self.assertEqual(proof['consecutive_base'],2)
