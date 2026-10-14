import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
DATA=json.loads((Path(__file__).parent/'fixtures/yggdrasil_persistent_collection.json').read_text(encoding='utf-8'))
CTX={'collection_capacity':DATA['capacity'],'basic_coin':'0.004'}
@pytest.mark.parametrize('event',DATA['events'])
def test_declared_incomplete_collection_is_saved_state(event):
    assert ordinary_flat_event(event,CTX)
@pytest.mark.parametrize('change',['capacity','full','count','negative','award','continuation'])
def test_unknown_or_active_collection_requires_review(change):
    event=deepcopy(DATA['events'][0]);ctx=deepcopy(CTX)
    if change=='capacity':ctx={}
    if change=='full':event['collectionMeter']['amounts'][0]=DATA['capacity'][0];event['collectionMeter']['values'][0]=['0.00']*DATA['capacity'][0]
    if change=='count':event['collectionMeter']['amounts'][0]=1
    if change=='negative':event['collectionMeter']['values'][2][0]='-1'
    if change=='award':event['prizeCoins']=1
    if change=='continuation':event['collectionWildPos']=0
    assert not ordinary_flat_event(event,ctx)


def test_capacity_is_read_from_current_server_declaration():
    from tester_spin.providers.yggdrasil.runtime import configuration
    game=DATA['configuration']
    cfg=configuration(game,str(game['gameid']),'EUR')
    assert cfg['ordinary_constraints']['collection_capacity']==DATA['capacity']

@pytest.mark.parametrize('invalid',[None,[True],[0],[-1],[65],['3'],[]])
def test_invalid_capacity_does_not_enable_saved_state(invalid):
    from tester_spin.providers.yggdrasil.runtime import configuration
    game=deepcopy(DATA['configuration'])
    for prop in game['cfg']['props']:
        if prop['prop']=='CollectionsCapacity':prop['value']=invalid
    cfg=configuration(game,str(game['gameid']),'EUR')
    assert 'collection_capacity' not in cfg['ordinary_constraints']
    assert not ordinary_flat_event(DATA['events'][0],cfg['ordinary_constraints'])
