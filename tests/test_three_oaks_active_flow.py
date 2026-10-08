"""Regressions reduced from public clients fetched by Actions 37732142044."""
import json
import unittest
from pathlib import Path
from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.code_primitives import canonical_source, flow_parameters
from tester_spin.providers.three_oaks.runtime import play_fields, continuation_fields

FIXTURES=Path(__file__).parent/'fixtures'


def override_source(kind):
    captured=json.loads((FIXTURES/'three_oaks_loaded_override.json').read_text())
    core=(FIXTURES/'three_oaks_legacy_flow.js').read_text()
    return ('bundle({1:[function(require,module,exports){'+core+'},{}],'
            '2:[function(require,module,exports){require("./controllers/FlowController");},'
            '{"./controllers/FlowController":3}],'
            '3:[function(require,module,exports){var _controllers=require("../core/controllers");'
            +captured['override']+';'+captured[kind+'_caller']+'},{}]},{},[2]);')

def state(modes):
    return {'context':{'current':'spins','actions':['spin','buy_spin'],
                       'available_buy_bonus':modes,'round_finished':True,
                       'spins':{'bet_per_line':2,'lines':25}},
            'settings':{'lines':[30],'bet_factor':[10]}}

class ActiveFlowTests(unittest.TestCase):
    def test_compact_expression_arrow_middleware_keeps_all_wire_fields(self):
        source=(FIXTURES/'three_oaks_compact_preserve_flow.js').read_text()
        self.assertEqual(flow_parameters(canonical_source(source),'SPIN'),['bet_per_line','lines','bet_factor'])

    def test_compact_ui_assignments_and_renamed_bridge_preserve_numeric_selector(self):
        data=state([1,2]);source=(FIXTURES/'three_oaks_compact_preserve_flow.js').read_text()
        profile=client_contract(source,data=data)
        self.assertIsNotNone(profile)
        self.assertEqual(profile['purchase_modes'],[1,2])
        self.assertEqual(play_fields(data,'buy_spin',2,client_profile=profile)['action']['params'],
                         {'bet_per_line':2,'lines':25,'bet_factor':10,'selected_mode':2})

    def test_compact_ui_string_conversion_is_not_dropped(self):
        data=state([1,2,3,4]);source=(FIXTURES/'three_oaks_compact_string_flow.js').read_text()
        profile=client_contract(source,data=data)
        self.assertIsNotNone(profile)
        self.assertEqual(play_fields(data,'buy_spin',4,client_profile=profile)['action']['params']['selected_mode'],'4')

    def test_compact_default_dispatcher_certifies_empty_continuations(self):
        source=(FIXTURES/'three_oaks_compact_preserve_flow.js').read_text()
        profile=client_contract(source,data=state([1,2]))
        self.assertIsNotNone(profile)
        for current,action in [('spins','bonus_init'),('bonus','respin'),('bonus','bonus_spins_stop')]:
            with self.subTest(action=action):
                data={'context':{'current':current,'round_finished':False,'actions':[action], 'bonus':{'back_to':'spins'}}}
                fields=continuation_fields(data,game_slug='unseen',family='enjoy',client_profile=profile)
                self.assertIsNotNone(fields)
                self.assertEqual(fields['action'],{'name':action,'params':{}})

    def test_entry_loaded_prototype_override_replaces_default_purchase_middleware(self):
        data=state([1]);source=override_source('single')
        profile=client_contract(source,data=data)
        self.assertIsNotNone(profile)
        self.assertEqual(profile['purchase_modes'],[1])
        self.assertEqual(play_fields(data,'buy_spin',1,client_profile=profile)['action']['params'],
                         {'bet_per_line':2,'lines':30})

    def test_entry_loaded_override_keeps_multiple_announced_selectors(self):
        data=state([1,2]);source=override_source('multiple')
        profile=client_contract(source,data=data)
        self.assertEqual(profile['purchase_modes'],[1,2])
        self.assertEqual(play_fields(data,'buy_spin',2,client_profile=profile)['action']['params'],
                         {'bet_per_line':2,'lines':30,'selected_mode':2})

    def test_unloaded_override_cannot_override_conflicting_input_contracts(self):
        source=override_source('single').replace('require("./controllers/FlowController");','')
        profile=client_contract(source,data=state([1]))
        self.assertFalse((profile or {}).get('purchase_modes'))

    def test_conditional_import_does_not_prove_override_is_active(self):
        source=override_source('single').replace('require("./controllers/FlowController");','if(false){require("./controllers/FlowController");}')
        profile=client_contract(source,data=state([1]))
        self.assertFalse((profile or {}).get('purchase_modes'))

    def test_compact_middleware_mutating_an_unknown_field_is_not_certified(self):
        source=(FIXTURES/'three_oaks_compact_preserve_flow.js').read_text().replace('this._act(bn.BUY_SPIN,e,','e.unproven=1,this._act(bn.BUY_SPIN,e,')
        profile=client_contract(source,data=state([1,2]))
        self.assertFalse((profile or {}).get('purchase_modes'))

if __name__=='__main__':unittest.main()
