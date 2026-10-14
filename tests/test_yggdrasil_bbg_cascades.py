import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import wager_state, continuation_request, validate_transition, Unsupported
DEFINITION=json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_definition.json').read_text())
CONTEXT={'bbg_definition':DEFINITION}

ROWS = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_cascade_sequence.json').read_text())

def test_real_bbg_sequence_accounts_cascades_without_creating_another_purchase():
    before = wager_state(ROWS[0])
    for row in ROWS[1:]:
        request = continuation_request(before, constraints=CONTEXT)
        assert request['amount'] == '0'
        after = wager_state(row)
        validate_transition(before, after, request, constraints=CONTEXT)
        after['root_step'] = before['root_step']
        before = after
    assert before['bets'][-1]['eventdata']['response']['clientData']['currentWinnings'] == 5.24
    assert continuation_request(before, constraints=CONTEXT)['cmd'] == 'FreeSpin'

@pytest.mark.parametrize('change', ['money', 'board_position', 'counter', 'stake', 'unknown_reward', 'unknown_field'])
def test_positive_cascade_requires_consistent_wire_geometry_money_and_progress(change):
    before = wager_state(ROWS[-2])
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(deepcopy(ROWS[-1]))
    cd = after['bets'][-1]['eventdata']['response']['clientData']
    first = cd['cascadeDetails'][0]
    if change == 'money':
        first['wins'][0]['winnings'] = 99
    elif change == 'board_position':
        first['wins'][0]['symbolPos'][0] = 99
    elif change == 'counter':
        cd['freeSpinState']['spinsRemaining'] += 1
    elif change == 'stake':
        cd['stake'] *= 2
    elif change == 'unknown_reward':
        first['rewardAwarded'] = 'NewRiskChoice'
    else:
        cd['newChoice'] = ['yes', 'no']
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

@pytest.mark.parametrize('field,value', [('wildOffSets', [{}]), ('rewardAwarded', []), ('cascadeIndex', True), ('accumulativeWinnings', float('nan')), ('doubleWildOffset', 999)])
def test_malformed_cascade_stays_unsupported_instead_of_crashing(field, value):
    before = wager_state(ROWS[-2])
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(deepcopy(ROWS[-1]))
    after['bets'][-1]['eventdata']['response']['clientData']['cascadeDetails'][0][field] = value
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

@pytest.mark.parametrize('change', ['accumulator', 'response_cash', 'previous_cash'])
def test_bbg_cycle_binds_cash_to_wire_response_and_previous_round_total(change):
    before = wager_state(deepcopy(ROWS[-2]))
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(deepcopy(ROWS[-1]))
    ed = after['bets'][-1]['eventdata']
    if change == 'accumulator':
        ed['accWa'] = '10.00'
    elif change == 'response_cash':
        ed['response']['cashWin'] = 10
    else:
        before['bets'][-1]['eventdata']['response']['clientData']['totalWinnings'] = 10
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def test_zero_progress_terminal_cascade_is_only_valid_at_final_no_win_board():
    from tester_spin.providers.yggdrasil.bbg_cascades import cascade_cash
    cd = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_cascade_terminal_row.json').read_text())
    assert str(cascade_cash(cd, definition=DEFINITION)) == '11.74'
    cd['cascadeDetails'][0]['cascadeProgressCount'] = 0
    assert cascade_cash(cd, definition=DEFINITION) is None

