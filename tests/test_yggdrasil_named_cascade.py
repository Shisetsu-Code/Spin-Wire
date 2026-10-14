import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.named_actions import ordinary_named_actions
ROWS=json.loads(Path('tests/fixtures/yggdrasil_named_cascade.json').read_text())
@pytest.mark.parametrize('row',ROWS)
def test_known_cascade_operations_and_visual_subsymbols_are_ordinary(row):
    assert ordinary_named_actions(row)

def test_unknown_award_operation_or_non_boolean_subsymbol_remains_unknown():
    for action in [{'name':'operateSymbols','operation':'awardFreeSpins','symbols':[]},{'name':'makeChoice','possibleChoices':['A','B']}]:
        row=deepcopy(ROWS[0]);row['actions'].append(action)
        assert not ordinary_named_actions(row)
    row=deepcopy(ROWS[0]);stop=next(a for a in row['actions'] if a['name']=='stopReels');stop['symbols'][0]['subsymbol']=1
    assert not ordinary_named_actions(row)
