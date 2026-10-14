from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tester_spin.models import Game, GameTestResult, SpinAttempt
from tester_spin.providers.redtiger.branch_coverage import ReplayOutcome, expand_all_choice_branches
from tester_spin.providers.redtiger.runtime import ChoicePrompt, response_summary


def terminal_payload(mode: str) -> dict:
    return {
        "success": True,
        "result": {
            "transactions": {"roundId": 99},
            "game": {
                "spinMode": mode,
                "stake": "2.00",
                "win": {"total": "0.00"},
                "features": [],
                "gameMode": 0,
                "hasState": False,
            },
        },
    }


def pending_payload(options: tuple[str, ...], mode: str = "SuperFreeSpins") -> dict:
    return {
        "success": True,
        "result": {
            "transactions": {"roundId": 42},
            "game": {
                "spinMode": mode,
                "stake": "2.00",
                "win": {"total": "0.00"},
                "choices": {"selected": None, "available": list(options)},
                "gameMode": 0,
                "hasState": True,
            },
        },
    }


class RedTigerExhaustiveChoicePathTests(unittest.TestCase):
    def test_missing_opportunity_is_bounded_and_unknown_state_never_retries(self):
        from tester_spin.providers.redtiger.branch_coverage import _replay_prefix, MAX_SELECTOR_ENTRY_SPINS
        from unittest.mock import Mock
        for closed, limit in ((terminal_payload("Normal"), MAX_SELECTOR_ENTRY_SPINS),
                              (terminal_payload("UnrecognizedBonus"), 1)):
            runtime = SimpleNamespace(default_stake=2, session=Mock(), settings_response={})
            with tempfile.TemporaryDirectory() as temp, patch(
                "tester_spin.providers.redtiger.branch_coverage.fresh_bootstrap", return_value=runtime
            ), patch("tester_spin.providers.redtiger.branch_coverage._post_spin",
                     return_value=(200, {}, closed, [])) as spin, patch(
                "tester_spin.providers.redtiger.branch_coverage._post_choice"
            ) as choice:
                with self.assertRaisesRegex(RuntimeError, "oportunidad"):
                    _replay_prefix(SimpleNamespace(bootstrap_endpoints=[]), self._game(),
                        launch_id="123", base_mode="SPIN", feature=None, repetition=1,
                        prefix=("collect",), timeout_s=1, stop_event=threading.Event(), run_root=Path(temp))
                self.assertEqual(spin.call_count, limit)
                choice.assert_not_called()

    def test_normal_round_without_choice_retries_before_replaying_root_action(self):
        from tester_spin.providers.redtiger.branch_coverage import _replay_prefix
        from unittest.mock import Mock
        runtime = SimpleNamespace(default_stake=2, session=Mock(), settings_response={})
        closed = terminal_payload("Normal")
        pending = pending_payload(("continue", "collect"), "Normal")
        with tempfile.TemporaryDirectory() as temp, patch(
            "tester_spin.providers.redtiger.branch_coverage.fresh_bootstrap", return_value=runtime
        ), patch("tester_spin.providers.redtiger.branch_coverage._post_spin",
                 side_effect=[(200, {}, closed, []), (200, {}, pending, [])]) as spin, patch(
            "tester_spin.providers.redtiger.branch_coverage._post_choice",
            return_value=(200, "choice", {}, closed, [])
        ) as choice:
            with patch('tester_spin.provider_return_checks.redtiger_check',return_value={'status':'CONFIRMED'}):
                outcome = _replay_prefix(SimpleNamespace(bootstrap_endpoints=[]), self._game(),
                    launch_id="123", base_mode="SPIN", feature=None, repetition=1,
                    prefix=("collect",), timeout_s=1, stop_event=threading.Event(), run_root=Path(temp))
            self.assertEqual(spin.call_count, 2)
            self.assertEqual(choice.call_count, 1)
            self.assertEqual(outcome.selected, ("collect",))
            self.assertEqual(outcome.wire_steps, 3)

    def test_replay_drains_confirmed_recurring_selector_and_requires_base_proof(self):
        from tester_spin.providers.redtiger.branch_coverage import _replay_prefix
        from unittest.mock import Mock
        for status in ['CONFIRMED','REVIEW_REQUIRED']:
            runtime=SimpleNamespace(default_stake=2,session=Mock(),settings_response={})
            pending=pending_payload(('continue','collect'),'Normal')
            closed=terminal_payload('Normal')
            def transition(prompt,selected,response):
                return {'recurring_selector':selected=='continue','round_id':42,
                    'game_data':{'spinMode':'Normal','selected':selected,'progress':{'level':{'current':1,'next':2}}},
                    'response_choice':{'status':'PENDING' if selected=='continue' else 'RESOLVED','available':['continue','collect']}}
            with tempfile.TemporaryDirectory() as temp, patch(
                'tester_spin.providers.redtiger.branch_coverage.fresh_bootstrap',return_value=runtime
            ),patch('tester_spin.providers.redtiger.branch_coverage._post_spin',return_value=(200,{},pending,[])),patch(
                'tester_spin.providers.redtiger.branch_coverage._post_choice',
                side_effect=[(200,'choice',{},pending,[]),(200,'choice',{},closed,[])]
            ),patch('tester_spin.providers.redtiger.branch_coverage.choice_transition',side_effect=transition),patch(
                'tester_spin.provider_return_checks.redtiger_check',return_value={'status':status}
            ):
                outcome=_replay_prefix(SimpleNamespace(bootstrap_endpoints=[]),self._game(),
                    launch_id='123',base_mode='SPIN',feature=None,repetition=1,prefix=('continue',),
                    timeout_s=1,stop_event=threading.Event(),run_root=Path(temp))
                self.assertEqual(outcome.selected,('continue','collect'))
                self.assertEqual(bool(outcome.warnings),status!='CONFIRMED')
                summary=json.loads((outcome.artifact_dir/'summary.json').read_text())
                self.assertEqual(len(summary['choice_continuations']),2)

    def test_failed_leaf_is_not_credited_as_covered(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self._base_result(root)
            self._seed_validated_base_path(root, result, [{"available": ["A", "B"], "selected": "A"}])
            outcome = ReplayOutcome(prompt=None, final_payload=terminal_payload("B"),
                summaries=[], warnings=["invalid balance"], wire_steps=2, status_code=200,
                selected=("B",), elapsed_ms=1, artifact_dir=root / "failed")
            with patch("tester_spin.providers.redtiger.branch_coverage._replay_prefix", return_value=outcome):
                expand_all_choice_branches(SimpleNamespace(), self._game(), result, launch_id="12345",
                    repetitions=1, timeout_s=1, stop_event=threading.Event(), progress=lambda _: None)
            branch = next(m for m in result.discovered_modes if m.get("kind") == "CHOICE_BRANCH")
            self.assertEqual(branch["covered_options"], ["A"])
            self.assertEqual(branch["sample_counts"], {"A": 1})
            self.assertEqual(result.status, "PARCIAL")

    def test_interrupted_expansion_keeps_coverage_and_cancellation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = self._base_result(root)
            self._seed_validated_base_path(root, result, [{"available": ["A", "B"], "selected": "A"}])
            with patch("tester_spin.providers.redtiger.branch_coverage._replay_prefix", side_effect=InterruptedError):
                expand_all_choice_branches(SimpleNamespace(), self._game(), result, launch_id="12345",
                    repetitions=1, timeout_s=1, stop_event=threading.Event(), progress=lambda _: None)
            self.assertEqual(result.status, "CANCELADO")
            self.assertTrue(any(m.get("kind") == "CHOICE_BRANCH" for m in result.discovered_modes))
            self.assertEqual(json.loads((root / "result.json").read_text(encoding="utf-8"))["status"], "CANCELADO")

    @staticmethod
    def _base_result(root: Path) -> GameTestResult:
        return GameTestResult(
            provider="redtiger",
            slug="synthetic",
            game_name="Synthetic",
            game_url="https://games.evolution.com/slots/synthetic/",
            requested_spins=1,
            successful_spins=1,
            failed_spins=0,
            status="OK",
            symbol="RuntimeGame",
            run_dir=str(root),
            discovered_modes=[
                {
                    "id": "PURCHASE_SUPER",
                    "kind": "PURCHASE",
                    "client_observed": True,
                    "feature_buy": "SuperFreeSpins",
                    "feature_multiplier": "300",
                },
                {
                    "id": "PURCHASE_SUPER__CHOICE_1",
                    "kind": "CHOICE_CONTINUATION",
                    "parent": "PURCHASE_SUPER",
                    "available": ["GOD_A", "GOD_B", "RANDOM"],
                    "selected_for_validation": "GOD_A",
                },
            ],
        )

    @staticmethod
    def _game() -> Game:
        return Game(
            provider="redtiger",
            slug="synthetic",
            name="Synthetic",
            url="https://games.evolution.com/slots/synthetic/",
            symbol="12345",
        )

    @staticmethod
    def _seed_validated_base_path(
        root: Path,
        result: GameTestResult,
        records: list[dict],
    ) -> None:
        attempt_root = root / "PURCHASE_SUPER" / "attempt-00001"
        attempt_root.mkdir(parents=True, exist_ok=True)
        (attempt_root / "summary.json").write_text(
            json.dumps({"success": True, "choice_continuations": records}),
            encoding="utf-8",
        )
        result.attempts.append(
            SpinAttempt(
                number=1,
                ok=True,
                mode_id="PURCHASE_SUPER",
                mode_kind="PURCHASE",
                terminal=True,
                wire_steps=1 + len(records),
                artifact_dir=str(attempt_root),
            )
        )

    def test_every_missing_root_choice_gets_its_own_fresh_path(self) -> None:
        options = ("GOD_A", "GOD_B", "RANDOM")

        def fake_replay(_provider, _game, *, prefix, run_root, **kwargs):
            payload = terminal_payload(prefix[-1])
            return ReplayOutcome(
                prompt=None,
                final_payload=payload,
                summaries=[response_summary(payload)],
                warnings=[],
                wire_steps=1 + len(prefix),
                status_code=200,
                selected=prefix,
                elapsed_ms=1.0,
                artifact_dir=run_root / "fake" / "-".join(prefix),
            )

        with tempfile.TemporaryDirectory() as temp, patch(
            "tester_spin.providers.redtiger.branch_coverage._replay_prefix",
            side_effect=fake_replay,
        ) as replay:
            root = Path(temp)
            result = self._base_result(root)
            self._seed_validated_base_path(
                root,
                result,
                [{"available": list(options), "selected": "GOD_A"}],
            )
            expand_all_choice_branches(
                SimpleNamespace(bootstrap_endpoints=None),
                self._game(),
                result,
                launch_id="12345",
                repetitions=1,
                timeout_s=5.0,
                stop_event=threading.Event(),
                progress=lambda _message: None,
            )

        prefixes = [call.kwargs["prefix"] for call in replay.call_args_list]
        self.assertEqual(set(prefixes), {("GOD_B",), ("RANDOM",)})
        self.assertNotIn(("GOD_A",), prefixes)
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.requested_spins, 3)
        self.assertEqual(result.successful_spins, 3)
        branch = next(item for item in result.discovered_modes if item.get("kind") == "CHOICE_BRANCH")
        self.assertEqual(branch["required_options"], list(options))
        self.assertEqual(branch["covered_options"], sorted(options))

    def test_nested_choices_expand_every_missing_leaf_without_replaying_validated_leaf(self) -> None:
        def fake_replay(_provider, _game, *, prefix, run_root, **kwargs):
            payload = terminal_payload(prefix[-1])
            return ReplayOutcome(
                prompt=None,
                final_payload=payload,
                summaries=[response_summary(payload)],
                warnings=[],
                wire_steps=1 + len(prefix),
                status_code=200,
                selected=prefix,
                elapsed_ms=1.0,
                artifact_dir=run_root / "fake" / "-".join(prefix),
            )

        with tempfile.TemporaryDirectory() as temp, patch(
            "tester_spin.providers.redtiger.branch_coverage._replay_prefix",
            side_effect=fake_replay,
        ) as replay:
            root = Path(temp)
            result = self._base_result(root)
            self._seed_validated_base_path(
                root,
                result,
                [
                    {"available": ["A", "B"], "selected": "A"},
                    {"available": ["X", "Y"], "selected": "X"},
                ],
            )
            expand_all_choice_branches(
                SimpleNamespace(bootstrap_endpoints=None),
                self._game(),
                result,
                launch_id="12345",
                repetitions=1,
                timeout_s=5.0,
                stop_event=threading.Event(),
                progress=lambda _message: None,
            )

        prefixes = {call.kwargs["prefix"] for call in replay.call_args_list}
        self.assertEqual(prefixes, {("B",), ("A", "Y")})
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.requested_spins, 3)  # validated A/X + fresh B + fresh A/Y
        branch_points = [item for item in result.discovered_modes if item.get("kind") == "CHOICE_BRANCH"]
        self.assertEqual(len(branch_points), 2)
        self.assertTrue(all(set(item["required_options"]) == set(item["covered_options"]) for item in branch_points))

    def test_new_nested_selector_is_expanded_recursively(self) -> None:
        def fake_replay(_provider, _game, *, prefix, run_root, **kwargs):
            if prefix == ("B",):
                options = ("B1", "B2")
                payload = pending_payload(options, mode="Nested")
                prompt = ChoicePrompt(round_id=2, available=options)
            else:
                payload = terminal_payload(prefix[-1])
                prompt = None
            return ReplayOutcome(
                prompt=prompt,
                final_payload=payload,
                summaries=[response_summary(payload)],
                warnings=[],
                wire_steps=1 + len(prefix),
                status_code=200,
                selected=prefix,
                elapsed_ms=1.0,
                artifact_dir=run_root / "fake" / "-".join(prefix),
            )

        with tempfile.TemporaryDirectory() as temp, patch(
            "tester_spin.providers.redtiger.branch_coverage._replay_prefix",
            side_effect=fake_replay,
        ) as replay:
            root = Path(temp)
            result = self._base_result(root)
            self._seed_validated_base_path(
                root,
                result,
                [{"available": ["A", "B"], "selected": "A"}],
            )
            expand_all_choice_branches(
                SimpleNamespace(bootstrap_endpoints=None),
                self._game(),
                result,
                launch_id="12345",
                repetitions=1,
                timeout_s=5.0,
                stop_event=threading.Event(),
                progress=lambda _message: None,
            )

        prefixes = {call.kwargs["prefix"] for call in replay.call_args_list}
        self.assertEqual(prefixes, {("B",), ("B", "B1"), ("B", "B2")})
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.requested_spins, 3)  # base A + B/B1 + B/B2

    def test_failed_choice_path_cannot_report_ok(self) -> None:
        options = ("LEFT", "RIGHT")

        def fake_replay(_provider, _game, *, prefix, run_root, **kwargs):
            if prefix == ("RIGHT",):
                raise RuntimeError("wire rejected")
            payload = terminal_payload(prefix[-1])
            return ReplayOutcome(
                prompt=None,
                final_payload=payload,
                summaries=[response_summary(payload)],
                warnings=[],
                wire_steps=2,
                status_code=200,
                selected=prefix,
                elapsed_ms=1.0,
                artifact_dir=run_root / "fake" / "left",
            )

        with tempfile.TemporaryDirectory() as temp, patch(
            "tester_spin.providers.redtiger.branch_coverage._replay_prefix",
            side_effect=fake_replay,
        ):
            root = Path(temp)
            result = self._base_result(root)
            self._seed_validated_base_path(
                root,
                result,
                [{"available": list(options), "selected": "LEFT"}],
            )
            expand_all_choice_branches(
                SimpleNamespace(bootstrap_endpoints=None),
                self._game(),
                result,
                launch_id="12345",
                repetitions=1,
                timeout_s=5.0,
                stop_event=threading.Event(),
                progress=lambda _message: None,
            )

        self.assertEqual(result.status, "PARCIAL")
        self.assertGreater(result.failed_spins, 0)
        self.assertIn("RIGHT", result.error)


if __name__ == "__main__":
    unittest.main()
