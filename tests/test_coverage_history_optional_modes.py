import tempfile,unittest
from pathlib import Path
from tester_spin.models import GameTestResult
from tester_spin.coverage_history import retain_pending_branches
class CoveragePolicyTests(unittest.TestCase):
 def test_history_does_not_make_unconfirmed_modes_required_again(self):
  def result(mode):return GameTestResult(provider='3oaks',slug='x',game_name='x',game_url='https://x',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',discovered_modes=[mode])
  with tempfile.TemporaryDirectory() as tmp:
   retain_pending_branches(Path(tmp),result({'id':'PURCHASE_1','kind':'PURCHASE','coverage_required':True,'required_options':['1'],'covered_options':[]}))
   now=result({'id':'PURCHASE_1','kind':'DISCOVERED_ONLY','coverage_required':False,'client_observed':False})
   retain_pending_branches(Path(tmp),now)
   self.assertIs(now.discovered_modes[0]['coverage_required'],False)
if __name__=='__main__':unittest.main()
