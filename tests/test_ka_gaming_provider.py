from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from tester_spin.models import Game
from tester_spin.providers.ka_gaming.adapter import KAGamingProvider


class KAGamingProviderTests(unittest.TestCase):
    def test_session_bound_runtime_stays_partial(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = KAGamingProvider(Path(directory))
            result = provider.test_game(Game("ka_gaming", "a", "Alpha", "https://demo/?g=A", symbol="A"), spins=1, timeout_s=1, stop_event=threading.Event(), progress=lambda _: None)
        self.assertEqual(result.status, "PARCIAL")
        self.assertEqual(result.successful_spins, 0)
        self.assertIn("vds", result.error)
        self.assertEqual(result.discovered_modes[0]["request_type"], "fr")
