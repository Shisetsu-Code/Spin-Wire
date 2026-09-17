from __future__ import annotations

from pathlib import Path

from tester_spin.providers.bgaming import BGamingProvider


def test_bgaming_default_concurrency_remains_serial(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path)
    assert provider.effective_test_concurrency(4) == 1


def test_bgaming_sweep_can_request_bounded_instance_concurrency(tmp_path: Path) -> None:
    provider = BGamingProvider(tmp_path, test_concurrency_cap=3)
    assert provider.effective_test_concurrency(4) == 3
