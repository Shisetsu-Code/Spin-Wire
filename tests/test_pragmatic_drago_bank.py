import json
from pathlib import Path
from tester_spin.providers.pragmatic_observed_transitions import observed_bonus_rule, automatic_fs_respin
DATA=json.loads((Path(__file__).parent/'fixtures/pragmatic_drago_bank_continuations.json').read_text(encoding='utf-8'))

def test_drago_har_auto_bonus_has_no_player_choice():
    for state in DATA['drago']:
        rule=observed_bonus_rule(state,'vs1600drago')
        assert rule is not None, 'Missing automatic flat bgt=45 continuation'
        assert rule['fields']=={} and rule['domain']==[]
    assert observed_bonus_rule(DATA['drago'][0],'unknown') is None
    assert observed_bonus_rule({**DATA['drago'][0],'rsb_c':'3'},'vs1600drago') is None
    assert observed_bonus_rule({**DATA['drago'][0],'rsb_w_mask':'other'},'vs1600drago') is None

def test_empty_bank_har_respins_do_not_request_manual_reel_choices():
    for state in DATA['bank']:
        assert automatic_fs_respin(state,symbol='vs20emptybank'), 'Missing automatic bank respin'
    state=DATA['bank'][0]
    assert not automatic_fs_respin(state,symbol='unknown')
    assert not automatic_fs_respin({**state,'trail':'sr~0,1'},symbol='vs20emptybank')
    assert not automatic_fs_respin({**state,'tmb_win':'NaN'},symbol='vs20emptybank')
    assert not automatic_fs_respin({**state,'g':state['g'].replace('sw:"7"','sw:"8"')},symbol='vs20emptybank')


def test_six_jokers_stale_counter_does_not_block_two_paid_base_rounds(tmp_path):
    from types import SimpleNamespace
    from tester_spin.providers import PragmaticProvider
    from tester_spin.provider_return_checks import pragmatic_check
    provider=PragmaticProvider(tmp_path)
    state={'na':'s','bl':'0','rs_c':'1','trail':'dr~0'}
    provider._post_and_store=lambda *args,**kwargs:(200,b'',state,{})
    proof=pragmatic_check(provider,SimpleNamespace(symbol='vs5magicdoor',reel_contract=None),state,{},tmp_path,1)
    assert proof['status']=='CONFIRMED'
