import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_neutral_sticky_mode.json').read_text(encoding='utf-8'))
CTX={'basic_coin':'0.004'}
@pytest.mark.parametrize('event',ROWS)
def test_neutral_sticky_mode_is_ordinary(event):
    assert ordinary_flat_event(event,CTX)
@pytest.mark.parametrize('field,value',[('penguinMode',True),('emperorShift',1),('previousEmperorShift',1),('newWildCount',1),('preStickyWilds',[0]),('postStickyWilds',[0]),('penguinAction',{'iconPositionToChange':0,'newIcon':'Wild'})])
def test_active_or_unknown_sticky_mode_requires_review(field,value):
    event=deepcopy(ROWS[0]);event[field]=value
    assert not ordinary_flat_event(event,CTX)
