"""Purchase declarations from the matching D1 game constructor, without guessing wire actions."""
import re


def discover_purchase_modes(sources: list[str], game_name: str) -> list[dict]:
    if not re.fullmatch(r'[A-Za-z0-9_]+', game_name):
        return []
    constructor = re.compile(r'\b' + re.escape(game_name) + r'View\s*=\s*function\([^)]*\)\s*\{(.*?)\};', re.S)
    compact = re.sub(r"\s+", "", "".join(sources))
    default_buy_profile = all(token in compact for token in (
        '0==this.buyFeatureToPlayActionIndex?this.sideBet=2',
        '(Game.game.sideBet-1).toString()',
        'this.sideBetPercent=this.sideBet=0',
        'this.buyFeaturePlayIndex=this.sideBetPlayIndex=this.buyFeatureToPlayActionIndex=this.sideBetToPlayActionIndex=this.extraAnimationState=0',
        'SlotNetworkController.prototype.play=function(a,b,c)',
    ))
    for source in sources:
        match = constructor.search(source)
        if not match:
            continue
        body = match.group(1)
        enabled = re.search(r'\bthis\.useBuyFeature\s*=\s*(!0|true)\s*[;,]', body)
        multiplier = re.search(r'\bthis\.buyFeatureMult\s*=\s*(\d+(?:\.\d+)?)\s*[;,]', body)
        if enabled:
            supported = default_buy_profile and 'BasicSlotView.call(this)' in body and not any(name in body for name in ('sideBet','buyFeatureToPlayActionIndex','buyFeaturePlayIndex'))
            return [{
                'id': 'D1_BUY_FEATURE', 'kind': 'PURCHASE', 'observed': True,
                'coverage_required': True, 'executable': supported, 'validated': False,
                'feature_selector': 1 if supported else None,
                'cost_multiplier': float(multiplier.group(1)) if multiplier else None,
                'contract_source': 'matching_game_client_constructor',
                'reason': 'CLIENT_DEFAULT_BUY_SELECTOR' if supported else 'PURCHASE_WS_REQUEST_AND_TERMINAL_RESPONSE_REQUIRED',
                'required_options': ['D1_BUY_FEATURE'], 'covered_options': [],
            }]
    return []


def apply_purchase_coverage(result, modes: list[dict]) -> None:
    known = {mode.get('id') for mode in result.discovered_modes}
    for mode in modes:
        if mode.get('id') not in known:
            result.discovered_modes.append(mode)
            known.add(mode.get('id'))
    if any(not mode.get('validated') for mode in modes) and result.status == 'OK':
        result.status = 'PARCIAL'
        result.error = 'D1: tirada base completa; compra detectada pendiente de validar con mensajes WebSocket y cierre.'


def purchase_modes_for_init(modes: list[dict], payload: dict) -> list[dict]:
    # Official client disables its buy UI when the init response has bf="f".
    return [] if payload.get("bf") == "f" else modes

def classify_spin_message(payload: dict, *, purchase_selectors=(), side_bet_selectors=()):
    """Shape identifies a variant; game-specific selector evidence supplies its meaning."""
    if not isinstance(payload, dict) or isinstance(payload.get('type'), bool) or str(payload.get('type')) != '1':
        return None
    data = payload.get('data')
    if not isinstance(data, str) or len(data) > 128:
        return None
    fields = data.split(',')
    if len(fields) not in {3, 4} or any(not re.fullmatch(r'\d{1,10}', field) for field in fields):
        return None
    values = list(map(int, fields))
    if values[0] <= 0:
        return None
    result = {'operation': 'SPIN', 'variant': 'normal', 'lines':values[0],
              'bet_index':values[1], 'playmode':values[2]}
    if len(values) == 4:
        selector = values[3]
        result['feature_selector'] = selector
        result['variant'] = ('bonus_buy' if selector in purchase_selectors and selector not in side_bet_selectors
                             else 'side_bet' if selector in side_bet_selectors and selector not in purchase_selectors
                             else 'feature_variant')
    return result


def purchase_response_evidence(request, response, *, base_bet=None, cost_multiplier=None, observed_debit=None):
    """Acceptance evidence is separate from a completed bonus/return-to-base contract.

    observed_debit must be an independently verified debit, not a raw balance
    difference that might include wins or other operations.
    """
    import math
    def number(value):
        if isinstance(value, bool):
            return None
        try:
            value = float(value)
        except (ValueError, TypeError, OverflowError):
            return None
        return value if math.isfinite(value) and value >= 0 else None
    result = {'purchase_accepted':False, 'terminal':False, 'bonus_spins':None, 'cost_matches':False}
    if not isinstance(request, dict) or not isinstance(response, dict):
        return result
    bet, multiplier, debit = map(number, (base_bet, cost_multiplier, observed_debit))
    if bet and multiplier and debit is not None:
        expected = bet * multiplier
        result['cost_matches'] = math.isfinite(expected) and math.isclose(debit, expected, rel_tol=1e-6, abs_tol=1e-6)
    current, total = number(response.get('b8')), number(response.get('b9'))
    in_bonus = (response.get('type') == 3 and type(response.get('st')) is int and response.get('st') in {5,6,11,12}
                and current is not None and total is not None and total > 0
                and current.is_integer() and total.is_integer() and current <= total)
    if in_bonus:
        result['bonus_spins'] = int(total)
    result['purchase_accepted'] = bool(request.get('variant') == 'bonus_buy' and in_bonus and result['cost_matches'])
    return result
