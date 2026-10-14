import json
from tester_spin.feature_summary import feature_summary
from tester_spin.models import Game


def test_spin_does_not_prove_absence():
    assert feature_summary({'discovered_modes':[{'id':'SPIN','kind':'SPIN'}]}) == 'Compras: Sin datos | Cantidad: Sin datos | Antebets: Sin datos'


def test_complete_empty_declarations_prove_absence_independently():
    row={'discovered_modes':[{'id':'SPIN','kind':'SPIN'}], 'feature_domains': {'purchase': {'complete': True, 'source':'server.init', 'options':[]}}}
    assert feature_summary(row) == 'Compras: No | Cantidad: 0 | Antebets: Sin datos'


def test_complete_declaration_counts_unexecuted_options():
    row={'feature_domains':{'purchase':{'complete':True,'source':'server.init','options':['a','b','c']}},'discovered_modes':[{'id':'PURCHASE_a','kind':'PURCHASE','observed':False}]}
    assert 'Compras: Sí | Cantidad: 3' in feature_summary(row)


def test_bgaming_literal_candidate_is_not_counted():
    row={'provider':'bgaming','discovered_modes':[{'id':'SPIN','kind':'SPIN'}, {'id':'PURCHASE_BUY_BONUS','kind':'PURCHASE','discovery_state':'DISCOVERED_LITERAL_ONLY','coverage_required':False,'executable':False}]}
    assert feature_summary(row) == 'Compras: Sin datos | Cantidad: Sin datos | Antebets: Sin datos'


def test_ka_declaration_does_not_depend_on_title(tmp_path):
    from tester_spin.providers.ka_gaming.adapter import KAGamingProvider
    from tester_spin.providers.ka_gaming.catalog import declared_modes_from_row
    p=KAGamingProvider(tmp_path)
    for slug in ['future_game','hotcoinbf']:
        p._catalog_modes[slug]=declared_modes_from_row({'gameType':'slots','supportsBuyFeature':True})
    def features(slug):
        return [m for m in p._discovered_modes(Game('ka_gaming',slug,slug,'https://example.invalid')) if m['id']!='SPIN']
    assert features('future_game') == features('hotcoinbf')
    assert features('future_game')[0]['coverage_required'] is True
    assert features('future_game')[0]['kind']=='UNKNOWN_FEATURE'


def test_yggdrasil_uses_declared_modes_even_without_captured_purchase():
    from tester_spin.providers.yggdrasil.protocol import declared_modes
    modes=declared_modes({'BB_A':{'coinsPerBet':1},'BB_B':{'coinsPerBet':1},'BASIC':{'coinsPerBet':1}}, [], '123')
    assert {m['id'] for m in modes if m['kind']=='PURCHASE'} == {'BB_A','BB_B'}
    assert all(m['coverage_required'] and not m['validated'] for m in modes)


def test_pragmatic_empty_purchase_declaration_and_single_base_are_known():
    from tester_spin.feature_domains import initialization_domains
    domains=initialization_domains('pragmatic', {'purInit':'', 'bls':'20'}, [])
    assert domains['purchase']['complete'] and domains['purchase']['options']==[]
    assert domains['ante']['complete'] and domains['ante']['options']==[]


def test_pragmatic_js_object_purchase_table_is_complete_without_evaluating_code():
    from tester_spin.feature_domains import initialization_domains
    data={'purInit':'[{bet:2000,type:"default"},{bet:4000,type:"fs"}]','purInit_e':'1,0','bls':'20,60'}
    domain=initialization_domains('pragmatic',data,[])['purchase']
    assert domain['complete'] and domain['options']==['PURCHASE_1']
    for raw in ['[{bet:2000},{bet:unknown}]','[{bet:2000,bet:4000}]','[{bet:NaN}]','[{bet:(function(){return 2000})()}]']:
        assert not initialization_domains('pragmatic',{**data,'purInit':raw},[])['purchase']['complete']


def test_missing_configuration_is_unknown():
    from tester_spin.feature_domains import initialization_domains
    assert initialization_domains('pragmatic', {}, []) == {}


def test_three_oaks_server_options_remain_expected_without_execution():
    from tester_spin.feature_domains import initialization_domains
    domains=initialization_domains('3oaks', {'context':{'available_buy_bonus':[0,1]}, 'settings':{}}, [])
    assert domains['purchase']['options']==['0','1']
    assert 'ante' not in domains


def test_redtiger_disabled_purchase_ignores_backend_templates():
    from tester_spin.providers.redtiger.runtime import feature_buys_from_settings
    data={'success':True,'result':{'user':{},'game':{'hasFeatureBuy':False,'featureBuy':[{'name':'FreeSpins','price':100}]}}}
    assert feature_buys_from_settings(data)==()


