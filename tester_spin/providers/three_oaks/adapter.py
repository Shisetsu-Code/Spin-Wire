from __future__ import annotations

import json
import threading
import time
import uuid
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

from curl_cffi import requests
from PIL import Image

from tester_spin.models import Game, GameTestResult, SpinAttempt, utc_now_iso
from tester_spin.providers.base import ProviderAdapter
from tester_spin.providers.result_farm_contract import ProviderFarmSpec, build_result_farm_contract, validate_result_farm_contract
from .catalog import CATALOG_API, ORIGIN, SLUG, client_family, family_map, games_from_page, launcher_config
from .runtime import DemoSession, base_terminal, discover_modes, play_fields

_SPEC = ProviderFarmSpec(provider="3oaks", protocol_family="three-oaks-goreel-commands",
    bootstrap_strategy="three-oaks-public-demo-login-start", transport="http-json-text-plain",
    terminal_contract={"type": "provider", "name": "three-oaks-completed-base-round",
        "round_finished": True, "current": "spins", "available_action": "spin"},
    stable_metadata_keys=("family", "vendor", "runtime_transport"),
    mode_option_keys=("selected_mode", "feature_multiplier", "family", "wire_action"),
    runtime_outputs=("demo_endpoint", "session_id"),
    protocol_static={"command": "play", "base_action": "spin", "purchase_action": "buy_spin"})


