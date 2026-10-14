import json
from copy import deepcopy
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.enum_outcomes import ordinary_enum_round
ROWS=json.loads(Path('tests/fixtures/yggdrasil_enum_paid_wins.json').read_text())
@pytest.mark.parametrize('row',ROWS)
def test_closed_main_enum_round_supports_typed_line_wins_or_no_fev(row):
    assert ordinary_enum_round(row)
def test_foreign_prize_cell_unknown_event_or_unbalanced_totals_are_unknown():
    for damage in ['cell','event','total','feature']:
        row=deepcopy(ROWS[0])
        if damage=='cell':row['Round']['VISData']['Prizes'][0]['Cells'][0]=[99,0]
        elif damage=='event':row['Round']['VISData']['Events'].append({'Type':999})
        elif damage=='total':row['Round']['TotalWin']=99
        else:row['Round']['Info']['RoundType']=1
        assert not ordinary_enum_round(row)


def test_swapped_symbol_position_uses_actual_board_bounds():
    row=deepcopy(ROWS[0])
    row['Round']['VISData']['Events'].append({'Type':50,'SwappedSymbols':[[1,4,0]]})
    assert not ordinary_enum_round(row)


def test_empty_expansion_positions_are_a_known_no_op():
    row=json.loads(Path('tests/fixtures/yggdrasil_enum_neutral_expansion.json').read_text())
    assert ordinary_enum_round(row)
