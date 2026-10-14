import json
from pathlib import Path
from copy import deepcopy
from tester_spin.providers.yggdrasil.runtime import ordinary_round
ROWS=json.loads(Path('tests/fixtures/yggdrasil_base_game_state.json').read_text())
def state(cd):return {'bets':[{'eventdata':{'response':{'clientData':cd}}}]}
def test_explicit_base_game_without_awarded_continuations_is_ordinary():
    for cd in ROWS:
        assert ordinary_round(state(cd))
def test_unknown_fields_bonus_and_invalid_winnings_block_base():
    for field,value in [('gameMode','BONUS_GAME'),('reSpinAwarded',True),('bonusGameSpinAwarded',True),('choice',{'options':[1,2]})]:
        cd=deepcopy(ROWS[0]);cd[field]=value
        assert not ordinary_round(state(cd))
    cd=deepcopy(ROWS[0]);cd['win']['wonCash']='NaN'
    assert not ordinary_round(state(cd))

def test_variable_reel_heights_are_base_without_resize_or_award():
    import json
    from copy import deepcopy
    from pathlib import Path
    from tester_spin.providers.yggdrasil.base_game_state import ordinary_variable_heights
    cd=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_variable_heights.json").read_text(encoding="utf-8"))
    assert ordinary_variable_heights(cd)
    for mutate in (lambda x:x.update(freeSpinsAwarded=1),lambda x:x["finalReelsHeight"].__setitem__(0,999),lambda x:x["reelsOrder"].__setitem__(0,1),lambda x:x.update(unknownChoice="CHOOSE")):
        bad=deepcopy(cd);mutate(bad);assert not ordinary_variable_heights(bad)

def test_variable_height_padding_is_not_a_playable_cell():
    import json
    from pathlib import Path
    from tester_spin.providers.yggdrasil.base_game_state import ordinary_variable_heights
    cd=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_variable_heights.json").read_text(encoding="utf-8"))
    cd['finalBoard'][0][cd['finalReelsHeight'][0]]='FAKE'
    assert not ordinary_variable_heights(cd)
