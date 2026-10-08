"""Small syntax/state regressions from catalogue run 37732526583 (DEMO only)."""
import copy
import json
from pathlib import Path
import unittest
from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.code_primitives import canonical_source, flow_parameters
from tester_spin.providers.three_oaks.runtime import continuation_fields, play_fields
from test_three_oaks_active_flow import override_source, state

FIXTURES = Path(__file__).parent / 'fixtures'


def compact_source():
    return (FIXTURES / 'three_oaks_compact_preserve_flow.js').read_text()


def modern_class_override(conditional=False):
    source = compact_source()
    middleware = source.split('initDefaultMiddleware(){',1)[1].split('\n_act(',1)[0].rstrip(';\n')
    old = 'initDefaultMiddleware(){' + middleware
    new = old.replace('this.setActionHandler(bn.BUY_SPIN,e=>((e=e||{}).',
                      'this.setActionHandler(bn.BUY_SPIN,e=>((e=e||{}).',1)
    # Keep the normal spin unchanged; only replace the purchase middleware.
    prefix, buy = new.split('this.setActionHandler(bn.BUY_SPIN,',1)
    buy = buy.replace('e.bet_factor="bet_factor"in e?e.bet_factor:this.app.model.betFactor()[0],','',1)
    new = prefix + 'this.setActionHandler(bn.BUY_SPIN,' + buy
    transport = source.split('_act(e,t,i=null){',1)[1].split('\nactBuyFeature',1)[0].rstrip(';\n')
    core = 'class Flow extends Base{static get abbreviatedName(){return"flow"}' + old + '_act(e,t,i=null){' + transport + '}'
    patch = 'Object.assign(Flow.prototype,{' + new + '})'
    caller = 'actBuyFeature' + source.split('\nactBuyFeature',1)[1]
    return core + ';' + ('if(false){' + patch + '}' if conditional else patch) + ';' + caller


class CatalogueRegressionTests(unittest.TestCase):
    def test_top_level_constant_actions_keep_their_wire_identity(self):
        source = compact_source().replace('bn.SPIN','SP').replace('bn.BUY_SPIN','BUY').replace('bn.RESPIN','RE')
        source = 'const SP="spin",BUY="buy_spin",RE="respin";' + source
        profile = client_contract(source, data=state([1,2]))
        self.assertEqual(profile['spin_params'],['bet_per_line','lines','bet_factor'])
        self.assertEqual(profile['purchase_modes'],[1,2])

    def test_action_constants_after_class_declaration_are_read(self):
        source = 'class Unrelated{}const SP="spin",BUY="buy_spin";' + compact_source().replace('bn.SPIN','SP').replace('bn.BUY_SPIN','BUY')
        profile=client_contract(source,data=state([1,2]))
        self.assertEqual(profile['purchase_modes'],[1,2])

    def test_unrelated_default_export_override_is_not_a_flow_override(self):
        source = override_source('multiple').replace('},{},[2]);', ',4:[function(require,module,exports){Object.assign(Other.default.prototype,{render:function(){}})},{}]},{},[2]);')
        profile=client_contract(source,data=state([1,2]))
        self.assertEqual(profile['purchase_modes'],[1,2])

    def test_assigned_alias_is_not_treated_as_constant(self):
        source = 'const BUY="buy_spin";BUY=chooseOtherAction();' + compact_source().replace('bn.BUY_SPIN','BUY')
        profile = client_contract(source, data=state([1,2]))
        self.assertFalse((profile or {}).get('purchase_modes'))

    def test_explicit_ui_bet_factor_is_preserved(self):
        source = compact_source().replace('t.lines=Va.model.gameLines(),','t.bet_factor=Va.model.betFactor()[0],t.lines=Va.model.gameLines(),')
        profile = client_contract(source, data=state([1,2]))
        self.assertEqual(profile['purchase_modes'],[1,2])
        self.assertEqual(play_fields(state([1,2]),'buy_spin',2,client_profile=profile)['action']['params']['bet_factor'],10)

    def test_default_export_prototype_override_loaded_by_entry(self):
        source = override_source('multiple').replace('var _controllers=require("../core/controllers");',
            'var _controllers=_interopRequireDefault(require("../core/controllers/FlowController"));function _interopRequireDefault(e){return e&&e.__esModule?e:{default:e}}').replace('_controllers.FlowController.prototype','_controllers.default.prototype')
        profile = client_contract(source,data=state([1,2]))
        self.assertEqual(profile['purchase_modes'],[1,2])
        self.assertNotIn('bet_factor',profile['purchase_params']['2'])

    def test_unconditional_module_scope_class_override(self):
        profile=client_contract(modern_class_override(),data=state([1,2]))
        self.assertEqual(profile['purchase_modes'],[1,2])
        self.assertNotIn('bet_factor',profile['purchase_params']['2'])

    def test_conditional_class_override_stays_unresolved(self):
        profile=client_contract(modern_class_override(conditional=True),data=state([1,2]))
        self.assertFalse((profile or {}).get('purchase_modes'))

    def test_explicit_empty_respin_handler_is_not_limited_to_bonus(self):
        profile=client_contract(compact_source(),data=state([1,2]))
        for current in ('spins','freespins','bonus'):
            with self.subTest(current=current):
                value=continuation_fields({'context':{'current':current,'actions':['respin'],'round_finished':False}},
                    game_slug='unknown',family='goreel',client_profile=profile)
                self.assertEqual(value['action'],{'name':'respin','params':{}})

    def test_collect_win_requires_explicit_no_argument_client_call(self):
        source=compact_source()+';app.controllers.flow.act("collect_win");'
        profile=client_contract(source,data=state([1,2]))
        for current in ('spins','freespins'):
            with self.subTest(current=current):
                value=continuation_fields({'context':{'current':current,'actions':['collect_win'],'round_finished':False}},
                    game_slug='unknown',family='goreel',client_profile=profile)
                self.assertEqual(value['action'],{'name':'collect_win','params':{}})
        profile=client_contract(compact_source(),data=state([1,2]))
        self.assertIsNone(continuation_fields({'context':{'current':'spins','actions':['collect_win'],'round_finished':False}},
            game_slug='unknown',family='goreel',client_profile=profile))

    def test_context_zero_lines_is_valid_only_when_server_announces_zero(self):
        data=state([]);data['context']['spins']['lines']=0;data['settings']['lines']=[0]
        profile={'spin_params':['bet_per_line','lines']}
        self.assertEqual(play_fields(data,'spin',client_profile=profile)['action']['params']['lines'],0)
        data['settings']['lines']=[20]
        with self.assertRaises(ValueError):play_fields(data,'spin',client_profile=profile)

    def test_unknown_extra_ui_field_is_not_silently_discarded(self):
        source=compact_source().replace('t.lines=Va.model.gameLines(),','t.unresolved=1,t.lines=Va.model.gameLines(),')
        profile=client_contract(source,data=state([1,2]))
        self.assertFalse((profile or {}).get('purchase_modes'))

if __name__=='__main__':unittest.main()
