"""Small read-only JavaScript input primitives, independent of titles and builds."""
import ast
import warnings
import json
import re
import math

ID = r'[A-Za-z_$][\w$]*'
_TOKEN = re.compile(r'/\*.*?\*/|//[^\r\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`|[A-Za-z_$][\w$]*|[0-9]+(?:\.[0-9]+)?|[^\s]', re.S)
_REGEX = re.compile(r'/(?:\\.|\[(?:\\.|[^\]\\])*\]|[^/\\\r\n])+/[dgimsuvy]*')


def canonical_source(source):
    pieces = []
    previous = ''
    index = 0
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        match = None
        if source[index] == '/' and not source.startswith(('//', '/*'), index) and previous in ('=', '(', '[', ',', ':', '!', '?', 'return', 'case', ';', '|', '&'):
            match = _REGEX.match(source, index)
        match = match or _TOKEN.match(source, index)
        if match is None:
            return ''
        token = match[0]
        index = match.end()
        if token.startswith(('/*', '//')):
            continue
        if token.startswith("'"):
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', SyntaxWarning)
                    token = json.dumps(ast.literal_eval(token), ensure_ascii=False)
            except (SyntaxError, ValueError):
                pass
        if previous and (previous[-1].isalnum() or previous[-1] in '_$') and (token[0].isalnum() or token[0] in '_$'):
            pieces.append(' ')
        pieces.append(token)
        previous = token
    # Static bracket properties are the same input primitive as dot properties.
    normalized = []
    index = 0
    while index < len(pieces):
        if pieces[index] == '[' and normalized and index+2 < len(pieces) and pieces[index+2] == ']' and (re.fullmatch(ID, normalized[-1]) or normalized[-1] in (']',')')):
            try:
                name = json.loads(pieces[index+1])
            except (ValueError, TypeError):
                name = None
            if isinstance(name,str) and re.fullmatch(ID,name):
                normalized.extend(('.',name))
                index += 3
                continue
        normalized.append(pieces[index])
        index += 1
    return _normalize_action_aliases(normalized)



def _normalize_action_aliases(tokens):
    """Resolve only module-scope literal action declarations, not arbitrary names.

    The replacement is token-based and only touches a dispatch argument. Strings,
    comments, function-local bindings, mutations and conditional assignments are
    not reinterpreted as a proven action constant.
    """
    compact = [t for t in tokens if t != ' ']
    source = ''.join(tokens)
    allowed = {'spin', 'buy_spin', 'respin', 'bonus_init', 'freespin_init',
               'freespin', 'freespin_stop', 'collect_win'}
    aliases = {}
    stack, declaration = [], False
    pairs = {')':'(', ']':'[', '}':'{'}
    for index, token in enumerate(compact):
        if not stack and token in ('var','let','const'):
            declaration = True
        if not stack and declaration and re.fullmatch(ID,token) and index > 0 and compact[index-1] in ('var','let','const',','):
            if index+2 < len(compact) and compact[index+1] == '=':
                try:
                    value = json.loads(compact[index+2])
                except ValueError:
                    value = None
                if isinstance(value,str) and value in allowed:
                    aliases[token] = value
        if token in ('(', '[', '{'):
            stack.append(token)
        elif token in pairs:
            if not stack or stack.pop() != pairs[token]:
                return source
        elif not stack and token == ';':
            declaration = False
    # A second assignment anywhere makes this limited static proof ambiguous.
    for alias in list(aliases):
        assigns = sum(t == alias and i+1 < len(compact) and compact[i+1] == '='
                      and (i == 0 or compact[i-1] != '.')
                      and (i+2 == len(compact) or compact[i+2] not in ('=', '>'))
                      for i,t in enumerate(compact))
        if assigns != 1:
            del aliases[alias]
    if not aliases:
        return source
    calls = {'setActionHandler', 'act', 'actIfPossible', '_act', 'canAction'}
    for index in range(3, len(tokens)):
        if tokens[index] in aliases and tokens[index-3] == '.' and tokens[index-2] in calls and tokens[index-1] == '(':
            tokens[index] = json.dumps(aliases[tokens[index]])
    return ''.join(tokens)


