import json
from copy import deepcopy
from pathlib import Path
from tester_spin.providers.yggdrasil.client_data_sequence import ordinary_sequence
ROWS=json.loads(Path('tests/fixtures/yggdrasil_client_data_sequence.json').read_text())
def test_explicit_base_sequence_without_awards_is_ordinary():
    assert ordinary_sequence(ROWS[0])
    assert not ordinary_sequence(ROWS[1])
def test_award_unknown_fields_and_foreign_geometry_are_not_base():
    for key,value in [('freeSpinsWon',True),('freeSpinsAwarded',1),('ragnarokWon',True),('ragnarokFreeSpinsAwarded',1),('finishedCollections',['new']),('unknown',True)]:
        row=deepcopy(ROWS[0]);row['clientDatas'][0][key]=value
        assert not ordinary_sequence(row)
    row=deepcopy(ROWS[0]);row['clientDatas'][0]['reels']['reelStopPositions']=[1]
    assert not ordinary_sequence(row)


def test_known_awarded_sequence_is_a_candidate_but_never_ordinary():
    from tester_spin.providers.yggdrasil.client_data_sequence import known_awarded_sequence
    assert known_awarded_sequence(ROWS[1])
    assert not ordinary_sequence(ROWS[1])
    row=deepcopy(ROWS[1]);row['clientDatas'][0]['ragnarokWon']=True
    assert not known_awarded_sequence(row)
