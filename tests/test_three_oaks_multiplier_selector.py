from tester_spin.providers.three_oaks.special_inputs import transformed_purchase_inputs
from tester_spin.providers.three_oaks.runtime import play_fields
SOURCE='function actBuyFeature(type){app.model.setFreespinsBuyingPrice(app.model.getBuyFeatureMultiplier(type));var params={};params.bet_per_line=GR.UI.model.get("bet_per_line");params.lines=app.model.settingsLines()[0];params.selected_mode=type;app.controllers.flow.act(constants.FLOW_ACTIONS.BUY_SPIN,params)};GameModel.prototype.getBuyFeatureMultiplier=function(type){if(this.isOldBack()){return this._get("settings.buy_bonus_price",[])[type]}return this._get("settings.buy_bonus_prices.".concat(type+1),null)};'
DATA={'context':{'current':'spins','actions':['spin','buy_spin'],'available_buy_bonus':[1,2],'spins':{'bet_per_line':20,'lines':5}},'settings':{'buy_bonus_prices':{'1':50,'2':100},'lines':[5],'bet_factor':[5]}}
def test_current_multiplier_getter_maps_advertised_ids_to_ui_types():
    profile=transformed_purchase_inputs(SOURCE,DATA,['bet_per_line','lines'])
    assert profile is not None
    assert profile['purchase_wire_values']=={'1':{'selected_mode':0},'2':{'selected_mode':1}}
    assert play_fields(DATA,'buy_spin',2,client_profile=profile)['action']=={'name':'buy_spin','params':{'bet_per_line':20,'lines':5,'selected_mode':1}}
def test_multiplier_without_explicit_shift_remains_unrecognized():
    assert transformed_purchase_inputs(SOURCE.replace('type+1','unknownType'),DATA,['bet_per_line','lines']) is None

def test_unused_multiplier_does_not_certify_active_caller():
    source=SOURCE.replace("app.model.getBuyFeatureMultiplier(type)","app.model.getActualCost(type)")+'GameModel.prototype.getActualCost=function(type){return this._get("settings.buy_bonus_prices.".concat(type),null)};'
    assert transformed_purchase_inputs(source,DATA,["bet_per_line","lines"]) is None

def test_redefined_multiplier_is_ambiguous():
    assert transformed_purchase_inputs(SOURCE+'GameModel.prototype.getBuyFeatureMultiplier=function(type){return type};',DATA,["bet_per_line","lines"]) is None
