import sys
from pathlib import Path

from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.code_primitives import canonical_source,flow_parameters
from tester_spin.providers.three_oaks.runtime import play_fields
FIXTURES=Path(__file__).parent/'fixtures'
OVERRIDE='var Current=require("../../slotscore/core/controllers");Object.assign(Current.FlowController.prototype,{initDefaultMiddleware:function(){this.setActionHandler(_constants.FLOW_ACTIONS.BUY_SPIN,function(args){args=args||{};args.bet_per_line="bet_per_line"in args?args.bet_per_line:this.app.model.betPerLine();args.lines="lines"in args?args.lines:this.app.model.gameLines();return this._act(_constants.FLOW_ACTIONS.BUY_SPIN,args)})}});'
CALLER='function actBuyFeature(){var params={};params.bet_per_line=GR.UI.model.get("bet_per_line");params.lines=app.model.settingsLines()[0];app.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN,params)}'
def source():return (FIXTURES/'three_oaks_legacy_flow.js').read_text(encoding='utf-8')+OVERRIDE+CALLER
def test_active_barrel_override_replaces_unused_purchase_middleware():
    assert flow_parameters(canonical_source(source()),'BUY_SPIN')==['bet_per_line','lines']
def test_single_purchase_matches_visual_capture_without_selector_or_factor():
    data={'context':{'current':'spins','actions':['spin','buy_spin'],'available_buy_bonus':[1],'spins':{'bet_per_line':5,'lines':30}},'settings':{'lines':[30],'bet_factor':[20]}}
    profile=client_contract(source(),data=data)
    assert profile['purchase_modes']==[1]
    assert play_fields(data,'buy_spin',1,client_profile=profile)['action']=={'name':'buy_spin','params':{'bet_per_line':5,'lines':30}}
def test_unrelated_controller_module_does_not_certify_override():
    changed=source().replace('../../slotscore/core/controllers','unrelated/controllers')
    assert flow_parameters(canonical_source(changed),'BUY_SPIN') is None
def test_later_handler_keeps_override_ambiguous():
    changed=source()+';this.setActionHandler(_constants.FLOW_ACTIONS.BUY_SPIN,unknownHandler);'
    assert flow_parameters(canonical_source(changed),'BUY_SPIN') is None
def test_reassigned_controller_import_does_not_certify_override():
    changed=source().replace('Object.assign(Current.FlowController.prototype','Current=unknownModule;Object.assign(Current.FlowController.prototype')
    assert flow_parameters(canonical_source(changed),'BUY_SPIN') is None
def test_replaced_middleware_after_override_remains_unknown():
    assert flow_parameters(canonical_source(source()+';Current.FlowController.prototype.initDefaultMiddleware=unknownMiddleware;'),'BUY_SPIN') is None
def test_mutated_barrel_before_override_remains_unknown():
    changed=source().replace('Object.assign(Current.FlowController.prototype','Object.assign(Current,{FlowController:unknownController});Object.assign(Current.FlowController.prototype')
    assert flow_parameters(canonical_source(changed),'BUY_SPIN') is None
def test_unrelated_core_controller_module_is_not_the_observed_library():
    assert flow_parameters(canonical_source(source().replace('../../slotscore/core/controllers','unrelated/core/controllers')),'BUY_SPIN') is None
