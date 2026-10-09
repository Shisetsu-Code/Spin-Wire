from pathlib import Path
import unittest
from tester_spin.providers.three_oaks.client_contracts import client_contract
root=Path(__file__).parent/'fixtures'
class InputPrimitiveTests(unittest.TestCase):
 def test_legacy_spin_is_independent_of_any_purchase(self):
  profile=client_contract((root/'three_oaks_legacy_flow.js').read_text(encoding='utf-8'))
  self.assertIsNotNone(profile);self.assertEqual(profile['spin_params'],['bet_per_line','lines','bet_factor']);self.assertEqual(profile['purchase_modes'],[])
 def test_arrow_and_single_quote_serializer_has_same_spin_contract(self):
  profile=client_contract((root/'three_oaks_arrow_flow.js').read_text(encoding='utf-8'))
  self.assertIsNotNone(profile);self.assertEqual(profile['spin_params'],['bet_per_line','lines','bet_factor'])
 def test_event_bridge_spin_needs_no_purchase_or_bundle_fingerprint(self):
  profile=client_contract((root/'three_oaks_event_flow.js').read_text(encoding='utf-8'))
  self.assertIsNotNone(profile);self.assertEqual(profile['spin_params'],['bet_per_line','lines'])
 def test_bus_spin_without_buy_button_is_supported(self):
  source='sendPlayAsync:function(a,b){return(0,c.M)().bus.play(a,b)};State.bus.sendPlayAsync({name:"spin",params:{bet_per_line:State.bus.getUI("bet_per_line"),lines:State.bus.getUI("lines")}},cost);'
  profile=client_contract(source);self.assertIsNotNone(profile);self.assertEqual(profile['purchase_modes'],[])
 def test_two_equivalent_string_expressions_do_not_make_contract_unknown(self):
  source=(root/'three_oaks_modern_purchase.js').read_text(encoding='utf-8')
  source=source.replace('lines:Y.bus.getUI("lines")}},t)','lines:Y.bus.getUI("lines"),selected_mode:t.toString()}},t)')
  source+=';Y.bus.sendPlayAsync({name:"buy_spin",params:{bet_per_line:Y.bus.getUI("bet_per_line"),lines:Y.bus.getUI("lines"),selected_mode:(t+1).toString()}},cost);'
  profile=client_contract(source,data={'context':{'available_buy_bonus':[1,2,3]}})
  self.assertEqual(profile['purchase_modes'],[1,2,3]);self.assertEqual(profile['purchase_selector_type'],'string')
class LegacyPurchasePrimitiveTests(unittest.TestCase):
 def test_legacy_purchase_passes_through_certified_middleware(self):
  source=(root/'three_oaks_legacy_flow.js').read_text()
  source+=';function actBuyFeature(optionType){var params={};params.bet_per_line=GR.UI.model.get("bet_per_line");params.lines=_app.default.model.gameLines();params.selected_mode=optionType.toString();_app.default.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN,params)}'
  profile=client_contract(source,data={'context':{'available_buy_bonus':[1,2,3]}})
  self.assertEqual(profile['purchase_modes'],[1,2,3]);self.assertEqual(profile['purchase_selector_type'],'string')
  self.assertIn('bet_factor',profile['purchase_params']['1'])
 def test_arrow_method_purchase_preserves_selector_and_declared_line_source(self):
  source=(root/'three_oaks_arrow_flow.js').read_text()
  profile=client_contract(source,data={'context':{'available_buy_bonus':[1,2,3]}})
  self.assertEqual(profile['purchase_modes'],[1,2,3]);self.assertEqual(profile['purchase_value_sources']['lines'],'bet_factor_first')
 def test_mutating_continuation_is_not_certified_as_empty(self):
  from tester_spin.providers.three_oaks.code_primitives import canonical_source,empty_flow_actions
  source=(root/'three_oaks_legacy_flow.js').read_text()+';.act(_constants.FLOW_ACTIONS.RESPIN);this.setActionHandler(_constants.FLOW_ACTIONS.RESPIN,function(args){args.selected_mode=1;return this._act(_constants.FLOW_ACTIONS.RESPIN,args)});'
  self.assertNotIn('respin',empty_flow_actions(canonical_source(source)))
if __name__=='__main__':unittest.main()

class SharedRunnerPrimitiveTests(unittest.TestCase):
 def test_shared_button_overrides_unused_three_field_core_handler(self):
  source=(root/'three_oaks_legacy_flow.js').read_text()
  profile=client_contract(source,runner_source=(root/'three_oaks_shared_runner.js').read_text(),init_source='window._PROVIDER.game={name:"unseen",use:["protocol","ui"]};')
  self.assertEqual(profile['spin_params'],['bet_per_line','lines'])
  self.assertEqual(profile['spin_route'],'shared-runner-button')
 def test_custom_play_never_inherits_shared_button_contract(self):
  from tester_spin.providers.three_oaks.code_primitives import runner_spin_contract
  self.assertIsNone(runner_spin_contract((root/'three_oaks_shared_runner.js').read_text(),'window._PROVIDER.game={name:"unseen",use:["protocol","custom_play"]};'))
 def test_regex_slashes_do_not_hide_following_handlers(self):
  source='var slash=/https?:\\/\\//;'+(root/'three_oaks_legacy_flow.js').read_text()
  self.assertEqual(client_contract(source)['spin_params'],['bet_per_line','lines','bet_factor'])

class InputOriginTests(unittest.TestCase):
 def test_event_spin_uses_settings_lines_even_if_context_differs(self):
  from tester_spin.providers.three_oaks.runtime import play_fields
  profile=client_contract((root/'three_oaks_event_flow.js').read_text())
  data={'context':{'current':'spins','actions':['spin'],'spins':{'bet_per_line':10,'lines':99}},'settings':{'lines':[15]}}
  self.assertEqual(play_fields(data,'spin',client_profile=profile)['action']['params'],{'bet_per_line':10,'lines':15})
 def test_static_bracket_property_is_the_same_as_a_dot_property(self):
  from tester_spin.providers.three_oaks.code_primitives import canonical_source
  self.assertEqual(canonical_source('app["default"].model.get("bet_per_line")'),'app.default.model.get("bet_per_line")')
 def test_a_missing_getter_default_cannot_close_an_unknown_bonus_origin(self):
  from tester_spin.providers.three_oaks.runtime import continuation_fields
  data={'context':{'current':'bonus','round_finished':False,'actions':['bonus_spins_stop'],'bonus':{}}}
  profile={'continuations':{'bonus_spins_stop':{'current':'bonus','back_to':'spins'}}}
  self.assertIsNone(continuation_fields(data,game_slug='unseen',family='goreel',client_profile=profile))

class UnknownOverrideTests(unittest.TestCase):
 def test_unparsed_spin_override_disables_default_handler_certification(self):
  from tester_spin.providers.three_oaks.code_primitives import canonical_source,flow_parameters
  source=(root/'three_oaks_legacy_flow.js').read_text()+';this.setActionHandler(_constants.FLOW_ACTIONS.SPIN,customSpin);'
  self.assertIsNone(flow_parameters(canonical_source(source),'SPIN'))
 def test_unparsed_continuation_override_does_not_look_like_no_handler(self):
  from tester_spin.providers.three_oaks.code_primitives import canonical_source,empty_flow_actions
  source=(root/'three_oaks_legacy_flow.js').read_text()+';this.setActionHandler(_constants.FLOW_ACTIONS.BONUS_INIT,customBonus);'
  self.assertNotIn('bonus_init',empty_flow_actions(canonical_source(source)))
