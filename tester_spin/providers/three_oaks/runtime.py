"""Goreel command transport. Discovery never substitutes for remote proof."""
import json
import math
import re
import time
import uuid
from pathlib import Path


def observed_spin_profile(game_slug: str, family: str) -> dict | None:
    rules = json.loads(Path(__file__).with_name('observed_game_rules.json').read_text(encoding='utf-8'))
    if rules.get('schema') != 'three-oaks/observed-spin-inputs/v1':
        raise ValueError('3 Oaks: esquema de reglas desconocido')
    profile = rules.get('games', {}).get(game_slug)
    if (isinstance(profile, dict) and profile.get('family') == family
            and profile.get('spin_params') == ['bet_per_line', 'lines']
            and profile.get('evidence')):
        return profile
    return None


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


def play_fields(data: dict, action: str, selected_mode=None, *, game_slug='', family='', client_profile=None) -> dict:
    context, settings = data["context"], data.get("settings", {})
    if action not in context.get("actions", []):
        raise ValueError("3 Oaks: acción no anunciada")
    params = {}
    if action in {"spin", "buy_spin"}:
        state = context.get(context.get("current"), {})
        factor = settings.get("bet_factor")
        profile = client_profile or {}
        captured_spin = action == 'spin' and profile.get('spin_params') == ['bet_per_line', 'lines']
        purchase_params = profile.get('purchase_params', {}).get(str(selected_mode)) if action == 'buy_spin' else None
        if purchase_params is not None:
            if (not isinstance(purchase_params, list) or not {'bet_per_line', 'lines'}.issubset(purchase_params)
                    or set(purchase_params) - {'bet_per_line', 'lines', 'bet_factor', 'selected_mode'}):
                raise ValueError('3 Oaks: contrato de compra inválido')
            if 'selected_mode' not in purchase_params and context.get('available_buy_bonus') != [selected_mode]:
                raise ValueError('3 Oaks: compra sin selector ambigua')
        zero_lines_announced = state.get('lines') == 0 and any(type(value) in (int, float) and value == 0 for value in settings.get('lines', []))
        if not all(isinstance(state.get(k), (int, float)) and not isinstance(state.get(k), bool) and math.isfinite(state[k])
                   and (state[k] > 0 or k == 'lines' and zero_lines_announced) for k in ("bet_per_line", "lines")):
            raise ValueError("3 Oaks: perfil de apuesta pendiente")
        params = {"bet_per_line": state["bet_per_line"], "lines": state["lines"]}
        if action in {'spin','buy_spin'}:
            source = profile.get('purchase_value_sources' if action == 'buy_spin' else 'spin_value_sources', {}).get('lines')
            if source == 'settings_lines_dynamic':
                raise ValueError('3 Oaks: índice de líneas del cliente sin resolver')
            values = settings.get('bet_factor' if source == 'bet_factor_first' else 'lines')
            if source in {'bet_factor_first', 'settings_lines_first'}:
                if not isinstance(values, list) or not values or not isinstance(values[0], (int, float)) or isinstance(values[0], bool) or values[0] <= 0:
                    raise ValueError('3 Oaks: origen de líneas de compra pendiente')
                params['lines'] = values[0]
        if not captured_spin and (purchase_params is None or 'bet_factor' in purchase_params):
            if not isinstance(factor, list) or not factor or not isinstance(factor[0], (int,float)) or isinstance(factor[0], bool) or factor[0] <= 0:
                raise ValueError("3 Oaks: perfil de apuesta pendiente")
            params['bet_factor'] = factor[0]
        if action == "buy_spin":
            if selected_mode not in context.get("available_buy_bonus", []):
                raise ValueError("3 Oaks: compra no anunciada")
            if purchase_params is None or 'selected_mode' in purchase_params:
                selector_type = profile.get('purchase_selector_type')
                value = selected_mode
                if selector_type == 'string':
                    value = str(value)
                elif selector_type == 'number':
                    # Mirror a certified Number(...) input, but never emit NaN,
                    # Infinity or a value obtained from an unknown expression.
                    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
                        raise ValueError('3 Oaks: selector numérico inválido')
                    if isinstance(value, str) and not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', value.strip()):
                        raise ValueError('3 Oaks: selector numérico inválido')
                    try:
                        numeric = float(value)
                    except (TypeError, ValueError, OverflowError) as exc:
                        raise ValueError('3 Oaks: selector numérico inválido') from exc
                    if not math.isfinite(numeric):
                        raise ValueError('3 Oaks: selector numérico no finito')
                    value = int(numeric) if numeric.is_integer() else numeric
                params["selected_mode"] = value
    return {"action": {"name": action, "params": params}, "set_denominator": 1,
            "quick_spin": False, "sound": True, "autogame": False,
            "mobile": "0", "portrait": False, "fullscreen": False, "viewportSize": "1280x720"}


def source_continuation_rules(source: str) -> dict:
    """Certify legacy empty-argument calls from the current fetched client."""
    if ('params:args||{}' not in source
            or not re.search(r'this\.handlers\[action\]\|\|function\(args\)\{return \w+\._act\(action,args\)\}', source)):
        return {}
    rules = {}
    if ('BONUS_INIT:"bonus_init"' in source
            and '.act(_constants.FLOW_ACTIONS.BONUS_INIT)' in source
            and 'setActionHandler(_constants.FLOW_ACTIONS.BONUS_INIT' not in source):
        rules['bonus_init'] = {'current': 'spins'}
    handlers = re.findall(r'setActionHandler\(_constants\.FLOW_ACTIONS\.RESPIN,function\(args\)\{(.{0,1000}?)\}\);', source)
    if ('RESPIN:"respin"' in source and '.act(_constants.FLOW_ACTIONS.RESPIN)' in source and handlers
            and all(re.search(r'return \w+\._act\(_constants\.FLOW_ACTIONS\.RESPIN,args\)', body)
                    and not re.search(r'args\s*=|args\.', body) for body in handlers)):
        rules['respin'] = {'current': 'bonus'}
    if ('.act(_constants.FLOW_ACTIONS.BONUS_STOP)' in source
            and 'setActionHandler(_constants.FLOW_ACTIONS.BONUS_STOP' not in source
            and 'get BONUS_STOP(){return"bonus_".concat(' in source
            and '.model.bonusOriginState(),"_stop")' in source
            and 'this._get("game.bonus.back_to","spins")' in source):
        rules['bonus_spins_stop'] = {'current': 'bonus', 'back_to': 'spins'}
    return rules


def continuation_fields(data: dict, *, game_slug: str, family: str, source_rules=None, client_profile=None) -> dict | None:
    """Only transitions demonstrated by HAR or an active empty-argument serializer."""
    profile = client_profile or {}
    context = data.get('context', {})
    actions = context.get('actions')
    if context.get('round_finished') is not False or not isinstance(actions, list) or len(actions) != 1:
        return None
    action = actions[0]
    rule = (profile or {}).get('continuations', {}).get(action) or (source_rules or {}).get(action)
    if not isinstance(rule, dict) or (context.get('current') != rule.get('current')
            and not (rule.get('state_independent') is True and context.get('current') in {'spins','freespins','bonus'})):
        return None
    if rule.get('back_to') and context.get('bonus', {}).get('back_to', rule.get('back_to_default')) != rule['back_to']:
        return None
    return play_fields(data, action, game_slug=game_slug, family=family, client_profile=client_profile)


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
