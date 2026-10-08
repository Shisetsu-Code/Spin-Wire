import json
from pathlib import Path

import unittest
import tempfile
import threading
from copy import deepcopy

from tester_spin.providers.three_oaks.runtime import play_fields


def captured_state():
    return json.loads((Path(__file__).parent / 'fixtures' / 'three_oaks_3coins_spin.json').read_text())


def test_3coins_matches_official_spin_without_bet_factor():
    fixture = captured_state()
    payload = play_fields(fixture['response'], 'spin', game_slug='unseen_title', family='goreel', client_profile={'spin_params':['bet_per_line','lines']})
    assert payload['action'] == fixture['request']['action']


def test_unknown_game_does_not_inherit_captured_profile():
    with unittest.TestCase().assertRaisesRegex(ValueError, 'apuesta'):
        play_fields(captured_state()['response'], 'spin', game_slug='unknown', family='goreel')


def test_known_name_with_unknown_family_stays_unresolved():
    with unittest.TestCase().assertRaisesRegex(ValueError, 'apuesta'):
        play_fields(captured_state()['response'], 'spin', game_slug='3_coins', family='unknown')

def run_captured_adapter(purchases=False):
    from tester_spin.models import Game
    from tester_spin.providers.three_oaks.adapter import ThreeOaksProvider
    config = {'options': {'token': 'fixture', 'queue': 'fixture', 'protocol': 'goreel', 'wl': 'demo'},
              'desktop': {'server_url': '//betman-demo.head.3oaks.com/betman-demo/gs/3_coins/desktop/{QUEUE}/demo/',
                          'client_url': 'https://static.3oaks.com/gs/clients_goreel/3_coins/v1/'}}
    class Response:
        def __init__(self, data=None, text=None):
            self.data = data
            self.text = text if text is not None else json.dumps(data)
        def raise_for_status(self): pass
        def json(self): return self.data
    # This reduced capture contains context lines, not settings.lines. The fake
    # client must read that same UI value rather than a missing settings array.
    class HTTP:
        def get(self, url, **kwargs):
            return Response(text='})(window, ' + json.dumps(config) + ', "url");') if url.endswith('/play') else Response(text=(Path(__file__).parent/'fixtures'/'three_oaks_modern_purchase.js').read_text().replace('name:"buy_spin"','name:"unsupported"').replace('Y.serverData.get("settingsLines")[0]', 'Y.bus.getUI("lines")'))
        def post(self, url, **kwargs):
            request = json.loads(kwargs['data'])
            response = deepcopy(captured_state()['response'])
            response['session_id'] = 'fixture'
            if purchases:
                response['context'].update(actions=['spin', 'buy_spin'], available_buy_bonus=[1])
            if request['command'] == 'play':
                assert request['action']['params'] == {'bet_per_line': 20, 'lines': 5}
            return Response(response)
    with tempfile.TemporaryDirectory() as directory:
        provider = ThreeOaksProvider(Path(directory))
        provider.http = HTTP()
        return provider.test_game(Game('3oaks', '3_coins', '3 Coins', 'https://3oaks.com/game/3_coins'),
                                  spins=2, timeout_s=1, stop_event=threading.Event(), progress=lambda _: None)


def test_adapter_replays_captured_spin_shape():
    result = run_captured_adapter()
    assert result.status == 'OK', result.error
    assert result.successful_spins == 2


def test_spin_profile_does_not_certify_unobserved_purchases():
    result = run_captured_adapter(purchases=True)
    assert result.status == 'OK'
    assert len(result.attempts) == 2  # Only the requested normal spins were sent.
    mode = result.discovered_modes[1]
    assert mode['kind'] == 'DISCOVERED_ONLY'
    assert mode['coverage_required'] is False
    assert mode['client_observed'] is False
    assert not mode['executable']
    assert not mode['validated']
    from tester_spin.feature_summary import feature_summary
    assert 'Compras: Sin datos' in feature_summary(result.to_dict())


def test_original_purchase_payload_remains_unchanged():
    data = captured_state()['response']
    data['context'].update(actions=['spin', 'buy_spin'], available_buy_bonus=[1])
    data['settings'] = {'bet_factor': [10]}
    assert play_fields(data, 'buy_spin', 1)['action']['params'] == {
        'bet_per_line': 20, 'lines': 5, 'bet_factor': 10, 'selected_mode': 1}


if __name__ == '__main__':
    suite = unittest.TestSuite(unittest.FunctionTestCase(f) for f in [test_3coins_matches_official_spin_without_bet_factor, test_unknown_game_does_not_inherit_captured_profile, test_known_name_with_unknown_family_stays_unresolved, test_adapter_replays_captured_spin_shape, test_spin_profile_does_not_certify_unobserved_purchases, test_original_purchase_payload_remains_unchanged])
    result = unittest.TextTestRunner().run(suite)
    raise SystemExit(not result.wasSuccessful())
