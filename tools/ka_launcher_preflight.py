"""Read-only availability check for every KA Gaming demo slot launcher."""

from __future__ import annotations

import concurrent.futures
import argparse
import json
import zlib
from collections import Counter
from typing import Any

from curl_cffi import requests

CATALOG_URL = "https://rmpdemo.kaga88.com/kaga/publicGameList"
HEADERS = {"Origin": "https://www.kaga88.com", "Referer": "https://www.kaga88.com/"}


def launch_url(base_url: str, game_id: str) -> str:
    user = (zlib.crc32(game_id.encode("utf-8")) % 1_000_000_000) + 1
    return (
        f"{base_url.rstrip('/')}/?g={game_id}&p=demo&u={user}&t=123"
        "&ak=accessKey&cr=USD&loc=es&l=https%3A%2F%2Fwww.kaga88.com%2F"
    )


def check_launcher(base_url: str, row: dict[str, Any]) -> dict[str, Any]:
    game_id = str(row["gameId"])
    try:
        response = requests.get(launch_url(base_url, game_id), impersonate="chrome", timeout=20)
        return {"game_id": game_id, "variant": row.get("variantType"), "status": response.status_code, "bytes": len(response.content)}
    except Exception as error:  # Retain failures for the pending-game queue.
        return {"game_id": game_id, "variant": row.get("variantType"), "status": "ERROR", "error": type(error).__name__}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0, help="0 checks every slot")
    args = parser.parse_args()
    catalog = requests.get(CATALOG_URL, params={"lang": "es"}, impersonate="chrome", headers=HEADERS, timeout=30).json()
    slots = [row for row in catalog["games"] if row.get("gameType") == "slots"]
    selected = slots[args.offset : args.offset + args.limit] if args.limit else slots[args.offset :]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda row: check_launcher(catalog["gameLaunchURL"], row), selected))
    by_status = Counter(str(result["status"]) for result in results)
    failures = [result for result in results if result["status"] != 200]
    print(
        json.dumps(
            {"catalog_slots": len(slots), "offset": args.offset, "checked": len(selected), "status_counts": dict(by_status), "failure_count": len(failures), "failures": failures[:50]},
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
