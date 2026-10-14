import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.belatra_exhaustive import _continue_round

ROUNDS = json.loads((Path(__file__).parent / 'fixtures/belatra_oct09_rounds.json').read_text(encoding='utf-8'))

@pytest.mark.parametrize('round_data', ROUNDS, ids=[f"{r['source']}-{i}" for i,r in enumerate(ROUNDS)])
def test_official_har_round_replays_every_continuation(round_data, tmp_path):
    exchanges = deepcopy(round_data['exchanges'])
    pending = exchanges[1:]
    class Provider:
        def _post_direct_game(self, state, request, **kwargs):
            expected = pending.pop(0)
            expected_body = {k: v for k, v in expected['request'].items() if k != 'ghistId' or request['q'] == 'finish'}
            assert request == expected_body
            return expected['response']
    outcome = _continue_round(Provider(), {}, exchanges[0]['response'], timeout_s=1, artifact_dir=tmp_path)
    assert outcome[0] is True
    assert outcome[1] == len(exchanges)
    assert outcome[2:] == ('finished', 'toIdle')
    assert not pending

@pytest.mark.parametrize('changes', [
    {'other': {}},
    {'subGameInfo': []},
    {'other': {'autochoice': 'invented-option'}},
])
def test_unknown_bonus_control_is_not_executed(changes, tmp_path):
    initial = {'gs': {'historyId': 12, 'phaseCur': 'Bonus2', 'phaseNext': 'toBonus2',
                     'other': {'autochoice': 'start'},
                     'subGameInfo': [{'category': 'Bonus2', 'attempt': 1,
                                      'respinRemain': 3, 'startRespin': 3,
                                      'stopBox': [[0]]}]}}
    initial['gs'].update(changes)
    class Provider:
        def _post_direct_game(self, *args, **kwargs):
            pytest.fail('Unknown control must remain pending')
    assert not _continue_round(Provider(), {}, initial, timeout_s=1, artifact_dir=tmp_path)[0]


def test_unacknowledged_bonus_attempt_is_not_repeated(tmp_path):
    initial = {'gs': {'historyId': 12, 'phaseCur': 'Bonus2', 'phaseNext': 'toBonus2',
                     'other': {'autochoice': 'start'},
                     'subGameInfo': [{'category': 'Bonus2', 'attempt': 1,
                                      'respinRemain': 3, 'startRespin': 3,
                                      'stopBox': [[0]], 'userChoice': 'start'}]}}
    calls = []
    class Provider:
        def _post_direct_game(self, state, request, **kwargs):
            calls.append(request)
            return deepcopy(initial)
    assert not _continue_round(Provider(), {}, initial, timeout_s=1, artifact_dir=tmp_path)[0]
    assert len(calls) == 1


def test_return_probe_preserves_free_round_and_requires_ordinary_base_cycles(tmp_path, monkeypatch):
    import tester_spin.provider_return_checks as checks
    monkeypatch.setattr(checks, 'verify_return_to_base', lambda directory, play, **kwargs: play(directory))
    exchanges = [
        ('start', {'q': 'start'}, {'gs': {'phaseCur': 'basedeal', 'phaseNext': 'toNextFG'}}),
        ('continue-001', {'q': 'play', 'userAction': 'askNextFG'}, {'gs': {'phaseCur': 'freedeal', 'phaseNext': 'toPaid'}}),
        ('finish', {'q': 'finish'}, {'gs': {'phaseCur': 'finished', 'phaseNext': 'toIdle'}}),
    ]
    class Provider:
        def _execute_direct_spin(self, state, *, attempt_dir, **kwargs):
            for label, req, resp in exchanges:
                (attempt_dir / f'{label}.request.json').write_text(json.dumps(req))
                (attempt_dir / f'{label}.response.json').write_text(json.dumps(resp))
            return True, True, 3, 'finished', 'toIdle'
    probe = checks.belatra_check(Provider(), {}, tmp_path, 1)
    assert [c['request']['q'] for c in probe['captures']] == ['start', 'play', 'finish']
    assert probe['known'] is True
    assert probe['base'] is False
