import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.saved_feature_neutral import declaration,ordinary
DATA=json.loads((Path(__file__).parent/'fixtures/yggdrasil_saved_feature_neutral.json').read_text(encoding='utf-8'))
def context():
    bet=DATA['bet']
    return {'saved_feature_geometry':declaration(DATA['config']),'basic_coin':bet['betdata']['coin'],'basic_amount':bet['betamount'],'currency':'EUR'}
def test_saved_quantity_without_active_feature_is_ordinary():
    assert declaration(DATA['config']) is not None
    assert ordinary(DATA['bet'],context())
@pytest.mark.parametrize('change',['active','count','mapping','order','cash','state','domain'])
def test_unknown_or_active_saved_feature_requires_review(change):
    bet=deepcopy(DATA['bet']);ctx=context();cd=bet['eventdata']['response']['clientData']
    if change=='active':cd['feature']='FullLine'
    if change=='count':cd['featureAfter']['FullLine']+=1
    if change=='mapping':cd['iconsMap'][0]=999
    if change=='order':cd['reelsOrder'][0]='WReel1'
    if change=='cash':cd['wonAmount']='1.00'
    if change=='state':bet['eventdata']['playerState']['FullLine']+=1
    if change=='domain':ctx.pop('saved_feature_geometry')
    assert not ordinary(bet,ctx)
