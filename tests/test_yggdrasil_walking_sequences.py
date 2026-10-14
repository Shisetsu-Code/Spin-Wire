import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.walking_sequence import known_sequence
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_walking_sequences.json').read_text(encoding='utf-8'))
CTX={'basic_coin':'0.01','basic_amount':'0.20'}
@pytest.mark.parametrize('bets',ROWS)
def test_server_closed_walking_sequence_is_known(bets):
    assert known_sequence(bets,CTX)
@pytest.mark.parametrize('change',['mask','movement','money','charge','closure','unknown'])
def test_inconsistent_walking_sequence_stays_unknown(change):
    bets=deepcopy(ROWS[0])
    if change=='mask':bets[1]['eventdata']['stickyA']='0'*15
    if change=='movement':bets[1]['eventdata']['walkingBefore']=[]
    if change=='money':bets[1]['eventdata']['accWa']='99.00'
    if change=='charge':bets[1]['betamount']='0.20'
    if change=='closure':bets.pop()
    if change=='unknown':bets[1]['eventdata']['choice']=['NEXT']
    assert not known_sequence(bets,CTX)
