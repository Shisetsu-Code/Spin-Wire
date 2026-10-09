import tempfile,threading,unittest
from pathlib import Path
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch
from tester_spin.models import Game,GameTestResult
from tester_spin.providers.redtiger import execution,branch_coverage
from tester_spin.providers.redtiger.adapter import RedTigerProvider
from tester_spin.providers.redtiger.runtime import FeatureBuy
from tests import test_redtiger_choice_continuation as fixtures
FakeSession=fixtures.FakeSession
class UnconfirmedPurchaseTests(unittest.TestCase):
 def test_server_buy_never_becomes_required_action(self):
  for features in [(),(FeatureBuy('FreeSpins',Decimal('100')), )]:
   session=FakeSession([fixtures.RedTigerChoiceContinuationTests._terminal('Normal')])
   runtime=SimpleNamespace(session=session,settings_url='https://g/settings',spin_url='https://g/spin',launcher_url='https://g/launch',game_id='Unknown',session_id='s',token='t',user_data={},custom={},settings_request={},settings_response={'result':{'game':{'hasFeatureBuy':True}}},stakes=(Decimal('2'),),default_stake=Decimal('2'),currency_decimals=2,feature_buys=features)
   with tempfile.TemporaryDirectory() as tmp:
    provider=RedTigerProvider(Path(tmp)); game=Game(provider='redtiger',slug='unknown',name='Unknown',url='https://example.invalid',symbol='1')
    with patch.object(execution,'bootstrap_game',return_value=runtime):
     result=provider.test_game(game,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    with self.subTest(features=features):
     self.assertEqual(result.status,'OK',result.error)
     self.assertEqual(len(result.attempts),1)
     self.assertEqual(len(session.calls),1)
     self.assertEqual(result.requested_spins,1)
     self.assertTrue(any(m.get('evidence_level')=='SERVER_ADVERTISED' for m in result.discovered_modes))
 def test_historic_unconfirmed_buy_cannot_be_replayed(self):
  result=GameTestResult(provider='redtiger',slug='x',game_name='x',game_url='https://g',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',discovered_modes=[{'id':'PURCHASE_X','kind':'PURCHASE','feature_buy':'X','feature_multiplier':'100'}])
  self.assertEqual(set(branch_coverage._base_mode_specs(result)),{'SPIN'})
 def test_unconfirmed_purchase_choices_do_not_create_coverage_obligation(self):
  result=GameTestResult(provider='redtiger',slug='x',game_name='x',game_url='https://g',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',discovered_modes=[{'id':'PURCHASE_X','kind':'PURCHASE','feature_buy':'X','feature_multiplier':'100'},{'id':'CHOICE_X','kind':'CHOICE_CONTINUATION','parent':'PURCHASE_X'}])
  self.assertEqual(branch_coverage._choice_parent_modes(result),set())
if __name__=='__main__':unittest.main()
