import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import ordinary_round
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_board_multiplier_neutral.json').read_text(encoding='utf-8'))
def ordinary(cd):
    return ordinary_round({'bets':[{'eventdata':{'response':{'clientData':cd}}}]})
@pytest.mark.parametrize('cd',ROWS)
def test_zero_win_board_multiplier_is_ordinary(cd):
    assert ordinary(cd)
@pytest.mark.parametrize('change',['multiplier','positions','award','cash','feature','geometry'])
def test_active_or_unknown_board_multiplier_stays_pending(change):
    cd=deepcopy(ROWS[0])
    if change=='multiplier':cd['multiplier']=2
    if change=='positions':cd['winPositions']=[{'column':0,'row':0}]
    if change=='award':cd['freeSpinsAwarded']=1
    if change=='cash':cd['win']['accumulatedWonCash']='1.00'
    if change=='feature':cd['reels']['reelSetName']='freeReels1'
    if change=='geometry':cd['finalBoard'][0].pop()
    assert not ordinary(cd)
