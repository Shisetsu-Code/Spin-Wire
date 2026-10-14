import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.collection_neutral import declaration
from tester_spin.providers.yggdrasil.fight_sequence import known_sequence
BETS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_fight_sequence.json').read_text(encoding='utf-8'))
CONFIG=json.loads((Path(__file__).parent/'fixtures/yggdrasil_collection_neutral.json').read_text(encoding='utf-8'))['config']
CTX={'hunter_definition':declaration(CONFIG),'basic_coin':BETS[0]['betdata']['coin'],'basic_amount':BETS[0]['betamount'],'currency':'EUR'}
def test_complete_base_fight_ledger_and_cash_out_are_known():
    assert known_sequence(BETS,CTX)
@pytest.mark.parametrize('change',['health','rage','cash','charge','collect','free','position','unknown'])
def test_inconsistent_or_awarded_fight_sequence_stays_unknown(change):
    bets=deepcopy(BETS);cd=bets[0]['eventdata']['response']['clientData']
    if change=='health':cd['fights'][0]['werewolfHpChange']=-99
    if change=='rage':cd['collections']['leftHunter']['amount']+=1
    if change=='cash':cd['wonMoney']='99.00'
    if change=='charge':bets[1]['betamount']='0.10'
    if change=='collect':bets[-1]['wonamount']='99.00'
    if change=='free':cd['freespinsAwarded']={'Freespin':8}
    if change=='position':cd['fights'][0]['field']['column']=999
    if change=='unknown':cd['choice']=['NEXT']
    assert not known_sequence(bets,CTX)


def test_runtime_classifies_only_closed_validated_base_combat(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    payloads=iter([{'code':0,'data':{'wager':{'wagerid':'fixture-round','status':'InProgress','bets':deepcopy(BETS[:-1])}}},{'code':0,'data':{'wager':{'wagerid':'fixture-round','status':'Finished','bets':[deepcopy(BETS[-1])]}}}])
    runtime=DemoRuntime(None,'fixture-game',30,threading.Event(),gate=None)
    runtime.config={'ordinary_constraints':CTX}
    runtime.call=lambda *args,**kwargs:next(payloads)
    result=runtime.round({'coin':CTX['basic_coin'],'amount':CTX['basic_amount'],'coins':'20'},tmp_path)
    assert result['known'] is True
    assert result['base'] is True
    assert result['terminal'] is True
    assert result['collected'] is True


def test_declared_symbol_respin_does_not_require_a_fight():
    bets=json.loads((Path(__file__).parent/'fixtures/yggdrasil_collection_respin_no_fight.json').read_text(encoding='utf-8'))
    assert known_sequence(bets,CTX)

def test_no_fight_cannot_change_collection_amounts():
    bets=json.loads((Path(__file__).parent/'fixtures/yggdrasil_collection_respin_no_fight.json').read_text(encoding='utf-8'))
    bets[0]['eventdata']['response']['clientData']['collections']['leftHunter']['amount']+=1
    assert not known_sequence(bets,CTX)
