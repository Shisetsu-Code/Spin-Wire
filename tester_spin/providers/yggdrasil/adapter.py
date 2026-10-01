from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup
from curl_cffi import requests

from tester_spin.models import Game, GameTestResult, utc_now_iso
from tester_spin.providers.base import ProviderAdapter
from tester_spin.providers.result_farm_contract import ProviderFarmSpec, build_result_farm_contract, validate_result_farm_contract
from .protocol import SLUG, ENDPOINT, play_records, discovered_modes

ORIGIN = "https://yggdrasilgaming.com"
SPEC = ProviderFarmSpec(provider="yggdrasil", protocol_family="yggdrasil-form-commands",
    bootstrap_strategy="yggdrasil-demo-capture-required", transport="http-form",
    terminal_contract={"type": "provider", "name": "yggdrasil-terminal-capture-required"},
    stable_metadata_keys=("catalog_source",),
    mode_option_keys=("request_shape", "observed_amount", "observed_coin"),
    runtime_outputs=("gameHistorySessionId", "gameHistoryTicketId", "clientinfo"),
    protocol_static={"endpoint": ENDPOINT, "content_type": "application/x-www-form-urlencoded",
                     "purchase_command_pattern": "BB_*"})


class YggdrasilProvider(ProviderAdapter):
    key = "yggdrasil"
    display_name = "Yggdrasil"
    catalog_url = ORIGIN + "/game-provider/yggdrasil-gaming"
    max_test_concurrency = 1

    def __init__(self, data_root: Path):
        self.provider_root = Path(data_root) / "providers" / self.key
        self.provider_root.mkdir(parents=True, exist_ok=True)
        self.http = requests.Session(impersonate="chrome")
        self.set_catalog_authority(False, "Catálogo importado de MultiPlay; actualización parcial")

    def game_dir(self, game: Game) -> Path:
        if game.provider != self.key or not SLUG.fullmatch(game.slug):
            raise ValueError("Yggdrasil: slug o proveedor inválido")
        directory = self.provider_root / game.slug
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def catalog_record_invalid_reason(self, game: Game) -> str:
        return "Yggdrasil: fila inválida" if (game.provider != self.key or not SLUG.fullmatch(game.slug)
            or game.url != ORIGIN + "/games/" + game.slug + "/") else ""

    def crawl_catalog(self, *, stop_event: threading.Event, progress, max_pages: int = 100, on_game=None):
        # A historical snapshot cannot authorize deleting newer catalog entries.
        self.set_catalog_authority(False, "Snapshot MultiPlay y enlaces públicos sin paginación completa verificada")
        if stop_event.is_set():
            return []
        snapshot = json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))
        rows = {row["slug"]: dict(row) for row in snapshot["games"]}
        try:
            response = self.http.get(self.catalog_url, timeout=25)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for link in soup.select('a[href]'):
                parsed = urlsplit(urljoin(ORIGIN, link["href"]))
                parts = parsed.path.strip("/").split("/")
                if parsed.hostname != "yggdrasilgaming.com" or len(parts) != 2 or parts[0] != "games" or not SLUG.fullmatch(parts[1]):
                    continue
                slug = parts[1]
                if slug not in rows:
                    title = link.get_text(" ", strip=True) or slug.replace("-", " ").title()
                    rows[slug] = {"slug": slug, "name": title}
            (self.provider_root / "catalog.html").write_text(response.text, encoding="utf-8")
        except Exception as exc:
            progress(f"Yggdrasil: usando catálogo MultiPlay ({type(exc).__name__}).")
        games = []
        for row in rows.values():
            if stop_event.is_set():
                break
            slug = row["slug"]
            if not SLUG.fullmatch(slug):
                continue
            game = Game(self.key, slug, row["name"], ORIGIN + "/games/" + slug + "/")
            directory = self.game_dir(game)
            metadata_path = directory / "game.json"
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                metadata = {}
            game.symbol = str(metadata.get("symbol") or "")
            metadata.update(provider=self.key, slug=slug, name=game.name, public_url=game.url,
                            catalog_source="multiplay-import-plus-public-links")
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            games.append(game)
            if on_game:
                on_game(game)
        progress(f"Yggdrasil: {len(games)} juegos; catálogo sin autoridad de eliminación.")
        return sorted(games, key=lambda game: game.name.casefold())

    def har_artifact_dir(self, game: Game):
        directory = self.game_dir(game) / "analysis"
        directory.mkdir(exist_ok=True)
        return directory

    def farm_contract_dir(self, game: Game):
        return self.game_dir(game)

    def prepare_test_artifacts(self, game: Game, *, timeout_s: float, stop_event: threading.Event, progress):
        if stop_event.is_set():
            return
        if self.catalog_record_invalid_reason(game):
            raise ValueError("Yggdrasil: página oficial inválida")
        response = self.http.get(game.url, timeout=timeout_s)
        response.raise_for_status()
        (self.har_artifact_dir(game) / "official-page.html").write_text(response.text, encoding="utf-8")
        soup = BeautifulSoup(response.text, "html.parser")
        identifiers = set()
        for element in soup.select('[data-iframe-src]'):
            parsed = urlsplit(element["data-iframe-src"])
            query = parse_qs(parsed.query)
            gameids = query.get("gameid", [])
            if (parsed.scheme == "https" and parsed.hostname == "staticdemo.yggdrasilgaming.com"
                    and parsed.path == "/init/launchClient.html" and query.get("org") == ["Demo"]
                    and len(gameids) == 1 and gameids[0].isdecimal()):
                identifiers.add(gameids[0])
        buy_bonus = False
        for label in soup.select('dt'):
            value = label.find_next_sibling('dd')
            if label.get_text(strip=True).lower() == "type" and value:
                buy_bonus = "buy bonus" in value.get_text(" ", strip=True).lower()
        path = self.game_dir(game) / "game.json"
        try:
            metadata = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            metadata = {}
        if len(identifiers) == 1:
            game.symbol = next(iter(identifiers))
            metadata.update(symbol=game.symbol, identifier_source=game.url)
        metadata.update(buy_bonus_advertised=buy_bonus)
        path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        progress(f"Yggdrasil: página consultada, ID={game.symbol or 'pendiente'}, Buy Bonus={'sí' if buy_bonus else 'no anunciado'}.")

    def test_game(self, game: Game, *, spins: int, timeout_s: float, stop_event: threading.Event, progress):
        result = GameTestResult(self.key, game.slug, game.name, game.url, max(1, int(spins)), 0, 0,
                                "PARCIAL", symbol=game.symbol)
        result.failed_spins = result.requested_spins
        if stop_event.is_set():
            result.error = "Ejecución detenida"
            return result
        started = time.monotonic()
        directory = self.game_dir(game)
        run_dir = directory / "tests" / (time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
        run_dir.mkdir(parents=True)
        result.run_dir = str(run_dir)
        records = []
        for path in sorted(self.har_artifact_dir(game).glob("*.har")):
            try:
                records.extend(play_records(json.loads(path.read_text(encoding="utf-8"))))
            except (OSError, ValueError, TypeError, AttributeError):
                progress(f"Yggdrasil: captura inválida {path.name}.")
        selected = [record for record in records if result.symbol and record["gameid"] == result.symbol]
        result.discovered_modes = discovered_modes(selected, result.symbol)
        (run_dir / "observed-play-commands.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
        result.error = "Yggdrasil: falta bootstrap, comando de giro base y cierre de ronda; compras capturadas sin executor validado"
        result.finished_at = utc_now_iso()
        result.elapsed_ms = (time.monotonic() - started) * 1000
        metadata_path = directory / "game.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            metadata = {}
        if metadata.get("buy_bonus_advertised") and not any(m["kind"] == "PURCHASE" for m in result.discovered_modes):
            result.discovered_modes.append({"id": "BUY_BONUS_UNRESOLVED", "kind": "UNKNOWN_FEATURE",
                "executable": False, "validated": False, "evidence_level": "SERVER_ADVERTISED",
                "coverage_required": True, "required_options": ["DOMAIN_UNRESOLVED"], "covered_options": [],
                "reason": "PURCHASE_COMMAND_CAPTURE_REQUIRED"})
        metadata.update(provider=self.key, slug=game.slug, name=game.name, public_url=game.url,
                        symbol=result.symbol, discovered_modes=result.discovered_modes)
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        progress(result.error)
        return result

    def build_farm_contract(self, game: Game, result: GameTestResult):
        return build_result_farm_contract(game, result, self.game_dir(game), SPEC)

    def validate_farm_contract(self, contract: dict):
        return validate_result_farm_contract(contract, SPEC)
