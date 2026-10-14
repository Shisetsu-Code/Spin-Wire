import copy,json
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.runtime import continuation_request,validate_transition,Unsupported
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_supermeter.json').read_text())
def state(index):
 row=copy.deepcopy(ROWS[index]);b=row['bet'];cmds=(b['eventdata'].get('nextCmds') or '').split(',');return {'wagerid':'fixture','status':row['status'],'bets':[b],'commands':[v for v in cmds if v],'max_step':b['step'],'root_step':1,'terminal':row['status']=='Finished'}
def test_load_then_collect_has_sdk_wire_and_conserves_prize():
 a,b,c=[state(i) for i in range(3)]
 req=continuation_request(a)
 assert req=={'cmd':'LS','wagerid':'fixture','step':'2','betid':'1'}
 validate_transition(a,b,req)
 req=continuation_request(b)
 assert req=={'cmd':'C','amount':'0','wagerid':'fixture','step':'3','betid':'1'}
 validate_transition(b,c,req)
@pytest.mark.parametrize('field,value',[('supermeter',101),('doubleAmount','2.00'),('doubleCount',2),('doubleResult','unknown'),('nextCmds','C,S,B')])
def test_load_ack_rejects_inconsistent_meter(field,value):
 a,b=state(0),state(1);b['bets'][0]['eventdata'][field]=value
 with pytest.raises(Unsupported):validate_transition(a,b,{'cmd':'LS','step':'2','betid':'1','wagerid':'fixture'})
def test_collect_rejects_wrong_payout():
 b,c=state(1),state(2);c['bets'][0]['wonamount']='2.00'
 with pytest.raises(Unsupported):validate_transition(b,c,{'cmd':'C','amount':'0','step':'3','betid':'1','wagerid':'fixture'})

def test_neutral_sticky_base_is_ordinary_but_active_state_is_not():
 from tester_spin.providers.yggdrasil.runtime import ordinary_round
 b=json.loads((Path(__file__).parent/'fixtures/yggdrasil_supermeter_ordinary.json').read_text())
 assert ordinary_round({'bets':[b]},{'basic_coin':'0.01','basic_amount':'0.10'})
 b['eventdata']['stickyA']='100000000000000'
 assert not ordinary_round({'bets':[b]},{'basic_coin':'0.01','basic_amount':'0.10'})
