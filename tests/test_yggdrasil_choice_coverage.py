import json
from copy import deepcopy
from pathlib import Path
import pytest
from tester_spin.models import GameTestResult,SpinAttempt
from tester_spin.providers.path_coverage import build_path_coverage_report
SCOPE="server_paid_domain_with_resolved_zero_cost_controls/v1"
PROTO="yggdrasil-current-zero-cost-menu/v1"

def setup_result(root):
    directory=root/'BUY_A_BONUS'/'sample-001';directory.mkdir(parents=True)
    result=GameTestResult(provider='yggdrasil',slug='synthetic',game_name='Synthetic',game_url='https://example.invalid',requested_spins=1,successful_spins=1,failed_spins=0,status='OK',run_dir=str(root))
    result.feature_domains={'purchase':{'complete':True},'ante':{'complete':True}}
    result.discovered_modes=[{'id':'BUY_A_BONUS','kind':'PURCHASE','validated':True,'execution_state':'PROVEN_TERMINAL','evidence_level':'REMOTE_EXECUTION','coverage_scope':SCOPE,'required_options':['BUY_A_BONUS'],'covered_options':['BUY_A_BONUS']}]
    result.attempts=[SpinAttempt(number=1,ok=True,terminal=True,mode_id='BUY_A_BONUS',artifact_dir=str(directory))]
    domain=['NON_GAMBLE_3','GAMBLE_3_1']
    initial={'round_ref':'round-1','bets':[{'step':1}], 'choices':{'available':domain,'selected':None,'protocol':PROTO}}
    selected={'round_ref':'round-1','bets':[{'step':1},{'step':2,'command':'NON_GAMBLE_3'}],'transition_validated':True,'choices':{'available':domain,'selected':'NON_GAMBLE_3','protocol':PROTO}}
    for name,payload in [('step-001-response.json',initial),('step-002-response.json',selected),('step-002-request.json',{'cmd':'NON_GAMBLE_3','amount':'0','step':'2'}),('return-to-base.json',{'status':'CONFIRMED','required':2,'consecutive_base':2})]:
        (directory/name).write_text(json.dumps(payload))
    return result,directory

def test_resolved_zero_cost_menu_does_not_require_every_gamble_alternative(tmp_path):
    result,_=setup_result(tmp_path)
    assert build_path_coverage_report(result)['complete']

@pytest.mark.parametrize('damage',['no_ack','foreign_round','charged','unproven','wrong_domain','no_return','foreign_provider','unknown_protocol'])
def test_unresolved_or_unproven_menu_remains_pending(tmp_path,damage):
    result,directory=setup_result(tmp_path)
    path=directory/'step-002-response.json';reply=json.loads(path.read_text())
    if damage=='no_ack':reply['transition_validated']=False
    elif damage=='foreign_round':reply['round_ref']='round-2'
    elif damage=='charged':(directory/'step-002-request.json').write_text(json.dumps({'cmd':'NON_GAMBLE_3','amount':'1','step':'2'}))
    elif damage=='unproven':result.attempts[0].terminal=False
    elif damage=='wrong_domain':reply['choices']['available']=['OTHER']
    elif damage=='no_return':(directory/'return-to-base.json').unlink()
    elif damage=='foreign_provider':result.provider='synthetic'
    elif damage=='unknown_protocol':reply['choices']['protocol']='unknown'
    path.write_text(json.dumps(reply))
    assert not build_path_coverage_report(result)['complete']
