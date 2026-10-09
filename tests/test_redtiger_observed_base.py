import importlib.util,json,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal
from tester_spin.return_to_base import audit_scope
from tester_spin.providers.redtiger import execution
root=Path(__file__).parent/'fixtures'
from tester_spin import provider_return_checks as m
class ObservedBaseTests(unittest.TestCase):
 def proof(self,row):
  runtime=SimpleNamespace(game_id=row['game_id'],default_stake=Decimal('2'))
  with tempfile.TemporaryDirectory() as tmp,audit_scope():
   with patch.object(execution,'_post_spin',return_value=(200,{},row['response'],[])):
    return m.redtiger_check(runtime,Path(tmp),1,threading.Event())
 def test_har_normal_spins_confirm_base(self):
  for row in json.loads((root/'redtiger_base_har.json').read_text(encoding='utf-8-sig')):
   with self.subTest(game=row['game_id']):self.assertEqual(self.proof(row)['status'],'CONFIRMED')
 def test_active_and_unknown_states_remain_partial(self):
  rows=json.loads((root/'redtiger_base_har.json').read_text(encoding='utf-8-sig'))
  for row in rows:
   game=row['response']['result']['game']
   if row['game_id']=='5Families':game['barrel']['mode']='Bonus'
   else:game['state']=['unknown']
   with self.subTest(game=row['game_id']):self.assertEqual(self.proof(row)['status'],'REVIEW_REQUIRED')
if __name__=='__main__':unittest.main()
