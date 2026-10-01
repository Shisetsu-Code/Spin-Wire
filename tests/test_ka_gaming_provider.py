from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from tester_spin.models import Game
from tester_spin.providers.ka_gaming.adapter import KAGamingProvider


class KAGamingProviderTests(unittest.TestCase):
    def test_unofficial_launcher_is_rejected_before_a_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            provider = KAGamingProvider(Path(directory))
            result = provider.test_game(Game("ka_gaming", "a", "Alpha", "https://demo/?g=A", symbol="A"), spins=1, timeout_s=1, stop_event=threading.Event(), progress=lambda _: None)
        self.assertEqual(result.status, "ERROR")
        self.assertEqual(result.successful_spins, 0)
        self.assertIn("launcher no oficial", result.error)
        self.assertEqual(result.discovered_modes[0]["request_type"], "fr")
        rmp = result.discovered_modes[0]["rmp_spin"]
        self.assertEqual(rmp["method"], "POST")
        self.assertIn("/kaga/command/spin", rmp["endpoint_template"])
        self.assertIn("ctx", rmp["required_header"])
        start = result.discovered_modes[0]["rmp_start_game"]
        self.assertIn("/kaga/rmp/startGame", start["endpoint_template"])
        self.assertIn("sid", start["returns"])
        self.assertIn("ida", start["ctx_fields"])
