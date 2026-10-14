import json
from pathlib import Path
from tester_spin.providers.pragmatic_observed_transitions import bonus_transition

def test_parameter_values_and_history_do_not_create_new_controls():
    rows=json.loads((Path(__file__).parent/'fixtures/pragmatic_parameterized_gamble.json').read_text())
    signatures=set()
    roles=set()
    for row in rows:
        pick=bonus_transition(row['before'],override=row['selected'])
        assert pick['fields']=={'ind':row['selected']}
        signatures.add(pick.get('coverage_branch_signature',pick['branch_signature']))
        assert pick['coverage_policy']=='parameterized-menu-actions/v1'
        roles.update(pick['coverage_domain_map'].values())
    assert len(signatures)==1
    assert roles=={'0','1','2'}

def test_server_acknowledges_each_har_choice():
    from tester_spin.providers.pragmatic_observed_transitions import parameterized_gamble_acknowledged
    rows=json.loads((Path(__file__).parent/'fixtures/pragmatic_parameterized_gamble.json').read_text())
    for row in rows:
        pick=bonus_transition(row['before'],override=row['selected'])
        assert parameterized_gamble_acknowledged(pick,row['after'])
        assert not parameterized_gamble_acknowledged(pick,row['before'])

def test_incompatible_numeric_relationship_is_not_normalized():
    rows=json.loads((Path(__file__).parent/'fixtures/pragmatic_parameterized_gamble.json').read_text())
    bad={**rows[0]['before'],'g':rows[0]['before']['g'].replace('sm5s7-6','sm5s7-2')}
    assert bonus_transition(bad).get('coverage_policy')!='parameterized-menu-actions/v1'

def test_reduced_sp_menu_keeps_wire_position_and_semantic_role_separate():
    state={'na':'b','g':'{gambling:{ask:"0",bgid:"0",bgt:"69",ch_k:"play,sp3s5-6",ch_v:"0,2",end:"0",level:"0",lifes:"1",rw:"0.00"}}'}
    pick=bonus_transition(state,override='1')
    assert pick['fields']=={'ind':'1'}
    assert pick['coverage_domain_map']=={'0':'0','1':'2'}

def test_coverage_combines_parameters_but_requires_acknowledgement(tmp_path):
    from tester_spin.models import GameTestResult,SpinAttempt
    from tester_spin.providers.pragmatic_bonus_coverage import annotate_bonus_coverage
    rows=json.loads((Path(__file__).parent/'fixtures/pragmatic_parameterized_gamble.json').read_text())
    chosen=[next(row for row in rows if row['selected']==i) for i in ['0','1','2']]
    result=GameTestResult(provider='pragmatic',slug='test',game_name='Test',game_url='https://example.invalid',requested_spins=3,successful_spins=3,failed_spins=0,status='OK')
    for number,row in enumerate(chosen,1):
        d=tmp_path/f'attempt-{number}';d.mkdir()
        result.attempts.append(SpinAttempt(number=number,ok=True,terminal=True,mode_id='PURCHASE_1',artifact_dir=str(d)))
        (d/'return-to-base.json').write_text(json.dumps({'status':'CONFIRMED','consecutive_base':2}))
        (d/'step-000-bonus.bonus-selection.json').write_text(json.dumps(bonus_transition(row['before'],override=row['selected'])))
        (d/'step-000-bonus.response.json').write_text(json.dumps(row['after']))
    annotate_bonus_coverage(result)
    branches=[r for r in result.discovered_modes if r.get('kind')=='CHOICE_BRANCH']
    assert len(branches)==1 and branches[0]['covered_options']==['0','1','2']
    # A successful HTTP response without the selected history is not a sample.
    (tmp_path/'attempt-3/step-000-bonus.response.json').write_text(json.dumps(chosen[2]['before']))
    result.status='OK';annotate_bonus_coverage(result)
    assert result.status=='PARCIAL'
    assert result.discovered_modes[-1]['covered_options']==['0','1']

def test_legacy_records_reconstructed_from_previous_response(tmp_path):
    from tester_spin.providers.pragmatic_bonus_coverage import _canonical_selection
    row=json.loads((Path(__file__).parent/'fixtures/pragmatic_parameterized_gamble.json').read_text())[0]
    (tmp_path/'step-000-spin.response.json').write_text(json.dumps(row['before']))
    old={'branch_signature':'PRAGMATIC:bonus-choice:bgt=69:choices=0,1,2:family=gambling:labels=play,sm5s7-6,sp7s5-6','selected':row['selected']}
    path=tmp_path/'step-001-bonus.bonus-selection.json';path.write_text(json.dumps(old))
    normalized=_canonical_selection(path,old)
    assert normalized['coverage_policy']=='parameterized-menu-actions/v1'
    assert json.loads(path.read_text())==old

def test_ack_rejects_incompatible_bonus_identity():
    from tester_spin.providers.pragmatic_observed_transitions import parameterized_gamble_acknowledged
    row=json.loads((Path(__file__).parent/'fixtures/pragmatic_parameterized_gamble.json').read_text())[0]
    pick=bonus_transition(row['before'],override=row['selected'])
    for before,after in [('bgt:"69"','bgt:"70"'),('bgid:"0"','bgid:"1"'),('sp6s5-6','sp6s5-9')]:
        assert not parameterized_gamble_acknowledged(pick,{**row['after'],'g':row['after']['g'].replace(before,after)})

def test_reduced_sp_ack_retains_wire_index():
    from tester_spin.providers.pragmatic_observed_transitions import parameterized_gamble_acknowledged
    before={'na':'b','g':'{gambling:{ask:"0",bgid:"0",bgt:"69",ch_k:"play,sp3s5-6",ch_v:"0,2",end:"0",level:"0",lifes:"1",rw:"0.00"}}'}
    after={'na':'c','g':'{gambling:{bgid:"0",bgt:"69",ch_h:"0~1",ch_k:"play,sp3s5-6",ch_v:"0,2",end:"1",level:"1",lifes:"0",rw:"0.00"}}'}
    pick=bonus_transition(before,override='1')
    assert pick['coverage_domain_map']['1']=='2'
    assert parameterized_gamble_acknowledged(pick,after)
    assert not parameterized_gamble_acknowledged(pick,{**after,'g':after['g'].replace('0~1','0~2')})
