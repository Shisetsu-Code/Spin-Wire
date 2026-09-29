from __future__ import annotations

import threading
from pathlib import Path

from curl_cffi import requests

from tester_spin.models import Game, GameTestResult
from tester_spin.providers.base import GameCallback, Progress, ProviderAdapter
from tester_spin.providers.ka_gaming.catalog import CATALOG_URL, games_from_catalog


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

    def crawl_catalog(self, *, stop_event: threading.Event, progress: Progress, max_pages: int = 100, on_game: GameCallback | None = None) -> list[Game]:
        del max_pages
        if stop_event.is_set():
            self.set_catalog_authority(False, "crawl detenido por el usuario")
            return []
        response = self.http.get(self.catalog_url, params={"lang": "es"}, headers={"Origin": "https://www.kaga88.com", "Referer": "https://www.kaga88.com/"}, timeout=30)
        response.raise_for_status()
        games = games_from_catalog(response.json(), language="es")
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
        progress(f"[{game.name}] KA Gaming: bootstrap descubierto; falta contrato de spin observado.")
        return GameTestResult(provider=self.key, slug=game.slug, game_name=game.name, game_url=game.url, symbol=game.symbol, requested_spins=spins, successful_spins=0, failed_spins=0, status="PARCIAL", error="KA Gaming: falta contrato de spin/modos demostrado; no se envió apuesta.", discovered_modes=[{"id": "SPIN", "executable": False, "reason": "CONTRACT_UNRESOLVED"}])
