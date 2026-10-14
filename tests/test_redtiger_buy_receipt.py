import unittest,json,copy
from decimal import Decimal
from pathlib import Path
from tester_spin.providers.redtiger.runtime import FeatureBuy,purchase_executed
class BuyReceiptTests(unittest.TestCase):
 def test_captured_purchases_have_debit_and_feature_evidence(self):
  rows=json.loads((Path(__file__).parent/'fixtures/redtiger_oct12_buys.json').read_text(encoding='utf-8'))
  for row in rows:
   with self.subTest(capture=row['capture']):
    self.assertTrue(purchase_executed(row['response'],row['request'],FeatureBuy('FreeSpins',Decimal(100))))
 def test_ignored_selector_or_missing_debit_cannot_cover_purchase(self):
  row=json.loads((Path(__file__).parent/'fixtures/redtiger_oct12_buys.json').read_text(encoding='utf-8'))[0]
  for missing in ['feature','debit']:
   response=copy.deepcopy(row['response'])
   if missing=='feature':response['result']['game']={'spinMode':'Normal','features':[],'hasState':False}
   else:response['result']['user']['balance']['cash']['afterBet']=response['result']['user']['balance']['cash']['atStart']
   self.assertFalse(purchase_executed(response,row['request'],FeatureBuy('FreeSpins',Decimal(100))))
