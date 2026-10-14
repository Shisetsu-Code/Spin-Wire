import json
from copy import deepcopy
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.respin_sequence import known_sequence
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_respin_sequence.json').read_text(encoding='utf-8'))
CTX={'basic_coin':'0.004','basic_amount':'0.10','currency':'EUR'}
@pytest.mark.parametrize('bets',ROWS)
def test_returned_respin_sequence_conserves_geometry_and_money(bets):
    assert known_sequence(bets,CTX)
@pytest.mark.parametrize('change',['charge','sum','multiplier','geometry','collect','unknown'])
def test_inconsistent_respin_sequence_stays_unknown(change):
    bets=deepcopy(ROWS[0]);cd=bets[1]['eventdata']['response']['clientData']
    if change=='charge':bets[1]['betamount']='0.10'
    if change=='sum':cd['accC']=999
    if change=='multiplier':cd['wonCoinsBeforeMultiplier']=1
    if change=='geometry':cd['colossalReel']['size']=4
    if change=='collect':bets[-1]['wonamount']='99.00'
    if change=='unknown':cd['choice']=['NEXT']
    assert not known_sequence(bets,CTX)


def test_final_server_board_must_preserve_geometry():
    bets=deepcopy(ROWS[-1]);bets[1]['eventdata']['response']['clientData']['finalBoard'][0].pop()
    assert not known_sequence(bets,CTX)
