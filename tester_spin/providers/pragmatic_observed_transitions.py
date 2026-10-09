"""Bounded transition families demonstrated by official-client demo HARs.

Evidence: 2026-10-02T23-06-58-694Z (vswayslions automatic FS respin),
2026-10-02T23-10-29-934Z (vs20wildparty bg_0 choice, doBonus ind=1).
Unknown signatures retain the existing contract validation and review path.
"""
import hashlib
import re
import json
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def game_rules():
    rules=json.loads(Path(__file__).with_name('pragmatic_game_rules.json').read_text(encoding='utf-8'))
    if rules.get('schema')!='pragmatic/observed-game-rules/v1':raise ValueError('Unsupported game rule schema')
    return rules


def observed_spin_fields(symbol):
    # Official client Olympus selection, HAR 2026-10-03T01-33-18-693Z.
    # l=15 is the wire line count; doInit l=10 remains the stake scale.
    rules=game_rules()
    entry=rules['games'].get(symbol)
    if not entry:return {}
    profile=rules['profiles'][entry['profile']]
    if profile['kind']!='spin_fields':return {}
    fields=profile['fields']
    if not profile.get('evidence') or set(fields)-{'l','ind'} or any(not re.fullmatch(r'0|[1-9][0-9]{0,3}',v) for v in fields.values()):
        raise ValueError('Invalid observed spin rule')
    return dict(fields)


def game_profile(symbol):
    rules=game_rules();entry=rules['games'].get(symbol)
    return rules['profiles'][entry['profile']] if entry else {}


def apply_spin_rule(fields,symbol):
    profile=game_profile(symbol)
    if profile.get('kind')=='scratchcard':
        if fields.get('action')=='doSpin':fields.update(profile['fields'])
        else:fields.pop('tickets',None)
    else:fields.update(observed_spin_fields(symbol))
    for key in profile.get('omit_fields',[]):fields.pop(key,None)


def observed_next_action(response,symbol):
    rule=game_profile(symbol).get('terminal')
    if rule and response.get(rule['key'])==rule['value'] and not any(response.get(k) for k in ('fs','fsmax','rs','rs_c')):
        if game_profile(symbol).get('kind')!='scratchcard' or all(response.get(k,'0')=='0' for k in ('t_left','fs_left')):return 's'
    if response.get('na'):return str(response['na'])
    return ''


def observed_continuation(response,symbol):
    return game_profile(symbol).get('continuations',{}).get(response.get('na'))


def observed_bonus_rule(response, symbol, override=None):
    if symbol == 'vswaysbbhas':
        group = _bonus_group(response)
        if group is None:
            return None
        family, state = group
        if (family != 'bg' or set(state) != {'bgid','bgt','end','level','lifes','rw'}
                or any(state.get(k) != v for k,v in {'bgid':'0','bgt':'69','end':'0'}.items())
                or (state['level'],state['lifes']) not in {('0','3'),('1','2'),('2','1')}
                or not re.fullmatch(r'[0-9]+\.[0-9]{2}', state['rw'])):
            return None
        if override is not None and str(override) != '0':
            raise ValueError('Observed hold-spinner continuation requires ind=0')
        evidence = 'Official demo HAR vswaysbbhas 2026-10-06 04-33-41: purchase pur=1, eight doBonus(ind=0), na=cb then doCollectBonus -> na=s'
        return {'fields':{'ind':'0'}, 'domain':['0'], 'selected':'0', 'default':None,
                'branch_signature':'PRAGMATIC:observed-continuation:vswaysbbhas:bgt=69:ind=0',
                'domain_basis':'Official client continuation; no selectable menu is advertised',
                'contract_source':evidence, 'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
                'selection_policy':'observed_continuation'}
    profile = game_profile(symbol)
    if profile.get('kind') != 'bonus_fields':
        return None
    if any(response.get(key) not in values for key, values in profile['match'].items()):
        return None
    fields = profile['fields']
    if set(fields) != {'ind'} or not re.fullmatch(r'0|[1-9][0-9]{0,3}', fields['ind']) or not profile.get('evidence'):
        raise ValueError('Invalid observed bonus rule')
    selected = fields['ind']
    if override is not None and str(override) != selected:
        raise ValueError('Observed continuation has no alternative selector')
    evidence = profile['evidence']
    return {'fields':dict(fields), 'domain':[selected], 'selected':selected, 'default':None,
            'branch_signature':f'PRAGMATIC:observed-continuation:{symbol}:bgt={response["bgt"]}:ind={selected}',
            'domain_basis':'Observed continuation selector, not an inferred menu choice domain',
            'contract_source':evidence, 'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
            'selection_policy':'observed_continuation'}