def block(source, opening):
    depth, index, quote = 1, opening + 1, None
    while index < min(len(source), opening + 8000):
        char = source[index]
        if quote:
            if char == '\\':
                index += 2
                continue
            if char == quote:
                quote = None
        elif char in '\"\'`':
            quote = char
        elif char == '{':
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                return source[opening+1:index]
        index += 1
    return None


def _js_tokens(source):
    """Token spans used only for bounded, read-only syntax decomposition."""
    previous, index = '', 0
    while index < len(source):
        if source[index].isspace():
            index += 1
            continue
        match = None
        if source[index] == '/' and not source.startswith(('//', '/*'), index) and previous in ('=', '(', '[', ',', ':', '!', '?', 'return', 'case', ';', '|', '&'):
            match = _REGEX.match(source, index)
        match = match or _TOKEN.match(source, index)
        if match is None:
            return
        start, index, token = index, match.end(), match[0]
        if not token.startswith(('//', '/*')):
            yield start, index, token
            previous = token


def _split_top_level(source, separators=';,'):
    stack, start, parts = [], 0, []
    pairs = {')': '(', ']': '[', '}': '{'}
    for left, right, token in _js_tokens(source):
        if token in ('(', '[', '{'):
            stack.append(token)
        elif token in pairs:
            if not stack or stack.pop() != pairs[token]:
                return []
        elif not stack and token in separators:
            parts.append(source[start:left])
            start = right
    return [] if stack else parts + [source[start:]]


def _group(source, opening, limit=12000):
    """Return a balanced group and its end, or refuse truncated/unknown syntax."""
    stack, pairs = [], {')': '(', ']': '[', '}': '{'}
    for left, right, token in _js_tokens(source[opening:opening + limit]):
        if token in ('(', '[', '{'):
            stack.append(token)
        elif token in pairs:
            if not stack or stack.pop() != pairs[token]:
                return None
            if not stack:
                return source[opening + 1:opening + left], opening + right
    return None


def _flow_body(body, argument):
    # Expression-arrow parentheses and comma operators are parsed, not globally
    # replaced: commas inside calls, arrays and objects retain their meaning.
    while body.startswith('('):
        group = _group(body, 0)
        if group is None or group[1] != len(body):
            break
        body = group[0]
    init = '(' + argument + '=' + argument + '||{}).'
    if body.startswith(init):
        body = argument + '=' + argument + '||{};' + argument + '.' + body[len(init):]
    return ';'.join(_split_top_level(body)) + ';'


def _flow_transport(source):
    if 'params:args||{}' in source and 'EventsGame.play(action)' in source:
        return True
    # Compact class method; the parameters and event payload must be the same
    # bound identifiers. A similarly named method alone is not proof.
    pattern = (r'_act\((' + ID + r'),(' + ID + r'),(' + ID + r')=null\)\{'
               r'(?:let|const|var) (' + ID + r')=\{action:\{name:\1,params:\2\|\|\{\}\},bet:\3\};'
               r'return ' + ID + r'(?:\.' + ID + r')*\.EventsGame\.play\(\4\),this\.deferred\.promise\}')
    return bool(re.search(pattern, source))


def _module_flow_override(source):
    candidates = list(re.finditer(r'Object\.assign\((' + ID + r')\.prototype,\{initDefaultMiddleware\(\)\{', source))
    if not candidates:
        return None
    proven = []
    candidate_positions = {match.start(): match for match in candidates}
    stack, last_boundary = [], 0
    pairs = {')': '(', ']': '[', '}': '{'}
    for left, right, token in _js_tokens(source):
        if left in candidate_positions:
            match = candidate_positions[left]
            if not stack and not source[last_boundary:left].strip():
                declaration = re.search(r'class ' + re.escape(match[1]) + r' extends ' + ID + r'\{static get abbreviatedName\(\)\{return"flow"\}', source[:left])
                if declaration:
                    opening = source.index('{', declaration.start())
                    body = _group(source, opening)
                    patch_opening = source.index('{', match.start())
                    patch = _group(source, patch_opening)
                    if body and patch and body[1] < left and 'initDefaultMiddleware()' in body[0] and '_act(' in body[0]:
                        proven.append(patch[0])
        if token in ('(', '[', '{'):
            stack.append(token)
        elif token in pairs:
            if not stack or stack.pop() != pairs[token]:
                return None
        elif not stack and token in (';', ','):
            last_boundary = right
    return proven[0] if len(candidates) == len(proven) == 1 else None


