from __future__ import annotations

import json
from pathlib import Path

import pytest

from tester_spin.action_bgaming_diagnostic import (
    copy_safe_diagnostics,
    select_game,
    write_result_summary,
)
from tester_spin.models import Game, GameTestResult, SpinAttempt


def _game(name: str, slug: str, symbol: str = "") -> Game:
    return Game(
        provider="bgaming",
        slug=slug,
        name=name,
        url=f"https://bgaming.com/games/{slug}/",
        symbol=symbol,
    )


def test_select_game_prefers_exact_name_slug_or_symbol() -> None:
    games = [
        _game("Alien Fruits 3", "alien-fruits-3", "alienfruits3"),
        _game("Alien Fruits", "alien-fruits", "alienfruits"),
    ]

    assert select_game(games, "Alien Fruits 3").slug == "alien-fruits-3"
    assert select_game(games, "alien-fruits-3").name == "Alien Fruits 3"
    assert select_game(games, "ALIENFRUITS3").name == "Alien Fruits 3"


def test_select_game_accepts_one_unique_substring() -> None:
    games = [
        _game("Alien Fruits 3", "alien-fruits-3"),
        _game("Adventures", "adventures"),
    ]

    assert select_game(games, "fruits 3").slug == "alien-fruits-3"


def test_select_game_rejects_missing_or_ambiguous_queries() -> None:
    games = [
        _game("Alien Fruits 3", "alien-fruits-3"),
        _game("Alien Fruits", "alien-fruits"),
    ]

    with pytest.raises(ValueError, match="no coincide"):
        select_game(games, "does-not-exist")
    with pytest.raises(ValueError, match="ambigu"):
        select_game(games, "alien")


def test_write_result_summary_redacts_session_material(tmp_path: Path) -> None:
    result = GameTestResult(
        provider="bgaming",
        slug="fixture",
        game_name="Fixture",
        game_url="https://demo.bgaming-network.com/play/F/FUN?launch_token=SECRET",
        requested_spins=1,
        successful_spins=0,
        failed_spins=1,
        status="ERROR",
        error="launch_token=SECRET",
        attempts=[
            SpinAttempt(
                number=1,
                ok=False,
                endpoint="https://demo.bgaming-network.com/api/game/currency/SESSION",
                error="token=SECRET",
            )
        ],
    )

    target = tmp_path / "summary.json"
    write_result_summary(target, result, catalog_size=12, query="Fixture")
    text = target.read_text(encoding="utf-8")
    payload = json.loads(text)

    assert "SECRET" not in text
    assert payload["schema"] == "spin-wire/action-bgaming-diagnostic/v1"
    assert payload["catalog_size"] == 12
    assert payload["result"]["status"] == "ERROR"


def test_copy_safe_diagnostics_only_exports_sanitized_reports(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "diagnostic.json").write_text('{"token":"[REDACTED]"}', encoding="utf-8")
    (run_dir / "diagnostic.md").write_text("safe report", encoding="utf-8")
    (run_dir / "raw-request.json").write_text('{"token":"SECRET"}', encoding="utf-8")

    out = tmp_path / "out"
    copied = copy_safe_diagnostics(run_dir, out)

    assert copied == ["diagnostic.json", "diagnostic.md"]
    assert (out / "diagnostic.json").is_file()
    assert (out / "diagnostic.md").is_file()
    assert not (out / "raw-request.json").exists()
