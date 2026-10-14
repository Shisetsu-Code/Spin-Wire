import pytest
from tester_spin.providers.three_oaks.runtime import play_fields
from tester_spin.providers.three_oaks import runtime
from tester_spin.providers.three_oaks.code_primitives import empty_flow_actions
from tester_spin.providers.three_oaks.client_contracts import client_contract
DATA={'context':{'current':'spins','actions':['spin','buy_spin'],'available_buy_bonus':[1,2,3,4],'spins':{'bet_per_line':5,'lines':20}},'settings':{'bets':[1,2,3,4,5],'lines':[20],'bet_factor':[20],'buy_bonus_prices':{'1':100,'3':2000,'4':5000}},'user':{'balance':100000}}
PROFILE={'spin_params':['bet_per_line','lines']}
def test_zero_lines_announced_by_server_is_valid():
    data={**DATA,'context':{**DATA['context'],'spins':{'bet_per_line':10,'lines':0}},'settings':{**DATA['settings'],'lines':[0]}}
    assert play_fields(data,'spin',client_profile=PROFILE)['action']['params']=={'bet_per_line':10,'lines':0}
def test_unannounced_zero_lines_stays_invalid():
    data={**DATA,'context':{**DATA['context'],'spins':{'bet_per_line':10,'lines':0}}}
    with pytest.raises(ValueError):play_fields(data,'spin',client_profile=PROFILE)
def test_collect_uses_proven_empty_flow_dispatch():
    source='params:args||{};EventsGame.play(action);handlers[action]||function(args){return flow._act(action,args)};app.controllers.flow.act("collect_win");'
    assert empty_flow_actions(source)['collect_win']['currents']==['spins','freespins']
def test_collect_rejects_custom_argument_handler():
    source='params:args||{};EventsGame.play(action);handlers[action]||function(args){return flow._act(action,args)};app.controllers.flow.act("collect_win");flow.setActionHandler("collect_win",function(args){args.x=1;return flow._act("collect_win",args)});'
    assert 'collect_win' not in empty_flow_actions(source)
def test_expensive_purchase_lowers_only_to_advertised_bet():
    assert hasattr(runtime,'affordable_purchase_fields')
    fields=play_fields(DATA,'buy_spin',3,client_profile=PROFILE)
    actual=runtime.affordable_purchase_fields(DATA,fields,3)
    assert actual['action']['params']['bet_per_line']==2
    assert fields['action']['params']['bet_per_line']==5
    assert actual['action']['params']['selected_mode']==3
def test_unaffordable_minimum_is_explicit():
    assert hasattr(runtime,'affordable_purchase_fields')
    data={**DATA,'user':{'balance':99999}}
    with pytest.raises(ValueError,match='DEMO_BALANCE_INSUFFICIENT'):runtime.affordable_purchase_fields(data,play_fields(data,'buy_spin',4,client_profile=PROFILE),4)
def test_paid_feature_maps_only_explicit_server_options():
    source='sendPlayAsync:function(a,b){return x.bus.play(a,b)};x.bus.sendPlayAsync({name:"spin",params:{bet_per_line:x.bus.getUI("bet_per_line"),lines:x.bus.getUI("lines")}},e);x.bus.sendPlayAsync({name:"buy_spin",params:{bet_per_line:x.bus.getUI("bet_per_line"),lines:x.bus.getUI("lines"),paid_feature:{1:"fs",2:"sfs"}[t]}},e);'
    profile=client_contract(source,DATA)
    assert profile['purchase_modes']==[1,2]
    assert play_fields(DATA,'buy_spin',2,client_profile=profile)['action']['params']=={'bet_per_line':5,'lines':20,'paid_feature':'sfs'}

def test_zero_lines_from_explicit_settings_source():
    data={**DATA,'context':{**DATA['context'],'spins':{'bet_per_line':10,'lines':0}},'settings':{**DATA['settings'],'lines':[0]}}
    profile={**PROFILE,'spin_value_sources':{'lines':'settings_lines_first'}}
    assert play_fields(data,'spin',client_profile=profile)['action']['params']['lines']==0

MODERN='params:args||{};EventsGame.play(action);flow.setActionHandler(C.BUY_SPIN,e=>((e=e||{}).bet_per_line="bet_per_line"in e?e.bet_per_line:this.app.model.betPerLine(),e.lines="lines"in e?e.lines:this.app.model.gameLines(),e.bet_factor="bet_factor"in e?e.bet_factor:this.app.model.betFactor()[0],this.app.model.setBetPerLine(e.bet_per_line),this.app.model.setLines(e.lines),this.app.model.setBetFactor(e.bet_factor),this._act(C.BUY_SPIN,e,this.app.model.freespinsBuyingPrice()*this.app.model.getRoundBet(e.bet_per_line,e.bet_factor))));class Shop{actBuyFeature(e){var t;let i={};i.bet_per_line=j.UI.model.get("bet_per_line"),i.lines=app.model.gameLines(),i.selected_mode=e,null==(t=app.controllers)||t.flow.act(C.BUY_SPIN,i)}}'
def test_modern_optional_controller_keeps_all_purchase_modes():
    profile=client_contract(MODERN,DATA)
    assert profile is not None and profile['purchase_modes']==[1,2,3,4]
    assert profile['purchase_params']['3']==['bet_per_line','lines','bet_factor','selected_mode']
def test_modern_handler_with_extra_parameter_remains_unsupported():
    profile=client_contract(MODERN.replace('this.app.model.setLines(e.lines)', 'e.extra=1,this.app.model.setLines(e.lines)'),DATA)
    assert profile is None or not profile['purchase_modes']

def test_modern_bridge_binds_action_and_parameter_arguments():
    source=MODERN.replace('params:args||{};EventsGame.play(action);','_act(e,t,i=null){let s={action:{name:e,params:t||{}},bet:i};return j.EventsGame.play(s),this.deferred.promise}')
    profile=client_contract(source,DATA)
    assert profile is not None and profile['purchase_modes']==[1,2,3,4]

def test_modern_default_dispatch_supports_empty_collect():
    source='_act(e,t,i=null){let s={action:{name:e,params:t||{}},bet:i};return j.EventsGame.play(s),this.deferred.promise}getActionHandler(e){return this.handlers[e]||(t=>this._act(e,t))}app.controllers.flow.act(C.COLLECT_WIN);'
    assert empty_flow_actions(source)['collect_win']['currents']==['spins','freespins']
