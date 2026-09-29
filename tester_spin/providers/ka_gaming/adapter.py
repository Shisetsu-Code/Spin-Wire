from __future__ import annotations

import json
import threading
from pathlib import Path

from curl_cffi import requests

from tester_spin.models import Game, GameTestResult
from tester_spin.providers.base import GameCallback, Progress, ProviderAdapter
from tester_spin.providers.ka_gaming.catalog import CATALOG_URL, declared_modes_from_row, games_from_catalog


class KAGamingProvider(ProviderAdapter):
    key = "ka_gaming"
    display_name = "KA Gaming"
    catalog_url = CATALOG_URL
    min_catalog_reconcile_ratio = 0.80

    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)
        self.provider_root = self.data_root / "providers" / self.key
        self.provider_root.mkdir(parents=True, exist_ok=True)
        self.http = requests.Session(impersonate="chrome", headers={"Accept-Language": "es-ES,es;q=0.9"})
        self._modes_path = self.provider_root / "catalog_modes.json"
        self._catalog_modes = self._load_catalog_modes()

    def _load_catalog_modes(self) -> dict[str, list[dict[str, object]]]:
        try:
            raw = json.loads(self._modes_path.read_text(encoding="utf-8"))
            return raw if isinstance(raw, dict) else {}
        except (OSError, ValueError):
            return {}

    def crawl_catalog(self, *, stop_event: threading.Event, progress: Progress, max_pages: int = 100, on_game: GameCallback | None = None) -> list[Game]:
        del max_pages
        if stop_event.is_set():
            self.set_catalog_authority(False, "crawl detenido por el usuario")
            return []
        response = self.http.get(self.catalog_url, params={"lang": "es"}, headers={"Origin": "https://www.kaga88.com", "Referer": "https://www.kaga88.com/"}, timeout=30)
        response.raise_for_status()
        payload = response.json()
        games = games_from_catalog(payload, language="es")
        self._catalog_modes = {
            str(row["gameId"]).casefold(): declared_modes_from_row(row)
            for row in payload["games"]
            if isinstance(row, dict) and str(row.get("gameType") or "").casefold() == "slots"
        }
        self._modes_path.write_text(json.dumps(self._catalog_modes, ensure_ascii=False, indent=2), encoding="utf-8")
        if stop_event.is_set():
            self.set_catalog_authority(False, "crawl detenido por el usuario")
            return games
        self.set_catalog_authority(True)
        for game in games:
            if on_game: on_game(game)
        progress(f"KA Gaming catálogo terminado: {len(games)} juegos; autoridad=sí.")
        return games

    def test_game(self, game: Game, *, spins: int, timeout_s: float, stop_event: threading.Event, progress: Progress) -> GameTestResult:
        del timeout_s, stop_event
        progress(f"[{game.name}] KA Gaming: transporte WebSocket confirmado; falta capturar vds de una sesión para ejecutar el spin.")
        return GameTestResult(
            provider=self.key,
            slug=game.slug,
            game_name=game.name,
            game_url=game.url,
            symbol=game.symbol,
            requested_spins=spins,
            successful_spins=0,
            failed_spins=0,
            status="PARCIAL",
            error="KA Gaming: WebSocket y mensaje de giro confirmados, pero vds es una credencial de sesión efímera; no se envió apuesta fuera del navegador.",
            discovered_modes=self._discovered_modes(game),
        )

    def _discovered_modes(self, game: Game) -> list[dict[str, object]]:
        declared = [dict(mode) for mode in self._catalog_modes.get(game.slug, [])]
        if not declared:
            declared = [{"id": "SPIN", "kind": "SLOTS", "source": "fallback", "executable": False, "coverage_required": False}]
        for mode in declared:
            if mode["id"] == "SPIN":
                mode.update({
                    "reason": "SESSION_VDS_CAPTURE_REQUIRED",
                    "transport": "websocket+rmp-http",
                    "endpoint_template": "wss://pml{host}/kaga/fish/{gameId}?vds=<session>&ak=accessKey",
                    "request_type": "fr",
                    "request_fields": ["rt", "mid", "a", "l", "c", "b", "bt"],
                    # Playwright asset evidence from a real normal spin in both
                    # CapyGo123 (lines) and GoldenBull (ways).  `ctx` and the
                    # startGame response remain session-bound, so this is a
                    # discovered candidate rather than an executable contract.
                    "rmp_spin": {
                        "method": "POST",
                        "endpoint_template": "https://rmp{host}/kaga/command/spin?ak=<accessKey>&cr=<currency>&m=<mode>&u=<user>",
                        "content_type": "application/json",
                        "request_fields": ["gn", "sel", "sid", "cps", "atb", "dn", "psp?", "pos?"],
                        "required_header": "ctx",
                        "evidence": ["CapyGo123", "GoldenBull"],
                    },
                    "rmp_start_game": {
                        "method": "POST",
                        "endpoint_template": "https://rmp{host}/kaga/rmp/startGame?ak=<accessKey>&cr=<currency>&m=<mode>&u=<user>",
                        "content_type": "application/json",
                        "request_fields": ["on?", "un", "pn", "ak", "gn", "loc", "to", "cr", "gm", "tb", "mi", "mc", "psp?", "jrd?", "to2?"],
                        "required_header": "ctx",
                        "ctx_fields": ["u?", "c?", "dt?", "dv?", "av", "ida", "idv", "lg", "do", "as", "ak"],
                        "signature": "sha256(client-side signed ctx; timestamp-bound)",
                        "returns": ["sid", "cps", "sel", "psp?"],
                        "evidence": "game.min.2070.js: Bca, Fc.G8e, Cc.I9e",
                    },
                })
            else:
                mode["reason"] = "WIRE_CONTRACT_NOT_OBSERVED"
        return declared
