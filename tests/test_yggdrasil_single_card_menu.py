from pathlib import Path
import json
import pytest
from tester_spin.providers.yggdrasil.sdk_mode_roles import source_roles
from tester_spin.providers.yggdrasil.runtime import configuration,Unsupported
F=json.loads((Path(__file__).parent/'fixtures/yggdrasil_single_card_menu.json').read_text(encoding='utf-8'))
def data():return {'gameid':'fixture','cfg':{'props':[{'prop':'ApiVersion','value':'2.6.0'},{'prop':'Modes','value':F['modes']}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.01,0.02','DefaultDenom':'EUR:0.02'},'extraOrgSettings':[{'type':'BONUS1','Denoms':'EUR:1,2','DefaultDenom':'EUR:2'}]}
def test_single_card_purchase_follows_confirmed_sdk_command_and_current_prices():
 proof=source_roles(F['source'],F['modes'])
 assert proof is not None
 assert proof['roles']=={'BASIC':'SPIN','BONUS1':'BUY_BONUS'}
 assert proof['purchase_price_factors']=={'BONUS1':100}
 cfg=configuration(data(),'fixture','EUR',sdk_source=F['source'])
 assert not cfg['unresolved']
 assert cfg['templates']['BONUS1']['coin']=='1'
 assert cfg['templates']['BONUS1']['amount']=='20'
@pytest.mark.parametrize('old,new',[('BONUS1','NEW_PURCHASE'),('onFirstBonus','onOtherPurchase'),('BONUS_GAME_1','ANY_CARD')])
def test_single_card_roles_do_not_depend_on_aliases(old,new):
 source=F['source'].replace(old,new);modes={k.replace(old,new):v for k,v in F['modes'].items()}
 assert source_roles(source,modes) is not None
@pytest.mark.parametrize('old,new',[('primaryButtonAction:n','primaryButtonAction:other'),('await z.gamePlay.start()','await z.gamePlay.other()'),('if(i==="BUY")','if(i==="INFO")'),('this.bonusBought(!0)','this.bonusBought(!1)'),('z.gameState.bet.set(e/100)','z.gameState.bet.set(e/99)')])
def test_unproved_confirmations_or_request_conversion_are_rejected(old,new):
 assert source_roles(F['source'].replace(old,new),F['modes']) is None

def test_foreign_mode_and_request_coin_quantity_conflicts_are_rejected():
 assert source_roles(F['source'],{**F['modes'],'OTHER':{'coinsPerBet':20}}) is None
 assert source_roles(F['source'],{'BASIC':{'coinsPerBet':25},'BONUS1':{'coinsPerBet':25}}) is None

def test_single_card_requires_complete_server_price_domain_match():
 d=data();d['extraOrgSettings'][0]['Denoms']='EUR:1,3'
 with pytest.raises(Unsupported,match='price domain'):configuration(d,'fixture','EUR',sdk_source=F['source'])


def awarded_state():
 b=json.loads((Path(__file__).parent/'fixtures/yggdrasil_side_award.json').read_text(encoding='utf-8'))
 return {'commands':['FREESPINS'],'bets':[b],'terminal':False,'wagerid':'fixture-round','max_step':1,'root_step':1}

def test_purchase_award_starts_current_server_declared_free_spins_at_zero_cost():
 from tester_spin.providers.yggdrasil.runtime import continuation_request
 cfg=configuration(data(),'fixture','EUR',sdk_source=F['source'])
 req=continuation_request(awarded_state(),cfg['ordinary_constraints'])
 assert req=={'cmd':'FREESPINS','amount':'0','wagerid':'fixture-round','step':'2','betid':'1'}

@pytest.mark.parametrize('change',['missing_source','count','menu','price'])
def test_award_acceptance_requires_sdk_action_current_count_and_price(change):
 from tester_spin.providers.yggdrasil.runtime import continuation_request
 cfg=configuration(data(),'fixture','EUR',sdk_source=F['source']);state=awarded_state();c=cfg['ordinary_constraints']
 if change=='missing_source':c.pop('sdk_single_card_award_command',None)
 elif change=='count':state['bets'][0]['eventdata']['response']['clientData']['rounds'][0]['reels']['freeSpin']['added']=0
 elif change=='menu':state['commands']=['OTHER']
 else:state['bets'][0]['betamount']='21'
 with pytest.raises(Unsupported):continuation_request(state,c)
