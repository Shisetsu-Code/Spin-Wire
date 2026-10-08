"""One-game-at-a-time 3 Oaks demo catalogue sweep on the actual Tester-Spin runtime.

Loads the saved public catalogue snapshot, never replays user sessions, and
publishes only allowlisted request/response fields (no tokens or raw HAR).
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import os
import re
import threading
import time
from collections import Counter
from pathlib import Path

from tester_spin.models import Game
from tester_spin.providers.three_oaks.adapter import ThreeOaksProvider

OUT = Path(os.environ.get("TESTER_SPIN_3OAKS_OUT", "action-three-oaks-sweep"))
SNAPSHOT = Path(os.environ.get("TESTER_SPIN_3OAKS_CATALOG", "archived-3oaks/catalog.json"))
PREFERRED = ("777_fruity_coins", "lady_fortune", "15_dragon_pearls")
SAFE_PARAMS = {
    "bet_per_line", "lines", "bet_factor", "selected_mode",
    "buy_spin_type", "buy_spin_scatters_count", "paid_feature", "ante_bet",
}
SLUG = re.compile(r"[a-z0-9_]+\Z")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    temporary.replace(path)


def safe_error(raw: object) -> str:
    value = str(raw or "")[:800]
    value = re.sub(
        r"(?i)(token|session[_-]?id|huid|secret|authorization|password|cookie|sid)[=:]\s*[^&\s,;]+",
        r"\1=[REDACTED]",
        value,
    )
    value = re.sub(r"\?[^\s]*", "?[QUERY_REDACTED]", value)
    return value[:300]


def public_catalogue(provider: ThreeOaksProvider, source: str) -> list[Game]:
    if source == "live":
        # Fetch the current public catalogue on the same local internet route
        # as the demo. Never silently replace a failed live crawl with stale data.
        provider._thumbnail = lambda game, progress: None
        result = provider.crawl_catalog(
            stop_event=threading.Event(), progress=lambda message: print(message, flush=True),
            max_pages=100,
        )
        if not result:
            raise ValueError("3 Oaks: catálogo público vacío")
        games = result
    elif source == "snapshot":
        data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        games = parse_snapshot(data)
    else:
        raise ValueError("Unknown catalogue source")
    order = {slug: n for n, slug in enumerate(PREFERRED)}
    return sorted(games, key=lambda g: (order.get(g.slug, 10000), g.name.casefold()))


def parse_snapshot(data: object) -> list[Game]:
    if not isinstance(data, list) or not data:
        raise ValueError("The archived public catalogue is missing or empty")
    games = []
    seen = set()
    for item in data:
        if not isinstance(item, dict):
            raise ValueError("Invalid catalogue row")
        game = Game(**{key: value for key, value in item.items() if key in Game.__dataclass_fields__})
        if (game.provider != "3oaks" or not SLUG.fullmatch(game.slug)
                or game.url != "https://3oaks.com/game/" + game.slug or game.slug in seen):
            raise ValueError("Invalid/duplicate 3 Oaks catalogue entry")
        seen.add(game.slug)
        games.append(game)
    return games


def safe_mode(mode: dict) -> dict:
    return {
        "id": str(mode.get("id", ""))[:100],
        "kind": str(mode.get("kind", ""))[:80],
        "executable": bool(mode.get("executable", False)),
        "validated": bool(mode.get("validated", False)),
        "coverage_required": bool(mode.get("coverage_required", True)),
        "client_observed": bool(mode.get("client_observed", False)),
        "reason": safe_error(mode.get("reason")),
        "required_options": [str(v)[:70] for v in (mode.get("required_options") or [])[:40]],
        "covered_options": [str(v)[:70] for v in (mode.get("covered_options") or [])[:40]],
        "sample_counts": {
            str(k)[:70]: int(v) for k, v in (mode.get("sample_counts") or {}).items()
            if isinstance(v, int) and not isinstance(v, bool)
        },
    }


def safe_trace(directory: Path) -> tuple[list[dict], list[dict]]:
    """Allowlist the exact play action shape and terminal state for diagnosis.

    Raw session_id, request_id, authentication and launcher bodies never
    enter the published output.
    """
    records = []
    returns = []
    if not directory.is_dir():
        return records, returns
    for path in sorted(directory.rglob("*.request.json")):
        if len(records) >= 1600 or path.stat().st_size > 2_000_000:
            break
        try:
            request = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(request, dict) or request.get("command") != "play":
            continue
        action = request.get("action")
        if not isinstance(action, dict):
            continue
        params = action.get("params") if isinstance(action.get("params"), dict) else {}
        record = {
            "command": "play",
            "action": str(action.get("name", ""))[:100],
            "params": {
                k: v for k, v in params.items()
                if k in SAFE_PARAMS and (type(v) in (int, float, str, bool))
            },
        }
        response_path = path.with_name(path.name.replace(".request.json", ".response.raw.json"))
        if response_path.exists() and response_path.stat().st_size <= 3_000_000:
            try:
                response = json.loads(response_path.read_text(encoding="utf-8"))
                status = response.get("status", {})
                context = response.get("context", {})
                if isinstance(status, dict):
                    record["status"] = str(status.get("code", ""))[:90]
                if isinstance(context, dict):
                    record["current"] = str(context.get("current", ""))[:90]
                    record["round_finished"] = context.get("round_finished")
                    actions = context.get("actions")
                    if isinstance(actions, list):
                        record["next_actions"] = [str(x)[:100] for x in actions[:30]]
                    bonus = context.get("bonus")
                    if isinstance(bonus, dict) and isinstance(bonus.get("back_to"), str):
                        record["back_to"] = bonus["back_to"][:100]
            except (ValueError, OSError):
                record["response_parse"] = "UNAVAILABLE"
        records.append(record)
    for path in sorted(directory.rglob("return-to-base.json")):
        try:
            obj = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(obj, dict):
                returns.append({
                    "status": str(obj.get("status", ""))[:60],
                    "required": obj.get("required"),
                    "consecutive_base": obj.get("consecutive_base"),
                })
        except (ValueError, OSError):
            continue
    return records, returns


def access_restricted(error: object) -> bool:
    value = str(error or "").lower()
    return (bool(re.search(r"(?<![0-9])(?:403|429)(?![0-9])", value))
            and any(word in value for word in ("http", "forbidden", "rate", "too many", "denied")))


def run_game(provider: ThreeOaksProvider, game: Game, *, spins: int, phase: str) -> dict:
    result = provider.test_game(
        game, spins=spins, timeout_s=12,
        stop_event=threading.Event(), progress=lambda msg: None,
    )
    modes = [safe_mode(mode) for mode in result.discovered_modes]
    trace, returns = safe_trace(Path(result.run_dir)) if result.run_dir else ([], [])
    attempts = [{
        "mode": str(attempt.mode_id)[:100],
        "kind": str(attempt.mode_kind)[:100],
        "terminal": bool(attempt.terminal),
        "ok": bool(attempt.ok),
        "wire_steps": int(attempt.wire_steps),
        "warning": safe_error(attempt.warning),
    } for attempt in result.attempts]
    unverified = [m["id"] for m in modes if m["coverage_required"] and not m["validated"]]
    uncertainty = [m["id"] for m in modes if m["kind"] in ("UNKNOWN_FEATURE", "DISCOVERED_ONLY")]
    purchases = [m for m in modes if m["kind"] == "PURCHASE"]
    natural_chains = [attempt for attempt in attempts
                      if attempt["kind"] == "SPIN" and attempt["wire_steps"] > 1]
    coverage_complete = (
        result.status == "OK" and not unverified and not uncertainty
        and all(a["terminal"] for a in attempts)
        and all(r["status"] == "CONFIRMED" for r in returns)
    )
    case = {
        "slug": game.slug, "name": game.name, "phase": phase,
        "status": result.status, "error": safe_error(result.error),
        "requested_spins": result.requested_spins,
        "successful_spins": result.successful_spins,
        "elapsed_s": round(result.elapsed_ms / 1000.0, 2),
        "purchase_count": len(purchases),
        "validated_purchases": sum(1 for m in purchases if m["validated"]),
        "pending_modes": unverified,
        "unknown_options": uncertainty,
        "coverage_complete": coverage_complete,
        "natural_bonus_observations": len(natural_chains),
        "return_checks": returns,
        "modes": modes,
        "attempts": attempts,
        "play_request_count": len(trace),
    }
    write_json(OUT / "games" / game.slug / (phase + ".json"), case)
    write_json(OUT / "games" / game.slug / (phase + "-wire.json"), trace)
    return case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget-seconds", type=int, default=1600)
    parser.add_argument("--base-spins", type=int, default=2)
    parser.add_argument("--natural-spins", type=int, default=24)
    parser.add_argument("--catalog-source", choices=["live", "snapshot"], default="live")
    parser.add_argument("--slugs", nargs="+", metavar="SLUG", default=None,
                        help="Run only these explicit game slugs (for a connectivity smoke test)")
    args = parser.parse_args()
    if args.base_spins < 1 or args.natural_spins < 1 or args.budget_seconds < 30:
        parser.error("Invalid positive sample/budget")

    OUT.mkdir(exist_ok=True)
    data_root = Path(os.environ.get("TESTER_SPIN_3OAKS_DATA_ROOT") or
                     os.environ.get("RUNNER_TEMP") or "data") / "three-oaks-full-sweep"
    provider = ThreeOaksProvider(data_root)
    try:
        games = public_catalogue(provider, args.catalog_source)
        catalogue_size = len(games)
        if args.slugs:
            unknown = sorted(set(args.slugs) - {game.slug for game in games})
            if unknown:
                raise ValueError("3 Oaks: juegos no encontrados en el catálogo: " + ", ".join(unknown))
            games = [game for game in games if game.slug in set(args.slugs)]
    except Exception:
        provider.http.close()
        raise
    write_json(OUT / "catalogue.json", [{"slug": g.slug, "name": g.name} for g in games])
    manifest = {
        "source_sha": os.environ.get("GITHUB_SHA"),
        "catalogue_source_run": 37735796749 if args.catalog_source == "snapshot" else None,
        "catalogue_source": args.catalog_source,
        "catalogue_size": catalogue_size,
        "selected_size": len(games),
        "test_scope": (f"sequential real demo: {args.base_spins} SPIN per game and each executable purchase; "
                       f"{args.natural_spins} further SPIN for games without purchases"),
        "full_random_outcome_coverage": False,
        "status": "RUNNING",
        "cases": [],
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    write_json(OUT / "summary.json", manifest)
    t0 = time.monotonic()
    try:
        for idx, game in enumerate(games):
            if time.monotonic() - t0 > args.budget_seconds:
                manifest["status"] = "STOPPED_TIME_BUDGET"
                break
            try:
                case = run_game(provider, game, spins=args.base_spins, phase="base-and-purchases")
                manifest["cases"].append(case)
                print(f"{idx+1}/{len(games)} {game.slug} {case['status']} spins={case['successful_spins']}/{args.base_spins} "
                      f"buy={case['validated_purchases']}/{case['purchase_count']} "
                      f"pending={case['pending_modes']} unknown={case['unknown_options']} "
                      f"natural={case['natural_bonus_observations']} sec={case['elapsed_s']}", flush=True)
                # 403/429 is a provider/network access limit, not game coverage.
                if access_restricted(case["error"]):
                    manifest["status"] = "STOPPED_REMOTE_ACCESS_403_OR_429"
                    manifest["stop_game"] = game.slug
                    break
                # Natural bonuses can appear without any purchasable function.
                # This is one additional fresh, isolated demo session, never
                # another simultaneously loaded game.
                no_buys = (case["status"] == "OK"
                           and len(case["modes"]) == 1 and case["modes"][0]["kind"] == "SPIN")
                if no_buys and time.monotonic() - t0 < args.budget_seconds - 75:
                    natural = run_game(provider, game, spins=args.natural_spins, phase="natural-bonus-sampling")
                    manifest["cases"].append(natural)
                    print(f"  natural {game.slug} {natural['status']} "
                          f"spins={natural['successful_spins']}/{args.natural_spins} "
                          f"bonus={natural['natural_bonus_observations']} "
                          f"sec={natural['elapsed_s']}", flush=True)
                    if access_restricted(natural["error"]):
                        manifest["status"] = "STOPPED_REMOTE_ACCESS_403_OR_429"
                        manifest["stop_game"] = game.slug
                        break
            except Exception as exc:
                failure = {"slug": game.slug, "name": game.name, "phase": "base-and-purchases",
                           "status": "RUNNER_ERROR", "error": safe_error(f"{type(exc).__name__}: {exc}"),
                           "coverage_complete": False, "purchase_count": 0, "validated_purchases": 0,
                           "natural_bonus_observations": 0}
                manifest["cases"].append(failure)
                write_json(OUT / "games" / game.slug / "runner-error.json", failure)
                print(f"{idx+1}/{len(games)} {game.slug} RUNNER_ERROR {failure['error']}", flush=True)
            finally:
                manifest["processed_unique"] = len({c["slug"] for c in manifest["cases"]})
                manifest["time_s"] = round(time.monotonic() - t0, 2)
                write_json(OUT / "summary.json", manifest)
            time.sleep(0.3)
        if manifest["status"] == "RUNNING":
            manifest["status"] = ("COMPLETED"
                                  if len({c["slug"] for c in manifest["cases"]}) == len(games)
                                  else "STOPPED_INCOMPLETE")
    finally:
        provider.http.close()
        primary = [c for c in manifest["cases"] if c["phase"] == "base-and-purchases"]
        natural = [c for c in manifest["cases"] if c["phase"] == "natural-bonus-sampling"]
        manifest.update(
            finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            processed_unique=len(primary),
            status_counts=dict(Counter(c["status"] for c in primary)),
            primary_coverage_complete=sum(bool(c.get("coverage_complete")) for c in primary),
            base_spins_ok=sum(c.get("successful_spins", 0) for c in primary),
            purchase_modes_validated=sum(c.get("validated_purchases", 0) for c in primary),
            purchase_modes_discovered=sum(c.get("purchase_count", 0) for c in primary),
            natural_sampling_games=len(natural),
            natural_bonus_observations=sum(c.get("natural_bonus_observations", 0)
                                           for c in manifest["cases"]),
            time_s=round(time.monotonic() - t0, 2),
        )
        write_json(OUT / "summary.json", manifest)
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a", encoding="utf-8") as stream:
                stream.write("## 3 Oaks full demo catalogue: current code\n\n")
                stream.write(
                    f"**{manifest['status']}**. Games {manifest['processed_unique']}/{len(games)}; "
                    f"coverage complete (current advertised modes only) {manifest['primary_coverage_complete']}; "
                    f"purchases {manifest['purchase_modes_validated']}/{manifest['purchase_modes_discovered']}; "
                    f"natural bonus observations {manifest['natural_bonus_observations']}.\n\n"
                )
                stream.write("| Game | Result | Purchase modes | Pending | Natural bonus |\n"
                             "|---|---|---:|---|---:|\n")
                for c in primary:
                    stream.write(
                        f"| {c['name']} | {c['status']} | "
                        f"{c.get('validated_purchases',0)}/{c.get('purchase_count',0)} | "
                        f"{', '.join(c.get('pending_modes',[]))[:80]} | "
                        f"{c.get('natural_bonus_observations',0)} |\n"
                    )
                stream.write(
                    "\nThis is a bounded sample of demo outcomes, not exhaustive enumeration "
                    "of random combinations. HTTP 403/429 halts further requests.\n"
                )
    # Distinguish successful workflow execution from full provider coverage.
    if manifest["status"] != "COMPLETED":
        return 2
    if any(not c.get("coverage_complete", False) for c in manifest["cases"]):
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
