import json
from pathlib import Path
import pytest
from tester_spin.providers.hacksaw.runtime import discover_modes
from tester_spin.feature_domains import initialization_domains

FIXTURES=json.loads(Path('tests/fixtures/hacksaw_oct11.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('row', FIXTURES, ids=lambda r:r['file'])
def test_real_declared_feature_spins_are_separate_from_bonus_purchases(row):
    modes=discover_modes(row['auth'])
    expected_purchase={'2378':2,'2458':2,'2356':0,'2613':0}[str(row['auth']['gameId'])]
    assert sum(m['kind']=='PURCHASE' for m in modes)==expected_purchase
    domains=initialization_domains('hacksaw',row['auth'],modes)
    assert len(domains['purchase']['options'])==expected_purchase
    assert len(domains['feature_spin']['options'])==len(row['auth']['bonusGames'])-expected_purchase
    assert 'ante' not in domains


def test_explicit_type_overrides_id_and_unknown_type_stays_pending():
    data={'bonusGames':[{'bonusGameId':'mod_future','featureBuyItemType':'BonusBuyItem','betCostMultiplier':'100'},
                        {'bonusGameId':'fs','featureBuyItemType':'FutureItem','betCostMultiplier':'200'}]}
    modes=discover_modes(data)
    assert modes[1]['kind']=='PURCHASE'
    assert modes[2]['kind']=='UNKNOWN_FEATURE'
    assert initialization_domains('hacksaw',data,modes)['purchase']['complete'] is False


def test_disabled_feature_spins_do_not_disable_bonus_buys():
    data={'disableFeatureSpins':True,'bonusGames':[{'bonusGameId':'mod_a','betCostMultiplier':'5'}, {'bonusGameId':'fs','betCostMultiplier':'100'}]}
    modes=discover_modes(data)
    assert [m['buyBonus'] for m in modes if 'buyBonus' in m]==['fs']
    domains=initialization_domains('hacksaw',data,modes)
    assert domains['feature_spin']['options']==[]
    assert domains['purchase']['options']==['fs']


def test_special_spins_are_visible_without_false_bonus_purchase():
    from tester_spin.feature_summary import feature_summary
    data={'bonusGames':[{'bonusGameId':'mod_future','betCostMultiplier':'1050'}]}
    modes=discover_modes(data)
    row={'provider':'hacksaw','discovered_modes':modes,'feature_domains':initialization_domains('hacksaw',data,modes)}
    assert feature_summary(row)=='Compras: No | Cantidad: 0 | Antebets: Sin datos | FeatureSpins: 1'


def test_unexecuted_special_spin_stays_pending():
    from tester_spin.models import GameTestResult
    from tester_spin.providers.path_coverage import enforce_complete_path_coverage
    data={'bonusGames':[{'bonusGameId':'mod_future','betCostMultiplier':'3'}]}
    modes=discover_modes(data)
    modes[0].update(validated=True,required_options=['spin'],covered_options=['spin'])
    result=GameTestResult('hacksaw','123','Example','',1,1,0,'OK',discovered_modes=modes,feature_domains=initialization_domains('hacksaw',data,modes))
    assert enforce_complete_path_coverage(result).status=='PARCIAL'


@pytest.mark.parametrize('row', FIXTURES, ids=lambda r:r['file'])
def test_client_constructor_positions_are_understood_across_versions(row):
    from tester_spin.providers.hacksaw.runtime import client_feature_types
    types=client_feature_types(row['client_source'])
    assert set(types)=={b['bonusGameId'] for b in row['auth']['bonusGames']}


def test_client_explicit_type_is_not_overridden_by_prefix():
    from tester_spin.providers.hacksaw.runtime import client_feature_types
    source="""x["hacksaw.common.types.FeatureBuyItem"]=Q;
function Q(a,b,c){this.bonusGameId=a;this.featureBuyItemType=null;null!=c&&(this.featureBuyItemType=c)}
getFeatureBuyItems:function(){return[new Q("mod_new","title","BonusBuyItem")]}
"""
    types=client_feature_types(source)
    assert types=={'mod_new':'BonusBuyItem'}
    data={'client_feature_types':types,'bonusGames':[{'bonusGameId':'mod_new','betCostMultiplier':'50'}]}
    assert discover_modes(data)[1]['kind']=='PURCHASE'


def test_failed_client_extraction_does_not_prove_absence():
    data={'client_types_complete':False,'client_feature_types':{},'bonusGames':[{'bonusGameId':'mod_future','betCostMultiplier':'50'}]}
    modes=discover_modes(data)
    assert modes[1]['kind']=='UNKNOWN_FEATURE'
    assert initialization_domains('hacksaw',data,modes)['purchase']['complete'] is False


@pytest.mark.parametrize('value', [{},[],3,True])
def test_nonscalar_feature_type_is_unknown(value):
    data={'bonusGames':[{'bonusGameId':'fs','featureBuyItemType':value}]}
    assert discover_modes(data)[1]['kind']=='UNKNOWN_FEATURE'


def test_partial_client_mapping_never_guesses_missing_types():
    data={'client_types_complete':True,'client_feature_types':{'fs':'BonusBuyItem'},'bonusGames':[{'bonusGameId':'fs'}, {'bonusGameId':'mod_future'}]}
    modes=discover_modes(data)
    assert modes[2]['kind']=='UNKNOWN_FEATURE'
    assert initialization_domains('hacksaw',data,modes)['purchase']['complete'] is False


def menu_source(branches):
    return ('x["hacksaw.common.types.FeatureBuyItem"]=Q;'
        'function Q(a,b,c){this.bonusGameId=a;this.featureBuyItemType=null;null!=c&&(this.featureBuyItemType=c)}'
        'getFeatureBuyItems:function(){switch(this.volatility){'+branches+'}}')

def test_literal_alternative_menus_preserve_roles_independent_of_volatility():
    from tester_spin.providers.hacksaw.runtime import client_feature_types
    source=menu_source('case"LOW":return[new Q("option_a","low","BonusBuyItem"),new Q("option_b","low","FeatureSpinItem")];'
        'case"HIGH":return[new Q("option_a","high","BonusBuyItem"),new Q("option_b","high","FeatureSpinItem")];')
    assert client_feature_types(source)=={'option_a':'BonusBuyItem','option_b':'FeatureSpinItem'}

def test_alternative_menus_cannot_give_same_selector_conflicting_roles():
    from tester_spin.providers.hacksaw.runtime import client_feature_types
    source=menu_source('case"LOW":return[new Q("same","low","BonusBuyItem")];'
        'case"HIGH":return[new Q("same","high","FeatureSpinItem")];')
    assert client_feature_types(source)=={}

def test_duplicate_within_one_menu_is_not_an_alternative():
    from tester_spin.providers.hacksaw.runtime import client_feature_types
    source=menu_source('case"LOW":return[new Q("same","low","BonusBuyItem"),new Q("same","low","BonusBuyItem")];')
    assert client_feature_types(source)=={}
