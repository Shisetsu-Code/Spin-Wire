"""Purchase declarations from the matching D1 game constructor, without guessing wire actions."""
import re


def discover_purchase_modes(sources: list[str], game_name: str) -> list[dict]:
    if not re.fullmatch(r'[A-Za-z0-9_]+', game_name):
        return []
    constructor = re.compile(r'\b' + re.escape(game_name) + r'View\s*=\s*function\([^)]*\)\s*\{(.*?)\};', re.S)
    for source in sources:
        match = constructor.search(source)
        if not match:
            continue
        body = match.group(1)
        enabled = re.search(r'\bthis\.useBuyFeature\s*=\s*(!0|true)\s*[;,]', body)
        multiplier = re.search(r'\bthis\.buyFeatureMult\s*=\s*(\d+(?:\.\d+)?)\s*[;,]', body)
        if enabled:
            return [{
                'id': 'D1_BUY_FEATURE', 'kind': 'PURCHASE', 'observed': True,
                'coverage_required': True, 'executable': False, 'validated': False,
                'cost_multiplier': float(multiplier.group(1)) if multiplier else None,
                'contract_source': 'matching_game_client_constructor',
                'reason': 'PURCHASE_WS_REQUEST_AND_TERMINAL_RESPONSE_REQUIRED',
                'required_options': ['D1_BUY_FEATURE'], 'covered_options': [],
            }]
    return []


def apply_purchase_coverage(result, modes: list[dict]) -> None:
    known = {mode.get('id') for mode in result.discovered_modes}
    for mode in modes:
        if mode.get('id') not in known:
            result.discovered_modes.append(mode)
            known.add(mode.get('id'))
    if modes and result.status == 'OK':
        result.status = 'PARCIAL'
        result.error = 'D1: tirada base completa; compra detectada pendiente de validar con mensajes WebSocket y cierre.'


def purchase_modes_for_init(modes: list[dict], payload: dict) -> list[dict]:
    # Official client disables its buy UI when the init response has bf="f".
    return [] if payload.get("bf") == "f" else modes
