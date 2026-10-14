import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.collection_neutral import declaration,ordinary
DATA=json.loads((Path(__file__).parent/'fixtures/yggdrasil_collection_neutral.json').read_text(encoding='utf-8'))
def context():
    b=DATA['bet']
    return {'hunter_definition':declaration(DATA['config']),'basic_coin':b['betdata']['coin'],'basic_amount':b['betamount'],'currency':'EUR'}
def test_declared_stable_collections_are_base_state():
    assert declaration(DATA['config']) is not None
    assert ordinary(DATA['bet'],context())
@pytest.mark.parametrize('change',['fight','free','respin','gathered','state','threshold','domain'])
def test_active_or_inconsistent_collection_requires_review(change):
    bet=deepcopy(DATA['bet']);ctx=context();cd=bet['eventdata']['response']['clientData']
    if change=='fight':cd['fights']=[{'outcome':'unknown'}]
    if change=='free':cd['freespinsAwarded']={'Freespin':8}
    if change=='respin':cd['respinWon']=True
    if change=='gathered':cd['collections']['leftHunter']['gathered']=1
    if change=='state':bet['eventdata']['playerState']['collections']['leftHunter']['amount']+=1
    if change=='threshold':cd['collections']['leftHunter']['amount']=DATA['config']['MaximumRage']
    if change=='domain':ctx.pop('hunter_definition')
    assert not ordinary(bet,ctx)


def test_first_demo_spin_clears_new_user_marker_without_activating_feature():
    bet=deepcopy(DATA['bet']);bet['eventdata']['initialPlayerState']['newUser']=True
    assert ordinary(bet,context())

def test_untyped_new_user_marker_is_not_accepted():
    bet=deepcopy(DATA['bet']);bet['eventdata']['initialPlayerState']['newUser']=0
    assert not ordinary(bet,context())


def test_zero_delta_fight_is_neutral_display_event():
    bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_no_change_fight.json').read_text(encoding='utf-8'))
    assert ordinary(bet,context())

@pytest.mark.parametrize('change',['delta','position'])
def test_neutral_fight_requires_zero_changes_and_valid_position(change):
    bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_no_change_fight.json').read_text(encoding='utf-8'))
    fight=bet['eventdata']['response']['clientData']['fights'][0]
    if change=='delta':fight['werewolfHpChange']=-1
    else:fight['field']['column']=999
    assert not ordinary(bet,context())