def automatic_fs_respin(response):
    three_respins = response.get('rs_m')=='3' and bool(re.fullmatch(r'\{reg:\{[^{}]*\},top:\{[^{}]*\}\}',str(response.get('g',''))))
    dynamic_cascade = (response.get('rs_more')=='1'
        and all(re.fullmatch(r'0|[1-9][0-9]{0,3}',str(response.get(k,''))) for k in ('rs_m','rs_c','rs_p'))
        and int(response['rs_m'])==int(response['rs_c'])==int(response['rs_p'])+1)
    if (response.get('na') != 's' or response.get('rs') != 'mc'
            or 'rs_t' in response or not re.fullmatch(r'0|[1-9][0-9]*', str(response.get('rs_p','')))
            or (response.get('rs_m') != '1' and not three_respins and not dynamic_cascade)
            or any('sr~' in str(value) for value in response.values())):
        return False
    if not re.fullmatch(r'(?:[0-9]+|[1-9][0-9]{0,2}(?:,[0-9]{3})+)(?:\.[0-9]+)?',str(response.get('tmb_win',''))): return False
    if not re.fullmatch(r'[1-9][0-9]*',str(response.get('rs_c',''))): return False
    if 'fs' not in response and 'fsmax' not in response: return True
    values = [str(response.get(key, '')) for key in ('fs','fsmax')]
    return all(re.fullmatch(r'[1-9][0-9]*', v) for v in values) and int(values[0]) <= int(values[1])


