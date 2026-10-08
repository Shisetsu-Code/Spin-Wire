from pathlib import Path
import json,copy,pytest
from tester_spin.providers.three_oaks.client_contracts import client_contract
from tester_spin.providers.three_oaks.runtime import play_fields,continuation_fields,base_terminal,discover_modes
ROOT=Path(__file__).parent/'fixtures'
RUNNER=(ROOT/'three_oaks_shared_runner.js').read_text()+';Object.assign(e.action.params,{ante_bet:this.model.get("ante_bet")});'
INIT='window._PROVIDER.game={name:"unseen",use:["protocol"]};'

@pytest.mark.parametrize('label,count,purchases',[('override',58,4),('scatters',122,3),('named',21,0)])
def test_captured_requests_replay_with_only_client_proven_primitives(label,count,purchases):
    steps=json.loads((ROOT/f'three_oaks_{label}_capture.json').read_text())
    filename=f'three_oaks_{label}_inputs.js' if label!='named' else 'three_oaks_named_flow.js'
    source=(ROOT/filename).read_text();initial=steps[0]
    d={'context':copy.deepcopy(initial['context']),'settings':initial['settings']}
    profile=client_contract(source,data=d,runner_source=RUNNER,init_source=INIT)
    modes=discover_modes(d,'goreel',True,client_profile=profile)
    assert len([m for m in modes if m['kind']=='ANTE_BET'])==(1 if label=='scatters' else 0)
    total=0;buys=[];ante=[]
    for step in steps:
        action=step['action']
        if not action:
            d={'context':copy.deepcopy(step['context']),'settings':step['settings']};continue
        name=action['name'];params=action['params']
        if name in ('spin','buy_spin'):
            d['context'].setdefault('spins',{}).update({k:v for k,v in params.items() if k in ['bet_per_line','lines']})
            selector=None
            if name=='buy_spin':
                selector=next(m for m in profile['purchase_modes'] if all(params.get(k)==v for k,v in profile['purchase_wire_values'][str(m)].items()))
                buys.append(selector)
            if params.get('ante_bet'):ante.append(params['ante_bet'])
            actual=play_fields(d,name,selector,client_profile=profile,antebet=params.get('ante_bet') if name=='spin' else None)
        else:
            actual=continuation_fields(d,game_slug='unseen',family='goreel',client_profile=profile)
        assert actual and actual['action']==action,(label,total,action,actual)
        total+=1;d={'context':copy.deepcopy(step['context']),'settings':step['settings']}
    assert total==count
    assert len(buys)==purchases
    assert base_terminal(d)
    if label=='scatters':assert ante==[1.25]*8
