from __future__ import annotations

import threading
from pathlib import Path

from tester_spin.models import Game
from tester_spin.providers.bgaming import BGamingProvider


def test_bgaming_default_concurrency_remains_serial(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path)
    assert provider.effective_test_concurrency(4) == 1


def test_bgaming_sweep_can_request_bounded_instance_concurrency(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path, test_concurrency_cap=3)
    assert provider.effective_test_concurrency(4) == 3


def test_bgaming_sweep_can_skip_automatic_har_capture_without_network(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path, capture_analysis_har=False)
    game = Game(
        provider="bgaming",
        slug="fixture",
        name="Fixture",
        url="https://bgaming.com/games/fixture/",
        symbol="Fixture",
    )
    messages: list[str] = []

    provider.prepare_test_artifacts(
        game,
        timeout_s=1.0,
        stop_event=threading.Event(),
        progress=messages.append,
    )

    assert not (provider.game_dir(game) / "analysis" / "browser.har").exists()
    assert any("HAR" in message and "omitida" in message for message in messages)
