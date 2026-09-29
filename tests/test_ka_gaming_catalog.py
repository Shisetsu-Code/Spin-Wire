from __future__ import annotations

import unittest

from tester_spin.providers.ka_gaming.catalog import build_launch_url, games_from_catalog


def payload() -> dict:
    return {"status": "ok", "statusCode": 0, "numGames": 2, "gameLaunchURL": "https://demo.kaga88.com/launch", "games": [{"gameId": "A", "gameName": "Alpha", "iconURLPrefix": "https://icons/a"}, {"gameId": "B", "gameName": "Beta"}]}


class KAGamingCatalogTests(unittest.TestCase):
    def test_valid_catalog_builds_deterministic_games(self) -> None:
        games = games_from_catalog(payload(), language="es")
        self.assertEqual([game.slug for game in games], ["a", "b"])
        self.assertEqual(games[0].symbol, "A")
        self.assertIn("g=A", games[0].url)
        self.assertIn("loc=es", games[0].url)

    def test_invalid_counts_or_ids_are_rejected(self) -> None:
        bad = payload(); bad["numGames"] = 3
        with self.assertRaisesRegex(ValueError, "numGames"):
            games_from_catalog(bad, language="es")
        duplicate = payload(); duplicate["games"][1]["gameId"] = "A"
        with self.assertRaisesRegex(ValueError, "duplicado"):
            games_from_catalog(duplicate, language="es")

    def test_launch_requires_https_base(self) -> None:
        with self.assertRaises(ValueError):
            build_launch_url("javascript:alert(1)", "A", language="es")
