import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.edge_replacements import declaration,valid_output
DATA=json.loads((Path(__file__).parent/'fixtures/yggdrasil_edge_replacement.json').read_text(encoding='utf-8'))
def context():return {'edge_replacement':declaration(DATA['properties'])}
def test_declared_replacement_and_walker_explain_final_board():
    assert declaration(DATA['properties']) is not None
    assert valid_output(DATA['event'],context())
@pytest.mark.parametrize('change',['symbol','column','board','domain','award','reels'])
def test_unknown_or_inconsistent_edge_effect_is_rejected(change):
    ed=deepcopy(DATA['event']);ctx=context()
    if change=='symbol':ed['spinData']['featuresOutputs']['edgeScatters']['0']='HIGH_4'
    if change=='column':ed['spinData']['featuresOutputs']['edgeScatters']={'1':'LOW_1'}
    if change=='board':ed['finalBoard'][1][0]='WILD'
    if change=='domain':ctx={}
    if change=='award':ed['spinData']['featuresOutputs']['scattersFreeSpins']={'count':8}
    if change=='reels':ed['reelSet']='FreeSpinReels'
    assert not valid_output(ed,ctx)


def test_classic_return_detector_uses_declared_effect_contract():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    assert ordinary_flat_event(DATA['event'],{**context(),'basic_coin':'0.002'})