def _active_flow_source(source):
    """Resolve a prototype replacement only when an entry imports its module.

    Merely finding a later handler is insufficient: Browserify includes unused
    modules too. Conditional or indirect imports stay unresolved here.
    """
    esm = _module_flow_override(source)
    if esm is not None:
        return esm
    patches = list(re.finditer(r'Object\.assign\((' + ID + r')\.(FlowController|default)\.prototype,\{(?=initDefaultMiddleware:)', source))
    entries = re.search(r'\},\{\},\[([0-9]+(?:,[0-9]+)*)\]\);?$', source)
    if len(patches) != 1 or not entries:
        return source
    patch = patches[0]
    headers = list(re.finditer(r'(?:^|[,{])([0-9]+):\[function\(require,module,exports\)\{', source[:patch.start()]))
    if not headers:
        return source
    header = headers[-1]
    module = _group(source, header.end() - 1)
    if module is None or not (header.end() <= patch.start() < module[1]):
        return source
    alias = re.escape(patch[1])
    namespace_import = patch[2] == 'FlowController' and re.search(r'(?:var|let|const) ' + alias + r'=require\("[^"\\]*core/controllers"\)', module[0])
    default_import = patch[2] == 'default' and re.search(r'(?:var|let|const) ' + alias + r'=(' + ID + r')\(require\("[^"\\]*core/controllers/FlowController"\)\)', module[0])
    if default_import:
        helper = default_import[1]
        default_import = re.search(r'function ' + re.escape(helper) + r'\((' + ID + r')\)\{return \1&&\1\.__esModule\?\1:\{default:\1\}\}', module[0])
    if not (namespace_import or default_import):
        return source
    patch_body = _group(source, patch.end() - 1)
    if patch_body is None or not re.search(r'initDefaultMiddleware:(?:function(?: '+ID+r')?\(\))\{', patch_body[0]):
        return source
    for entry in entries[1].split(','):
        start = re.search(r'(?:^|[,{])' + re.escape(entry) + r':\[function\(require,module,exports\)\{', source)
        if not start:
            continue
        body = _group(source, start.end() - 1)
        if body is None or source[body[1]:body[1]+2] != ',{':
            continue
        dependencies = _group(source, body[1]+1)
        if dependencies is None:
            continue
        try:
            mapping = json.loads('{' + dependencies[0] + '}')
        except ValueError:
            continue
        imports = [re.fullmatch(r'require\("([^"\\]+)"\)', part)
                   for part in _split_top_level(body[0], ';')]
        if any(match and str(mapping.get(match[1])) == header[1] for match in imports):
            return patch_body[0]
    return source


def action_handlers(source, symbol):
    pattern = r'\.setActionHandler\((' + ID + r'(?:\.' + ID + r')*\.' + symbol + r'|"' + symbol.lower() + r'"),'
    result = []
    for match in re.finditer(pattern, source):
        opening = source.index('(', match.start())
        call = _group(source, opening)
        if call is None:
            continue
        callback = source[match.end():call[1]-1]
        signature = re.match(r'(?:function\((' + ID + r')\)|\(?(' + ID + r')\)?=>)', callback)
        if not signature:
            continue
        argument = signature[1] or signature[2]
        body = callback[signature.end():]
        if body.startswith('{'):
            contents = _group(body, 0)
            if contents is None or contents[1] != len(body):
                continue
            body = contents[0]
        result.append((match[1], argument, _flow_body(body, argument)))
    return result


