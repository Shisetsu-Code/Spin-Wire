import json
from pathlib import Path
from copy import deepcopy
import pytest

ROWS=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_typed_actions.json").read_text(encoding="utf-8"))

def test_cash_normalized_action_rounds_have_current_base_mode():
    from tester_spin.providers.yggdrasil.typed_actions import ordinary_typed_actions
    assert all(ordinary_typed_actions(b) for b in ROWS)

@pytest.mark.parametrize("mutation",["mode","choice","currency","money","normalization","position","counter","finished","sequence"])
def test_unknown_controls_or_inconsistent_cash_are_not_base(mutation):
    from tester_spin.providers.yggdrasil.typed_actions import ordinary_typed_actions
    b=deepcopy(ROWS[0]);cd=b["eventdata"]["response"]["clientData"];actions=cd["actions"]
    if mutation=="mode":actions[0]["modeName"]="free_spins"
    elif mutation=="choice":actions.append({"$type":"ActionGame_PlayerChoice"})
    elif mutation=="currency":actions[-1]["modeWin"]["currency"]="USD"
    elif mutation=="money":actions[-1]["modeWin"]["amount"]=999
    elif mutation=="normalization":actions[-1]["modeWin"]["amountNormalizedToBet"]=999
    elif mutation=="position":actions[3]["winningCells"][0]["x"]=999
    elif mutation=="counter":actions[1]["board"]["counters"]=[{"trigger":True}]
    elif mutation=="finished":cd["isFinished"]=False
    elif mutation=="sequence":actions[2],actions[4]=actions[4],actions[2]
    assert not ordinary_typed_actions(b)

def test_invalid_current_command_field_is_not_ignored():
    from tester_spin.providers.yggdrasil.typed_actions import ordinary_typed_actions
    for invalid in (False,{},123):
        b=deepcopy(ROWS[0]);b['eventdata']['nextCmds']=invalid
        assert not ordinary_typed_actions(b)

def test_saved_cash_actions_retain_revalidatable_evidence_without_balance(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    from tester_spin.providers.yggdrasil.typed_actions import ordinary_typed_actions
    bet=deepcopy(ROWS[0]);bet['betdata']['initialBalance']='11000'
    runtime=DemoRuntime(None,'fixture',5,threading.Event(),gate=None)
    state={'wagerid':'fixture','status':'Pending','terminal':False,'commands':['C'],'bets':[bet],'max_step':1}
    runtime.save(tmp_path,1,{'amount':'0.1','coin':'0.1'},state)
    saved=json.loads((tmp_path/'step-001-response.json').read_text())
    envelope=saved['ordinary_typed_action_outcomes'][0]
    assert ordinary_typed_actions(envelope['bet'])
    assert 'initialBalance' not in envelope['bet']['betdata']
    assert saved['bets'][0]['clientData']['actions']==bet['eventdata']['response']['clientData']['actions']