def _bonus_group(response):
    raw = str(response.get('g', ''))
    if response.get('na') != 'b' or len(raw) > 4096:
        return None
    match = re.fullmatch(r'\s*\{([A-Za-z_][A-Za-z_0-9]*):\{([^{}]*)\}\}\s*', raw)
    if not match:
        pieces=re.findall(r'([A-Za-z_][A-Za-z_0-9]*):\{([^{}]*)\}',raw)
        if not pieces or raw!='{'+','.join(name+':{'+body+'}' for name,body in pieces)+'}':return None
        groups=[_bonus_group({'na':'b','g':'{'+name+':{'+body+'}}'}) for name,body in pieces]
        if any(group is None for group in groups):return None
        bonuses=[group for group in groups if 'bgt' in group[1] and group[1].get('end')=='0']
        if len(bonuses)!=1:return None
        if any(group[1].get('end') not in {'0','1'} for group in groups if 'bgt' in group[1]):return None
        screens=[group[1] for group in groups if 'bgt' not in group[1]]
        screen_keys={'s','sa','sb','sh','st','sw'}
        for screen in screens:
            if screen_keys<=set(screen)<=screen_keys|{'reel_set','mo','mo_t'} and screen['st']=='rect':continue
            if set(screen)<={'mo','mo_t'}:continue
            # Reward overlays accompany a menu but contribute no action domain.
            if (set(screen)=={'mo_tv','mo_tw','mo_wpos'}
                    and all(re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',screen[k]) for k in ('mo_tv','mo_tw'))
                    and re.fullmatch(r'[0-9]+(?:,[0-9]+)*',screen['mo_wpos'])):continue
            return None
        return bonuses[0]
    family=match[1]
    chunks = match[2].split('",')
    pairs=[]
    for index, chunk in enumerate(chunks):
        if index < len(chunks)-1: chunk += '"'
        item=re.fullmatch(r'\s*([a-z_][a-z_0-9]*):"([^"\\]*)"\s*',chunk)
        if not item: return None
        pairs.append(item.groups())
    fields=dict(pairs)
    if len(fields)!=len(pairs):return None
    return family,fields


def bonus_choice(response, override=None):
    group=_bonus_group(response)
    if group is None:return None
    family,fields=group
    if ';' in fields.get('ch_k',''):
        return _segmented_bonus_choice(family, fields, override)
    expected={'ask','bgid','bgt','ch_k','ch_v','end','rw'}
    optional={'level','lifes','rw_c','trail','ch_h','reel_set','s','sa','sb','sh','st','sw','mo','mo_t'}
    if not expected<=set(fields) or set(fields)-expected-optional:
        return None
    if any(fields[key] != value for key,value in {'ask':'0','bgt':'69','end':'0'}.items()) or not re.fullmatch(r'0|[1-9][0-9]{0,3}',fields['bgid']):
        return None
    if not re.fullmatch(r'0(?:\.0+)?',fields['rw']): return None
    values=fields['ch_v'].split(',');labels=fields['ch_k'].split(',')
    if (not 1 <= len(values) <= 128 or len(values) != len(labels)
            or any(not re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)?',v) for v in values)
            or any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z_0-9-]{0,63}',v) for v in labels)):
        return None
    if 'ch_h' in fields:
        history=fields['ch_h'].split(',')
        if any(not re.fullmatch(r'0~(?:0|[1-9][0-9]{0,3})',v) or int(v[2:])>=len(labels) for v in history):return None
    if family=='f':
        if fields.get('level')!='0' or fields.get('lifes')!='1' or any(not re.fullmatch(r'fm|f[1-9][0-9]*',v) for v in labels):return None
        domain=list(map(str,range(len(labels))))
        evidence='HAR:vsways5lionsr:f:bgt=69:option-index->doBonus(ind):2026-10-02T23-40-19-976Z'
        basis='Official demo client sends the zero-based option index; ch_v contains reward values'
    else:
        if any(k in fields and not re.fullmatch(r'0|[1-9][0-9]*',fields[k]) for k in ('level','lifes','rw_c')):return None
        domain=list(map(str,range(len(labels))))
        evidence='HAR:vswaysdh1000:2026-10-03T01-25-11-735Z+network-event;vs20mammoth:bg_1:2026-10-03T02-18-28-001Z+network-event:option-index->doBonus(ind)'
        basis='Official client sends the option position; ch_v describes rewards (Dog House values 7,7 map to indices 0,1)'
    selected=domain[0] if override is None else str(override)
    if selected not in domain: raise ValueError('Bonus choice is outside the server domain')
    return {'fields':{'ind':selected},'domain':domain,'selected':selected,'default':None,
            'branch_signature':'PRAGMATIC:bonus-choice:bgt=69:choices='+','.join(domain)+':family='+family+':labels='+','.join(labels),
            'domain_basis':basis,
            'contract_source':evidence,'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
            'selection_policy':'first_available_test_choice' if override is None else 'explicit_override'}


def _segmented_bonus_choice(family, fields, override):
    # Official Kraken 2 HAR: ask selects a menu, ind selects within that menu.
    required={'ask','bgid','bgt','ch_k','ch_v','end','rw'}
    optional={'level','lifes','trail','rw_c','ch_h','status','wins','wins_mask','wi'}
    if not required<=set(fields) or set(fields)-required-optional:
        return None
    if any(fields[k]!=v for k,v in {'bgt':'69','end':'0','rw':'0.00'}.items()):return None
    if any(not re.fullmatch(r'0|[1-9][0-9]*',fields[k]) for k in ('bgid','ask')):return None
    if any(k in fields and not re.fullmatch(r'0|[1-9][0-9]*',fields[k]) for k in ('level','lifes','rw_c')):return None
    labels=[row.split(',') for row in fields['ch_k'].split(';')]
    values=[row.split(',') for row in fields['ch_v'].split(';')]
    if not 2<=len(labels)<=16 or len(labels)!=len(values):return None
    for row,numbers in zip(labels,values):
        if not 1<=len(row)<=128 or len(row)!=len(numbers):return None
        if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z_0-9-]{0,63}',v) for v in row):return None
        if any(not re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)?',v) for v in numbers):return None
    if int(fields['ask'])>=len(labels):return None
    ask=int(fields['ask']);domain=list(map(str,range(len(labels[ask]))))
    if 'ch_h' in fields:
        for pair in fields['ch_h'].split(','):
            match=re.fullmatch(r'([0-9]+)~([0-9]+)',pair)
            if not match or int(match[1])>=len(labels) or int(match[2])>=len(labels[int(match[1])]):return None
    if all(v.isdecimal() for v in labels[ask]):
        # Numeric hidden menus are currently evidenced only for this exact table.
        if (family!='bg_0' or ask!=2 or labels != [['fs','deal_or_not'],['deal','not_deal'],list(map(str,range(16))),['swap','not_swap']]
                or values != [['0','1'],['0','1'],['0']*16,['0','1']]):return None
        status=fields.get('status','').split(',')
        if len(status)!=16 or any(v not in {'0','1'} for v in status):return None
        domain=[str(i) for i,v in enumerate(status) if v=='0']
    if not domain:return None
    selected=domain[0] if override is None else str(override)
    if selected not in domain:raise ValueError('Bonus choice is outside the active menu domain')
    evidence='HAR:vs20kraken2:2026-10-03T02-42-33-219Z+HTTP-tab31:ask-table->doBonus(ind), no ask request field'
    return {'fields':{'ind':selected},'domain':domain,'selected':selected,'default':None,
            'branch_signature':f'PRAGMATIC:bonus-choice:bgt=69:family={family}:ask={ask}:labels='+','.join(labels[ask]),
            'domain_basis':'Official menu table indexed by ask; positions within active table, hidden cells exclude positive status',
            'contract_source':evidence,'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
            'selection_policy':'first_available_test_choice' if override is None else 'explicit_override'}


