import json
from copy import deepcopy
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.runtime import ordinary_round
BET=json.loads((Path(__file__).parent/'fixtures/yggdrasil_respin_neutral.json').read_text(encoding='utf-8'))
CTX={'basic_coin':BET['betdata']['coin'],'basic_amount':BET['betamount'],'currency':BET['betcurrency']}
def test_zero_win_respin_profile_returns_to_base():
    assert ordinary_round({'bets':[BET]},CTX)
@pytest.mark.parametrize('field,value',[('consecutiveWins',1),('multiplier',2),('freeSpins',1),('reSpins',True),('wonCoinsBeforeMultiplier',1),('choice',['NEXT'])])
def test_active_or_unknown_respin_state_requires_review(field,value):
    bet=deepcopy(BET);bet['eventdata']['response']['clientData'][field]=value
    assert not ordinary_round({'bets':[bet]},CTX)
def test_respin_boost_flags_cannot_be_active():
    bet=deepcopy(BET);bet['eventdata']['boostData']['startedRespins']=True
    assert not ordinary_round({'bets':[bet]},CTX)
