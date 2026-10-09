import json,unittest,copy
from pathlib import Path
from tester_spin.providers.three_oaks.runtime import play_fields,continuation_fields
from tester_spin.providers.three_oaks.client_contracts import client_contract
root=Path(__file__).parent/'fixtures'
class ClientContractTests(unittest.TestCase):
 def test_captured_actions_match_without_using_title(self):
  registry=json.loads((root/'three_oaks_client_contracts.json').read_text())['clients']
  for row in json.loads((root/'three_oaks_oct7_har.json').read_text(encoding='utf-8')):
   profile=registry[row['source_hashes'][0]];before=None;settings={}
   for step in row['steps']:
    if step['settings']:settings=step['settings']
    action=step['action']
    if action and before:
     data={'context':copy.deepcopy(before),'settings':settings}
     if action['name'] in ('spin','buy_spin'):
      data['context'][data['context']['current']].update({k:v for k,v in action['params'].items() if k in ('bet_per_line','lines')})
      actual=play_fields(data,action['name'],int(action['params']['selected_mode']) if 'selected_mode' in action['params'] else None,game_slug='unseen',family='goreel',client_profile=profile)
     else:actual=continuation_fields(data,game_slug='unseen',family='goreel',client_profile=profile)
     with self.subTest(source=row['slug'],action=action):
      self.assertIsNotNone(actual)
      self.assertEqual(actual['action'],action)
    if step['context']:before=step['context']
 def test_changed_unrelated_assets_keep_same_purchase_contract(self):
  source=(root/'three_oaks_purchase_serializer.js').read_text(encoding='utf-8')
  profile=client_contract(source+';var unrelatedAssetVersion=20261007;')
  self.assertIsNotNone(profile)
  self.assertEqual(profile['purchase_modes'],[1,2])
  self.assertEqual(profile['contract_source'],'accepted-har-with-current-client-handlers')
 def test_changed_purchase_handler_or_transport_is_not_certified(self):
  source=(root/'three_oaks_purchase_serializer.js').read_text(encoding='utf-8')
  for changed in (source.replace('optionType.toString()','optionType'),source.replace('params:args||{}','params:other||{}'),source.replace('args.bet_factor=','args.changed_factor=')):
   with self.subTest(source=changed):
    profile=client_contract(changed) or {}
    self.assertFalse(profile.get('spin_params'))
    self.assertEqual(profile.get('purchase_modes',[]),[])
    self.assertEqual(profile.get('purchase_params',{}),{})
    self.assertNotIn(profile.get('contract_source'),('accepted-official-client-har','accepted-har-with-current-client-handlers'))
 def test_unknown_client_stays_unknown(self):
  self.assertIsNone(client_contract('bet_per_line lines spin buy_spin'))
 def test_same_legacy_serializer_new_build_is_supported(self):
  source=(root/'three_oaks_legacy_serializer.js').read_text(encoding='utf-8')+'\n// different build'
  contract=client_contract(source)
  self.assertIsNotNone(contract)
  self.assertEqual(contract['contract_source'],'current-client-serializer')
if __name__=='__main__':unittest.main()
