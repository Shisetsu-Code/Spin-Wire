"""Passive Yggdrasil wire discovery; historical purchases never imply a spin."""
import re
from urllib.parse import parse_qs, urlsplit

SLUG = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")
COMMAND = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")
PURCHASE = re.compile(r"BB_[A-Za-z0-9_-]+\Z", re.I)
ENDPOINT = "https://demo.yggdrasilgaming.com/game.web/service?fn=play"


def play_records(har: dict) -> list[dict]:
    records = []
    for entry in har.get("log", {}).get("entries", []):
        if not isinstance(entry, dict):
            continue
        request = entry.get("request", {})
        parsed = urlsplit(request.get("url", ""))
        host = (parsed.hostname or "").lower()
        if (request.get("method") != "POST" or parsed.scheme != "https"
                or host != "demo.yggdrasilgaming.com"
                or parsed.path.rstrip("/") != "/game.web/service"
                or parse_qs(parsed.query).get("fn") != ["play"]):
            continue
        post = request.get("postData", {})
        if not str(post.get("mimeType", "")).startswith("application/x-www-form-urlencoded"):
            continue
        values = parse_qs(str(post.get("text", "")), keep_blank_values=True)
        if not values and isinstance(post.get("params"), list):
            for item in post["params"]:
                values.setdefault(str(item.get("name", "")), []).append(str(item.get("value", "")))
        if any(len(value) != 1 for value in values.values()):
            continue
        body = {key: value[0] for key, value in values.items()}
        cmd, gameid = body.get("cmd", ""), body.get("gameid", "")
        if not COMMAND.fullmatch(cmd) or not gameid.isdecimal() or not {"amount", "coin"}.issubset(body):
            continue
        # Explicit allowlist: credentials, clientinfo and raw response never leave the HAR.
        records.append({"gameid": gameid, "cmd": cmd, "amount": body["amount"],
                        "coin": body["coin"], "http_status": entry.get("response", {}).get("status"),
                        "endpoint": ENDPOINT})
    return records


def discovered_modes(records: list[dict], gameid: str) -> list[dict]:
    modes = [{"id": "SPIN", "kind": "SPIN", "validated": False, "executable": False,
              "coverage_required": True, "required_options": ["DOMAIN_UNRESOLVED"],
              "covered_options": [], "reason": "BASE_COMMAND_AND_TERMINAL_CAPTURE_REQUIRED"}]
    seen = set()
    for record in records:
        if not gameid or record["gameid"] != gameid or record["cmd"] in seen:
            continue
        cmd = record["cmd"]
        seen.add(cmd)
        purchase = bool(PURCHASE.fullmatch(cmd))
        modes.append({"id": cmd, "kind": "PURCHASE" if purchase else "UNKNOWN_FEATURE",
            "wire_command": cmd, "observed": True, "validated": False, "executable": False,
            "evidence_level": "WIRE_CAPTURE", "coverage_required": True,
            "required_options": [cmd], "covered_options": [],
            "request_shape": {"cmd": cmd, "gameid": "<dynamic:gameid>",
                              "amount": "<dynamic:amount>", "coin": "<dynamic:coin>"},
            "observed_amount": record["amount"], "observed_coin": record["coin"],
            "reason": "BOOTSTRAP_AND_TERMINAL_CAPTURE_REQUIRED"})
    return modes
