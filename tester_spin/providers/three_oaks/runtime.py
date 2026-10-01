"""Goreel command transport. Discovery never substitutes for remote proof."""
import json
import time
import uuid


def checked_response(response) -> dict:
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("3 Oaks: respuesta no es objeto")
    status = data.get("status")
    if not isinstance(status, dict) or str(status.get("code", "")).upper() != "OK" or str(status.get("type", "ok")).lower() != "ok":
        raise ValueError("3 Oaks: " + str(status.get("code", "INVALID_STATUS") if isinstance(status, dict) else "INVALID_STATUS"))
    return data


def base_terminal(data: dict) -> bool:
    context = data.get("context", {})
    return (isinstance(context, dict) and context.get("round_finished") is True
            and context.get("current") == "spins" and "spin" in context.get("actions", []))


def discover_modes(data: dict, family: str, serializer_observed: bool) -> list[dict]:
    context, settings = data.get("context", {}), data.get("settings", {})
    usable = serializer_observed and family in {"enjoy", "goreel", "ratpack", "hraymo", "kendoo"}
    modes = [{"id": "SPIN", "kind": "SPIN", "executable": usable, "validated": False,
              "observed": False, "source": "server-start", "family": family,
              "wire_action": "spin", "wire_command": "play", "coverage_required": True,
              "required_options": ["spin"], "covered_options": [], "sample_counts": {}}]
    values = context.get("available_buy_bonus", [])
    prices = settings.get("buy_bonus_prices", {})
    if isinstance(values, list):
        for value in values:
            if not isinstance(value, (int, str)) or isinstance(value, bool):
                continue
            modes.append({"id": f"PURCHASE_{value}", "kind": "PURCHASE", "executable": usable,
                "validated": False, "observed": False, "coverage_required": True,
                "source": "server-start", "family": family, "wire_action": "buy_spin", "wire_command": "play",
                "required_options": [str(value)], "covered_options": [], "sample_counts": {},
                "selected_mode": value,
                "request_options": {"selected_mode": value}, "feature_multiplier": prices.get(str(value)) if isinstance(prices, dict) else None})
    # Other purchase/booster formats remain visible and unimplemented.
    for key in ("available_boosters", "available_buy_freespins"):
        values = context.get(key)
        if values:
            modes.append({"id": key.upper(), "kind": "UNKNOWN_FEATURE", "executable": False,
                          "validated": False, "coverage_required": True, "required_options": values,
                          "reason": "WIRE_FORMAT_CAPTURE_REQUIRED"})
    return modes


def play_fields(data: dict, action: str, selected_mode=None) -> dict:
    context, settings = data["context"], data.get("settings", {})
    if action not in context.get("actions", []):
        raise ValueError("3 Oaks: acción no anunciada")
    params = {}
    if action in {"spin", "buy_spin"}:
        state = context.get(context.get("current"), {})
        factor = settings.get("bet_factor")
        if not isinstance(factor, list) or not factor or not all(isinstance(state.get(k), (int, float)) and not isinstance(state.get(k), bool) for k in ("bet_per_line", "lines")):
            raise ValueError("3 Oaks: perfil de apuesta pendiente")
        params = {"bet_per_line": state["bet_per_line"], "lines": state["lines"], "bet_factor": factor[0]}
        if action == "buy_spin":
            if selected_mode not in context.get("available_buy_bonus", []):
                raise ValueError("3 Oaks: compra no anunciada")
            params["selected_mode"] = selected_mode
    return {"action": {"name": action, "params": params}, "set_denominator": 1,
            "quick_spin": False, "sound": True, "autogame": False,
            "mobile": "0", "portrait": False, "fullscreen": False, "viewportSize": "1280x720"}


class DemoSession:
    def __init__(self, http, endpoint: str, run_dir, timeout: float):
        self.http, self.endpoint, self.run_dir, self.timeout = http, endpoint, run_dir, timeout
        self.session_id = None
        self.index = 0

    def post(self, command: str, fields: dict, *, artifact_dir=None) -> dict:
        body = {"command": command, "request_id": uuid.uuid4().hex,
                "client_command_timestamp": int(time.time() * 1000), **fields}
        if self.session_id:
            body["session_id"] = self.session_id
        label = f"{self.index:03d}-{command}"
        self.index += 1
        directory = artifact_dir if artifact_dir is not None else self.run_dir
        directory.mkdir(parents=True, exist_ok=True)
        # Exact local evidence, never put these session values into reusable exports.
        (directory / (label + ".request.json")).write_text(json.dumps(body, indent=2), encoding="utf-8")
        response = self.http.post(self.endpoint, params={"gsc": command},
            data=json.dumps(body, separators=(",", ":")), timeout=self.timeout,
            headers={"Content-Type": "text/plain", "Origin": "https://3oaks.com", "Referer": "https://3oaks.com/"})
        (directory / (label + ".response.raw.json")).write_text(response.text, encoding="utf-8")
        data = checked_response(response)
        self.session_id = data.get("session_id", self.session_id)
        return data
