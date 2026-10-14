import json
from pathlib import Path
from copy import deepcopy
from tester_spin.providers.yggdrasil.runtime import ordinary_round,configuration

ROWS=json.loads(Path('tests/fixtures/yggdrasil_named_actions.json').read_text())
def state(cd):return {'bets':[{'eventdata':{'response':{'clientData':cd}}}]}
def test_observed_named_animation_sequences_are_ordinary_outcomes():
    assert all(ordinary_round(state(cd)) for cd in ROWS if cd.get("actions"))

def test_unknown_or_selection_actions_do_not_prove_base():
    cd=deepcopy(ROWS[0]);cd['actions'].append({'name':'freeSpinChoice','options':[1,2]})
    assert not ordinary_round(state(cd))
    cd=deepcopy(ROWS[0]);cd['actions'][0]['choice']=3
    assert not ordinary_round(state(cd))
    cd=deepcopy(ROWS[0]);cd['freeSpins']={'pending':True}
    assert not ordinary_round(state(cd))
    assert not ordinary_round(state({}))

def test_current_server_buy_and_golden_bet_domains_are_not_title_based():
    modes={'BASIC':{'coinsPerBet':10},'BUY_BONUS_0':{'coinsPerBet':1000},'GOLDEN_BET':{'coinsPerBet':12}}
    data={'gameid':'synthetic','cfg':{'props':[{'prop':'ApiVersion','value':'2.6.0'},{'prop':'Modes','value':modes}]},
          'orgSettings':{'type':'BASIC','Denoms':'EUR:0.01'},
          'extraOrgSettings':[{'type':k,'Denoms':'EUR:0.01'} for k in modes if k!='BASIC']}
    cfg=configuration(data,'synthetic','EUR')
    assert not cfg['unresolved']
    assert cfg['templates']['BUY_BONUS_0']['cmd']=='BUY_BONUS_0'
    assert cfg['templates']['GOLDEN_BET']['amount']=='0.12'


def test_safe_round_artifact_preserves_known_named_outcome(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    runtime=DemoRuntime(None,'synthetic',1,threading.Event(),gate=None)
    value={'wagerid':'local','status':'Finished','terminal':True,'commands':[],
           'bets':[{'step':1,'status':'RESULTED','betdata':{'cmd':'BASE_SPIN'},'eventdata':{'response':{'clientData':ROWS[0]}}}]}
    runtime.save(tmp_path,1,{'amount':'0.1'},value)
    saved=json.loads((tmp_path/'step-001-response.json').read_text())
    assert saved['bets'][0]['clientData']['actions'][0]['name']=='stopReels'
