import pytest
from tester_spin.providers.yggdrasil.sdk_mode_roles import source_roles
CONSTRUCTOR='createBettingModes(e){let t=[];for(const n in e)t.push({command:"BASIC"===n?"":n,type:"BASIC"===n?"BASIC":"BUY_BONUS",coinsPerBet:e[n].coinsPerBet});return t}'
MENU='getBettingModesConfigsByType("BUY_BONUS")'
def test_generic_modes_follow_sdk_constructor_and_current_server_prices():
 modes={'BASIC':{'coinsPerBet':20},'UNFAMILIAR_PURCHASE':{'coinsPerBet':1000}}
 assert source_roles(CONSTRUCTOR+MENU,modes)['roles']=={'BASIC':'SPIN','UNFAMILIAR_PURCHASE':'BUY_BONUS'}
def test_declared_golden_exclusion_separates_antebet():
 source=CONSTRUCTOR+MENU+'GOLDEN_BET_IDS=["ALT_ANTE"];filter((e=>"ALT_ANTE"!==e.type));delete t.originalData.settings.slotConfig.Modes.ALT_ANTE;'
 modes={'BASIC':{'coinsPerBet':20},'ALT_ANTE':{'coinsPerBet':40},'BUY':{'coinsPerBet':1000}}
 assert source_roles(source,modes)['roles']['ALT_ANTE']=='ANTE_BET'
@pytest.mark.parametrize('mutation',[lambda s:s.replace('BUY_BONUS','SPIN'),lambda s:s+s,lambda s:s.replace('return t','return x')])
def test_unknown_or_ambiguous_constructor_has_no_roles(mutation):
 assert source_roles(mutation(CONSTRUCTOR+MENU),{'BASIC':{'coinsPerBet':20}}) is None
def test_golden_declaration_without_exclusion_and_inconsistent_cards_rejected():
 modes={'BASIC':{'coinsPerBet':20},'EXTRA':{'coinsPerBet':40}}
 assert source_roles(CONSTRUCTOR+MENU+'GOLDEN_BET_IDS=["EXTRA"];',modes) is None
 assert source_roles(CONSTRUCTOR+MENU+'gameBonusDescriptions=[{id:"MISSING",descriptionKey:"buy"}]',modes) is None

def test_configuration_uses_source_roles_and_keeps_current_server_prices():
 from tester_spin.providers.yggdrasil.runtime import configuration
 data={'gameid':'fixture','cfg':{'props':{'ApiVersion':'2.6.0','Modes':{'BASIC':{'coinsPerBet':20},'ANY_NEW_BUY':{'coinsPerBet':1000}}}},'orgSettings':{'Denoms':'EUR:0.01'},'extraOrgSettings':[{'type':'ANY_NEW_BUY','Denoms':'EUR:0.02'}]}
 data['cfg']['props']=[{'prop':k,'value':v} for k,v in data['cfg']['props'].items()]
 data['orgSettings']['type']='BASIC'
 cfg=configuration(data,'fixture','EUR',sdk_source=CONSTRUCTOR+MENU)
 assert cfg['mode_kinds']['ANY_NEW_BUY']=='PURCHASE'
 assert cfg['templates']['ANY_NEW_BUY']['amount']=='20'
 assert not cfg['unresolved']
 assert cfg['role_source']=='sdk.dynamicModes/defaultBuy/excludedGolden/v1+server.Modes'

def test_loader_follows_current_official_launcher_and_bundle(tmp_path):
 from tester_spin.providers.yggdrasil.sdk_mode_roles import load_source
 class Response:
  status_code=200
  def __init__(self,text,url):self.text,self.url=text,url
 class HTTP:
  def get(self,url,timeout):
   if '/init/' in url:return Response('<script src="app.hash.js"></script>','https://staticdemo.yggdrasilgaming.com/999/index.html')
   return Response(CONSTRUCTOR+MENU,url)
 page='<div data-iframe-src="https://staticdemo.yggdrasilgaming.com/init/launchClient.html?org=Demo&amp;gameid=999"></div>'
 assert load_source(HTTP(),page,'999',{'BASIC':{'coinsPerBet':20}},tmp_path,1)==CONSTRUCTOR+MENU
 assert (tmp_path/'sdk-mode-role-proof.json').exists()
def test_loader_rejects_foreign_identity_before_network(tmp_path):
 from tester_spin.providers.yggdrasil.sdk_mode_roles import load_source
 class HTTP:
  def get(self,*args,**kwargs):raise AssertionError('network should not be called')
 page='<div data-iframe-src="https://evil.example/init/launchClient.html?gameid=999"></div>'
 assert load_source(HTTP(),page,'999',{'BASIC':{'coinsPerBet':20}},tmp_path,1) is None

def test_loader_accepts_large_official_bundle_with_embedded_assets(tmp_path):
 from tester_spin.providers.yggdrasil.sdk_mode_roles import load_source
 source=CONSTRUCTOR+MENU+'/*'+' '*(13*1024*1024)+'*/'
 class Response:
  status_code=200
  def __init__(self,text,url):self.text,self.url=text,url
 class HTTP:
  def get(self,url,timeout):return Response('<script src="main.js"></script>' if '/init/' in url else source,'https://staticdemo.yggdrasilgaming.com/999/index.html' if '/init/' in url else url)
 page='<div data-iframe-src="https://staticdemo.yggdrasilgaming.com/init/launchClient.html?org=Demo&amp;gameid=999"></div>'
 assert load_source(HTTP(),page,'999',{'BASIC':{'coinsPerBet':20}},tmp_path,1)==source
