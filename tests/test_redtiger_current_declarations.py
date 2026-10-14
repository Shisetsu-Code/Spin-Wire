import copy,json,unittest
from pathlib import Path
from tester_spin.providers.redtiger import runtime

class CurrentDeclarationsTests(unittest.TestCase):
 def test_six_captured_declarations(self):
  rows=json.loads((Path(__file__).parent/'fixtures/redtiger_oct11_declarations.json').read_text(encoding='utf-8'))
  for row in rows:
   with self.subTest(game=row['game_id']):
    domain=runtime.purchase_declaration(row['game'])
    self.assertTrue(domain['complete'])
    self.assertEqual(domain['options'],row['expected'])
 def test_missing_or_conflicting_declaration_stays_unknown(self):
  good={'hasFeatureBuy':True,'featureBuy':[{'name':'X','price':20}],'mathModes':[{'type':'featureBuy','name':'X','priceMultiplier':'20'}]}
  for key in ['hasFeatureBuy','featureBuy','mathModes']:
   value=copy.deepcopy(good);value.pop(key)
   self.assertFalse(runtime.purchase_declaration(value)['complete'])
  for value in [None,[],[{'type':'featureBuy','name':'X','priceMultiplier':'21'}],[{'type':'other','name':'X','priceMultiplier':'20'}]]:
   case=copy.deepcopy(good);case['mathModes']=value
   self.assertFalse(runtime.purchase_declaration(case)['complete'])
 def test_disabled_ignores_templates(self):
  self.assertEqual(runtime.purchase_declaration({'hasFeatureBuy':False,'featureBuy':[{'name':'Template','price':100}]})['options'],[])

 def test_current_server_contract_executes_both_buys_and_counts_once(self):
  import tempfile,threading
  from decimal import Decimal
  from types import SimpleNamespace
  from unittest.mock import patch
  from tester_spin.models import Game
  from tester_spin.feature_summary import feature_summary
  from tester_spin.providers.redtiger import execution,branch_coverage
  from tester_spin.providers.redtiger.adapter import RedTigerProvider
  from tests import test_redtiger_choice_continuation as fixtures
  game_settings={'hasFeatureBuy':True,'featureBuy':[{'name':'FreeSpins','price':50},{'name':'HoldRespins','price':20}], 'mathModes':[{'type':'featureBuy','name':'FreeSpins','priceMultiplier':'50'},{'type':'featureBuy','name':'HoldRespins','priceMultiplier':'20'}]}
  replies=[fixtures.RedTigerChoiceContinuationTests._terminal('Normal')]
  for cost in [100,40]:
   reply=fixtures.RedTigerChoiceContinuationTests._terminal('FreeSpins')
   reply['result']['game']['features']=[{'type':'bonus'}]
   reply['result']['user']={'balance':{'cash':{'atStart':'1000','afterBet':str(1000-cost)}}}
   replies.append(reply)
  session=fixtures.FakeSession(replies)
  r=SimpleNamespace(session=session,settings_url='https://g/settings',spin_url='https://g/spin',launcher_url='https://g/launch',game_id='DifferentTitle',session_id='s',token='t',user_data={},custom={},settings_request={},settings_response={'result':{'game':game_settings}},stakes=(Decimal('2'),),default_stake=Decimal('2'),currency_decimals=2,feature_buys=runtime.feature_buys_from_settings({'success':True,'result':{'game':game_settings,'user':{}}}))
  with tempfile.TemporaryDirectory() as tmp:
   p=RedTigerProvider(Path(tmp));g=Game(provider='redtiger',slug='x',name='x',url='https://example.invalid',symbol='1')
   with patch.object(execution,'bootstrap_game',return_value=r):
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
   self.assertEqual(result.feature_domains['purchase']['options'],['FreeSpins','HoldRespins'])
   self.assertIn('Cantidad: 2',feature_summary(result.to_dict()))
   self.assertEqual(result.status, 'OK', result.error)
   self.assertTrue(all(m.get('validated') is True and m.get('covered_options') == [m['feature_buy']] for m in result.discovered_modes if m.get('kind') == 'PURCHASE'))
   self.assertEqual(len(result.attempts),3)
   self.assertEqual(len(branch_coverage._base_mode_specs(result)),3)
   buys=[m for m in result.discovered_modes if m.get('kind')=='PURCHASE']
   self.assertEqual(len(buys),2)
   self.assertTrue(all(m['server_declared'] and not m['client_observed'] for m in buys))
