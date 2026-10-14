import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import wager_state, continuation_request, validate_transition, Unsupported
DEFINITION=json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_definition.json').read_text())
CONTEXT={'bbg_definition':DEFINITION}

ROWS = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_parameterized_bonus.json').read_text(encoding='utf-8'))

def test_bonus_refusal_preserves_award_then_requests_the_bulk_freespins():
    before = wager_state(ROWS['BUY_BONUS'])
    request = continuation_request(before, constraints=CONTEXT)
    assert request['cmd'] == 'Bonus' and request['amount'] == '0' and (request['step'] == '2')
    assert json.loads(request['clientParams']) == {'bonusRound': False, 'playerChoice': -1}
    after = wager_state(ROWS['Bonus'])
    validate_transition(before, after, request, constraints=CONTEXT)
    after['root_step'] = before['root_step']
    play = continuation_request(after, constraints=CONTEXT)
    assert play['cmd'] == 'FreeSpin' and play['step'] == '3' and (play['betid'] == '1') and (play['amount'] == '0')
    assert json.loads(play['clientParams']) == {'bonusRound': False}
    full = wager_state(ROWS['FreeSpin'])
    validate_transition(after, full, play, constraints=CONTEXT)
    assert full['commands'] == ['C']

@pytest.mark.parametrize('bad', [True, 0, -1, '8'])
def test_awarded_count_must_be_current_positive_integer(bad):
    state = wager_state(deepcopy(ROWS['BUY_BONUS']))
    state['bets'][-1]['eventdata']['response']['clientData']['freeSpinsLeft'] = bad
    with pytest.raises(Unsupported):
        continuation_request(state, constraints=CONTEXT)

@pytest.mark.parametrize('kind', ['echo', 'lost', 'quantity', 'foreign_menu'])
def test_refusal_requires_echo_and_same_offered_free_spins(kind):
    before = wager_state(ROWS['BUY_BONUS'])
    after = wager_state(deepcopy(ROWS['Bonus']))
    request = continuation_request(before, constraints=CONTEXT)
    bd = after['bets'][0]['betdata']
    cd = after['bets'][-1]['eventdata']['response']['clientData']
    if kind == 'echo':
        bd['clientParams']['playerChoice'] = 1
    elif kind == 'lost':
        cd['GambleAwarded'] = 'True'
    elif kind == 'quantity':
        cd['freeSpinsAwarded'] = cd['freeSpinsLeft'] = 12
    else:
        after['commands'] = ['Bonus']
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def test_freespin_echo_must_acknowledge_non_bonus_round():
    before = wager_state(ROWS['Bonus'])
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(deepcopy(ROWS['FreeSpin']))
    after['bets'][0]['betdata']['clientParams']['bonusRound'] = True
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def bbg_state():
    row = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_award.json').read_text())
    return wager_state(row)

def test_bbg_current_award_uses_sdk_no_gamble_parameters():
    state = bbg_state()
    request = continuation_request(state, constraints=CONTEXT)
    assert request['cmd'] == 'Bonus' and request['amount'] == '0'
    assert json.loads(request['clientParams']) == {'bonusRound': False, 'playerChoice': -1}

@pytest.mark.parametrize('field,value', [('gambleAwarded', True), ('freeSpinsAwarded', False), ('finished', True), ('nextActions', ['Spin']), ('reelId', 'FreeSpin'), ('totalWinnings', 12), ('isSuperBuyBonusActive', True), ('newChoice', 1), ('initialGrid', [[True]])])
def test_bbg_refusal_does_not_guess_unknown_or_changed_award(field, value):
    state = bbg_state()
    state['bets'][-1]['eventdata']['response']['clientData'][field] = value
    with pytest.raises(Unsupported):
        continuation_request(state, constraints=CONTEXT)

def test_parameter_artifacts_keep_current_offer_and_all_generated_results(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    runtime = DemoRuntime(None, 'fixture', 1, threading.Event(), gate=None)
    before = wager_state(ROWS['BUY_BONUS'])
    runtime.save(tmp_path, 1, {'cmd': 'BUY_BONUS'}, before)
    menu = json.loads((tmp_path / 'step-001-response.json').read_text())['sdk_parameter_menu']
    assert menu['free_spins_awarded'] == 8
    assert menu['options']['playerChoice'] == {'-1': 'KEEP_CURRENT_FREE_SPINS', '1': 'GAMBLE'}
    after = wager_state(ROWS['Bonus'])
    request = continuation_request(after, constraints=CONTEXT)
    full = wager_state(ROWS['FreeSpin'])
    runtime.save(tmp_path, 2, request, full, transition_validated=True)
    result = json.loads((tmp_path / 'step-002-response.json').read_text())
    assert result['sdk_parameter_request']['parameters'] == {'bonusRound': False}
    assert result['sdk_parameter_request']['transition_validated'] is True
    expected = [b for b in full['bets'] if isinstance(((b.get('eventdata') or {}).get('response') or {}).get('clientData'), dict)]
    assert len(result['parameterized_bonus_results']) == len(expected)
    assert result['parameterized_bonus_results'][-1]['clientData'] == expected[-1]['eventdata']['response']['clientData']
    assert 'fixture-parameter-round' not in json.dumps(result)
    runtime.save(tmp_path, 3, request, full, transition_validated=False)
    assert json.loads((tmp_path / 'step-003-response.json').read_text())['sdk_parameter_request']['transition_validated'] is False

def test_bbg_refusal_resets_entry_flags_but_keeps_current_awarded_quantity():
    before = bbg_state()
    request = continuation_request(before, constraints=CONTEXT)
    after = wager_state(json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_refusal.json').read_text()))
    validate_transition(before, after, request, constraints=CONTEXT)
    follow = continuation_request(after, constraints=CONTEXT)
    assert follow['cmd'] == 'FreeSpin' and follow['amount'] == '0'
    assert 'clientParams' not in follow
    after['bets'][-1]['eventdata']['response']['clientData']['freeSpinState']['spinsRemaining'] = 6
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def test_bbg_refusal_requires_post_choice_free_spin_state_not_relabelled_root():
    before = bbg_state()
    request = continuation_request(before, constraints=CONTEXT)
    row = json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_refusal.json').read_text())
    after = wager_state(row)
    wrong = deepcopy(before['bets'][-1]['eventdata']['response']['clientData'])
    wrong['currentAction'] = 'Bonus'
    wrong['nextActions'] = ['FreeSpin']
    after['bets'][-1]['eventdata']['response']['clientData'] = wrong
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)

def bbg_fixture(name):
    return wager_state(json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_bbg_' + name + '.json').read_text()))

def test_bbg_current_free_spin_continues_only_remaining_awarded_spins():
    before = bbg_fixture('refusal')
    request = continuation_request(before, constraints=CONTEXT)
    after = bbg_fixture('free_spin')
    validate_transition(before, after, request, constraints=CONTEXT)
    assert continuation_request(after, constraints=CONTEXT)['cmd'] == 'FreeSpin'
    after['bets'][-1]['eventdata']['response']['clientData']['freeSpinState']['spinsRemaining'] = 7
    with pytest.raises(Unsupported):
        validate_transition(before, after, request, constraints=CONTEXT)
