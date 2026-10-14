import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.random_multiplier_base import ordinary
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_random_multiplier_base.json').read_text(encoding='utf-8'))
def context(bet):return {'basic_coin':bet['betdata']['coin'],'basic_amount':bet['betamount'],'currency':'EUR'}
@pytest.mark.parametrize('bet',ROWS)
def test_base_random_multiplier_with_line_money_is_ordinary(bet):
    assert ordinary(bet,context(bet))
@pytest.mark.parametrize('change',['free','active','cash','position','cap','unknown'])
def test_active_or_inconsistent_random_multiplier_stays_pending(change):
    bet=deepcopy(ROWS[0]);cd=bet['eventdata']['response']['clientData']
    if change=='free':cd['fsMultiplier']=2
    if change=='active':bet['eventdata']['boostData']['isFreeGame']=True
    if change=='cash':cd['winLinesWins'][0]=99
    if change=='position':cd['winLines'][0][0]=[999,0]
    if change=='cap':cd['maxWinReached']=True
    if change=='unknown':cd['choice']=['NEXT']
    assert not ordinary(bet,context(bet))