def handler_count(source, symbol):
    return len(re.findall(r'\.setActionHandler\((?:' + ID + r'(?:\.' + ID + r')*\.' + symbol + r'|"' + symbol.lower() + r'"),', source))


def flow_parameters(source, symbol):
    active = _active_flow_source(source)
    handlers = action_handlers(active, symbol)
    if not handlers or len(handlers) != handler_count(active, symbol) or not _flow_transport(source):
        return None
    signatures = []
    getters = {'bet_per_line':'betPerLine', 'lines':'gameLines', 'bet_factor':'betFactor'}
    for action, argument, body in handlers:
        assigned = re.findall(re.escape(argument)+r'\.('+ID+r')=(?!=)', body)
        if set(assigned) not in ({'bet_per_line','lines'}, {'bet_per_line','lines','bet_factor'}) or len(assigned) != len(set(assigned)):
            return None
        for field in assigned:
            expression = re.escape(argument)+r'\.'+field+r'="'+field+r'"in '+re.escape(argument)+r'\?'+re.escape(argument)+r'\.'+field+r':'+ID+r'(?:\.'+ID+r')*\.'+getters[field]+r'\(\)'+(r'\[0\]' if field=='bet_factor' else '')+r';'
            if not re.search(expression, body):
                return None
        if not re.search(r'\._act\('+re.escape(action)+','+re.escape(argument)+r'(?:,|\))', body):
            return None
        if re.search(re.escape(argument)+r'\[|Object\.assign\('+re.escape(argument)+r'|delete '+re.escape(argument), body):
            return None
        signatures.append([k for k in getters if k in assigned])
    return signatures[0] if all(value == signatures[0] for value in signatures) else None


def empty_flow_actions(source):
    if not _flow_transport(source):
        return {}
    active = _active_flow_source(source)
    default_dispatch = bool(re.search(r'handlers\[action\]\|\|(?:function\(args\)\{return '+ID+r'\._act\(action,args\)\}|\(?args\)?=>this\._act\(action,args\))', source))
    default_dispatch = default_dispatch or bool(re.search(r'handlers\[(' + ID + r')\]\|\|\((' + ID + r')=>this\._act\(\1,\2\)\)', source))
    rules = {}
    states = {'BONUS_INIT':('bonus_init','spins'), 'RESPIN':('respin','bonus'),
              'FREESPIN_INIT':('freespin_init','spins'), 'FREESPIN':('freespin','freespins'),
              'FREESPIN_STOP':('freespin_stop','freespins'), 'COLLECT_WIN':('collect_win','spins')}
    for symbol, (name, current) in states.items():
        if not re.search(r'\.(?:act|actIfPossible)\((?:'+ID+r'(?:\.'+ID+r')*\.'+symbol+r'|"'+name+r'")\)',source):
            continue
        handlers = action_handlers(active, symbol)
        if len(handlers) == handler_count(active, symbol) and (handlers or default_dispatch) and all(not re.search(r'(?<![\w$.])'+re.escape(arg)+r'(?:\s*=|\.|\[)', body)
               and re.search(r'\._act\('+re.escape(action)+','+re.escape(arg)+r'\)',body)
               for action,arg,body in handlers):
            rules[name]={'current':current, 'state_independent':True}
    # Games can override the dynamic getter with the literal bonus_stop.
    # Require the actual override, call site, and default empty-argument bridge.
    literal_stop = (re.search(r'Object\.defineProperty\(_constants\.FLOW_ACTIONS,"BONUS_STOP",\{get:function get\(\)\{return"bonus_stop"\}\}\)', source)
                    and '.controllers.flow.act(_constants.FLOW_ACTIONS.BONUS_STOP)' in source)
    if literal_stop and default_dispatch and not handler_count(active,'BONUS_STOP'):
        rules['bonus_stop'] = {'current':'bonus'}
    # Preserve the dynamic branch only when a literal override is absent.
    elif ('.bonusOriginState()' in source and '.BONUS_STOP)' in source
            and default_dispatch and not handler_count(active,'BONUS_STOP')):
        for origin in ('spins','freespins'):
            rules['bonus_'+origin+'_stop']={'current':'bonus','back_to':origin}
            if 'this._get("game.bonus.back_to","spins")' in source:
                rules['bonus_'+origin+'_stop']['back_to_default']='spins'
    return rules


