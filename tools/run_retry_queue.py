"""Run a provider recovery queue with a hard per-game wall-clock limit.

The GUI scheduler is intentionally used inside an isolated child process so its
normal artifact/finalization pipeline is preserved.  The parent process keeps
the queue moving when a provider browser or transport stalls indefinitely.
"""

from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import sys
import threading
from pathlib import Path

# Workers are spawned under Windows with the active console code page.  Provider
# diagnostics deliberately contain protocol symbols, so force UTF-8 before a
# child inherits the environment and turns a successful run into a logging error.
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def provider_for(key: str, data_root: Path):
    from tester_spin.providers import (
        BGamingProvider,
        BelatraProvider,
        KAGamingProvider,
        OneSpin4WinProvider,
        PragmaticProvider,
        RedTigerProvider,
        RubyPlayProvider,
    )

    providers = (
        PragmaticProvider,
        OneSpin4WinProvider,
        BelatraProvider,
        BGamingProvider,
        KAGamingProvider,
        RubyPlayProvider,
        RedTigerProvider,
    )
    for provider_type in providers:
        provider = provider_type(data_root)
        if provider.key == key:
            return provider
    raise ValueError(f"Proveedor no registrado: {key}")


def _run_one(project_root: str, provider_key: str, game, timeout_s: float) -> None:
    os.chdir(project_root)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from tester_spin.scheduler import run_game_tests
    from tester_spin.storage import Storage

    data_root = Path(project_root) / "data"
    storage = Storage(data_root / "tester-spin.sqlite3")
    provider = provider_for(provider_key, data_root)
    run_game_tests(
        provider,
        [game],
        concurrency=1,
        spins_per_game=1,
        delay_between_starts_s=0,
        timeout_s=timeout_s,
        stop_event=threading.Event(),
        progress=lambda message: print(f"[{game.name}] {message}", flush=True),
        on_result=storage.record_result,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("provider")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--timeout", type=float, default=35.0, help="provider request timeout")
    parser.add_argument("--wall-timeout", type=float, default=60.0, help="hard timeout for an entire game")
    parser.add_argument("--statuses", nargs="+", default=["ERROR", "PARCIAL", "SIN_DEMO"])
    args = parser.parse_args()

    # Provider discovery launches Python helpers.  On Windows the inherited
    # console can otherwise be cp1252, which turns harmless protocol arrows
    # in diagnostics into a bootstrap failure before the game is contacted.
    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    root = Path.cwd().resolve()
    if not (root / "tester_spin").is_dir():
        raise SystemExit("Ejecutar desde la raíz de Tester-Spin.")
    sys.path.insert(0, str(root))
    from tester_spin.models import GameTestResult
    from tester_spin.storage import Storage

    data_root = root / "data"
    storage = Storage(data_root / "tester-spin.sqlite3")
    provider = provider_for(args.provider, data_root)
    allowed = {status.upper() for status in args.statuses}
    games = [game for game in storage.list_games(provider.key) if game.last_status.upper() in allowed]
    if args.limit:
        games = games[: args.limit]
    print(f"QUEUE provider={provider.key} games={len(games)} statuses={sorted(allowed)}", flush=True)

    context = mp.get_context("spawn")
    for index, game in enumerate(games, start=1):
        print(f"START {index}/{len(games)} {game.name}", flush=True)
        process = context.Process(target=_run_one, args=(str(root), provider.key, game, args.timeout))
        process.start()
        process.join(max(1.0, args.wall_timeout))
        if process.is_alive():
            process.terminate()
            process.join(10)
            storage.record_result(
                GameTestResult(
                    provider=game.provider,
                    slug=game.slug,
                    game_name=game.name,
                    game_url=game.url,
                    symbol=game.symbol,
                    requested_spins=1,
                    successful_spins=0,
                    failed_spins=1,
                    status="ERROR",
                    error=f"RUNNER_WALL_TIMEOUT: excedió {args.wall_timeout:.0f}s; pendiente para revisión puntual.",
                )
            )
            print(f"TIMEOUT {game.name}", flush=True)
        else:
            print(f"END {game.name} exit={process.exitcode}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