class ThreeOaksProvider(ProviderAdapter):
    key = "3oaks"
    display_name = "3 Oaks Gaming"
    catalog_url = ORIGIN + "/games"
    max_test_concurrency = 1
    min_catalog_reconcile_ratio = 0.8

    def __init__(self, data_root: Path):
        self.data_root = Path(data_root)
        self.provider_root = self.data_root / "providers" / self.key
        self.provider_root.mkdir(parents=True, exist_ok=True)
        self.http = requests.Session(impersonate="chrome")

    def game_dir(self, game: Game) -> Path:
        if not SLUG.fullmatch(game.slug):
            raise ValueError("3 Oaks: slug inválido")
        path = self.provider_root / game.slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _metadata(self, game: Game) -> dict:
        try:
            data = json.loads((self.game_dir(game) / "game.json").read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (ValueError, OSError):
            return {}

    def _save_metadata(self, game: Game, **fields):
        data = {**self._metadata(game), "provider": self.key, "slug": game.slug,
                "name": game.name, "public_url": game.url, "symbol": game.symbol, **fields}
        (self.game_dir(game) / "game.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def catalog_record_invalid_reason(self, game: Game) -> str:
        return "3 Oaks: fila inválida" if game.provider != self.key or not SLUG.fullmatch(game.slug) or game.url != ORIGIN + "/game/" + game.slug else ""

    def _thumbnail(self, game: Game, progress):
        parsed = urlparse(game.thumbnail_url)
        if parsed.hostname != "3oaks.com" or not parsed.path.startswith("/media/"):
            return
        suffix = Path(parsed.path).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            return
        target = self.game_dir(game) / ("thumbnail" + suffix)
        try:
            if not target.is_file():
                response = self.http.get(game.thumbnail_url, timeout=20)
                response.raise_for_status()
                if len(response.content) > 10_000_000:
                    raise ValueError("miniatura demasiado grande")
                with Image.open(BytesIO(response.content)) as image:
                    image.verify()
                target.write_bytes(response.content)
            game.thumbnail_path = str(target)
        except Exception as exc:
            progress(f"[{game.name}] miniatura pendiente ({type(exc).__name__}).")

    def crawl_catalog(self, *, stop_event: threading.Event, progress, max_pages: int = 100, on_game=None) -> list[Game]:
        self.set_catalog_authority(False, "crawl incompleto")
        limit = int(max_pages)
        page, total = 1, None
        games = {}
        raw_dir = self.provider_root / "catalog"
        raw_dir.mkdir(exist_ok=True)
        while not stop_event.is_set() and (total is None or page <= total) and (limit <= 0 or page <= limit):
            response = self.http.get(CATALOG_API, params={"page_num": page, "page_items_num": 15, "sort": "release_date:desc"}, timeout=30)
            response.raise_for_status()
            payload = response.json()
            rows = games_from_page(payload)
            pages = payload["data"].get("total_pages")
            if not isinstance(pages, int) or isinstance(pages, bool) or pages < 1 or pages > 1000:
                raise ValueError("3 Oaks: total_pages inválido")
            if total is not None and pages != total:
                raise ValueError("3 Oaks: catálogo cambió durante la paginación")
            total = pages
            (raw_dir / f"page-{page:03d}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            if not payload["data"]["items"]:
                raise ValueError("3 Oaks: página vacía antes del final")
            for game in rows:
                if game.slug in games:
                    raise ValueError("3 Oaks: paginación repitió un juego")
                games[game.slug] = game
                self._thumbnail(game, progress)
                self._save_metadata(game, thumbnail_url=game.thumbnail_url, thumbnail_path=game.thumbnail_path)
                if on_game:
                    on_game(game)
            progress(f"3 Oaks: página {page}/{total}, {len(games)} juegos.")
            page += 1
        complete = total is not None and page > total and not stop_event.is_set()
        self.set_catalog_authority(complete, "" if complete else "límite de páginas o crawl detenido")
        # One launcher describes all client families; no per-game demo sweep.
        if complete and games:
            try:
                representative = next(iter(games.values()))
                response = self.http.get(CATALOG_API + "/" + representative.slug + "/play", params={"lang": "en"}, timeout=30)
                response.raise_for_status()
                config = launcher_config(response.text)
                families = family_map(config)
                (self.provider_root / "families.json").write_text(json.dumps(families, indent=2), encoding="utf-8")
                for game in games.values():
                    self._save_metadata(game, family=families.get(game.slug, "unknown"))
            except Exception as exc:
                progress(f"3 Oaks: mapa de familias pendiente ({type(exc).__name__}).")
        progress(f"3 Oaks catálogo: {len(games)} juegos; autoridad={'sí' if complete else 'no'}.")
        return sorted(games.values(), key=lambda g: g.name.casefold())

    def test_game(self, game: Game, *, spins: int, timeout_s: float, stop_event: threading.Event, progress) -> GameTestResult:
        requested = max(1, int(spins))
        result = GameTestResult(self.key, game.slug, game.name, game.url, requested, 0, 0, "PARCIAL", symbol=game.symbol)
        if stop_event.is_set():
            result.error = "Ejecución detenida"
            return result
        start_time = time.monotonic()
        root = self.game_dir(game)
        run_dir = root / "tests" / (time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
        run_dir.mkdir(parents=True)
        result.run_dir = str(run_dir)
        result.discovered_modes = self._metadata(game).get("discovered_modes", [])
        try:
            response = self.http.get(CATALOG_API + "/" + game.slug + "/play", params={"lang": "en"}, timeout=timeout_s)
            response.raise_for_status()
            (run_dir / "launcher.html").write_text(response.text, encoding="utf-8")
            config = launcher_config(response.text)
            options, desktop = config["options"], config["desktop"]
            family = client_family(desktop["client_url"])
            endpoint = desktop["server_url"].replace("{QUEUE}", str(options["queue"]))
            if endpoint.startswith("//"):
                endpoint = "https:" + endpoint
            parsed = urlparse(endpoint)
            if parsed.scheme != "https" or parsed.hostname != "betman-demo.head.3oaks.com" or not parsed.path.endswith("/demo/") or options.get("wl") != "demo" or options.get("protocol") != "goreel":
                raise ValueError("3 Oaks: launcher fuera del contrato demo observado")
            session = DemoSession(self.http, endpoint, run_dir, timeout_s)
            login = session.post("login", {"token": options["token"], "language": options.get("lang", "en")})
            if not session.session_id:
                raise ValueError("3 Oaks: login no devolvió session_id")
            data = session.post("start", {"mode": "auto", "huid": login.get("user", {}).get("huid")})
            asset = self.http.get(desktop["client_url"] + "src/game.js", timeout=timeout_s)
            asset.raise_for_status()
            (root / "client.js").write_text(asset.text, encoding="utf-8")
            # Require each client's public serializer, not just a vendor label.
            observed = 'setActionHandler(bn.SPIN' in asset.text and 'bet_per_line' in asset.text and 'bet_factor' in asset.text
            purchase_observed = observed and 't.selected_mode=e' in asset.text and 'bn.BUY_SPIN' in asset.text
            modes = discover_modes(data, family, observed)
            for mode in modes:
                if mode["kind"] == "PURCHASE" and not purchase_observed:
                    mode["executable"] = False
                    mode["reason"] = "PURCHASE_SERIALIZER_CAPTURE_REQUIRED"
            result.discovered_modes = modes
            self._save_metadata(game, family=family, vendor=options.get("vendor"),
                                runtime_transport="goreel-http-commands", discovered_modes=modes)
            if not observed or not base_terminal(data):
                result.error = "3 Oaks: serializer o continuación inicial pendiente de captura"
                return result
            # Purchases are tried once each; never enumerate selector guesses.
            jobs = [(modes[0], None)] * requested + [(m, m["request_options"]["selected_mode"]) for m in modes[1:] if m["kind"] == "PURCHASE" and m["executable"]]
            for mode, selector in jobs:
                if stop_event.is_set():
                    result.error = "Ejecución detenida"
                    break
                action = mode["wire_action"]
                fields = play_fields(data, action, selector)
                previous_settings = data.get("settings", {})
                attempt_dir = run_dir / f"attempt-{len(result.attempts) + 1:03d}"
                data = session.post("play", fields, artifact_dir=attempt_dir)
                data.setdefault("settings", previous_settings)
                terminal = base_terminal(data)
                if terminal:
                    option = "spin" if mode["id"] == "SPIN" else str(selector)
                    mode["covered_options"] = [option]
                    counts = mode.setdefault("sample_counts", {})
                    counts[option] = counts.get(option, 0) + 1
                mode.update(observed=True, validated=terminal, evidence_level="REMOTE_EXECUTION",
                            execution_state="PROVEN_TERMINAL" if terminal else "CONTINUATION_PENDING")
                attempt = SpinAttempt(number=len(result.attempts) + 1, ok=terminal, mode_id=mode["id"], mode_kind=mode["kind"],
                    status_code=200, symbol=game.symbol, endpoint=endpoint, terminal=terminal,
                    wire_steps=1, artifact_dir=str(attempt_dir), warning="" if terminal else "Continuación pendiente de captura")
                result.attempts.append(attempt)
                if mode["id"] == "SPIN":
                    result.successful_spins += int(terminal)
                progress(f"[{game.name}] {mode['id']}: {'OK' if terminal else 'PARCIAL'}.")
                if not terminal:
                    result.error = "3 Oaks: continuación pendiente; no se inventan parámetros"
                    break
            result.status = "OK" if result.successful_spins == requested and all(m.get("validated") for m in modes) else "PARCIAL"
        except Exception as exc:
            result.status = "PARCIAL" if result.successful_spins else "ERROR"
            result.error = f"{type(exc).__name__}: {exc}"
            progress(f"[{game.name}] 3 Oaks pendiente: {result.error}")
        finally:
            result.failed_spins = max(0, requested - result.successful_spins)
            result.finished_at = utc_now_iso()
            result.elapsed_ms = (time.monotonic() - start_time) * 1000
            self._save_metadata(game, discovered_modes=result.discovered_modes)
        return result

    def har_artifact_dir(self, game: Game):
        path = self.game_dir(game) / "analysis"
        path.mkdir(exist_ok=True)
        return path

    def farm_contract_dir(self, game: Game):
        return self.game_dir(game)

    def build_farm_contract(self, game: Game, result: GameTestResult) -> dict:
        return build_result_farm_contract(game, result, self.game_dir(game), _SPEC)

    def validate_farm_contract(self, contract: dict):
        return validate_result_farm_contract(contract, _SPEC)
