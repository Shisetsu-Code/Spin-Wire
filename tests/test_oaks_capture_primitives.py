from pathlib import Path
import pytest
from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.runtime import play_fields, continuation_fields, discover_modes
ROOT=Path(__file__).parent/'fixtures'

def data(modes):
    return {'context':{'current':'spins','round_finished':True,'actions':['spin','buy_spin'],'available_buy_bonus':modes,'spins':{'bet_per_line':10,'lines':5}},'settings':{'lines':[5],'bet_factor':[20],'buy_bonus_prices':{str(m):100*m for m in modes},'ante_bet':[1.25]}}

def test_prototype_override_and_price_key_offset_define_wire_selectors():
    d=data([1,2,3,4]);p=client_contract((ROOT/'three_oaks_override_inputs.js').read_text(),data=d)
    assert p['purchase_modes']==[1,2,3,4]
    for mode in [1,2,3,4]:
        assert play_fields(d,'buy_spin',mode,client_profile=p)['action']['params']=={'bet_per_line':10,'lines':5,'selected_mode':mode-1}
    d['context'].update(current='bonus',round_finished=False,actions=['bonus_stop'])
    assert continuation_fields(d,game_slug='unseen',family='goreel',client_profile=p)['action']=={'name':'bonus_stop','params':{}}

def test_scatters_purchase_uses_source_transform_and_booster_off():
    d=data([1,2,3]);p=client_contract((ROOT/'three_oaks_scatters_inputs.js').read_text(),data=d)
    assert p['purchase_modes']==[1,2,3]
    for mode in [1,2,3]:
        assert play_fields(d,'buy_spin',mode,client_profile=p)['action']['params']=={'bet_per_line':10,'lines':20,'bet_factor':20,'ante_bet':0,'buy_spin_scatters_count':mode+3}

@pytest.mark.parametrize('state',['spins','freespins','bonus'])
def test_advertised_empty_respin_is_valid_in_each_normal_protocol_state(state):
    d=data([1,2,3]);p=client_contract((ROOT/'three_oaks_scatters_inputs.js').read_text(),data=d)
    d['context'].update(current=state,round_finished=False,actions=['respin'])
    assert continuation_fields(d,game_slug='unseen',family='goreel',client_profile=p)['action']=={'name':'respin','params':{}}

def test_unknown_state_and_multiple_actions_remain_pending():
    d=data([1,2,3]);p=client_contract((ROOT/'three_oaks_scatters_inputs.js').read_text(),data=d)
    d['context'].update(current='unknown',round_finished=False,actions=['respin'])
    assert continuation_fields(d,game_slug='unseen',family='goreel',client_profile=p) is None
    d['context'].update(current='spins',actions=['respin','spin'])
    assert continuation_fields(d,game_slug='unseen',family='goreel',client_profile=p) is None

def test_antebet_requires_client_route_not_server_coefficient_only():
    d=data([1,2,3]);source=(ROOT/'three_oaks_scatters_inputs.js').read_text();p=client_contract(source,data=d)
    assert p['antebet_ui_observed'] is True
    assert not (client_contract(source.replace('GR.Events.game.ante_bet(param);',''),data=d) or {}).get('antebet_ui_observed')

def test_override_without_wire_bridge_remains_unproven():
    d=data([1,2,3,4]);source=(ROOT/'three_oaks_override_inputs.js').read_text()
    p=client_contract(source.replace('params:args||{}','params:serialize(args)'),data=d)
    assert not (p or {}).get('purchase_modes')

def test_unrecognized_scatters_transform_is_not_guessed():
    d=data([1,2,3]);source=(ROOT/'three_oaks_scatters_inputs.js').read_text()
    p=client_contract(source.replace('scattersCount+3','lookup(scattersCount)'),data=d)
    assert not p['purchase_modes']

def test_coefficient_without_runner_forwarding_is_not_executable():
    d=data([1,2,3]);source=(ROOT/'three_oaks_scatters_inputs.js').read_text()
    p=client_contract(source,data=d)
    modes=discover_modes(d,'goreel',True,client_profile=p)
    assert any(m['kind']=='ANTE_BET' and not m['executable'] for m in modes)
    with pytest.raises(ValueError,match='antebet'):
        play_fields(d,'spin',client_profile=p,antebet=1.25)