def test_consistent_geometry_cannot_turn_an_unknown_symbol_into_a_wild():
    before = wager_state(ROWS[-2])
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(deepcopy(ROWS[-1]))
    cd = after['bets'][-1]['eventdata']['response']['clientData']
    cd['initialGrid'][1][0] = cd['cascadeDetails'][0]['cascadeGrid'][1][0] = 65535
    for win in cd['cascadeDetails'][0]['wins']:
        for i, p in enumerate(win['symbolPos']):
            if p == 1:
                win['winSymbols'][i] = 65535
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def ordinary_fixture():
    return wager_state(json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_ordinary_cascade.json').read_text()))

def test_paid_bbg_cascade_is_ordinary_only_with_no_feature_and_cash_bound_to_current_stake():
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    assert ordinary_round(ordinary_fixture(), constraints=CONTEXT)

@pytest.mark.parametrize('change', ['purchase', 'award', 'paid_amount', 'dto_stake', 'cash_response', 'unknown_field'])
def test_ordinary_bbg_cascades_require_real_base_wager_and_conserved_money(change):
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    state = ordinary_fixture()
    bet = state['bets'][0]
    ed = bet['eventdata']
    cd = ed['response']['clientData']
    if change == 'purchase':
        cd['isBuyBonusActive'] = True
    elif change == 'award':
        cd['freeSpinsAwarded'] = 1
    elif change == 'paid_amount':
        bet['betamount'] = '10.00'
    elif change == 'dto_stake':
        cd['stake'] = 2
    elif change == 'cash_response':
        ed['response']['cashWin'] = 2
    else:
        cd['newControl'] = 1
    assert not ordinary_round(state, constraints=CONTEXT)

@pytest.mark.parametrize('location', ['eventdata', 'response', 'betdata', 'initialPlayerState', 'playerState'])
def test_ordinary_bbg_does_not_ignore_unknown_envelope_controls(location):
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    state = ordinary_fixture()
    bet = state['bets'][0]
    ed = bet['eventdata']
    target = bet['betdata'] if location == 'betdata' else ed['response'] if location == 'response' else ed[location] if location != 'eventdata' else ed
    target['pendingChoice'] = ['left', 'right']
    assert not ordinary_round(state, constraints=CONTEXT)

def test_extra_life_links_zero_win_frame_to_declared_replacement_board():
    from tester_spin.providers.yggdrasil.bbg_cascades import cascade_cash
    cd = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_extra_life.json').read_text())
    assert str(cascade_cash(cd, definition=DEFINITION)) == '2.50'
    cd['cascadeDetails'][4]['extraLifeRemoveOffset'].append(12)
    assert cascade_cash(cd, definition=DEFINITION) is None

@pytest.mark.parametrize('location', ['eventdata', 'response', 'betdata', 'playerState', 'initialPlayerState'])
def test_bbg_free_spin_ack_does_not_ignore_unknown_envelope_controls(location):
    before = wager_state(ROWS[-2])
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(deepcopy(ROWS[-1]))
    bet = after['bets'][-1]
    ed = bet['eventdata']
    target = bet['betdata'] if location == 'betdata' else ed['response'] if location == 'response' else ed[location] if location != 'eventdata' else ed
    target['pendingChoice'] = ['left', 'right']
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def test_closed_losing_bbg_ordinary_may_omit_both_collect_domain_fields():
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    state = ordinary_fixture()
    b = state['bets'][0]
    ed = b['eventdata']
    cd = ed['response']['clientData']
    cd.pop('cascadeDetails')
    cd['finalGrid'] = deepcopy(cd['initialGrid'])
    for k in ('currentWinnings', 'totalWinnings', 'baseGameWinnings'):
        cd[k] = 0
    ed['playerState'] = {k: v for k, v in cd.items() if k != 'wins'}
    ed.pop('nextCmds')
    b['betdata'].pop('cmds')
    b['betdata']['accWa'] = ed['accWa'] = ed['response']['cashWin'] = 0
    assert ordinary_round(state, constraints=CONTEXT)
    ed['nextCmds'] = False
    assert not ordinary_round(state, constraints=CONTEXT)

def test_bbg_reply_cash_is_current_spin_while_accwa_is_running_total():
    rows = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_current_vs_accumulated_cash.json').read_text())
    before = wager_state(rows[0])
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(rows[1])
    validate_transition(before, after, request, constraints=CONTEXT)
    assert continuation_request(after, constraints=CONTEXT)['cmd'] == 'FreeSpin'
    ed = after['bets'][-1]['eventdata']
    assert ed['accWa'] == '0.06' and ed['response']['cashWin'] == '0.00'
    ed['response']['cashWin'] = '0.06'
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def test_mission_goal_is_threshold_not_cap_on_reported_progress():
    from tester_spin.providers.yggdrasil.bbg_cascades import boost_data_valid
    boost = {'data': [{'mission': 'WildCollector', 'goal': 20, 'progress': 21, 'states': []}]}
    assert boost_data_valid(boost)
    boost['data'][0]['pendingChoice'] = ['left', 'right']
    assert not boost_data_valid(boost)

def test_extra_life_can_follow_no_win_progress_one_and_drop_the_retained_wild():
    from tester_spin.providers.yggdrasil.bbg_cascades import cascade_cash
    cd = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_extra_life_gravity.json').read_text())
    assert cascade_cash(cd, definition=DEFINITION) is not None
    row = next((x for x in cd['cascadeDetails'] if 'extraLifeRemoveOffset' in x))
    row['cascadeGrid'][0][2] = 65535
    assert cascade_cash(cd, definition=DEFINITION) is None


def test_symbol_and_position_codes_follow_current_definition_without_numeric_aliases():
    from tester_spin.providers.yggdrasil.bbg_cascades import cascade_cash
    cd=deepcopy(wager_state(ROWS[-1])['bets'][-1]['eventdata']['response']['clientData'])
    definition=deepcopy(DEFINITION)
    definition['symbolDefs']['47']=definition['symbolDefs'].pop('0')
    definition['winDefs']['47:5']=definition['winDefs'].pop('0:5')
    definition['winDefs']['47:5']['symbol']='47'
    for col in definition['viewDefs']['view']:
        for i,p in enumerate(col):col[i]=p+100
    for board in [cd['initialGrid'],cd['finalGrid']]+[r['cascadeGrid'] for r in cd['cascadeDetails']]:
        for col in board:
            for i,sym in enumerate(col):
                if sym==0:col[i]=47
    for row in cd['cascadeDetails']:
        for key in ('wildOffSets','wildStackOffsets','offsetsToRemove'):
            row[key]=[p+100 for p in row[key]]
        if row['doubleWildOffset']!=-1:row['doubleWildOffset']+=100
        for win in row['wins']:
            win['symbolPos']=[p+100 for p in win['symbolPos']]
            win['winSymbols']=[47 if sym==0 else sym for sym in win['winSymbols']]
    assert str(cascade_cash(cd,definition=definition))=='5.24'
    definition['symbolDefs']['47']['isWild']=False
    assert cascade_cash(cd,definition=definition) is None

def test_announced_paytable_rejects_a_self_consistent_but_different_factor():
    from tester_spin.providers.yggdrasil.bbg_cascades import cascade_cash
    cd=deepcopy(wager_state(ROWS[-1])['bets'][-1]['eventdata']['response']['clientData'])
    definition=deepcopy(DEFINITION)
    definition['winDefs'][cd['cascadeDetails'][0]['wins'][0]['id']]['payoutFactor']=99
    assert cascade_cash(cd,definition=definition) is None


def test_prize_multiplier_is_bound_to_its_direction_or_both_full_width_sides():
    from tester_spin.providers.yggdrasil.bbg_cascades import cascade_cash
    cd=deepcopy(wager_state(ROWS[-1])['bets'][-1]['eventdata']['response']['clientData'])
    cd['cascadeDetails'][0]['leftMultiplier']=999
    assert cascade_cash(cd,definition=DEFINITION) is None


def test_seven_free_spins_finish_local_game_then_require_server_collect():
    rows=json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_feature_final.json').read_text())
    before=wager_state(rows[0])
    for row in rows[1:]:
        request=continuation_request(before,constraints=CONTEXT)
        after=wager_state(row);validate_transition(before,after,request,constraints=CONTEXT)
        after['root_step']=before['root_step'];before=after
    assert before['commands']==['C'] and before['terminal'] is False
    cd=before['bets'][-1]['eventdata']['response']['clientData']
    assert cd['finished'] is True and cd['nextActions']==['Spin']
    assert continuation_request(before,constraints=CONTEXT)['cmd']=='C'


def test_direct_current_award_starts_free_spins_without_creating_a_bonus_choice():
    row=json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_direct_award.json').read_text())
    state=wager_state(row);request=continuation_request(state,constraints=CONTEXT)
    assert request['cmd']=='FreeSpin' and request['step']=='2' and request['amount']=='0'
    assert 'clientParams' not in request
    state['bets'][-1]['eventdata']['response']['clientData']['freeSpinState']['triggeringDetails']['offsets']=[5]
    with pytest.raises(Unsupported):continuation_request(state,constraints=CONTEXT)