def event_spin_parameters(source):
    pattern = r'\.Events\.flow\.play\(\{action:\{name:"spin",params:\{bet_per_line:'+ID+r'(?:\.'+ID+r')*\.betPerLine,lines:'+ID+r'(?:\.'+ID+r')*\.serverData\.settings\.lines\[0\]\}\},bet:'+ID+r'(?:\.'+ID+r')*\.bet\}\)'
    return ['bet_per_line','lines'] if re.search(pattern,source) else None


def _price_keyed_purchase_mode_values(source, data, modes, selector):
    """Prove UI enum -> wire selector mapping from the active client's JS.

    The clicked button sends the numeric enum, whereas its displayed cost
    is read from settings.buy_bonus_prices.[enum + 1]. This is NOT a
    provider-wide convention and must be demonstrated by the client.
    """
    if not re.fullmatch(ID, selector or '') or not isinstance(modes, list):
        return None
    enum = re.search(r'\bBuyFeatureType=exports\.BuyFeatureType=\{([^{}]{1,500})\}', source)
    if not enum:
        return None
    parts = enum[1].split(',')
    if not parts or any(not re.fullmatch(r'[A-Za-z_$][\w$]*:[0-9]+', part) for part in parts):
        return None
    indices = [int(part.rsplit(':', 1)[1]) for part in parts]
    if len(set(indices)) != len(indices):
        return None
    price_getter = re.search(
        r'\.getBuyFeatureCostByType=function\(('+ID+r')\)\{.{0,500}?'
        r'return this\._get\("settings\.buy_bonus_prices\."\.concat\(\1\+1\),null\)',
        source,
    )
    if not price_getter:
        return None
    settings = (data or {}).get('settings', {})
    if not isinstance(settings, dict) or settings.get('buy_bonus_price'):
        return None
    prices = settings.get('buy_bonus_prices')
    if not isinstance(prices, dict) or not prices or not modes:
        return None
    allowed = {index + 1: index for index in indices}
    if any(type(mode) is not int or mode not in allowed
           or not isinstance(prices.get(str(mode)), (int, float))
           or isinstance(prices[str(mode)], bool) or not math.isfinite(prices[str(mode)])
           or prices[str(mode)] <= 0 for mode in modes):
        return None
    return {str(mode): {'selected_mode': allowed[mode]} for mode in modes}


