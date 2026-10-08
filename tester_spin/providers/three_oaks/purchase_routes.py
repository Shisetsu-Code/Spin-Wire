"""Finite purchase inputs from current client calls, not game/vendor defaults.

Only literal fields, advertised options and settings-backed branches are handled.
An unknown write, expression or controller binding leaves the route unresolved.
"""
import json
import re
from .code_primitives import ID, _group, _split_top_level, flow_parameters

_REF = ID + r'(?:\.' + ID + r')*'


def _setting(data, path):
    value = data
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            return 0
        value = value[key]
    return value


def _resolve_branches(prefix, source, data):
    pattern = r'if\(' + _REF + r'\.model\.(' + ID + r')\(\)\)\{'
    for _ in range(4):
        match = re.search(pattern, prefix)
        if not match:
            return prefix
        getter = r'\.prototype\.' + re.escape(match[1]) + r'=function\(\)\{return!this\._get\("(settings\.[^"\\]+)",0\)\}'
        paths = set(re.findall(getter, source))
        if len(paths) != 1:
            return None
        yes = _group(prefix, match.end()-1)
        if yes is None or prefix[yes[1]:yes[1]+5] != 'else{':
            return None
        no = _group(prefix, yes[1]+4)
        if no is None:
            return None
        selected = yes[0] if not _setting(data, paths.pop()) else no[0]
        prefix = prefix[:match.start()] + ';' + selected + ';' + prefix[no[1]:]
    return None


def _neutral_toggle(prefix, source, variable):
    # A conditional ante field can be omitted only for a client toggle whose
    # constructor starts inactive and which disables the purchase button while
    # active. This contract is explicitly scoped to the neutral purchase UI.
    pattern = r'if\((' + _REF + r')\.(' + ID + r')\.active\)\{'
    match = re.search(pattern, prefix)
    if not match:
        return prefix, False
    body = _group(prefix, match.end()-1)
    if not body or not re.fullmatch(re.escape(variable) + r'\.ante_bet=' + _REF + r'\(\)', body[0]):
        return None, False
    binding = re.search(re.escape(match[1]+'.'+match[2]) + r'=new ' + _REF + r'\.(' + ID + r')(?=[;,])', source)
    if not binding:
        return None, False
    constructor = re.search(r'function ' + re.escape(binding[1]) + r'\(\)\{[^{};]*;this\.active=false\}', source)
    disabled = re.search(r'if\(this\.active\)\{' + re.escape(match[1]) + r'\.board\.buyFeatureButton\.disable\(\)', source)
    if not constructor or not disabled:
        return None, False
    return prefix[:match.start()] + ';' + prefix[body[1]:], True


def _neutral_ante_field(fields, source):
    if not fields or 'ante_bet' not in fields:
        return fields, False
    expression = fields['ante_bet']
    if not re.fullmatch(_REF + r'\.board\.anteBetButton\.isActive\?' + _REF + r'\.model\.getAnteBetCoef\(\):0', expression):
        return None, False
    # Both the button's state source and the purchase disable guard are required.
    state = re.search(r'!!' + _REF + r'\.UI\.model\.get\("ante_bet"\);this\.isActive=' + ID, source)
    guard = re.search(r'if\([^{};]*\.board\.buyFeature\.isNotEnoughBalance\([^{};]*\)\|\|!!' + _REF + r'\.UI\.model\.get\("ante_bet"\)[^{};]*\)\{' + ID + r'\.disable\(\)\}', source)
    if not state or not guard:
        return None, False
    return {**fields, 'ante_bet':'0'}, True


def _assignments(prefix, variable):
    """Every write must be top-level and every object mutation must be known."""
    fields = {}
    count = 0
    for part in _split_top_level(prefix):
        match = re.fullmatch(re.escape(variable) + r'\.(' + ID + r')=(.+)', part)
        if match:
            fields[match[1]] = match[2]
            count += 1
    writes = re.findall(r'(?<![\w$.])' + re.escape(variable) + r'\.(' + ID + r')=(?!=)', prefix)
    if count != len(writes) or re.search(r'(?<![\w$.])' + re.escape(variable) + r'\[|\(\s*' + re.escape(variable) + r'[,)]|delete ' + re.escape(variable), prefix):
        return None
    return fields


def _selector_value(expression, mode):
    if re.fullmatch(ID, expression):
        return True, mode
    if re.fullmatch(ID + r'\.toString\(\)', expression):
        return True, str(mode)
    literal_map = re.fullmatch(r'\{(.+)\}\[(' + ID + r')\]', expression)
    if literal_map:
        entries = {}
        for item in _split_top_level(literal_map[1], ','):
            match = re.fullmatch(r'([0-9]+|"[^"\\]+"):("[^"\\]*"|[0-9]+)', item)
            if not match:
                return False, None
            key = str(json.loads(match[1]))
            if key in entries:
                return False, None
            entries[key] = json.loads(match[2])
        return (True, entries[str(mode)]) if str(mode) in entries else (False, None)
    offset = re.fullmatch(ID + r'\+([0-9]+)', expression)
    if offset and type(mode) is int:
        return True, mode + int(offset[1])
    return False, None


