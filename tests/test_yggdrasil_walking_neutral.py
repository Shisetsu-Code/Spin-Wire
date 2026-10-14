import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event

ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_walking_neutral.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('event',ROWS)
def test_neutral_walking_state_is_ordinary(event):
    assert ordinary_flat_event(event)

@pytest.mark.parametrize('field',['walkingBefore','walkingAfter','walkingNew'])
def test_persistent_walking_position_requires_review(field):
    event=deepcopy(ROWS[0]);event[field]=[0]
    assert not ordinary_flat_event(event)

def test_walking_respin_is_not_return_to_base():
    event=deepcopy(ROWS[0]);event['reSpins']=True
    assert not ordinary_flat_event(event)

def test_unknown_walking_control_requires_review():
    event=deepcopy(ROWS[0]);event['nextChoice']=['ADVANCE']
    assert not ordinary_flat_event(event)
