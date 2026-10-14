import json
from pathlib import Path
from copy import deepcopy
from tester_spin.providers.yggdrasil.runtime import ordinary_round
ROW=json.loads(Path('tests/fixtures/yggdrasil_balanced_features.json').read_text())
def state(cd):return {'bets':[{'eventdata':{'response':{'clientData':cd}}}]}
def test_balanced_visual_features_finish_in_base_game():assert ordinary_round(state(ROW))
def test_unclosed_toggle_pending_counter_or_unknown_action_is_not_base():
    cd=deepcopy(ROW);cd['actions']=[a for a in cd['actions'] if a.get('featureIdentifier')!='ScatterFeatureOff']
    assert not ordinary_round(state(cd))
    cd=deepcopy(ROW);cd['actions'].append({'$type':'ActionGame_Pick','options':[1,2]})
    assert not ordinary_round(state(cd))
    cd=deepcopy(ROW)
    for a in cd['actions']:
        if a.get('name')=='C_FreeSpinsLeft':a['value']=1
    assert not ordinary_round(state(cd))


def test_rejected_typed_schema_cannot_fall_back_to_a_loose_classifier():
    cd={'isFinished':True,'actions':[{'$type':'ActionGame_PresentModeStart','modeName':'BaseGame'}, {'$type':'ActionGame_NewSpin','board':{}}, {'$type':'ActionGame_FeatureHappened','featureIdentifier':'spin'}, {'$type':'ActionGame_SetCounterBoard','name':'C_FreeSpinsLeft','value':5}]}
    assert not ordinary_round(state(cd))
    cd=deepcopy(ROW)
    for a in cd['actions']:
        if a.get('name')=='C_Multiplier':a['name']='C_PicksLeft'
    assert not ordinary_round(state(cd))
