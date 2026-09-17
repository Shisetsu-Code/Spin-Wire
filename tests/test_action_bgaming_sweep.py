from __future__ import annotations

import json
from pathlib import Path

import pytest

from tester_spin.action_bgaming_sweep import (
    SweepConfig,
    build_sweep_summary,
    load_sweep_config,
    resolve_sweep_games,
)
from tester_spin.models import Game


def _game(name: str, slug: str, symbol: str = "") -> Game:
    return Game(
        provider="bgaming",
        slug=slug,
        name=name,
        url=f"https://bgaming.com/games/{slug}/",
        symbol=symbol,
    )


def _write_config(path: Path, **overrides) -> None:
    payload = {
        "concurrency": 3,
        "spins": 1,
        "timeout_seconds": 60,
        "max_catalog_pages": 100,
        "targets": ["*"],
        "run_nonce": "baseline",
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_load_sweep_config_reads_bounded_parallel_settings(tmp_path: Path) -> None:
    path = tmp_path / "config.json"
    _write_config(path)

    config = load_sweep_config(path)

    assert config == SweepConfig(3, 1, 60.0, 100, ("*",), "baseline")


@pytest.mark.parametrize("concurrency", [0, 5])
def test_load_sweep_config_rejects_unbounded_concurrency(
    tmp_path: Path,
    concurrency: int,
) -> None:
    path = tmp_path / "config.json"
    _write_config(path, concurrency=concurrency)

    with pytest.raises(ValueError, match="concurrency"):
        load_sweep_config(path)


def test_resolve_sweep_games_supports_all_and_exact_cohorts() -> None:
    games = [
        _game("Alien Fruits 3", "alien-fruits-3", "alienfruits3"),
        _game("Multi Rush", "multi-rush", "multirush"),
    ]

    assert resolve_sweep_games(games, ["*"]) == games
    assert [g.slug for g in resolve_sweep_games(games, ["Multi Rush"])] == ["multi-rush"]
    assert [g.slug for g in resolve_sweep_games(games, ["alienfruits3"])] == ["alien-fruits-3"]


def test_resolve_sweep_games_deduplicates_cohort_targets() -> None:
    games = [_game("Multi Rush", "multi-rush", "multirush")]

    resolved = resolve_sweep_games(games, ["Multi Rush", "multi-rush", "multirush"])

    assert [g.slug for g in resolved] == ["multi-rush"]


def test_sweep_uses_active_bgaming_farm_adapter(tmp_path: Path) -> None:
    import tester_spin.action_bgaming_sweep as action_module
    from tester_spin.providers import BGamingProvider as ActiveBGamingProvider

    assert action_module.BGamingProvider is ActiveBGamingProvider
    provider = ActiveBGamingProvider(tmp_path, test_concurrency_cap=3)
    game = _game("Fixture", "fixture", "fixture")
    assert provider.farm_contract_dir(game) == provider.game_dir(game)
    assert provider.effective_test_concurrency(4) == 3


def test_sweep_summary_preserves_ok_but_not_ready_signal() -> None:
    records = [
        {
            "slug": "fixture",
            "game_name": "Fixture",
            "status": "OK",
            "farm_ready": False,
            "farm_unresolved": [
                "MODE_NOT_DEMONSTRATED:PURCHASE_X:SOLO_ANUNCIADO"
            ],
        }
    ]

    summary = build_sweep_summary(
        catalog_size=1,
        selected_size=1,
        records=records,
    )

    assert summary["status_counts"] == {"OK": 1}
    assert summary["ok_not_ready_count"] == 1
    assert summary["ok_not_ready"] == ["fixture"]
    assert summary["completed_size"] == 1
