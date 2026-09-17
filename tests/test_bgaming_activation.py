import tempfile,unittest,threading
from pathlib import Path
from types import SimpleNamespace
from tester_spin.providers.bgaming.runtime import flow_continuation_command,validate_spin
from tester_spin.provider_return_checks import bgaming_check
from tester_spin.return_to_base import audit_scope

def response(feature='',state='closed',command='spin',actions=None):
    return {'api_version':'2','balance':{'wallet':1000},'outcome':{'bet':20,'win':0,'screen':[[1]]},
        'flow':{'state':state,'command':command,'available_actions':actions or ['init','spin'],
                'purchased_feature':{'name':feature} if feature else {}}}

class BGamingActivationTests(unittest.TestCase):
    def test_bonus_game_uses_explicit_advertised_command(self):
        self.assertEqual(flow_continuation_command(response(state='select_bonus',actions=['init','play_bonus_game'])),'play_bonus_game')
        self.assertEqual(flow_continuation_command(response(state='select_bonus',actions=['init','other_action'])),'')

    def test_purchase_selection_is_not_required_to_have_reels_yet(self):
        r=response(state='select_bonus',actions=['init','play_bonus_game']);r['outcome'].pop('screen')
        warnings=validate_spin(r,requested_bet=20,previous_balance_total=1000,expected_reels=None,expected_rows=None,expected_debit=0)
        self.assertEqual(warnings,[])

    def test_active_modifier_does_not_count_as_base_confirmation(self):
        samples=[response('bonus_chance'),response('bonus_chance'),response(),response()]
        calls=[]
        def send(command,**kwargs):
            calls.append(command);return SimpleNamespace(status_code=200),{'command':command},samples.pop(0)
        with tempfile.TemporaryDirectory() as tmp,audit_scope():
            proof=bgaming_check(send,{'bet':20},Path(tmp),threading.Event())
        self.assertEqual(proof['status'],'CONFIRMED');self.assertEqual(len(calls),4)

    def test_bonus_during_base_check_is_completed_first(self):
        samples=[response(state='select_bonus',actions=['init','play_bonus_game']),response(command='play_bonus_game'),response(),response()]
        calls=[]
        def send(command,**kwargs):
            calls.append(command);return SimpleNamespace(status_code=200),{'command':command},samples.pop(0)
        with tempfile.TemporaryDirectory() as tmp,audit_scope():
            proof=bgaming_check(send,{'bet':20},Path(tmp),threading.Event())
        self.assertEqual(proof['status'],'CONFIRMED');self.assertEqual(calls,['spin','play_bonus_game','spin','spin'])

    def test_api_v2_scalar_modes_can_be_probed_without_title_rules(self):
        from tester_spin.providers import bgaming_path_policy as p
        p.begin_policy_run()
        try:
            p._remember_profile(SimpleNamespace(family='api-v2',purchase_features=[]))
            modes=p._discover_purchase_modes_policy({'options':{'feature_options':{'feature_multipliers':{'base_bet':20,'bonus_chance':30,'bonus_buy':2000},'disabled_features':['bonus_buy']}}})
            self.assertEqual([m['name'] for m in modes],['bonus_chance'])
            from tester_spin.providers.bgaming_paths_v2 import _purchase_modes_guard
            guarded=_purchase_modes_guard({'options':{'feature_options':{'feature_multipliers':{'base_bet':20,'bonus_chance':30}}}})
            self.assertEqual([m['name'] for m in guarded],['bonus_chance'])
        finally:p.end_policy_run()

    def test_bundled_results_and_animation_frames_remain_separate(self):
        from tester_spin.providers.bgaming.response_rounds import response_rounds
        value=response_rounds({'outcome':{'storage':{'saved_screens':[[[1]],[[2]],[[3]]]},'spins':[{'win':1},{'win':2}]}})
        self.assertEqual(value['collections'],[{'path':'/outcome/spins','count':2,'kind':'bundled_results'}])
        self.assertEqual(value['animation_frames'],3)
        self.assertEqual(response_rounds({'outcome':None})['collections'],[])

    def test_rejected_purchase_requires_server_permission_before_probe(self):
        from tester_spin.providers.bgaming.rejected_purchase import probe_rejected_purchase
        from unittest.mock import Mock
        init=Mock(return_value=(SimpleNamespace(status_code=200),{'command':'init'},response(state='select_bonus',actions=['play_bonus_game'])))
        send=Mock()
        with tempfile.TemporaryDirectory() as tmp,audit_scope():
            proof=probe_rejected_purchase(init,send,{'bet':20},Path(tmp),threading.Event())
        send.assert_not_called();self.assertNotEqual(proof['status'],'CONFIRMED')

    def test_debit_includes_prize_instead_of_net_balance_loss(self):
        from tester_spin.providers.bgaming.runtime import infer_observed_debit
        data=response();data['balance']={'wallet':950,'game':0};data['outcome']['win']=10
        self.assertEqual(infer_observed_debit(data,1000),60)
