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

from playwright.sync_api import Error, sync_playwright

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
    parser.add_argument("--headed", action="store_true", help="abre Chromium visible para superar desafíos de navegador")
    args = parser.parse_args()

    captured: list[dict[str, str]] = []
    requests: list[dict[str, object]] = []
    url = build_launch_url(args.base_url, args.game_id, language="es")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stop_reason = "completed"
    error = ""

    def save_capture() -> None:
        temporary = args.output.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps({"launch_url": url, "events": captured, "requests": requests,
                        "stop_reason": stop_reason, "error": error}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(args.output)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=not args.headed)
        context = browser.new_context(record_har_path=str(args.output.with_suffix(".har")))
        page = context.new_page()

        def on_request(request) -> None:
            url = request.url
            if len(requests) < 500:
                requests.append({
                    "method": request.method,
                    "url": url,
                    "resource_type": request.resource_type,
                    "headers": {key: value for key, value in request.headers.items()
                                if key.lower() in {"content-type", "ctx", "origin", "referer"}},
                    "post_data": request.post_data if request.resource_type in {"fetch", "xhr"} else None,
                })
                save_capture()

        def on_socket(socket) -> None:
            captured.append({"event": "open", "url": socket.url})
            save_capture()

            def frame(event: str, payload) -> None:
                captured.append({"event": event, "payload": str(payload)})
                save_capture()

            socket.on("framesent", lambda payload: frame("sent", payload))
            socket.on("framereceived", lambda payload: frame("received", payload))

        page.on("websocket", on_socket)
        page.on("request", on_request)
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            deadline = time.monotonic() + max(1.0, args.wait)
            while time.monotonic() < deadline:
                page.wait_for_timeout(250)
        except Error as exc:
            if page.is_closed():
                stop_reason = "browser_closed"
            else:
                stop_reason = "capture_error"
                error = str(exc)
        finally:
            save_capture()
            try:
                context.close()
            except Error:
                pass
            try:
                browser.close()
            except Error:
                pass

    print(json.dumps({"events": len(captured), "output": str(args.output)}, ensure_ascii=False))
    return 1 if error else 0


if __name__ == "__main__":
    raise SystemExit(main())
