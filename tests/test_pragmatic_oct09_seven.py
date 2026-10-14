import json
from pathlib import Path
from tester_spin.providers.pragmatic_observed_transitions import bonus_transition

def captures():return json.loads((Path(__file__).parent/'fixtures/pragmatic_oct09_seven.json').read_text())

def test_hold_spin_continues_all_observed_lives_and_resets():
    game=next(g for g in captures() if g['symbol']=='vswaysfltdrg')
    assert len(game['choices'])==8
    for x in game['choices']:
        selection=bonus_transition(x['before'],override=x['ind'])
        assert selection is not None and selection['fields']=={'ind':'0'}
        assert selection['domain']==['0']

def test_repeatable_yes_no_menu_does_not_split_by_depth():
    game=next(g for g in captures() if g['symbol']=='vswayswildb')
    selections=[bonus_transition(x['before'],override=x['ind']) for x in game['choices']]
    assert len({s.get('coverage_branch_signature',s['branch_signature']) for s in selections})==1
    assert all(s['coverage_policy']=='repeatable-menu-actions/v1' for s in selections)


def test_repeatable_coverage_annotation_preserves_its_policy(tmp_path):
    from tester_spin.models import GameTestResult, SpinAttempt
    from tester_spin.providers.pragmatic_bonus_coverage import annotate_bonus_coverage
    game=next(g for g in captures() if g['symbol']=='vswayswildb')
    item=game['choices'][0]
    record=bonus_transition(item['before'],override=item['ind'])
    (tmp_path/'step-001-bonus.bonus-selection.json').write_text(json.dumps(record))
    (tmp_path/'step-001-bonus.response.json').write_text(json.dumps(item['after']))
    (tmp_path/'return-to-base.json').write_text(json.dumps({'status':'CONFIRMED','consecutive_base':2}))
    result=GameTestResult(provider='pragmatic',slug='test',game_name='Test',game_url='https://example.invalid',
        requested_spins=1,successful_spins=1,failed_spins=0,status='OK',
        attempts=[SpinAttempt(number=1,ok=True,terminal=True,mode_id='PURCHASE_1',artifact_dir=str(tmp_path))])
    annotate_bonus_coverage(result)
    row=next(m for m in result.discovered_modes if m.get('kind')=='CHOICE_BRANCH')
    assert row['coverage_policy']=='repeatable-menu-actions/v1'

def test_range_pick_uses_hidden_position_structural_policy():
    game=next(g for g in captures() if g['symbol']=='vs20bblup')
    for x in game['choices']:
        s=bonus_transition(x['before'],override=x['ind'])
        assert s['coverage_policy']=='hidden-position-structural/v1'
        assert x['ind'] in s['domain']

def test_all_recorded_selections_and_acknowledgements():
    from tester_spin.providers.pragmatic_observed_transitions import repeatable_yes_no_acknowledged,range_pick_acknowledged
    for game in captures():
        for x in game['choices']:
            selection=bonus_transition(x['before'],override=x['ind'])
            assert selection is not None and selection['fields']=={'ind':x['ind']}
            if selection.get('coverage_policy')=='repeatable-menu-actions/v1':
                assert repeatable_yes_no_acknowledged(selection,x['after'])
                assert not repeatable_yes_no_acknowledged(selection,x['before'])
            if selection.get('pick_size'):
                assert range_pick_acknowledged(selection,x['after'])
                assert not range_pick_acknowledged(selection,x['before'])

def test_counter_shape_does_not_accept_unknown_actions_or_lives():
    import pytest
    from tester_spin.providers.pragmatic_observed_transitions import counter_bonus_continuation
    state=next(g for g in captures() if g['symbol']=='vswaysfltdrg')['choices'][1]['before']
    assert counter_bonus_continuation({**state,'g':state['g'].replace('lifes:"2"','lifes:"3"')}) is None
    assert counter_bonus_continuation({**state,'na':'s'}) is None
    with pytest.raises(ValueError):counter_bonus_continuation(state,override='1')

def test_repeatable_history_must_match_available_positions():
    from tester_spin.providers.pragmatic_observed_transitions import repeatable_yes_no_selection
    state=next(g for g in captures() if g['symbol']=='vswayswildb')['choices'][-1]['before']
    assert repeatable_yes_no_selection({**state,'g':state['g'].replace('0~0','0~2')}) is None

def test_range_ack_rejects_changes_to_other_cells():
    from tester_spin.providers.pragmatic_observed_transitions import range_pick_acknowledged
    game=next(g for g in captures() if g['symbol']=='vs20bblup')
    for x in [game['choices'][0],game['choices'][3]]:
        selection=bonus_transition(x['before'],override=x['ind'])
        after=x['after']
        assert not range_pick_acknowledged(selection,{**after,'g':after['g'].replace('status:"','status:"999,',1)})
        import re
        match=re.search(r'status:"([^"]+)"',after['g']);values=match[1].split(',')
        other=next(i for i in range(len(values)) if str(i)!=x['ind']);values[other]='999'
        bad=after['g'][:match.start(1)]+','.join(values)+after['g'][match.end(1):]
        assert not range_pick_acknowledged(selection,{**after,'g':bad})
