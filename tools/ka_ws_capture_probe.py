"""Capture the WebSocket contract exposed by one official KA Gaming demo.

This is deliberately observational: it records only browser-created socket URLs
and frames.  It does not manufacture a session token or send a wager itself.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tester_spin.providers.ka_gaming.catalog import build_launch_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("game_id")
    parser.add_argument("--base-url", default="https://gamesdemo.kaga88.com")
    parser.add_argument("--wait", type=float, default=20.0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    captured: list[dict[str, str]] = []
    requests: list[dict[str, str]] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(record_har_path=str(args.output.with_suffix(".har")))
        page = context.new_page()

        def on_request(request) -> None:
            url = request.url
            if len(requests) < 500:
                requests.append({"method": request.method, "url": url, "resource_type": request.resource_type})

        def on_socket(socket) -> None:
            captured.append({"event": "open", "url": socket.url})
            socket.on("framesent", lambda payload: captured.append({"event": "sent", "payload": str(payload)[:2000]}))
            socket.on("framereceived", lambda payload: captured.append({"event": "received", "payload": str(payload)[:2000]}))

        page.on("websocket", on_socket)
        page.on("request", on_request)
        url = build_launch_url(args.base_url, args.game_id, language="es")
        page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        deadline = time.monotonic() + max(1.0, args.wait)
        while time.monotonic() < deadline and not captured:
            page.wait_for_timeout(250)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps({"launch_url": url, "events": captured, "requests": requests}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        context.close()
        browser.close()

    print(json.dumps({"events": len(captured), "output": str(args.output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
