import copy,json,tempfile,threading,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from decimal import Decimal
from tester_spin.return_to_base import audit_scope
from tester_spin.providers.redtiger import execution
from tester_spin.provider_return_checks import redtiger_check
root=Path(__file__).parent/'fixtures'
class GenericBaseTests(unittest.TestCase):
 def proof(self,row):
  runtime=SimpleNamespace(game_id='UnseenGame',default_stake=Decimal('2'))
  with tempfile.TemporaryDirectory() as tmp,audit_scope():
   with patch.object(execution,'_post_spin',return_value=(200,{},row['response'],[])):
    return redtiger_check(runtime,Path(tmp),1,threading.Event())
 def test_same_protocol_does_not_depend_on_game_name(self):
  for row in json.loads((root/'redtiger_base_har.json').read_text(encoding='utf-8-sig')):
   with self.subTest(shape=row['game_id']):
    proof=self.proof(row)
    self.assertEqual(proof['status'],'CONFIRMED')
    self.assertTrue(proof['probes'][0].get('classification',{}).get('reason'))
 def test_conflicting_feature_signals_are_never_base(self):
  rows=json.loads((root/'redtiger_base_har.json').read_text(encoding='utf-8-sig'))
  for key,value in [('features',['FreeSpins']),('spinMode','FreeSpins'),('gameMode',1),('fsp',{'remaining':3}),('choices',{'available':['A','B']})]:
   for row in rows:
    mutated=copy.deepcopy(row);mutated['response']['result']['game'][key]=value
    with self.subTest(key=key,shape=row['game_id']):self.assertEqual(self.proof(mutated)['status'],'REVIEW_REQUIRED')
 def test_persistent_state_without_normal_evidence_remains_unknown(self):
  row=json.loads((root/'redtiger_base_har.json').read_text(encoding='utf-8-sig'))[0]
  row['response']['result']['game'].pop('debugNormal',None)
  self.assertEqual(self.proof(row)['status'],'REVIEW_REQUIRED')
if __name__=='__main__':unittest.main()
