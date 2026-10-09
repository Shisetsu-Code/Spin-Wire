"""Red Tiger base-state evidence, independent of catalog names and identifiers."""
from .result_tree import result_nodes, walk_tree


def classify_base_state(payload):
    def verdict(base, reason, **signals):
        return {'base':base, 'known':base, 'reason':reason, 'signals':signals}
    if not isinstance(payload, dict) or payload.get('success') is not True:
        return verdict(False, 'unsuccessful_response')
    result=payload.get('result')
    game=result.get('game') if isinstance(result, dict) else None
    if not isinstance(game, dict):
        return verdict(False, 'missing_game_result')
    nodes=result_nodes(game)
    if not nodes:
        return verdict(False, 'missing_outcome_evidence')
    # Success and a normal request do not override a returned bonus/choice.
    for path, value in walk_tree(game):
        if not isinstance(value, dict):
            continue
        choices=value.get('choices')
        if isinstance(choices, dict) and choices.get('available') and not choices.get('selected'):
            return verdict(False, 'pending_choice', path=path)
        if any(value.get(k) for k in ('fsp','rsp','features')):
            return verdict(False, 'feature_or_continuation_present', path=path)
        if 'state' in value and value['state'] not in (None, [], {}):
            return verdict(False, 'uninterpreted_state', path=path)
        if 'mode' in value and str(value['mode']).lower() != 'normal':
            return verdict(False, 'non_normal_component', path=path)
    for node in nodes:
        if node.spin_mode and node.spin_mode.lower() != 'normal':
            return verdict(False, 'non_normal_spin_mode', path=node.path, spin_mode=node.spin_mode)
        if node.game_mode is not None and (type(node.game_mode) is not int or node.game_mode != 0):
            return verdict(False, 'non_normal_game_mode', path=node.path, game_mode=node.game_mode)
    normal=bool(game.get('spinMode') and str(game['spinMode']).lower()=='normal') or type(game.get('gameMode')) is int and game['gameMode']==0
    if all(node.has_state is False for node in nodes) and normal:
        return verdict(True, 'closed_normal_result', has_state=False)
    nsp=game.get('nsp')
    if (all(node.has_state is False for node in nodes) and game.get('state')==[]
            and isinstance(nsp,dict) and isinstance(nsp.get('reels'),list) and nsp['reels']):
        return verdict(True, 'closed_normal_spin_outcome', has_state=False, outcome='nsp', state=[])
    if (normal and game.get('debugNormal') is True and game.get('features')==[]
            and isinstance(game.get('reelsBuffer'),list) and game['reelsBuffer']
            and len(nodes)==1):
        return verdict(True, 'explicit_normal_outcome_with_persistent_state',
                       has_state=game.get('hasState'), debug_normal=True)
    return verdict(False, 'insufficient_base_evidence',
                   has_state=game.get('hasState'), normal_mode=normal,
                   note='hasState alone does not identify a bonus or prove base state')
