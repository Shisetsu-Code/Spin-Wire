import json
from copy import deepcopy
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
EVENT=json.loads((Path(__file__).parent/'fixtures/yggdrasil_direct_cup.json').read_text(encoding='utf-8'))
CTX={'basic_coin':'0.01','cup_coin_awards':{'COINS_100':100}}
def test_declared_direct_coin_award_is_closed_base_result():
    assert ordinary_flat_event(EVENT,CTX)
@pytest.mark.parametrize('change',['undeclared','amount','cash','feature','free','unknown'])
def test_inconsistent_or_noncoin_cup_award_stays_unknown(change):
    event=deepcopy(EVENT);ctx=deepcopy(CTX)
    if change=='undeclared':ctx.pop('cup_coin_awards')
    if change=='amount':event['bonusWin']=99
    if change=='cash':event['accWa']='99.00'
    if change=='feature':event['featureNames']=['unknownFeature']
    if change=='free':event['baseSilverCupWin']='FREE_SPIN_7'
    if change=='unknown':event['selection']=['NEXT']
    assert not ordinary_flat_event(event,ctx)


def test_coin_awards_use_declared_amount_and_positive_probability():
    from tester_spin.providers.yggdrasil.direct_cup import declaration
    props={'BaseSilverCupPrizes':{'COINS_100':100,'COINS_200':200,'FREE_SPIN_7':7},'BaseSilverCupDistribution':{'COINS_100':1,'COINS_200':0,'FREE_SPIN_7':1}}
    assert declaration(props)=={'COINS_100':100}

@pytest.mark.parametrize('change',['missing','amount','boolean','negative','foreign'])
def test_invalid_cup_domain_is_not_enabled(change):
    from tester_spin.providers.yggdrasil.direct_cup import declaration
    props={'BaseSilverCupPrizes':{'COINS_100':100},'BaseSilverCupDistribution':{'COINS_100':1}}
    if change=='missing':props.pop('BaseSilverCupDistribution')
    if change=='amount':props['BaseSilverCupPrizes']['COINS_100']=99
    if change=='boolean':props['BaseSilverCupDistribution']['COINS_100']=True
    if change=='negative':props['BaseSilverCupDistribution']['COINS_100']=-1
    if change=='foreign':props['BaseSilverCupDistribution']['COINS_200']=1
    assert declaration(props) is None
