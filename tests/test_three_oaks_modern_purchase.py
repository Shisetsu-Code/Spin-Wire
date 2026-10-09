import copy,json,unittest
from pathlib import Path
from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.runtime import play_fields,continuation_fields
root=Path(__file__).parent/'fixtures'
class ModernPurchaseTests(unittest.TestCase):
 def test_single_purchase_uses_exact_captured_wire_shape(self):
  row=json.loads((root/'three_oaks_single_buy_har.json').read_text());source=(root/'three_oaks_modern_purchase.js').read_text();before=None;settings={}
  for step in row['steps']:
   if step['settings']:settings=step['settings']
   if step['action'] and before:
    data={'context':copy.deepcopy(before),'settings':settings};profile=client_contract(source,data=data)
    self.assertIsNotNone(profile)
    action=step['action'];name=action['name']
    if name in ('spin','buy_spin'):actual=play_fields(data,name,1 if name=='buy_spin' else None,client_profile=profile)
    else:actual=continuation_fields(data,game_slug='unseen',family='kendoo',client_profile=profile)
    self.assertIsNotNone(actual);self.assertEqual(actual['action'],action)
   if step['context']:before=step['context']
 def test_single_option_serializer_does_not_invent_selectors(self):
  row=json.loads((root/'three_oaks_single_buy_har.json').read_text());data=next({'context':s['context'],'settings':s['settings']} for s in row['steps'] if s['command']=='start');data['context']['available_buy_bonus']=[1,2]
  profile=client_contract((root/'three_oaks_modern_purchase.js').read_text(),data=data)
  self.assertIsNotNone(profile);self.assertEqual(profile['purchase_modes'],[])
 def test_renamed_bundle_has_same_contract(self):
  s=(root/'three_oaks_modern_purchase.js').read_text().replace('Y.bus','Services.bus').replace('Y.serverData','Services.serverData')
  self.assertIsNotNone(client_contract(s))
class SelectorPolicyTests(unittest.TestCase):
 def source(self,expression,prefix=''):
  base=(root/'three_oaks_modern_purchase.js').read_text()
  return base.replace('lines:Y.bus.getUI("lines")}},t)', 'lines:Y.bus.getUI("lines"),selected_mode:'+expression+'}},t)').replace(';Y.bus.sendPlayAsync({name:"buy_spin"',';'+prefix+'Y.bus.sendPlayAsync({name:"buy_spin"')
 def test_string_selector_is_preserved(self):
  data={'context':{'available_buy_bonus':[1,2]}}
  profile=client_contract(self.source('t.toString()'),data=data)
  self.assertEqual(profile['purchase_modes'],[1,2]);self.assertEqual(profile['purchase_selector_type'],'string')
 def test_numeric_ui_map_excludes_server_only_options(self):
  profile=client_contract(self.source('n[e]','BO(r={},UE,1),BO(r,GE,2),n=r,'),data={'context':{'available_buy_bonus':[1,2,3]}})
  self.assertEqual(profile['purchase_modes'],[1,2]);self.assertEqual(profile['purchase_selector_type'],'number')
 def test_version_condition_uses_the_actual_settings_mapping(self):
  source=self.source('r','var r=Y.serverData.get("version")?Number(t):String(t);')+';t.set("version",(function(t){var e;return null!==(e=t.settings.version)&&void 0!==e?e:null}));'
  for version,expected in [(None,'string'),('2','number')]:
   profile=client_contract(source,data={'context':{'available_buy_bonus':[1,2]},'settings':{'version':version}})
   self.assertEqual(profile['purchase_selector_type'],expected)
 def test_unknown_selector_type_is_visible_but_not_executable(self):
  profile=client_contract(self.source('unknownSelector()'),data={'context':{'available_buy_bonus':[1,2]}})
  self.assertTrue(profile['purchase_ui_observed']);self.assertEqual(profile['purchase_modes'],[])
