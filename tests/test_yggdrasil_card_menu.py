import json
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.sdk_mode_roles import source_roles
from tester_spin.providers.yggdrasil.runtime import configuration, Unsupported

FIXTURE=json.loads((Path(__file__).parent/'fixtures/yggdrasil_card_menu.json').read_text(encoding='utf-8'))

def config(source=None):
 data={'gameid':'fixture','cfg':{'props':[{'prop':'ApiVersion','value':'2.6.0'},{'prop':'Modes','value':FIXTURE['modes']}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.01,0.02','DefaultDenom':'EUR:0.02'},'extraOrgSettings':[{'type':'BONUS1','Denoms':'EUR:1,2','DefaultDenom':'EUR:2'},{'type':'BONUS2','Denoms':'EUR:6,12','DefaultDenom':'EUR:12'}]}
 return data

def test_official_card_handlers_classify_buys_with_equal_coin_quantity():
 proof=source_roles(FIXTURE['source'],FIXTURE['modes'])
 assert proof is not None
 assert proof['roles']=={'BASIC':'SPIN','BONUS1':'BUY_BONUS','BONUS2':'BUY_BONUS'}
 assert proof['purchase_price_factors']=={'BONUS1':100,'BONUS2':600}
 result=configuration(config(),'fixture','EUR',sdk_source=FIXTURE['source'])
 assert not result['unresolved']
 assert result['templates']['BONUS1']['amount']=='10'
 assert result['templates']['BONUS2']['amount']=='60'

@pytest.mark.parametrize('old,new',[('BONUS1','OTHER_BUY'),('onFirstBonus','onDifferentPurchase'),('BONUS_GAME_1','OTHER_CARD')])
def test_roles_do_not_depend_on_command_or_handler_alias(old,new):
 source=FIXTURE['source'].replace(old,new)
 modes={k.replace(old,new):v for k,v in FIXTURE['modes'].items()}
 assert source_roles(source,modes) is not None

@pytest.mark.parametrize('old,new',[('primaryButtonAction:n','primaryButtonAction:other'),('await Ee.gamePlay.start()','await Ee.gamePlay.other()'),('if(s==="BUY")','if(s==="INFO")'),('this.bonusBought(!0)','this.bonusBought(!1)')])
def test_unproven_purchase_actions_are_rejected(old,new):
 assert source_roles(FIXTURE['source'].replace(old,new),FIXTURE['modes']) is None

def test_extra_unmapped_server_mode_is_rejected():
 assert source_roles(FIXTURE['source'],{**FIXTURE['modes'],'UNKNOWN':{'coinsPerBet':10}}) is None

@pytest.mark.parametrize('change',['denoms','default','quantity'])
def test_sdk_price_factor_requires_full_current_server_domain_agreement(change):
 data=config()
 if change=='denoms':data['extraOrgSettings'][0]['Denoms']='EUR:1,3'
 elif change=='default':data['extraOrgSettings'][0]['DefaultDenom']='EUR:1'
 else:data['cfg']['props'][1]['value']={**FIXTURE['modes'],'BONUS1':{'coinsPerBet':20}}
 with pytest.raises(Unsupported,match='price domain'):
  configuration(data,'fixture','EUR',sdk_source=FIXTURE['source'])


def award_state():
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_card_award.json').read_text(encoding='utf-8'))
 return {'commands':['FREESPINS','GAMBLE'],'terminal':False,'bets':[bet],'wagerid':'fixture-round','max_step':1,'root_step':1}

def test_current_award_menu_selects_sdk_acceptance_and_zero_charge():
 from tester_spin.providers.yggdrasil.runtime import continuation_request
 cfg=configuration(config(),'fixture','EUR',sdk_source=FIXTURE['source'])
 request=continuation_request(award_state(),cfg['ordinary_constraints'])
 assert request=={'cmd':'FREESPINS','amount':'0','wagerid':'fixture-round','step':'2','betid':'1'}

@pytest.mark.parametrize('mutation',['missing_proof','no_award','unknown_effect','extra_command'])
def test_unproven_or_malformed_award_remains_partial(mutation):
 from tester_spin.providers.yggdrasil.runtime import continuation_request
 cfg=configuration(config(),'fixture','EUR',sdk_source=FIXTURE['source'])
 state=award_state();constraints=cfg['ordinary_constraints']
 if mutation=='missing_proof':constraints={}
 elif mutation=='no_award':state['bets'][0]['eventdata']['response']['clientData']['fsMultiplier']=0
 elif mutation=='unknown_effect':state['bets'][0]['eventdata']['response']['clientData']['unknownEffect']=True
 else:state['commands'].append('OTHER')
 with pytest.raises(Unsupported):continuation_request(state,constraints)


def test_awarded_spins_may_also_pay_base_denomination_line_prize():
 from tester_spin.providers.yggdrasil.runtime import continuation_request
 cfg=configuration(config(),'fixture','EUR',sdk_source=FIXTURE['source'])
 state=award_state();state['bets']=[json.loads((Path(__file__).parent/'fixtures/yggdrasil_card_paid_award.json').read_text(encoding='utf-8'))];state['commands']=['FREESPINS']
 assert continuation_request(state,cfg['ordinary_constraints'])['cmd']=='FREESPINS'
 state['bets'][0]['eventdata']['response']['cashWin']='0.11'
 with pytest.raises(Unsupported):continuation_request(state,cfg['ordinary_constraints'])
