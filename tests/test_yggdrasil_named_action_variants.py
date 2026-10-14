import json,copy
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.named_actions import ordinary_named_actions
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_named_action_variants.json').read_text())
@pytest.mark.parametrize('row',ROWS,ids=lambda r:r['slug'])
def test_shared_named_variants_are_ordinary(row):assert ordinary_named_actions(row['cd'])
@pytest.mark.parametrize('row',ROWS,ids=lambda r:r['slug'])
def test_active_free_spin_counter_does_not_prove_base(row):
 cd=copy.deepcopy(row['cd'])
 for a in cd['actions']:
  for c in a.get('counters',a.get('winCounters',[])):
   if c['name']=='freeSpinsWin':c['value']={'cash':1,'coins':100}
 assert not ordinary_named_actions(cd)
def test_unknown_side_or_cell_control_is_rejected():
 cd=copy.deepcopy(ROWS[2]['cd']);symbol=next(a for a in cd['actions'] if a['name']=='stopReels')['symbols'][0];symbol['side']='CHOOSE'
 assert not ordinary_named_actions(cd)
 cd=copy.deepcopy(ROWS[0]['cd']);next(a for a in cd['actions'] if a['name']=='stopReels')['board'][0][0]['choice']=1
 assert not ordinary_named_actions(cd)
