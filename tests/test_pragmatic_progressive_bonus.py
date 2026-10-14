from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from tester_spin.providers import PragmaticProvider
from tester_spin.provider_return_checks import pragmatic_check
from tester_spin.return_to_base import audit_scope
from tester_spin.providers.pragmatic_observed_transitions import bonus_transition

MENU = {'na':'fso','fs_opt_mask':'fs,m,rs,rsv','fs_opt':'20,1,5,2~10,1,5;4,2~5,1,5;4;3,2'}
ENVELOPES = {'na':'b','prg_m':'cp,tp,r,acw','prg':'40,40,0,7.20','wins':'0,0,0,0,0,0,0,0','status':'0,0,0,0,0,0,0,0','wins_mask':'h,h,h,h,h,h,h,h','level':'0','lifes':'1','bw':'1','end':'0','rw':'7.20'}

def test_return_audit_completes_natural_fs_choice(tmp_path):
    provider=PragmaticProvider(tmp_path)
    responses=[MENU,{'na':'s','fs':'1','fsmax':'1'}, {'na':'c'}, {'na':'s'}, {'na':'s'}, {'na':'s'}]
    provider._post_and_store=Mock(side_effect=[(200,b'',r,{}) for r in responses])
    with audit_scope():
        proof=pragmatic_check(provider,SimpleNamespace(symbol='demo',reel_contract=None),{'na':'s'}, {'symbol':'demo','mgckey':'test','pur':'0','bl':'1','c':'.08','l':'25'},tmp_path,1)
    assert proof['status']=='CONFIRMED'
    calls=[call.args[1] for call in provider._post_and_store.call_args_list]
    assert [c['action'] for c in calls]==['doSpin','doFSOption','doSpin','doCollect','doSpin','doSpin']
    assert calls[1]['ind']=='0'
    assert not set(calls[1]) & {'pur','bl','c','l'}
    assert proof['consecutive_base']==2
    assert list(tmp_path.rglob('base-fs-option-*.json'))
    assert not list(tmp_path.rglob('fso-selection-*.json'))

def test_flat_progressive_envelopes_use_position_not_reward():
    result=bonus_transition(ENVELOPES,override='7')
    assert result['fields']=={'ind':'7'}
    assert result['domain']==list(map(str,range(8)))
    assert result['coverage_policy']=='hidden-position-structural/v1'
    with pytest.raises(ValueError):bonus_transition(ENVELOPES,override='8')

@pytest.mark.parametrize('change',[{'na':'s'},{'end':'1'},{'lifes':'2'},{'prg':'39,40,0,7.20'},{'wins_mask':'m,h,h,h,h,h,h,h'},{'wins':'0,0'},{'g':'unknown'},{'rw':'8.00'}])
def test_unknown_progressive_shape_is_not_executable(change):
    assert bonus_transition({**ENVELOPES,**change}) is None

def test_progressive_coverage_requires_server_acknowledgement(tmp_path):
    import json
    from tester_spin.models import GameTestResult, SpinAttempt
    from tester_spin.providers.pragmatic_bonus_coverage import annotate_bonus_coverage
    result=GameTestResult(provider='pragmatic',slug='test',game_name='Test',game_url='https://example.invalid',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',run_dir=str(tmp_path))
    result.attempts=[SpinAttempt(number=1,ok=True,terminal=True,mode_id='SPIN',artifact_dir=str(tmp_path))]
    (tmp_path/'return-to-base.json').write_text(json.dumps({'status':'CONFIRMED','consecutive_base':2}))
    (tmp_path/'step-000-bonus.bonus-selection.json').write_text(json.dumps(bonus_transition(ENVELOPES,override='7')))
    response_path=tmp_path/'step-000-bonus.response.json'
    response_path.write_text(json.dumps({'na':'cb','end':'1','level':'1','lifes':'0','status':'0,0,0,0,1,0,0,0'}))
    annotate_bonus_coverage(result)
    row=result.discovered_modes[-1]
    assert row['covered_options']==[]
    response_path.write_text(json.dumps({'na':'cb','end':'1','level':'1','lifes':'0','status':'0,0,0,0,0,0,0,1'}))
    annotate_bonus_coverage(result)
    row=result.discovered_modes[-1]
    assert row['covered_options']==['0']
    assert row['observed_position_domain']==list(map(str,range(8)))
    assert row['origin_mode_id']=='SPIN' and row['kind']=='CHOICE_BRANCH'

def test_official_har_choices_and_no_paid_features():
    import json
    from tester_spin.providers.pragmatic_modes import discover_modes
    from tester_spin.providers.pragmatic_har_states import parse_fs_options
    fixture=json.loads((Path(__file__).parent/'fixtures/pragmatic_progressive_choices.json').read_text(encoding='utf-8'))
    assert [m.kind for m in discover_modes(fixture['init']).enabled()]==['SPIN']
    seen=set()
    for exchange in fixture['choices']:
        request=exchange['request'];before=exchange['before'];after=exchange['after']
        if request['action']=='doBonus':
            assert bonus_transition(before,override=request['ind'])['fields']=={'ind':request['ind']}
            assert after['end']=='1' and after['status'].split(',')[int(request['ind'])]=='1'
        else:
            assert int(request['ind']) in [o['index'] for o in parse_fs_options(before)]
            seen.add(request['ind'])
            assert after['fsmax']=={'0':'20','1':'10','2':'5'}[request['ind']]
    assert seen=={'0','1','2'}

def test_persistent_progress_is_not_an_active_bonus(tmp_path):
    provider=PragmaticProvider(tmp_path)
    state={'na':'s','prg_m':'cp,tp,r,acw','prg':'39,40,0,7.20'}
    assert not provider._feature_active(state)
    provider._post_and_store=Mock(side_effect=[(200,b'',state,{})]*2)
    with audit_scope():
        proof=pragmatic_check(provider,SimpleNamespace(symbol='demo',reel_contract=None),state,{'symbol':'demo'},tmp_path,1)
    assert proof['status']=='CONFIRMED'
    assert [c.args[1]['action'] for c in provider._post_and_store.call_args_list]==['doSpin','doSpin']
