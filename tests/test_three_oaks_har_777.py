"""Regression evidence from a 63-request 777 Fruity Coins demo HAR.

No raw HAR, session identifiers, cookies, credentials or user data are committed.
The client source fragments below are public serializer excerpts.
"""
import unittest
from unittest.mock import patch

from tester_spin.providers.three_oaks.code_primitives import flow_purchase_inputs, empty_flow_actions
from tester_spin.providers.three_oaks.runtime import play_fields, continuation_fields, source_continuation_rules, base_terminal

SOURCE = '''
var BuyFeatureType=exports.BuyFeatureType={Small:0,Big:1,Small3Collect:2,Big3Collect:3};
_GameModel.default.prototype.getBuyFeatureCostByType=function(buySpineType){
var oldPrices=this._get("settings.buy_bonus_price",[]);
if(oldPrices.length>0){return oldPrices[buySpineType]}
return this._get("settings.buy_bonus_prices.".concat(buySpineType+1),null)};
function actBuyFeature(buyFeatureType){var params={};
params.bet_per_line=_GameRunnerController.GR.UI.model.get("bet_per_line");
params.lines=_app.default.model.settingsLines()[0];
params.selected_mode=buyFeatureType;
_app.default.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN,params)}
Object.defineProperty(_constants.FLOW_ACTIONS,"BONUS_STOP",{get:function get(){return"bonus_stop"}});
_app.default.controllers.flow.act(_constants.FLOW_ACTIONS.BONUS_STOP);
this.handlers[action]||function(args){return this._act(action,args)};
params:args||{};
'''
PRICES = {'1':65,'2':200,'3':150,'4':400}
DATA = {
    'settings': {'lines': [5], 'bet_factor':[1], 'buy_bonus_prices': PRICES},
    'context': {'current':'spins', 'actions':['spin','buy_spin'], 'round_finished':True,
                'available_buy_bonus':[1,2,3,4],
                'spins':{'bet_per_line':10,'lines':5}},
}

class Observed777HARTests(unittest.TestCase):
    def purchase_contract(self, source=SOURCE, data=DATA):
        with patch('tester_spin.providers.three_oaks.code_primitives.flow_parameters', return_value=['bet_per_line','lines']):
            return flow_purchase_inputs(source.replace("\n", ""), data)

    def test_four_har_buy_selectors_are_not_server_price_keys(self):
        profile = self.purchase_contract()
        self.assertEqual(profile['purchase_modes'],[1,2,3,4])
        self.assertEqual(profile['purchase_mode_values'],
                         {str(k):{'selected_mode': k-1} for k in (1,2,3,4)})
        for key, price in PRICES.items():
            with self.subTest(price_key=key,price=price):
                actual = play_fields(DATA,'buy_spin',int(key), client_profile=profile)['action']
                self.assertEqual(actual,{'name':'buy_spin','params':{
                    'bet_per_line':10,'lines':5,'selected_mode':int(key)-1}})

    def test_unproven_enum_or_price_source_does_not_run_purchase(self):
        unknown = self.purchase_contract(source=SOURCE.replace(
            'BuyFeatureType=exports.BuyFeatureType=', 'unrecognized='))
        self.assertEqual(unknown['purchase_modes'],[])
        self.assertNotIn('purchase_mode_values',unknown)
        incompatible={'context':{**DATA['context'],'available_buy_bonus':[1,2,3,4,5]},
                      'settings':DATA['settings']}
        unresolved = self.purchase_contract(data=incompatible)
        self.assertEqual(unresolved['purchase_modes'],[])
        self.assertNotIn('purchase_mode_values',unresolved)

    def test_legacy_price_array_does_not_assume_plus_one(self):
        legacy={'context':DATA['context'],
                'settings':{**DATA['settings'],'buy_bonus_price':[65,200,150,400]}}
        self.assertEqual(self.purchase_contract(data=legacy)['purchase_modes'],[])

    def test_literal_bonus_stop_is_backed_by_active_client_handler(self):
        with patch('tester_spin.providers.three_oaks.code_primitives._flow_transport', return_value=True):
            with patch('tester_spin.providers.three_oaks.code_primitives._active_flow_source', return_value=SOURCE):
                rules=empty_flow_actions(SOURCE)
        self.assertEqual(rules.get('bonus_stop'),{'current':'bonus'})
        self.assertNotIn('bonus_spins_stop',rules)
        self.assertEqual(source_continuation_rules(SOURCE)['bonus_stop'],{'current':'bonus'})

    def test_har_bonus_stop_closes_and_reenables_spins(self):
        profile={'continuations':{'bonus_stop':{'current':'bonus'}}}
        before={'context':{'current':'bonus','actions':['bonus_stop'],'round_finished':False}}
        actual=continuation_fields(before,game_slug='any',family='ratpack',client_profile=profile)
        self.assertEqual(actual['action'],{'name':'bonus_stop','params':{}})
        after={'context':{'current':'spins','actions':['spin','buy_spin'],'round_finished':True}}
        self.assertTrue(base_terminal(after))
        self.assertIsNone(continuation_fields(after,game_slug='any',family='ratpack',client_profile=profile))
        invalid={'context':{'current':'bonus','actions':['bonus_stop','respin'],'round_finished':False}}
        self.assertIsNone(continuation_fields(invalid,game_slug='any',family='ratpack',client_profile=profile))

    def test_no_literal_override_means_no_bonus_stop_action(self):
        unproven=SOURCE.replace(
            'Object.defineProperty(_constants.FLOW_ACTIONS,"BONUS_STOP",{get:function get(){return"bonus_stop"}});','')
        with patch('tester_spin.providers.three_oaks.code_primitives._flow_transport', return_value=True):
            with patch('tester_spin.providers.three_oaks.code_primitives._active_flow_source', return_value=unproven):
                rules=empty_flow_actions(unproven)
        self.assertNotIn('bonus_stop',rules)
        self.assertNotIn('bonus_stop',source_continuation_rules(unproven))
