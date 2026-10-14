import pytest
from tester_spin.providers.yggdrasil.runtime import configuration,Unsupported

def data(minimum=25,maximum=25):
 return {'gameid':'fixture','cfg':{'props':[{'prop':'Modes','value':{'BASIC':{'coinsPerBet':25}}},{'prop':'MinCoins','value':minimum},{'prop':'MaxCoins','value':maximum},{'prop':'Paylines','value':[[1,1,1,1,1]]}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.01'}}

def test_fixed_server_coin_domain_is_independent_of_payline_quantity():
 cfg=configuration(data(),'fixture','EUR')
 assert cfg['templates']['BASIC']['amount']=='0.25'
 assert cfg['templates']['BASIC']['coins']=='25'
 assert cfg['classic_line_quantity'] is False
 assert not cfg['unresolved']

@pytest.mark.parametrize('minimum,maximum',[(None,None),(24,24),(24,26),(True,True),('bad',25),(25,False)])
def test_missing_inconsistent_or_variable_coin_domain_is_not_assumed(minimum,maximum):
 with pytest.raises((Unsupported,ValueError)):
  configuration(data(minimum,maximum),'fixture','EUR')

def test_null_server_settings_remain_explicitly_unresolved():
 d=data();d['orgSettings']=None;d['extraOrgSettings']=None
 cfg=configuration(d,'fixture','EUR')
 assert not cfg['templates']
 assert 'BASIC' in cfg['unresolved']
