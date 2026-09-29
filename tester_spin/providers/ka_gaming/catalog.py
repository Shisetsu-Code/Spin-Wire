from __future__ import annotations

import zlib
from typing import Any
from urllib.parse import urlencode, urlparse

from tester_spin.models import Game

CATALOG_URL = "https://rmpdemo.kaga88.com/kaga/publicGameList"


def build_launch_url(base_url: str, game_id: str, *, language: str) -> str:
    parsed = urlparse(str(base_url))
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("KA Gaming: gameLaunchURL inválida")
    user = (zlib.crc32(game_id.encode("utf-8")) % 1_000_000_000) + 1
    query = urlencode({"g": game_id, "p": "demo", "u": user, "t": 123, "ak": "accessKey", "cr": "USD", "loc": language, "l": "https://www.kaga88.com/"})
    return f"{base_url.rstrip('/')}/?{query}"


def games_from_catalog(payload: Any, *, language: str) -> list[Game]:
    if not isinstance(payload, dict) or payload.get("status") != "ok" or payload.get("statusCode") != 0:
        raise ValueError("KA Gaming: catálogo inválido")
    rows = payload.get("games")
    if not isinstance(rows, list) or int(payload.get("numGames", -1)) != len(rows):
        raise ValueError("KA Gaming: numGames no coincide")
    base = str(payload.get("gameLaunchURL") or "")
    seen: set[str] = set(); out: list[Game] = []
    for row in rows:
        game_id = str(row.get("gameId") or "").strip() if isinstance(row, dict) else ""
        if not game_id:
            raise ValueError("KA Gaming: gameId vacío")
        if game_id in seen:
            raise ValueError(f"KA Gaming: gameId duplicado: {game_id}")
        seen.add(game_id)
        name = str(row.get("gameName") or game_id).strip()
        icon = str(row.get("iconURLPrefix") or "").strip()
        thumbnail = f"{icon}{'&' if '?' in icon else '?'}type=square" if icon else ""
        out.append(Game(provider="ka_gaming", slug=game_id.casefold(), name=name, symbol=game_id, url=build_launch_url(base, game_id, language=language), thumbnail_url=thumbnail))
    return sorted(out, key=lambda game: game.name.casefold())
