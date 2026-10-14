from pathlib import Path
import json
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event

EVENTS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_neutral_wild_maps.json').read_text(encoding='utf-8'))
@pytest.mark.parametrize('event',EVENTS)
def test_empty_base_wild_maps_are_ordinary(event):
 assert ordinary_flat_event(event,{'basic_coin':'0.01'})

@pytest.mark.parametrize('key',['thisWilds','addedWilds','nextWilds'])
@pytest.mark.parametrize('value',[{'0':[1]},[],None])
def test_nonempty_or_wrongly_typed_maps_are_unlearned(key,value):
 event=deepcopy(EVENTS[0]);event[key]=value
 assert not ordinary_flat_event(event,{'basic_coin':'0.01'})

def test_partial_map_domain_or_free_spin_metadata_is_unlearned():
 event=deepcopy(EVENTS[0]);event.pop('nextWilds')
 assert not ordinary_flat_event(event,{'basic_coin':'0.01'})
 event=deepcopy(EVENTS[0]);event['fsThisWilds']={}
 assert not ordinary_flat_event(event,{'basic_coin':'0.01'})
