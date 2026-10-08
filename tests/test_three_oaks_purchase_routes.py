"""Wire-route regressions reduced from current public demo clients, no sessions."""
import json
from pathlib import Path
import unittest
from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.runtime import play_fields
from test_three_oaks_active_flow import state

FIXTURES=Path(__file__).parent/'fixtures'
CALLS=json.loads((FIXTURES/'three_oaks_purchase_route_calls.json').read_text())


def client(kind):
    core=(FIXTURES/'three_oaks_compact_preserve_flow.js').read_text()
    # Preserve the real shared middleware but remove its unrelated purchase UI.
    start=core.index('actBuyFeature('); end=core.index('\nget BONUS_STOP',start)
    core=core[:start]+core[end:]
    return core+';'+CALLS[kind]['caller']+';'+CALLS[kind]['settings_getter']


class PurchaseRouteTests(unittest.TestCase):
    def fields(self, source, data, option):
        profile=client_contract(source,data=data)
        self.assertIn(option,(profile or {}).get('purchase_modes',[]))
        return play_fields(data,'buy_spin',option,client_profile=profile)['action']['params']

    def test_inline_object_purchase_keeps_server_option_identity(self):
        p=self.fields(client('grand'),state([1,2]),2)
        self.assertEqual(p,{'bet_per_line':2,'lines':25,'bet_factor':10,'selected_mode':2})

    def test_optional_controller_alias_is_bound_before_dispatch(self):
        p=self.fields(client('lucky_penny_powerscatter'),state([1,2,3]),3)
        self.assertEqual(p['selected_mode'],3)

    def test_unbound_optional_controller_is_not_certified(self):
        source=client('lucky_penny_powerscatter').replace('(t=Uo.controllers)','(t=unknownService)')
        profile=client_contract(source,data=state([1,2,3]))
        self.assertFalse((profile or {}).get('purchase_modes'))

    def test_animation_callback_purchase_keeps_string_selector(self):
        self.assertEqual(self.fields(client('space_coins'),state([1,2]),2)['selected_mode'],'2')

    def test_settings_guard_resolves_selected_mode_branch(self):
        p=self.fields(client('lucky_penny'),state([1,2]),1)
        self.assertEqual(p['selected_mode'],1)
        self.assertEqual(p['lines'],10)
        self.assertNotIn('buy_spin_type',p)

    def test_settings_guard_resolves_legacy_wire_field_without_guess(self):
        data=state([1,2]);data['settings']['freespins_buying_price_by_buy_spin_type']={'1':80}
        p=self.fields(client('lucky_penny'),data,2)
        self.assertEqual(p['buy_spin_type'],2)
        self.assertNotIn('selected_mode',p)

    def test_last_selected_mode_assignment_uses_current_version(self):
        source=client('super_china_pots');data=state([1,2,3,4])
        self.assertIs(type(self.fields(source,data,4)['selected_mode']),int)
        data['settings']['buy_bonus_price_1']=80
        self.assertIs(type(self.fields(source,data,4)['selected_mode']),str)

    def test_literal_paid_feature_map_selects_exact_wire_strings(self):
        source='sendPlayAsync:function(e,t){return Y.bus.play(e,t)};'+CALLS['super_sticky_piggy']['caller']
        for option,value in [(1,'fs'),(2,'sfs')]:
            with self.subTest(option=option):
                p=self.fields(source,state([1,2]),option)
                self.assertEqual(p,{'bet_per_line':2,'lines':25,'paid_feature':value})

    def test_literal_map_does_not_extend_to_unmapped_server_option(self):
        source='sendPlayAsync:function(e,t){return Y.bus.play(e,t)};'+CALLS['super_sticky_piggy']['caller']
        profile=client_contract(source,data=state([1,2,3]))
        self.assertEqual(profile['purchase_modes'],[1,2])

    def test_buy_disabled_by_ante_guard_uses_the_proven_neutral_payload(self):
        p=self.fields(client('lady_fortune'),state([1,2,3]),2)
        self.assertEqual(p['buy_spin_scatters_count'],5)
        self.assertEqual(p['ante_bet'],0)
        self.assertNotIn('selected_mode',p)

    def test_neutral_client_toggle_omits_conditional_ante(self):
        p=self.fields(client('lava_coins_2'),state([1,2,3]),3)
        self.assertEqual(p['selected_mode'],3)
        self.assertNotIn('ante_bet',p)

    def test_ante_default_is_not_assumed_without_constructor_evidence(self):
        source=client('lava_coins_2').replace('this.active=false','this.active=unknown()')
        profile=client_contract(source,data=state([1,2,3]))
        self.assertFalse((profile or {}).get('purchase_modes'))

    def test_neutral_contract_rejects_active_server_ante_state(self):
        data=state([1,2,3]);profile=client_contract(client('lady_fortune'),data=data)
        data['context']['last_args']={'ante_bet':2}
        with self.assertRaises(ValueError):
            play_fields(data,'buy_spin',1,client_profile=profile)

    def test_conditional_unknown_param_is_never_silently_discarded(self):
        source=client('space_coins').replace('params.lines=', 'if(unknownState){params.different=1};params.lines=')
        profile=client_contract(source,data=state([1,2]))
        self.assertFalse((profile or {}).get('purchase_modes'))

if __name__=='__main__':unittest.main()
