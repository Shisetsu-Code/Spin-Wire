"""HAR-backed offline assertions for two 3 Oaks demo clients.

Source excerpts below contain only static public JavaScript and no raw HAR,
credentials, request IDs, player balances or session identifiers.
"""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from tester_spin.providers.three_oaks.purchase_routes import additional_purchase_inputs
from tester_spin.providers.three_oaks.runtime import (
    base_terminal, continuation_fields, discover_modes, play_fields,
)

REGISTRY = Path(__file__).resolve().parent.parent / "tester_spin/providers/three_oaks/observed_client_contracts.json"
DRAGON_SHA = "f9492c4f6bf9b86c5a98c6fb45abe5f3412a924838c799b5a81ec93cf89a74d6"

# These minified excerpts reproduce the observed Lady Fortune purchase callback,
# neutral ante-bet binding and guard on the real purchase buttons.
LADY_JS = (
    'this.isActive=!!_GameRunnerController.GR.UI.model.get("ante_bet");'
    'var isActive=arguments.length>0&&arguments[0]!==undefined?arguments[0]'
    ':!!_GameRunnerController.GR.UI.model.get("ante_bet");this.isActive=isActive;'
    'if(_app.default.board.buyFeature.isNotEnoughBalance(button.fsParam)'
    '||!!_GameRunnerController.GR.UI.model.get("ante_bet")'
    '||_app.default.model.isFreeBets()){button.disable()}else{button.enable()}'
    'function actBuyFeature(scattersCount){'
    'var params={};'
    'params.bet_per_line=GR.UI.model.get("bet_per_line");'
    'params.lines=_app.default.model.betFactor()[0];'
    'params.ante_bet=_app.default.board.anteBetButton.isActive'
    '?_app.default.model.getAnteBetCoef():0;'
    'params.buy_spin_scatters_count=scattersCount+3;'
    '_app.default.controllers.flow.act(_constants.FLOW_ACTIONS.BUY_SPIN,params)}'
)

LADY_START = {
    "context": {
        "current": "spins", "round_finished": True,
        "actions": ["spin", "buy_spin"],
        "available_buy_bonus": [1, 2, 3],
        "spins": {"bet_per_line": 5, "lines": 20},
        "last_args": {},
    },
    "settings": {
        "lines": [20], "bet_factor": [20], "ante_bet": [1.25],
        "buy_bonus_prices": {"1": 100, "2": 200, "3": 300},
    },
}
DRAGON_START = {
    "context": {
        "current": "spins", "round_finished": True,
        "actions": ["spin"],
        "spins": {"bet_per_line": 4, "lines": 25},
    },
    "settings": {"lines": [25], "bet_factor": [25]},
}


class LadyFortuneHARTests(unittest.TestCase):
    def profile(self, source=LADY_JS):
        with patch(
            "tester_spin.providers.three_oaks.purchase_routes.flow_parameters",
            return_value=["bet_per_line", "lines", "bet_factor"],
        ):
            return additional_purchase_inputs(source, LADY_START)

    def test_all_three_official_purchase_request_shapes(self):
        profile = self.profile()
        self.assertIsNotNone(profile)
        self.assertEqual(profile["purchase_modes"], [1, 2, 3])
        self.assertEqual(profile["purchase_ui_defaults"], {"ante_bet": 0})
        self.assertEqual(profile["purchase_value_sources"], {"lines": "bet_factor_first"})
        for option, scatters in ((1, 4), (2, 5), (3, 6)):
            with self.subTest(option=option):
                request = play_fields(LADY_START, "buy_spin", option, client_profile=profile)
                self.assertEqual(request["action"], {
                    "name": "buy_spin",
                    "params": {
                        "bet_per_line": 5, "lines": 20, "bet_factor": 20,
                        "buy_spin_scatters_count": scatters, "ante_bet": 0,
                    },
                })

    def test_purchase_does_not_ignore_active_antebet(self):
        profile = self.profile()
        active = {
            **LADY_START,
            "context": {**LADY_START["context"], "last_args": {"ante_bet": 1.25}},
        }
        with self.assertRaisesRegex(ValueError, "antebet"):
            play_fields(active, "buy_spin", 1, client_profile=profile)

    def test_purchase_shape_not_proven_if_ante_disable_guard_disappears(self):
        missing_guard = LADY_JS.replace("||_app.default.model.isFreeBets()){button.disable()}", "||_app.default.model.isFreeBets()){button.enable()}")
        result = self.profile(missing_guard)
        self.assertIsNone(result)

    def test_free_spin_and_respin_chain_requires_advertised_action(self):
        profile = {
            "continuations": {
                "freespin_init": {"current": "spins", "state_independent": True},
                "freespin": {"current": "freespins", "state_independent": True},
                "respin": {"current": "bonus", "state_independent": True},
                "freespin_stop": {"current": "freespins", "state_independent": True},
            },
        }
        for state, action in [
            ("spins", "freespin_init"), ("freespins", "freespin"),
            ("freespins", "respin"), ("freespins", "freespin_stop"),
        ]:
            with self.subTest(action=action):
                current = {"context": {"current": state, "actions": [action], "round_finished": False}}
                fields = continuation_fields(current, game_slug="not_bound_to_name", family="goreel", client_profile=profile)
                self.assertEqual(fields["action"], {"name": action, "params": {}})
        ambiguous = {"context": {"current": "freespins", "actions": ["respin", "freespin"], "round_finished": False}}
        self.assertIsNone(continuation_fields(ambiguous, game_slug="x", family="goreel", client_profile=profile))


class DragonPearlsNaturalBonusHARTests(unittest.TestCase):
    def profile(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        return registry["clients"][DRAGON_SHA]

    def test_no_purchases_or_antebet_in_official_start(self):
        modes = discover_modes(DRAGON_START, "goreel", serializer_observed=True)
        self.assertEqual(len(modes), 1)
        self.assertEqual(modes[0]["id"], "SPIN")

    def test_natural_bonus_exits_after_seven_respins(self):
        profile = self.profile()
        self.assertEqual(profile["purchase_modes"], [])
        self.assertEqual(profile["continuations"], {
            "bonus_init": {"current": "spins"},
            "respin": {"current": "bonus"},
            "bonus_spins_stop": {"current": "bonus", "back_to": "spins"},
        })
        trace = [("spins", "bonus_init", None)]
        trace += [("bonus", "respin", "spins")] * 7
        trace += [("bonus", "bonus_spins_stop", "spins")]
        for current, action, back_to in trace:
            with self.subTest(action=action, current=current):
                state = {
                    "context": {
                        "current": current, "round_finished": False, "actions": [action],
                        "bonus": {"back_to": back_to} if back_to else {},
                    }
                }
                fields = continuation_fields(
                    state, game_slug="any_client_with_same_hash",
                    family="goreel", client_profile=profile,
                )
                self.assertEqual(fields["action"], {"name": action, "params": {}})
        terminal = {"context": {"current": "spins", "actions": ["spin"], "round_finished": True}}
        self.assertTrue(base_terminal(terminal))

    def test_wrong_bonus_origin_is_not_authorized(self):
        state = {
            "context": {
                "current": "bonus", "round_finished": False,
                "actions": ["bonus_spins_stop"], "bonus": {"back_to": "freespins"},
            }
        }
        self.assertIsNone(continuation_fields(
            state, game_slug="unknown", family="goreel", client_profile=self.profile(),
        ))
