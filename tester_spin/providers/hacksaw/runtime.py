"""Bootstrap and advertised purchases. A source serializer is not execution proof."""
import re
import math

API = "https://rgs-demo.hacksawgaming.com/api"
BONUS_ID = re.compile(r"[A-Za-z0-9_-]{1,100}\Z")


def checked_response(response):
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or type(data.get("statusCode")) is not int or data["statusCode"] != 0:
        raise ValueError("Hacksaw: statusCode no exitoso o ausente")
    return data


def terminal(data):
    round_data = data.get("round")
    return (isinstance(round_data, dict) and round_data.get("status") == "completed"
            and round_data.get("possibleActions") == [] and bool(round_data.get("roundId")))


def minimum_round_seconds(raw):
    try:
        value = float(raw or 0)
    except (ValueError, TypeError):
        raise ValueError("Hacksaw: duración mínima inválida")
    if not math.isfinite(value) or value < 0:
        raise ValueError("Hacksaw: duración mínima inválida")
    return value / 1000 if value >= 100 else value


def discover_modes(data):
    modes = [{"id": "SPIN", "kind": "SPIN", "executable": False, "validated": False,
        "coverage_required": True, "required_options": ["DOMAIN_UNRESOLVED"], "covered_options": [],
        "wire_command": "bet", "reason": "TERMINAL_AND_CONTINUATION_CAPTURE_REQUIRED"}]
    bonuses = data.get("bonusGames", [])
    seen = set()
    if not isinstance(bonuses, list):
        return modes
    for bonus in bonuses:
        if not isinstance(bonus, dict):
            continue
        identifier = bonus.get("bonusGameId")
        if isinstance(identifier, bool) or not isinstance(identifier, (str, int)):
            continue
        if not BONUS_ID.fullmatch(str(identifier)) or str(identifier) in seen:
            continue
        seen.add(str(identifier))
        raw_multiplier = bonus.get("betCostMultiplier")
        multiplier = None
        if not isinstance(raw_multiplier, bool):
            try:
                value = float(raw_multiplier)
                if math.isfinite(value) and value > 0:
                    multiplier = int(value) if value.is_integer() else value
            except (ValueError, TypeError, OverflowError):
                pass
        modes.append({"id": "BUY_" + str(identifier), "kind": "PURCHASE", "buyBonus": identifier,
            "feature_multiplier": multiplier,
            "wire_command": "bet", "executable": False, "validated": False, "observed": True,
            "evidence_level": "SERVER_ADVERTISED", "coverage_required": True,
            "required_options": [str(identifier)], "covered_options": [],
            "request_shape": {"bets": [{"betAmount": "<dynamic:betAmount>", "buyBonus": identifier}]},
            "reason": "PURCHASE_TERMINAL_AND_CONTINUATION_CAPTURE_REQUIRED"})
    return modes
