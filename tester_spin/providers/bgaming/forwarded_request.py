"""Trace a narrowly proven JSON-RPC play wrapper without evaluating client JS."""
import re


def _lexical_source(source):
    clean, code = list(source), list(source)
    i = 0
    while i < len(source):
        if source[i] in {'"', "'", '`'}:
            quote, start = source[i], i
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                    continue
                if source[i] == quote:
                    i += 1
                    break
                i += 1
            code[start:i] = ' ' * (i - start)
        elif source.startswith('//', i) or source.startswith('/*', i):
            start = i
            if source.startswith('//', i):
                end = source.find('\n', i + 2)
                i = len(source) if end < 0 else end
            else:
                end = source.find('*/', i + 2)
                i = len(source) if end < 0 else end + 2
            clean[start:i] = code[start:i] = ' ' * (i - start)
        elif source[i] == '/' and (not source[:i].rstrip()
                or source[:i].rstrip()[-1] in '=(:,![&|?{;'
                or re.search(r'\b(?:return|throw|case)\s*$', source[max(0, i-30):i])):
            # A regex literal may itself contain quotes, slashes and braces.
            # Keep them out of the executable-token mask.
            start, in_class = i, False
            i += 1
            while i < len(source):
                if source[i] == '\\':
                    i += 2
                    continue
                if source[i] == '[':
                    in_class = True
                elif source[i] == ']':
                    in_class = False
                elif source[i] == '/' and not in_class:
                    i += 1
                    while i < len(source) and source[i].isalpha():
                        i += 1
                    break
                i += 1
            code[start:i] = ' ' * (i - start)
        else:
            i += 1
    return ''.join(clean), ''.join(code)


def forwarded_request_contracts(source: str) -> str:
    ident = r"[A-Za-z_$][A-Za-z0-9_$]*"
    text, code = _lexical_source(source or "")
    def unambiguous(name):
        escaped = re.escape(name)
        if (re.search(rf'\([^()]{{0,500}}\b{escaped}\b[^()]{{0,500}}\)\s*(?:=>|\{{)', code)
                or re.search(rf'(?<![\w$.]){escaped}\s*=>', code)
                or re.search(rf'\b(?:let|var|const)\s+{escaped}\s*(?:;|,|\))', code)):
            return False
        definitions = set()
        for assignment in re.finditer(rf'(?<![\w$.]){re.escape(name)}\s*=(?!=|>)', code):
            start = assignment.end()
            header = re.match(r'\s*async\b[^{};]{1,160}=>\s*\{', code[start:])
            if header is None:
                return False
            opening = start + header.end() - 1
            depth, end = 1, opening + 1
            while end < len(code) and depth:
                depth += (code[end] == '{') - (code[end] == '}')
                end += 1
            if depth:
                return False
            definitions.add(text[start:end].strip())
        # Bundle and engine collectors can include the identical source twice.
        # Conflicting assignments, including lexical shadows, remain ambiguous.
        return len(definitions) == 1
    transports = set()
    for match in re.finditer(rf"\b({ident})\s*=\s*async\s*\(\s*({ident})\s*,\s*({ident})\s*\)\s*=>\s*\{{", text):
        name, method, params = match.groups()
        if not code[match.start()].strip() or not unambiguous(name):
            continue
        segment = text[match.end():match.end() + 500]
        # The same arguments must become the method and params of JSON-RPC.
        if (re.search(rf'^(?:return\s+await\s+|var\s+{ident};try\{{const\s+{ident}=await\s+){ident}\.post\(["\']/api["\'],\{{[^{{}}]{{0,300}}jsonrpc:["\']2\.0["\']', segment)
                and re.search(rf'\bmethod:{re.escape(method)}\s*,\s*params:{re.escape(params)}\s*\}}', segment)):
            transports.add(name)
    contracts = []
    for match in re.finditer(rf"\b({ident})\s*=\s*async\s+({ident})\s*=>\s*\{{", text):
        name, arg = match.groups()
        if not code[match.start()].strip() or not unambiguous(name):
            continue
        a = re.escape(arg)
        # Exact identity forwarding: nested parameter, spread and invocation all
        # use the same argument; no request overrides or transformations.
        pattern = (rf'^const\s+({ident})=await\(async\s+{a}=>\{{const\s+({ident})=({ident})\(\);'
                   rf'return\s+await\s+({ident})\(["\']play["\'],\{{token:\2,req:\{{\.\.\.{a}\}}\}}\)\}}\)'
                   rf'\({a}\);return\s+\1\}}')
        forwarded = re.match(pattern, text[match.end():match.end() + 600])
        if not forwarded or forwarded.group(4) not in transports:
            continue
        for call in re.finditer(rf'(?<![\w$.]){re.escape(name)}\(\{{([^{{}}]{{1,1600}})\}}\)', text):
            if not code[call.start()].strip():
                continue
            body = call.group(1)
            if "..." not in body:
                # Optional feature flags serialize a literal only on the true
                # branch; absence is explicitly undefined, never another mode.
                body = re.sub(
                    rf'\bpurchased_feature:!{ident}&&{ident}\.{ident}\?["\']([A-Za-z0-9_]+)["\']:void\s*0',
                    lambda m: 'purchased_feature:"' + m.group(1) + '"', body,
                )
                contracts.append("req:{" + body + "}")
    return "\n".join(contracts)