def flow_purchase_inputs(source, data):
    """Compose UI assignments with a certified flow middleware, never vendor defaults."""
    available = (data or {}).get('context', {}).get('available_buy_bonus', [])
    if not isinstance(available, list):
        available = []
    middleware = flow_parameters(source, 'BUY_SPIN')
    declarations = []
    for match in re.finditer(r'actBuyFeature\(([^)]*)\)\{', source):
        body = block(source, match.end()-1)
        if not body:
            continue
        sent = re.search(r'\.controllers\.flow\.act\((?:'+ID+r'(?:\.'+ID+r')*\.BUY_SPIN|"buy_spin"),('+ID+r')\)',body)
        if not sent:
            continue
        variable = sent[1]
        prefix = body[:sent.start()]
        assignments = []
        for part in _split_top_level(prefix):
            assignment = re.fullmatch(re.escape(variable)+r'\.('+ID+r')=(.+)', part)
            if assignment:
                assignments.append(assignment.groups())
        # Do not ignore assignments hidden in branches or nested mutations.
        writes = re.findall(r'(?<![\w$.])' + re.escape(variable) + r'\.(' + ID + r')=(?!=)', prefix)
        if len(writes) != len(assignments):
            continue
        fields = dict(assignments)
        if len(fields) != len(assignments) or not {'bet_per_line','lines'}.issubset(fields) or set(fields)-{'bet_per_line','lines','bet_factor','selected_mode'}:
            continue
        if not re.fullmatch(ID+r'(?:\.'+ID+r')*\.get\("bet_per_line"\)',fields['bet_per_line']):
            continue
        lines = fields['lines']
        if re.fullmatch(ID+r'(?:\.'+ID+r')*\.gameLines\(\)',lines):
            line_source = 'current_lines'
        elif re.fullmatch(ID+r'(?:\.'+ID+r')*\.settingsLines\(\)\[0\]',lines):
            line_source = 'settings_lines_first'
        elif re.fullmatch(ID+r'(?:\.'+ID+r')*\.betFactor\(\)\[0\]',lines):
            line_source = 'bet_factor_first'
        else:
            continue
        if 'bet_factor' in fields and not re.fullmatch(ID+r'(?:\.'+ID+r')*\.betFactor\(\)\[0\]', fields['bet_factor']):
            continue
        selector = fields.get('selected_mode')
        selector_type = None
        if selector is None:
            modes = available if len(available)==1 else []
        elif re.fullmatch(ID+r'\.toString\(\)',selector):
            selector_type, modes = 'string', available
        elif re.fullmatch(ID,selector) and selector in match[1].split(','):
            selector_type, modes = 'preserve', available
        elif re.fullmatch(ID+r'(?:\.'+ID+r')*\.isNewModel\(\)\?('+ID+r'):\1\.toString\(\)',selector):
            mapping = 'isNewModel=function(){return this._get("settings.buy_bonus_prices.1",null)>0}'
            if mapping not in source:
                continue
            price = (data or {}).get('settings',{}).get('buy_bonus_prices',{}).get('1')
            selector_type = 'preserve' if isinstance(price,(int,float)) and price>0 else 'string'
            modes = available
        else:
            continue
        params = list(middleware or [])
        if selector is not None:
            params.append('selected_mode')
        row = {'purchase_ui_observed':True, 'purchase_modes':modes if middleware else [],
               'purchase_selector_type':selector_type,
               'purchase_params':{str(mode):params for mode in modes} if middleware else {},
               'purchase_value_sources':{'lines':line_source}}
        if middleware and selector_type == 'preserve':
            # Price keys and wire selectors differ on explicitly indexed
            # clients. Unknown enum/price domains must fail closed.
            indexed_getter = ('settings.buy_bonus_prices.' in source
                              and '.concat(' in source and '.getBuyFeatureCostByType=function(' in source)
            if indexed_getter:
                mapped = _price_keyed_purchase_mode_values(source, data, modes, selector)
                if mapped is None:
                    row['purchase_modes'] = []
                    row['purchase_params'] = {}
                else:
                    row['purchase_mode_values'] = mapped
        declarations.append(row)
    return declarations[0] if declarations and all(row==declarations[0] for row in declarations) else None


def runner_spin_contract(runner_source, init_source):
    """Certify the active shared spin button independently of unused client middleware."""
    source = canonical_source(runner_source)
    init = canonical_source(init_source)
    declaration = re.search(r'window\._PROVIDER\.game=\{name:"[^"\\]+",use:\[([^\]]*)\]', init)
    if not declaration:
        return None
    uses = re.findall(r'"([^"\\]+)"', declaration[1])
    if 'protocol' not in uses or any(value.split('|')[0] == 'custom_play' for value in uses):
        return None
    normal = r'action:\{name:"spin",params:\{bet_per_line:this\.model\.get\("bet_per_line"\),lines:this\.model\.get\("lines"\)\}\},bet:this\.model\.get\("bet"\)'
    if not re.search(normal, source) or '.onGamePlay({data:' not in source or '._getPlayParams()}' not in source:
        return None
    forwarding = r'\.use\.custom_play\|\|'+ID+r'(?:\.'+ID+r')*\.flow\.play\.on\(function\(('+ID+r')\)\{return '+ID+r'(?:\.'+ID+r')*\.game\.play\(\1\.data\)\}\)'
    if not re.search(forwarding, source):
        return None
    return {'spin_params':['bet_per_line','lines'], 'spin_route':'shared-runner-button',
            'evidence':'Current init enables protocol without custom_play; current GameRunner button forwards bet_per_line/lines directly'}