class LegacyUIEvidenceTests(unittest.TestCase):
 def test_shared_core_buy_handler_does_not_prove_a_purchase(self):
  source='BUY_SPIN:"buy_spin";this.setActionHandler(_constants.FLOW_ACTIONS.BUY_SPIN,function(args){return this._act(_constants.FLOW_ACTIONS.BUY_SPIN,args)});'
  self.assertIsNone(client_contract(source,data={'context':{'available_buy_bonus':[1,2]}}))
 def test_actual_legacy_ui_caller_proves_existence_without_guessing_shape(self):
  source='BUY_SPIN:"buy_spin";function actBuyFeature(optionType){var params={};params.bet_per_line=GR.UI.model.get("bet_per_line");params.lines=_app.default.model.gameLines();params.selected_mode=optionType.toString();_app.default.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN,params)}'
  profile=client_contract(source,data={'context':{'available_buy_bonus':[1,2]}})
  self.assertTrue(profile['purchase_ui_observed']);self.assertEqual(profile['purchase_modes'],[])

class ModernContinuationTests(unittest.TestCase):
 def test_free_spin_chain_uses_advertised_empty_action(self):
  source=(root/'three_oaks_modern_purchase.js').read_text();profile=client_contract(source)
  for current,action in [('spins','freespin_init'),('freespins','freespin'),('freespins','freespin_stop')]:
   data={'context':{'current':current,'actions':[action],'round_finished':False}}
   self.assertEqual(continuation_fields(data,game_slug='unseen',family='kendoo',client_profile=profile)['action'],{'name':action,'params':{}})
 def test_dynamic_line_index_does_not_change_wire_fields(self):
  source=(root/'three_oaks_modern_purchase.js').read_text().replace('settingsLines")[0]','settingsLines")[Y.bus.setUI("lines",t.value)]')
  self.assertEqual(client_contract(source)['spin_params'],['bet_per_line','lines'])

class AdapterPurchaseEvidenceTests(unittest.TestCase):
 def run_adapter(self,source,available):
  import tempfile,threading
  from tester_spin.providers.three_oaks.adapter import ThreeOaksProvider
  from tester_spin.models import Game
  row=json.loads((root/'three_oaks_single_buy_har.json').read_text())
  state=next({'context':step['context'],'settings':step['settings'],'status':{'code':'OK'}} for step in row['steps'] if step['command']=='start')
  state['context']['available_buy_bonus']=available
  sent=[]
  config={'options':{'queue':'fixture','token':'fixture','protocol':'goreel','wl':'demo'},'desktop':{'server_url':'https://betman-demo.head.3oaks.com/gs/unseen/desktop/fixture/demo/','client_url':'https://static.3oaks.com/gs/clients_kendoo/unseen/v1/'}}
  class Response:
   def __init__(self,text=None,data=None):self.text=text if text is not None else json.dumps(data);self.data=data
   def raise_for_status(self):pass
   def json(self):return self.data
  class HTTP:
   def get(self,url,**kwargs):return Response(text='})(window, '+json.dumps(config)+', "url");' if url.endswith('/play') else source)
   def post(self,url,**kwargs):
    payload=json.loads(kwargs['data']);sent.append(payload.get('action'))
    return Response(data={**copy.deepcopy(state),'session_id':'fixture','user':{'huid':'fixture'}})
  with tempfile.TemporaryDirectory() as directory:
   provider=ThreeOaksProvider(Path(directory));provider.http=HTTP()
   result=provider.test_game(Game('3oaks','unseen','Unseen','https://3oaks.com/game/unseen'),spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
   return result,sent
 def test_visible_unsupported_purchase_is_counted_and_remains_pending(self):
  from tester_spin.feature_summary import feature_summary
  result,sent=self.run_adapter(SelectorPolicyTests().source('unknownSelector()'),[1])
  self.assertEqual(result.status,'PARCIAL');self.assertIn('Cantidad: 1',feature_summary(result.to_dict()))
  self.assertTrue(result.discovered_modes[1]['client_observed'])
  self.assertFalse(any(a and a['name']=='buy_spin' for a in sent))
 def test_extra_server_option_is_neither_counted_nor_executed(self):
  from tester_spin.feature_summary import feature_summary
  source=SelectorPolicyTests().source('n[e]','BO(r={},UE,1),BO(r,GE,2),n=r,')
  result,sent=self.run_adapter(source,[1,2,3])
  self.assertEqual(result.status,'OK',result.error);self.assertIn('Cantidad: 2',feature_summary(result.to_dict()))
  self.assertEqual([a['params']['selected_mode'] for a in sent if a and a['name']=='buy_spin'],[1,2])
  self.assertIs(result.discovered_modes[3]['client_observed'],False)
if __name__=='__main__':unittest.main()