def bonus_transition(response, override=None):
    choice=bonus_choice(response,override=override)
    if choice is not None:return choice
    group=_bonus_group(response)
    if group is None:return None
    family,fields=group
    wheel_keys={'bgid','bgt','end','rw','whms','whnwi','whsc','whvs','whws'}
    if wheel_keys<=set(fields) and not set(fields)-wheel_keys-{'rw_c','level','lifes','whs'}:
        if fields['bgt']!='69' or fields['end']!='0':return None
        if not all(re.fullmatch(r'0|[1-9][0-9]*',fields[k]) for k in ('bgid','whsc')):return None
        if not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',fields['rw']):return None
        masks=[row.split(',') for row in fields['whms'].split(';')]
        values=[row.split(',') for row in fields['whvs'].split(';')]
        weights=[row.split(',') for row in fields['whws'].split(';')]
        if not 1<=len(masks)<=16 or len(values)!=len(masks) or len(weights)!=len(masks):return None
        for labels,numbers,chances in zip(masks,values,weights):
            if not 1<=len(labels)<=128 or len(numbers)!=len(labels) or len(chances)!=len(labels):return None
            if any(not re.fullmatch(r'[a-z0-9][a-z_0-9]{0,31}',v) for v in labels):return None
            if any(not re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)?',v) for v in numbers):return None
            if any(not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',v) for v in chances):return None
        active=fields['whnwi'].split(',')
        if any(not re.fullmatch(r'0|[1-9][0-9]*',v) or int(v)>=len(masks) for v in active):return None
        if override is not None:raise ValueError('Automatic wheel has no selectable index')
        evidence='HAR:vs20bison:wheel:bgt=69->doBonus(no-ind):2026-10-03T01-20-13-076Z'
        return {'fields':{},'domain':[],'selected':None,'default':None,
            'branch_signature':f'PRAGMATIC:automatic-wheel:{family}:bgt=69',
            'domain_basis':'Server supplies wheel outcomes; official client requests the next wheel without ind',
            'contract_source':evidence,'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
            'selection_policy':'observed_automatic_continuation'}
    minimal={'bgid':'0','bgt':'69','end':'0','rw':'0.00'}
    if family in {'bg_0','bg','pc','pl','flat'} and fields in (minimal,{**minimal,'rw_c':'0'}):
        if override is not None and str(override)!='0':raise ValueError('Observed continuation requires ind=0')
        evidence='HAR:vs10bbsplxmas:bg_0:minimal->doBonus(ind=0):2026-10-03T00-43-39-528Z'
        if 'rw_c' in fields:
            evidence='HAR:vs20wraanu:bg_0:rw_c=0:COLLECT->doBonus(ind=0):2026-10-03T03-46-33-123Z; collect path only'
        return {'fields':{'ind':'0'},'domain':['0'],'selected':'0','default':None,
            'branch_signature':f'PRAGMATIC:bonus-continuation:{family}:bgt=69:minimal',
            'domain_basis':'Official demo client sends ind=0 for this exact continuation state',
            'contract_source':evidence,'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
            'selection_policy':'observed_continuation'}
    required={'ask','bgid','bgt','ch_k','ch_v','end','level','lifes','rw','status','wins','wins_mask'}
    if family!='bg_0' or not required<=set(fields) or set(fields)-required-{'ch_h','wi'}:return None
    if any(fields[k]!=v for k,v in {'ask':'0','bgid':'0','bgt':'69','end':'0','lifes':'1'}.items()):return None
    if not re.fullmatch(r'0(?:\.0+)?',fields['rw']):return None
    labels=fields['ch_k'].split(',');values=fields['ch_v'].split(',')
    statuses=fields['status'].split(',');wins=fields['wins'].split(',');masks=fields['wins_mask'].split(',')
    size=len(labels)
    if not 1<=size<=128 or any(len(v)!=size for v in [values,statuses,wins,masks]):return None
    indices=list(map(str,range(size)))
    if labels!=indices or values!=indices:return None
    if any(not re.fullmatch(r'0|[1-9][0-9]*',v) for v in statuses+[fields['level']]):return None
    if any(not re.fullmatch(r'[0-9]+(?:\.[0-9]+)?',v) for v in wins):return None
    if any(v not in {'h','s','l','f','w','m','be'} for v in masks):return None
    level=int(fields['level']);numbers=list(map(int,statuses))
    if level>=size:return None
    # Official client pre-reveals the bonus enhancer (be) before player picks.
    # It disables all positive-status cells; be is not part of ch_h history.
    player_statuses=[v for v,mask in zip(numbers,masks) if mask!='be' and v]
    if sorted(player_statuses)!=list(range(1,level+1)):return None
    if any(mask=='be' and (status!=1 or float(win)!=0) for mask,status,win in zip(masks,numbers,wins)):return None
    if any((status==0)!=(mask=='h') for status,mask in zip(numbers,masks)):return None
    if level:
        history=fields.get('ch_h','').split(',')
        if len(history)!=level or any(not re.fullmatch(r'0~(?:0|[1-9][0-9]*)',v) for v in history):return None
        picked=[int(v[2:]) for v in history]
        if len(set(picked))!=level or any(i>=size or masks[i]=='be' or numbers[i]!=n+1 for n,i in enumerate(picked)):return None
        if fields.get('wi')!=str(picked[-1]):return None
    elif 'ch_h' in fields:return None
    elif 'wi' in fields:
        if not re.fullmatch(r'0|[1-9][0-9]*',fields['wi']):return None
        initial=int(fields['wi'])
        if initial>=size or masks[initial]!='be':return None
    domain=[str(i) for i,status in enumerate(numbers) if status==0]
    if not domain:return None
    selected=domain[0] if override is None else str(override)
    if selected not in domain:raise ValueError('Bonus grid position is already revealed or outside the server domain')
    evidence='HAR:vs10bbextreme:bg_0:bgt=69:status->doBonus(ind):2026-10-03T00-31-17-027Z'
    return {'fields':{'ind':selected},'domain':domain,'selected':selected,'default':None,
        'branch_signature':f'PRAGMATIC:bonus-grid:bgt=69:level={level}:status='+','.join(statuses),
        'coverage_branch_signature':f'PRAGMATIC:bonus-grid:bg_0:bgt=69:size={size}:level={level}',
        'coverage_policy':'hidden-position-structural/v1',
        'domain_basis':'Official client selects a zero-based hidden position; selected positions have positive status and cannot be repeated',
        'contract_source':evidence,'contract_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
        'selection_policy':'first_available_test_choice' if override is None else 'explicit_override'}
