import json,tempfile,copy,unittest
from pathlib import Path
from tester_spin.models import GameTestResult
from tester_spin.coverage_history import retain_pending_branches
from tester_spin.providers.path_coverage import build_path_coverage_report
class RecurrenceHistoryTests(unittest.TestCase):
 def modes(self):
  return [{'id':'LOOP','kind':'DIAGNOSTIC','parent':'SPIN','observed':True,'executable':False,'coverage_required':False,'options':['continue','collect'],'repeat_actions':['continue'],'entry_prefix':[],'coverage_scope':'available_actions_not_all_repeat_counts','source':'choice_transition.gameData.progress.level'}, {'id':'SPIN__BRANCH_ROOT','kind':'CHOICE_BRANCH','parent':'SPIN','prefix':[],'observed':True,'executable':True,'coverage_required':True,'required_options':['continue','collect'],'covered_options':['continue','collect'],'sample_counts':{'continue':1,'collect':1},'required_samples':1}]
 def run_history(self,modes,prior):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);path=root/'coverage-history.json';path.write_text(json.dumps({'provider':'redtiger','slug':'x','pending':prior}),encoding='utf-8')
   result=GameTestResult(provider='redtiger',slug='x',game_name='x',game_url='',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',discovered_modes=modes)
   retain_pending_branches(root,result)
   return result,json.loads(path.read_text(encoding='utf-8'))
 def prior(self,prefix=None):
  return {'OLD':{'id':'OLD','kind':'CHOICE_BRANCH','parent':'SPIN','prefix':prefix or ['continue','continue'],'coverage_required':True,'required_options':['continue','collect'],'covered_options':[],'required_samples':1}}
 def test_current_closed_action_coverage_archives_old_depth_obligation(self):
  result,saved=self.run_history(self.modes(),self.prior())
  self.assertNotIn('OLD',saved['pending'])
  self.assertEqual(saved['policy_migrations'][0]['previous']['prefix'],['continue','continue'])
  self.assertTrue(build_path_coverage_report(result)['complete'])
 def test_missing_action_or_insufficient_samples_keep_old_pending(self):
  for field,value in [('covered_options',['continue']),('sample_counts',{'continue':1,'collect':0})]:
   modes=self.modes();modes[1][field]=value
   _result,saved=self.run_history(modes,self.prior())
   self.assertIn('OLD',saved['pending'])
 def test_other_prefixes_and_closing_actions_cannot_be_migrated(self):
  for prefix in [['left','continue'],['collect','continue']]:
   _result,saved=self.run_history(self.modes(),self.prior(prefix))
   self.assertIn('OLD',saved['pending'])
 def test_nested_ladder_keeps_its_entry_prefix(self):
  modes=self.modes();modes[0]['entry_prefix']=['left'];modes[1]['prefix']=['left']
  _result,saved=self.run_history(modes,self.prior(['left','continue']))
  self.assertNotIn('OLD',saved['pending'])
