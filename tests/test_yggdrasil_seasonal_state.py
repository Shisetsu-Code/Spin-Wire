import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_seasonal_state.json').read_text(encoding='utf-8'))
CTX={'season_reels':{'SPRING':'ReelsWalking','SUMMER':'ReelsPlus','FALL':'ReelsMultiplier','WINTER':'ReelsWonky'}}
@pytest.mark.parametrize('event',ROWS)
def test_declared_season_reels_are_ordinary(event):
    assert ordinary_flat_event(event,CTX)
@pytest.mark.parametrize('change',['declaration','season','counter','feature','control'])
def test_unknown_season_state_requires_review(change):
    event=deepcopy(ROWS[0]);ctx=deepcopy(CTX)
    if change=='declaration':ctx={}
    if change=='season':event['currentSeason']='UNKNOWN'
    if change=='counter':event['numberOfSpins']=True
    if change=='feature':event['reelSet']='FeatureReelsWonky'
    if change=='control':event['nextChoice']=['NEXT']
    assert not ordinary_flat_event(event,ctx)


def test_current_server_reel_domain_enables_season_profile():
    from tester_spin.providers.yggdrasil.runtime import configuration
    game=json.loads((Path(__file__).parent/'fixtures/yggdrasil_seasonal_configuration.json').read_text(encoding='utf-8'))
    cfg=configuration(game,str(game['gameid']),'EUR')
    assert cfg['ordinary_constraints']['season_reels']==CTX['season_reels']

def test_incomplete_season_declaration_stays_unrecognized():
    from tester_spin.providers.yggdrasil.runtime import configuration
    game=json.loads((Path(__file__).parent/'fixtures/yggdrasil_seasonal_configuration.json').read_text(encoding='utf-8'))
    game['cfg']['props']=[p for p in game['cfg']['props'] if p['prop']!='FeatureReelsWonky']
    cfg=configuration(game,str(game['gameid']),'EUR')
    assert 'season_reels' not in cfg['ordinary_constraints']


def test_season_multiplier_is_already_in_server_prizes():
    event=json.loads((Path(__file__).parent/'fixtures/yggdrasil_seasonal_multiplier.json').read_text(encoding='utf-8'))
    assert ordinary_flat_event(event,{**CTX,'basic_coin':'0.01'})

@pytest.mark.parametrize('field,value',[('wonCoins',50),('accWa','0.50'),('multiplier',True)])
def test_inconsistent_season_multiplier_requires_review(field,value):
    event=json.loads((Path(__file__).parent/'fixtures/yggdrasil_seasonal_multiplier.json').read_text(encoding='utf-8'))
    event[field]=value
    assert not ordinary_flat_event(event,{**CTX,'basic_coin':'0.01'})