def _compile(fields, middleware, available):
    if not fields or not middleware or not {'bet_per_line', 'lines'}.issubset(fields):
        return None
    if set(fields) - {'bet_per_line', 'lines', 'bet_factor', 'selected_mode', 'buy_spin_type', 'buy_spin_scatters_count', 'paid_feature', 'ante_bet'}:
        return None
    if not re.fullmatch(_REF + r'\.(?:get|getUI)\("bet_per_line"\)', fields['bet_per_line']):
        return None
    line_source = None
    for pattern, source in [(r'\.gameLines\(\)', 'current_lines'),
                            (r'\.settingsLines\(\)\[0\]', 'settings_lines_first'),
                            (r'\.betFactor\(\)\[0\]', 'bet_factor_first'),
                            (r'\.getUI\("lines"\)', 'ui_lines')]:
        if re.fullmatch(_REF + pattern, fields['lines']):
            line_source = source
    if line_source is None:
        return None
    if 'bet_factor' in fields and not re.fullmatch(_REF + r'\.betFactor\(\)\[0\]', fields['bet_factor']):
        return None
    if 'ante_bet' in fields and fields['ante_bet'] != '0':
        return None
    selectors = {k:v for k,v in fields.items() if k not in {'bet_per_line','lines','bet_factor','ante_bet'}}
    if len(selectors) != 1:
        return None
    field, expression = next(iter(selectors.items()))
    modes, values = [], {}
    for mode in available:
        supported, value = _selector_value(expression, mode)
        if supported:
            modes.append(mode)
            values[str(mode)] = {field: value, **({'ante_bet':0} if 'ante_bet' in fields else {})}
    params = list(middleware)
    if field not in params:
        params.append(field)
    if 'ante_bet' in fields:
        params.append('ante_bet')
    return {'purchase_ui_observed': True, 'purchase_ui_modes': modes,
            'purchase_modes': modes, 'purchase_value_sources': {'lines':line_source},
            'purchase_params': {str(mode):params for mode in modes},
            'purchase_mode_values': values, 'purchase_route_evidence':'finite-current-client-fields'} if modes else None


def additional_purchase_inputs(source, data):
    available = (data or {}).get('context',{}).get('available_buy_bonus',[])
    if not isinstance(available,list):
        return None
    available = [v for v in available if type(v) in (int,str)]
    middleware = flow_parameters(source, 'BUY_SPIN')
    contracts = []
    # UI may dispatch from an animation callback or a literal object rather than
    # a method named actBuyFeature. The unchanged flow middleware still applies.
    pattern = r'(' + _REF + r')\.flow\.act\((?:' + _REF + r'\.BUY_SPIN|"buy_spin"),'
    for match in re.finditer(pattern, source):
        owner = match[1]
        preceding = source[max(0,match.start()-2000):match.start()]
        if not owner.endswith('.controllers'):
            alias = re.escape(owner)
            if not re.search(r'null==\(' + alias + '=' + _REF + r'\.controllers\)\|\|$', preceding):
                continue
        neutral = False
        if source[match.end():match.end()+1] == '{':
            group = _group(source, match.end())
            if not group or source[group[1]:group[1]+1] != ')':
                continue
            pairs = [re.fullmatch('(' + ID + r'):(.+)', part) for part in _split_top_level(group[0], ',')]
            if not pairs or any(p is None for p in pairs):
                continue
            fields = {p[1]:p[2] for p in pairs}
            if len(fields) != len(pairs):
                continue
        else:
            argument = re.match('(' + ID + r')\)', source[match.end():])
            if not argument:
                continue
            variable = argument[1]
            declarations = list(re.finditer(r'(?:var|let|const) ' + re.escape(variable) + r'=\{\};', preceding))
            if not declarations:
                continue
            prefix = preceding[declarations[-1].end():]
            prefix = _resolve_branches(prefix, source, data)
            if prefix is not None:
                prefix, neutral = _neutral_toggle(prefix, source, variable)
            fields = _assignments(prefix, variable) if prefix is not None else None
        fields, neutral_field = _neutral_ante_field(fields, source)
        contract = _compile(fields, middleware, available)
        if contract:
            if neutral or neutral_field:
                contract['purchase_ui_defaults'] = {'ante_bet':0}
            contracts.append(contract)
    # Literal lookup serializers in modern clients require the active bus bridge.
    bridge = re.search(r'sendPlayAsync:function\((' + ID + r'),(' + ID + r')\)\{return[^{};]{1,100}\.bus\.play\(\1,\2\)\}', source)
    if bridge:
        for match in re.finditer(r'\.bus\.sendPlayAsync\(\{name:"buy_spin",params:', source):
            group = _group(source, match.end())
            if not group or source[group[1]:group[1]+2] != '},':
                continue
            pairs = [re.fullmatch('(' + ID + r'):(.+)', part) for part in _split_top_level(group[0], ',')]
            if not pairs or any(p is None for p in pairs):
                continue
            fields = {p[1]:p[2] for p in pairs}
            if len(fields) != len(pairs) or 'paid_feature' not in fields:
                continue
            contract = _compile(fields,['bet_per_line','lines'],available)
            if contract:
                contracts.append(contract)
    return contracts[0] if contracts and all(c == contracts[0] for c in contracts) else None
