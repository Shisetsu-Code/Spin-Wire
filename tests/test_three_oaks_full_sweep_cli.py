"""Unit checks for local Windows 3 Oaks sequential sweep, no network calls."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tester_spin.models import Game
from tools.three_oaks_full_sweep import access_restricted, parse_snapshot, public_catalogue, safe_error, safe_trace


class LocalThreeOaksSweepTests(unittest.TestCase):
    def test_http_403_and_429_end_provider_checks(self):
        self.assertTrue(access_restricted("HTTPError: 403 Client Error: Forbidden for url: https://demo.invalid/"))
        self.assertTrue(access_restricted("HTTPError: 429 Client Error: Too Many Requests"))
        self.assertTrue(access_restricted("HTTP 403"))
        self.assertFalse(access_restricted("game outcome was 403 coins"))
        self.assertFalse(access_restricted("HTTP 200"))
        self.assertFalse(access_restricted("HTTP 404"))

    def test_snapshot_validation_rejects_unknown_or_duplicate_urls(self):
        game = {"provider": "3oaks", "slug": "15_dragon_pearls",
                "name": "15 Dragon Pearls", "url": "https://3oaks.com/game/15_dragon_pearls"}
        self.assertEqual(len(parse_snapshot([game])), 1)
        with self.assertRaisesRegex(ValueError, "Invalid/duplicate"):
            parse_snapshot([game, game])
        with self.assertRaisesRegex(ValueError, "Invalid/duplicate"):
            parse_snapshot([{**game, "url": "https://invalid.example/game/15_dragon_pearls"}])

    def test_live_catalogue_uses_provider_not_cloud_snapshot(self):
        class Provider:
            def __init__(self):
                self._thumbnail = None
                self.calls = 0

            def crawl_catalog(self, **kwargs):
                self.calls += 1
                self.assert_page_limit = kwargs["max_pages"]
                return [
                    Game("3oaks", "lady_fortune", "Lady Fortune",
                         "https://3oaks.com/game/lady_fortune"),
                    Game("3oaks", "15_dragon_pearls", "15 Dragon Pearls",
                         "https://3oaks.com/game/15_dragon_pearls"),
                ]

        provider = Provider()
        with patch("tools.three_oaks_full_sweep.SNAPSHOT", Path("definitely-absent-snapshot.json")):
            games = public_catalogue(provider, "live")
        self.assertEqual(provider.calls, 1)
        self.assertEqual(provider.assert_page_limit, 100)
        self.assertEqual([g.slug for g in games], ["lady_fortune", "15_dragon_pearls"])

    def test_only_sanitized_wire_fields_get_exported(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            request = {
                "command": "play", "request_id": "private-request-id",
                "session_id": "private-session", "client_command_timestamp": 123,
                "action": {"name": "buy_spin", "params": {
                    "selected_mode": 0, "bet_per_line": 2, "lines": 5, "token": "secret",
                }},
            }
            response = {
                "session_id": "private-session", "user": {"huid": "private-user"},
                "status": {"code": "OK"},
                "context": {"current": "bonus", "round_finished": False,
                            "actions": ["respin"], "bonus": {"back_to": "spins"}},
            }
            (folder / "000-play.request.json").write_text(json.dumps(request), encoding="utf-8")
            (folder / "000-play.response.raw.json").write_text(json.dumps(response), encoding="utf-8")
            trace, returns = safe_trace(folder)
            self.assertEqual(returns, [])
            self.assertEqual(len(trace), 1)
            self.assertEqual(trace[0]["params"], {
                "selected_mode": 0, "bet_per_line": 2, "lines": 5,
            })
            output = json.dumps(trace)
            for text in ("private", "secret", "huid", "session_id", "request_id", "token"):
                self.assertNotIn(text, output)

    def test_error_sanitization_hides_query_tokens(self):
        message = safe_error("HTTPError token=secret-value https://3oaks.com/path?session_id=hidden")
        self.assertNotIn("secret-value", message)
        self.assertNotIn("hidden", message)


if __name__ == "__main__":
    unittest.main()
