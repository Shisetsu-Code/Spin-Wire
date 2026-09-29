from __future__ import annotations

import unittest

from tester_spin.providers.ka_gaming.catalog import build_launch_url, declared_modes_from_row, games_from_catalog


def payload() -> dict:
    return {"status": "ok", "statusCode": 0, "numGames": 2, "gameLaunchURL": "https://demo.kaga88.com/launch", "games": [{"gameId": "A", "gameName": "Alpha", "gameType": "slots", "iconURLPrefix": "https://icons/a"}, {"gameId": "B", "gameName": "Beta", "gameType": "table"}]}


class KAGamingCatalogTests(unittest.TestCase):

    def test_declared_modes_keep_catalog_features_non_executable(self) -> None:
        modes = declared_modes_from_row({"gameType": "slots", "variantType": "ways", "availableFeatures": ["fg", "bp"], "supportsBuyFeature": True})
        self.assertEqual(modes[0], {"id": "SPIN", "kind": "WAYS", "source": "catalog", "executable": False, "coverage_required": False})
        self.assertIn({"id": "FREE_GAMES", "kind": "FEATURE", "source": "catalog", "executable": False, "coverage_required": False}, modes)
        self.assertIn({"id": "BONUS_PURCHASE", "kind": "FEATURE", "source": "catalog", "executable": False, "coverage_required": False}, modes)
    def test_valid_catalog_builds_deterministic_games(self) -> None:
        games = games_from_catalog(payload(), language="es")
        self.assertEqual([game.slug for game in games], ["a"])
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
