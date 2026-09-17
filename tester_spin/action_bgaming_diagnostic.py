from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import threading
from pathlib import Path
from typing import Any, Iterable

from tester_spin.models import Game, GameTestResult
from tester_spin.providers.bgaming.adapter import BGamingProvider
from tester_spin.providers.bgaming.runtime import sanitize_error_text, sanitize_session_url
from tester_spin.run_diagnostics import sanitize
from tester_spin.scheduler import run_game_tests


def _fold(value: str) -> str:
    return " ".join(str(value or "").casefold().split())


def select_game(games: Iterable[Game], query: str) -> Game:
    items = list(games)
    needle = _fold(query)
    if not needle:
        raise ValueError("La consulta del juego está vacía.")

    exact: list[Game] = []
    for game in items:
        values = {_fold(game.name), _fold(game.slug), _fold(game.symbol)} - {""}
        if needle in values:
            exact.append(game)
    if len(exact) == 1:
        return exact[0]
    if len(exact) > 1:
        raise ValueError(f"La consulta es ambigua: {query!r} coincide exactamente con {len(exact)} juegos.")

    partial: list[Game] = []
    for game in items:
        haystack = " ".join((_fold(game.name), _fold(game.slug), _fold(game.symbol)))
        if needle in haystack:
            partial.append(game)
    if len(partial) == 1:
        return partial[0]
    if not partial:
        raise ValueError(f"La consulta {query!r} no coincide con ningún juego del catálogo BGaming.")
    names = ", ".join(game.name for game in partial[:8])
    suffix = " …" if len(partial) > 8 else ""
    raise ValueError(
        f"La consulta es ambigua: {query!r} coincide con {len(partial)} juegos: {names}{suffix}"
    )


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, str):
        cleaned = sanitize_error_text(value)
        if cleaned.startswith(("http://", "https://")):
            cleaned = sanitize_session_url(cleaned)
        return sanitize(cleaned)
    return value


def write_result_summary(
    path: Path,
    result: GameTestResult,
    *,
    catalog_size: int,
    query: str,
) -> None:
    payload = {
        "schema": "spin-wire/action-bgaming-diagnostic/v1",
        "query": query,
        "catalog_size": int(catalog_size),
        "result": result.to_dict(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(_sanitize_value(payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def copy_safe_diagnostics(run_dir: Path, output_dir: Path) -> list[str]:
    """Export only reports produced by run_diagnostics, never raw wire captures."""
    copied: list[str] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in ("diagnostic.json", "diagnostic.md"):
        source = run_dir / name
        if not source.is_file():
            continue
        target = output_dir / name
        if source.suffix == ".json":
            try:
                value = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            target.write_text(
                json.dumps(_sanitize_value(value), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        else:
            target.write_text(
                str(_sanitize_value(source.read_text(encoding="utf-8", errors="replace"))),
                encoding="utf-8",
            )
        copied.append(name)
    return copied


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ejecuta el adaptador BGaming real de Spin-Wire sin GUI para diagnóstico de GitHub Actions."
    )
    parser.add_argument("--game", required=True, help="Nombre, slug o identificador del juego.")
    parser.add_argument("--spins", type=int, default=1, help="Muestras por ruta; mínimo 1.")
    parser.add_argument("--timeout", type=float, default=60.0, help="Timeout por operación en segundos.")
    parser.add_argument("--max-pages", type=int, default=100, help="Límite de páginas del catálogo.")
    parser.add_argument("--data-root", required=True, help="Directorio temporal de datos crudos; no se publica.")
    parser.add_argument("--output-dir", default="action-diagnostics", help="Directorio de evidencia sanitizada.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.spins < 1:
        raise SystemExit("--spins debe ser >= 1")
    if args.timeout < 1:
        raise SystemExit("--timeout debe ser >= 1")
    if args.max_pages < 1:
        raise SystemExit("--max-pages debe ser >= 1")

    output_dir = Path(args.output_dir).resolve()
    data_root = Path(args.data_root).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    data_root.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "spin-wire.log"

    def progress(message: str) -> None:
        text = str(_sanitize_value(str(message)))
        print(text, flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(text + "\n")

    stop_event = threading.Event()
    provider = BGamingProvider(data_root)
    results: list[GameTestResult] = []

    try:
        progress("BGaming Actions: leyendo catálogo con el adaptador real de Spin-Wire.")
        games = provider.crawl_catalog(
            stop_event=stop_event,
            progress=progress,
            max_pages=args.max_pages,
        )
        game = select_game(games, args.game)
        progress(f"BGaming Actions: juego seleccionado={game.name!r}; iniciando una ejecución serial.")
        run_game_tests(
            provider,
            [game],
            concurrency=1,
            spins_per_game=args.spins,
            delay_between_starts_s=0.0,
            timeout_s=args.timeout,
            stop_event=stop_event,
            progress=progress,
            on_result=results.append,
        )
        if len(results) != 1:
            raise RuntimeError(f"Se esperaba un resultado y se recibieron {len(results)}.")
        result = results[0]
        write_result_summary(
            output_dir / "summary.json",
            result,
            catalog_size=len(games),
            query=args.game,
        )
        safe = []
        if result.run_dir:
            safe = copy_safe_diagnostics(Path(result.run_dir), output_dir)
        progress(
            f"BGaming Actions: estado={result.status}; "
            f"intentos={len(result.attempts)}; reportes_sanitizados={safe}."
        )
        return 0
    except BaseException as exc:
        detail = _sanitize_value(f"{type(exc).__name__}: {exc}")
        failure = {
            "schema": "spin-wire/action-bgaming-diagnostic/v1",
            "query": args.game,
            "status": "INFRA_ERROR",
            "error": detail,
        }
        (output_dir / "summary.json").write_text(
            json.dumps(failure, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        progress(f"BGaming Actions ERROR: {detail}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
