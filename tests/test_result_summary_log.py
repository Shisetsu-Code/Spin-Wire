import queue
import unittest
from types import SimpleNamespace

from tester_spin.app_current import CurrentTesterSpinApp
from tester_spin.models import GameTestResult


class ResultSummaryLogTests(unittest.TestCase):
    def test_pragmatic_completion_shows_purchases_and_antebet(self):
        result = GameTestResult(provider='pragmatic', slug='example', game_name='Example',
            game_url='', requested_spins=0, successful_spins=0, failed_spins=0, status='OK',
            discovered_modes=[{'id': 'SPIN', 'kind': 'SPIN'},
                {'id': 'PURCHASE_1', 'kind': 'PURCHASE'},
                {'id': 'PURCHASE_2', 'kind': 'PURCHASE'},
                {'id': 'ANTE_BET_1', 'kind': 'ANTE_BET'}])
        events = queue.Queue()
        events.put(('test_result', result))
        logs = []
        app = SimpleNamespace(_events=events, _games={}, _feature_results={}, _mechanics_index={}, _test_done=0, _test_total=1,
            _MAX_EVENTS_PER_TICK=100, _UI_DRAIN_BUDGET_S=1,
            progress=SimpleNamespace(configure=lambda **kwargs: None),
            status_var=SimpleNamespace(set=lambda value: None),
            _append_log=logs.append, after=lambda *args: None,
            _drain_events=lambda: None)
        CurrentTesterSpinApp._drain_events(app)
        self.assertEqual(app._feature_results['pragmatic::example'], result.to_dict())
        self.assertIn('Compras: Sí | Cantidad: 2 detectadas; total sin confirmar | Antebets: Sí', '\n'.join(logs))