def test_yggdrasil_configuration_is_game_scoped():
    from tester_spin.providers.yggdrasil.protocol import game_declarations
    entry={'request':{'url':'https://demo.yggdrasilgaming.com/game.web/service?fn=game'},'response':{'status':200,'content':{'text':json.dumps({'code':0,'data':{'gameid':123,'cfg':{'props':[{'prop':'Modes','value':{'BASIC':{},'BB_A':{}}}]}}})}}}
    assert game_declarations({'log':{'entries':[entry]}})[0]['gameid']=='123'
    entry['request']['url']='https://attacker.example/game.web/service?fn=game'
    assert game_declarations({'log':{'entries':[entry]}})==[]


def test_d1_antebet_does_not_require_an_executable_purchase():
    import importlib.util
    spec=importlib.util.spec_from_file_location('d1fixtures', 'tests/test_one_spin4win_purchases.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    from tester_spin.providers.one_spin4win_purchases import discover_antebet_modes, discover_purchase_modes
    source=module.MODERN_BUY_CLIENT.replace('this.buyFeatureToPlayActionIndex=3;', '')
    source=source.replace('confirmBuyFeature(){', 'toggleSideBet(){this.sideBetPlayIndex=this.sideBetToPlayActionIndex;}getSidebetValue(){return a+Math.round(a*this.sideBetPercent);}confirmBuyFeature(){')
    assert not discover_purchase_modes([source], 'FixtureBuy')[0]['executable']
    assert discover_antebet_modes([source], 'FixtureBuy')[0]['feature_selector']==1


def test_bgaming_server_levels_and_chance_have_separate_domains():
    from tester_spin.feature_domains import initialization_domains
    data={'options':{'feature_options':{'feature_multipliers':{'base_bet':20,'bonus_buy':{'a':100,'b':200},'bonus_chance':30}}}}
    domains=initialization_domains('bgaming',data,[])
    assert len(domains['purchase']['options'])==2
    assert len(domains['ante']['options'])==1


def test_invalid_prices_do_not_prove_empty_bgaming_domain():
    from tester_spin.feature_domains import initialization_domains
    data={'options':{'feature_options':{'feature_multipliers':{'bonus_buy':float('nan')}}}}
    assert initialization_domains('bgaming',data,[])['purchase']['complete'] is False


def test_partial_pragmatic_declaration_is_not_complete():
    from tester_spin.feature_domains import initialization_domains
    from tester_spin.providers.pragmatic_modes import discover_modes
    init={'bls':'20','purInit':'[{"bet":100},{"unknown":200}]'}
    modes=discover_modes(init).modes
    assert initialization_domains('pragmatic',init,modes)['purchase']['complete'] is False


def test_incomplete_domain_prevents_ok():
    from tester_spin.models import GameTestResult
    from tester_spin.providers.path_coverage import enforce_complete_path_coverage
    result=GameTestResult('pragmatic','example','Example','',1,1,0,'OK',feature_domains={'purchase':{'complete':False,'source':'doInit.purInit','options':[],'reason':'UNRECOGNIZED_DECLARATION'}})
    assert enforce_complete_path_coverage(result).status=='PARCIAL'


def test_pragmatic_total_comes_from_config_not_selected_modes():
    from tester_spin.feature_domains import initialization_domains
    domains=initialization_domains('pragmatic',{'purInit':'[{"bet":100},{"bet":200}]'},[])
    assert domains['purchase']['options']==['PURCHASE_1','PURCHASE_2']


def test_omitted_declared_mode_stays_pending():
    from tester_spin.models import GameTestResult
    from tester_spin.providers.path_coverage import enforce_complete_path_coverage
    result=GameTestResult('pragmatic','example','Example','',1,1,0,'OK',discovered_modes=[{'id':'PURCHASE_1','kind':'PURCHASE','validated':True}],feature_domains={'purchase':{'complete':True,'source':'doInit.purInit','options':['PURCHASE_1','PURCHASE_2']}})
    assert enforce_complete_path_coverage(result).status=='PARCIAL'
    assert 'PURCHASE_2' in result.error


def test_single_csv_price_is_a_complete_declaration():
    from tester_spin.feature_domains import initialization_domains
    assert initialization_domains('pragmatic',{'purInit':'100'},[])['purchase']['options']==['PURCHASE_1']


def test_bgaming_empty_level_map_is_not_absence():
    from tester_spin.feature_domains import initialization_domains
    data={'options':{'feature_options':{'feature_multipliers':{'base_bet':20,'bonus_buy':{}}}}}
    assert initialization_domains('bgaming',data,[])['purchase']['complete'] is False


def test_nonfinite_csv_price_is_not_complete():
    from tester_spin.feature_domains import initialization_domains
    assert initialization_domains('pragmatic', {'purInit':'9'*400}, [])['purchase']['complete'] is False


def test_blank_three_oaks_identifier_is_not_a_declared_option():
    from tester_spin.feature_domains import initialization_domains
    for value in ['', '   ']:
        assert 'purchase' not in initialization_domains('3oaks', {'context':{'available_buy_bonus':[value]}}, [])
