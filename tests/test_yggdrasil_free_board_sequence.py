import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.free_board_sequence import known_sequence
BETS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_free_board_sequence.json').read_text(encoding='utf-8'))
CTX={'basic_coin':BETS[0]['betdata']['coin'],'basic_amount':BETS[0]['betamount'],'currency':'EUR'}
def test_complete_free_spin_respin_counter_and_payout():
    assert known_sequence(BETS,CTX)
@pytest.mark.parametrize('change',['counter','charge','multiplier','cash','geometry','collect','unknown'])
def test_inconsistent_free_board_sequence_stays_unknown(change):
    bets=deepcopy(BETS);cd=bets[2]['eventdata']['response']['clientData']
    if change=='counter':cd['freeSpinsLeft']-=1
    if change=='charge':bets[2]['betamount']='0.10'
    if change=='multiplier':cd['multiplier']=99
    if change=='cash':cd['win']['wonCash']='99.00'
    if change=='geometry':cd['positionShifts'][0]['origin']['column']=999
    if change=='collect':bets[-1]['wonamount']='99.00'
    if change=='unknown':cd['choice']=['NEXT']
    assert not known_sequence(bets,CTX)


def test_same_cascade_can_start_from_paid_win_without_free_spins():
    bets=json.loads((Path(__file__).parent/'fixtures/yggdrasil_paid_board_cascade.json').read_text(encoding='utf-8'))
    ctx={'basic_coin':bets[0]['betdata']['coin'],'basic_amount':bets[0]['betamount'],'currency':'EUR'}
    assert known_sequence(bets,ctx)


def test_initial_balance_metadata_does_not_hide_closed_sequence():
    bets=deepcopy(BETS);bets[0]['betdata']['initialBalance']='10000.00'
    assert known_sequence(bets,CTX)

@pytest.mark.parametrize('invalid',[True,'NaN',-1])
def test_invalid_initial_balance_requires_review(invalid):
    bets=deepcopy(BETS);bets[0]['betdata']['initialBalance']=invalid
    assert not known_sequence(bets,CTX)


@pytest.mark.parametrize('index',[-2,-1])
def test_final_acknowledgements_can_include_balance_metadata(index):
    bets=deepcopy(BETS);bets[index]['betdata']['initialBalance']='10000.00'
    assert known_sequence(bets,CTX)


@pytest.mark.parametrize('fixture,base',[('yggdrasil_paid_board_cascade.json',True),('yggdrasil_free_board_sequence.json',False)])
def test_runtime_distinguishes_closed_base_cascade_from_free_spins(fixture,base,tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    bets=json.loads((Path(__file__).parent/'fixtures'/fixture).read_text(encoding='utf-8'))
    payloads=iter([{'code':0,'data':{'wager':{'wagerid':'fixture-round','status':'InProgress','bets':bets[:-1]}}},{'code':0,'data':{'wager':{'wagerid':'fixture-round','status':'Finished','bets':[bets[-1]]}}}])
    requests=[]
    def transport(fn,body=None,query=None):
        assert fn=='play';requests.append(body);return next(payloads)
    runtime=DemoRuntime(None,'fixture-game',30,threading.Event(),gate=None)
    runtime.call=transport
    ctx={'basic_coin':bets[0]['betdata']['coin'],'basic_amount':bets[0]['betamount'],'currency':'EUR'}
    runtime.config={'ordinary_constraints':ctx}
    result=runtime.round({'coin':ctx['basic_coin'],'amount':ctx['basic_amount'],'coins':'20'},tmp_path)
    assert result['known'] is True
    assert result['base'] is base
    assert result['terminal'] is True
    assert result['collected'] is True
    assert len(requests)==2
    assert requests[-1]['cmd']=='C'
