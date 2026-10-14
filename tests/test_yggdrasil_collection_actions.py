import json
from copy import deepcopy
from pathlib import Path
from tester_spin.providers.yggdrasil.collection_actions import ordinary_collection_actions
ROW=json.loads(Path('tests/fixtures/yggdrasil_collection_actions.json').read_text())
def test_current_paid_coin_collection_counter_is_non_awarded_base_animation():
    assert ordinary_collection_actions(ROW)
def test_awarded_feature_foreign_coin_or_unmatched_counter_is_unknown():
    for damage in ['award','coin','counter','unknown']:
        row=deepcopy(ROW)
        if damage=='award':row['eventdata']['boostData']['freeSpinsEntered']=True
        elif damage=='coin':row['betdata']['coin']='0.02'
        elif damage=='counter':row['eventdata']['response']['clientData']['actions'][-1]['counters'][0]['value']=99
        else:row['eventdata']['response']['clientData']['actions'].append({'name':'unknown'})
        assert not ordinary_collection_actions(row)


def test_rejected_collection_award_cannot_fall_back_to_board_animation():
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    row=deepcopy(ROW)
    row['eventdata']['boostData']['freeSpinsEntered']=True
    row['eventdata']['response']['clientData']={'actions':[{'name':'stopReels','board':[['A']]}]}
    assert not ordinary_round({'bets':[row]})


def test_saver_keeps_revalidatable_collection_envelope(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    row=deepcopy(ROW);row.update(step=1,status='RESULTED')
    runtime=DemoRuntime(None,'fixture',1,threading.Event(),gate=None)
    runtime.save(tmp_path,1,{'coin':'0.01','amount':'0.2'},{'wagerid':'fixture','status':'Finished','terminal':True,'commands':[],'bets':[row]})
    saved=json.loads((tmp_path/'step-001-response.json').read_text())['ordinary_collection_outcomes'][0]
    assert ordinary_collection_actions(saved)
    assert 'initialBalance' not in saved['betdata']


def test_malformed_collection_state_cannot_escape_schema_dispatch():
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    row=deepcopy(ROW);row['eventdata']['initialPlayerState']=[];row['eventdata']['playerState']=[]
    row['eventdata']['boostData']['freeSpinsEntered']=True
    row['eventdata']['response']['clientData']={'actions':[{'name':'stopReels','board':[['A']]}]}
    assert not ordinary_round({'bets':[row]})


def test_unchanged_collection_state_needs_no_counter_animation():
    row=deepcopy(ROW)
    row['eventdata']['initialPlayerState']=deepcopy(row['eventdata']['playerState'])
    row['eventdata']['response']['clientData']['actions']=[a for a in row['eventdata']['response']['clientData']['actions'] if a['name']!='setCounters']
    assert ordinary_collection_actions(row)
    row['eventdata']['initialPlayerState']['collectionsMap']['BASIC']['0.0100']['progress']+=1
    assert not ordinary_collection_actions(row)


def test_completed_cash_collection_is_an_ordinary_award():
    row=json.loads(Path('tests/fixtures/yggdrasil_collection_cash_win.json').read_text())
    assert ordinary_collection_actions(row)
    for damage in ['collector','price','future']:
        bad=deepcopy(row)
        action=next(a for a in bad['eventdata']['response']['clientData']['actions'] if a.get('type')=='collection')
        if damage=='collector':action['wins'][0]['collectors'][0]['column']=99
        elif damage=='price':action['wins'][0]['value']['cash']+=1
        else:bad['eventdata']['boostData']['freeSpinsEntered']=True
        assert not ordinary_collection_actions(bad)


def test_historical_collection_buckets_must_belong_to_current_server_domain():
    row=deepcopy(ROW)
    for key in ('initialPlayerState','playerState'):
        row['eventdata'][key]['collectionsMap']['BB_0']=deepcopy(row['eventdata']['playerState']['collectionsMap']['BASIC'])
    assert not ordinary_collection_actions(row)
    assert ordinary_collection_actions(row,{'collection_modes':['BASIC','BB_0']})
    assert not ordinary_collection_actions(row,{'collection_modes':['BASIC','GB']})


def test_cash_collection_response_and_symbol_values_must_be_consistent():
    row=json.loads(Path('tests/fixtures/yggdrasil_collection_cash_win.json').read_text())
    bad=deepcopy(row);bad['eventdata']['response']['cashWin']=999
    assert not ordinary_collection_actions(bad)
    bad=deepcopy(row)
    symbol=next(s for a in bad['eventdata']['response']['clientData']['actions'] if a.get('name')=='stopReels' for s in a['symbols'] if s['name']=='CASH')
    symbol.pop('value')
    assert not ordinary_collection_actions(bad)


def test_malformed_prize_list_is_unknown_instead_of_an_exception():
    row=deepcopy(ROW)
    row['eventdata']['response']['clientData']['actions'].append({'name':'showWinResults','type':'regular','wins':None})
    assert not ordinary_collection_actions(row)
