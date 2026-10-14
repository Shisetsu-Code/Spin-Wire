import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import wager_state
ROW=json.loads(Path('tests/fixtures/yggdrasil_server_choice.json').read_text())
def state(row):return wager_state({'code':0,'data':{'wager':row}})
def test_csv_command_domain_is_current_server_choice_domain():
    s=state(ROW)
    assert s['commands']==['NON_GAMBLE_9','GAMBLE_9_11','GAMBLE_9_19']
    assert not s['terminal']
def test_non_gamble_selection_is_zero_cost_same_round_next_step():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    assert continuation_request(state(ROW))=={'cmd':'NON_GAMBLE_9','amount':'0','wagerid':'fixture-choice-round','step':'3','betid':'1'}
@pytest.mark.parametrize('commands',[['UNLEARNED'],['NON_GAMBLE_9','UNKNOWN'],['NON_GAMBLE_9','NON_GAMBLE_12']])
def test_unknown_or_ambiguous_selection_is_not_guessed(commands):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    s=state(ROW);s['commands']=commands
    with pytest.raises(ValueError):continuation_request(s)

@pytest.mark.parametrize('field,value',[('betamount','1'),('betcurrency','USD'),('betamount','NaN')])
def test_continuation_ack_must_not_charge_or_change_currency(field,value):
    from tester_spin.providers.yggdrasil.runtime import collect_request,validate_transition
    fixtures=json.loads(Path('tests/fixtures/yggdrasil_demo_contracts.json').read_text())
    before=wager_state(fixtures[0]['rounds'][3]['response']);after=wager_state(fixtures[0]['rounds'][4]['response']);request=collect_request(before)
    ack=next(b for b in after['bets'] if b['step']==int(request['step']));ack[field]=value
    with pytest.raises(ValueError):validate_transition(before,after,request)

def test_mismatched_free_spin_choice_group_is_not_authorized():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    s=state(ROW);s['commands']=['NON_GAMBLE_9','GAMBLE_12_11']
    with pytest.raises(ValueError):continuation_request(s)
def test_selected_free_spins_without_c_are_not_reported_as_collect(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    closed=deepcopy(ROW);closed['status']='Finished';closed['bets']=[{'step':3,'status':'RESULTED','betamount':'0','betcurrency':'EUR','betdata':{'cmd':'NON_GAMBLE_9','coin':'0.01','cashBet':'0.20'},'eventdata':{}}]
    values=iter([ROW,closed])
    class Response:
        status_code=200
        def __init__(self,value):self.value=value
        def json(self):return {'code':0,'data':{'wager':self.value}}
    class HTTP:
        def post(self,*a,**kw):return Response(next(values))
    runtime=DemoRuntime(HTTP(),'fixture',1,threading.Event(),gate=None)
    result=runtime.round({'coin':'0.01','coins':'20','amount':'0.20'},tmp_path)
    assert result['terminal'] and not result['collected']
    assert result['continuation_commands']==['NON_GAMBLE_9']

@pytest.mark.parametrize('commands,exit',[(['GAMBLE_01','GAMBLE_02','NO_GAMBLE','GAMBLE_03'],'NO_GAMBLE'),(['NO_GAMBLE_0','GAMBLE_0'],'NO_GAMBLE_0')])
def test_shared_make_choice_request_exit_variants(commands,exit):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=commands
    request=continuation_request(current)
    assert request['cmd']==exit and request['amount']=='0' and request['step']=='3'

def named_choice_state():
    current=state(ROW);current['commands']=['MYSTERY','TREASURE']
    current['bets'][-1]['eventdata']={'response':{'clientData':{'actions':[{'name':'makeChoice','possibleChoices':['MYSTERY','TREASURE']}]}}}
    return current
def test_shared_make_choice_cross_checks_both_current_domains():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    request=continuation_request(named_choice_state())
    assert request['cmd']=='MYSTERY' and request['amount']=='0'
@pytest.mark.parametrize('change',['different','duplicate','extra_payload','unknown_type'])
def test_named_choice_cannot_invent_options_or_extra_payload(change):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=named_choice_state();action=current['bets'][-1]['eventdata']['response']['clientData']['actions'][0]
    if change=='different':action['possibleChoices']=['MYSTERY','OTHER']
    elif change=='duplicate':action['possibleChoices']=['MYSTERY','MYSTERY','TREASURE']
    elif change=='extra_payload':action['requiredIndex']=1
    else:action['type']='UNLEARNED_PAID_CHOICE'
    with pytest.raises(ValueError):continuation_request(current)

@pytest.mark.parametrize("typed",[True,False])
def test_gamble_only_named_menu_is_not_selected(typed):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=named_choice_state();current["commands"]=["GAMBLE_9_11","GAMBLE_9_19"]
    action=current["bets"][-1]["eventdata"]["response"]["clientData"]["actions"][0]
    action["possibleChoices"]=current["commands"][:]
    if typed:action["type"]="GAMBLE"
    with pytest.raises(ValueError):continuation_request(current)

@pytest.mark.parametrize("mode",["BASIC","GOLDEN_BET"])
def test_current_pick_gamble_forfeit_profile(mode):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=[f'FREE_SPIN_{mode}_3_PICKS',f'GAMBLE_{mode}_LVL_4_POS_0',f'GAMBLE_{mode}_LVL_4_POS_1']
    assert continuation_request(current)['cmd']==current['commands'][0]

def test_pick_forfeit_cannot_cross_mode_domain():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=['FREE_SPIN_BASIC_3_PICKS','GAMBLE_GOLDEN_BET_LVL_4_POS_0']
    with pytest.raises(ValueError):continuation_request(current)

@pytest.mark.parametrize('commands,ok',[(['RG_5','AG_5_6_0','AG_5_12_1'],True),(['RG_5','AG_6_12_1'],False),(['AG_5_6_0'],False)])
def test_refuse_gamble_uses_matching_current_reward(commands,ok):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=commands
    if ok:assert continuation_request(current)['cmd']=='RG_5'
    else:
        with pytest.raises(ValueError):continuation_request(current)

def test_current_egg_gamble_forfeit_preserves_mode_scatter_domain_and_coin():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=['NON_GAMBLE_BASIC_3_SCATTERS','GAMBLE_EGG_0_BASIC_3_SCATTERS','GAMBLE_EGG_1_BASIC_3_SCATTERS']
    req=continuation_request(current)
    assert req['cmd']==current['commands'][0] and req['amount']=='0' and req['coin']=='0.01'

@pytest.mark.parametrize('commands',[['NON_GAMBLE_BASIC_3_SCATTERS','GAMBLE_EGG_0_GOLDEN_3_SCATTERS'],['NON_GAMBLE_BASIC_3_SCATTERS','GAMBLE_EGG_0_BASIC_4_SCATTERS']])
def test_egg_forfeit_cannot_cross_mode_or_scatter_group(commands):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=commands
    with pytest.raises(ValueError):continuation_request(current)

def test_box_choice_is_taken_from_current_offered_commands():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=['PICK_BOX_09','PICK_BOX_21']
    req=continuation_request(current)
    assert req['cmd']=='PICK_BOX_09' and req['amount']=='0'

@pytest.mark.parametrize('commands',[['PICK_BOX_09','GAMBLE'],['PICK_BOX_09','UNKNOWN']])
def test_box_choice_does_not_ignore_unknown_or_gamble_commands(commands):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=commands
    with pytest.raises(ValueError):continuation_request(current)

@pytest.mark.parametrize('commands',[['FREESPIN','GAMBLE'],['FREESPIN']])
def test_leander_free_spin_exit_is_current_zero_cost_bonus_step(commands):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=commands
    request=continuation_request(current)
    assert request['cmd']=='FREESPIN' and request['type']=='bonus' and request['amount']=='0'

def test_free_spin_exit_does_not_hide_another_command():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=['FREESPIN','GAMBLE','UNKNOWN']
    with pytest.raises(ValueError):continuation_request(current)

def test_finished_checkpoint_uses_learned_player_finish_payload():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=['Finished','Checkpoint']
    request=continuation_request(current)
    assert request['cmd']=='Finished' and request['amount']=='0'
    assert json.loads(request['clientParams'])=={'finishedByPlayer':True}

@pytest.mark.parametrize('commands',[['Finished','UNKNOWN'],['Checkpoint']])
def test_finish_does_not_guess_checkpoint_or_unknown_state_payload(commands):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    current=state(ROW);current['commands']=commands
    with pytest.raises(ValueError):continuation_request(current)

def test_finished_then_collect_closes_same_gati_round_and_retains_payload(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    cd=json.loads(Path('tests/fixtures/yggdrasil_outcome_families.json').read_text())['gati_gigagong-gigablox']
    root={'wagerid':'fixture-gati-round','status':'Pending','bets':[{'step':1,'status':'RESULTED','betamount':'0.2','betcurrency':'EUR','betdata':{'cmd':'BASE_SPIN','coin':'0.002','cashBet':'0.2','cmds':['Finished','Checkpoint']},'eventdata':{'nextCmds':'Finished,Checkpoint','response':{'clientData':cd}}}]}
    def following(step,cmd,pending):
        return {'wagerid':'fixture-gati-round','status':'Pending' if pending else 'Finished','bets':[{'step':step,'status':'RESULTED','betamount':'0','betcurrency':'EUR','betdata':{'cmd':cmd,'coin':'0.002','cashBet':'0.2'},'eventdata':{'nextCmds':'C' if pending else None}}]}
    responses=iter([root,following(2,'Finished',True),following(3,'C',False)])
    class Response:
        status_code=200
        def json(self):return {'code':0,'data':{'wager':next(responses)}}
    class HTTP:
        calls=[]
        def post(self,*a,**kw):self.calls.append(kw['data']);return Response()
    http=HTTP();runtime=DemoRuntime(http,'fixture',1,threading.Event(),gate=None)
    result=runtime.round({'coin':'0.002','coins':'100','amount':'0.2'},tmp_path)
    assert result['base'] and result['terminal'] and result['collected']
    assert result['continuation_commands']==['Finished','C']
    req=json.loads((tmp_path/'step-002-request.json').read_text())
    assert json.loads(req['clientParams'])=={'finishedByPlayer':True}
    assert [call.get('amount') for call in http.calls]==['0.2','0','0']
    for step in (1,2):assert 'choices' not in json.loads((tmp_path/f'step-{step:03d}-response.json').read_text())


def test_pick_position_uses_only_current_server_menu_and_next_step():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    s=state(ROW);s['commands']=['PICK_POSITION_12','PICK_POSITION_3']
    request=continuation_request(s)
    assert request['cmd']=='PICK_POSITION_12' and request['amount']=='0' and request['step']=='3' and request['betid']=='1'
    for commands in [['PICK_POSITION_12','GAMBLE'],['PICK_POSITION_12','UNKNOWN']]:
        s['commands']=commands
        with pytest.raises(ValueError):continuation_request(s)


def test_mixed_pick_protocols_are_not_one_known_menu():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    s=state(ROW);s['commands']=['PICK_BOX_01','PICK_POSITION_1']
    with pytest.raises(ValueError):continuation_request(s)


def test_gati_typed_collect_uses_exact_offered_command_and_empty_client_params():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_typed_collect_choice.json').read_text())
    s=state(row);request=continuation_request(s)
    collect=row['bets'][0]['eventdata']['response']['clientData']['Gamble']['Options']['collect']['command']
    assert request['cmd']==collect and request['amount']=='0' and request['clientParams']==''
    assert len(s['commands'])==3 and 'UNSUPPORTED_COMMAND' not in s['commands']
    row['bets'][0]['eventdata']['response']['clientData']['Gamble']['Options']['collect']['command']='OTHER'
    with pytest.raises(ValueError):continuation_request(state(row))


def test_typed_gati_selection_keeps_server_roles_for_reconstruction(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    row=json.loads(Path('tests/fixtures/yggdrasil_typed_collect_choice.json').read_text())
    runtime=DemoRuntime(None,'fixture',1,threading.Event(),gate=None)
    runtime.save(tmp_path,1,{'cmd':'BONUSBUY1','amount':'15'},state(row))
    saved=json.loads((tmp_path/'step-001-response.json').read_text())
    assert saved['gati_choice_options']['Gamble']==row['bets'][0]['eventdata']['response']['clientData']['Gamble']
    assert saved['choices']['selected'] is None


def test_malformed_typed_collect_cannot_fall_back_to_command_names():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_typed_collect_choice.json').read_text())
    root=row['bets'][0];root['betdata']['cmds']=['NON_GAMBLE_9','GAMBLE_9_11'];root['eventdata']['nextCmds']='NON_GAMBLE_9,GAMBLE_9_11'
    options=root['eventdata']['response']['clientData']['Gamble']['Options']
    options['collect']={'command':'GAMBLE_9_11','spins':99}
    options['riskList']=[{'command':'NON_GAMBLE_9','spins':11,'chance':0.5}]
    with pytest.raises(ValueError):continuation_request(state(row))


@pytest.mark.parametrize('damage',['collect_shortcut','neutral_extra'])
def test_typed_gati_role_validation_precedes_all_label_shortcuts(damage):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_typed_collect_choice.json').read_text());root=row['bets'][0]
    gamble=root['eventdata']['response']['clientData']['Gamble']
    if damage=='collect_shortcut':
        root['betdata']['cmds']=['C'];root['eventdata']['nextCmds']='C'
        gamble['Options']['collect']['command']='OTHER'
        gamble['Options']['riskList']=[{'command':'C','spins':12,'chance':0.5}]
    else:
        root['betdata']['cmds']=['NON_GAMBLE_9','GAMBLE_9_11'];root['eventdata']['nextCmds']='NON_GAMBLE_9,GAMBLE_9_11'
        root['eventdata']['response']['clientData']['Gamble']={'Options':{'collect':{},'riskList':[]},'unknown':True}
    with pytest.raises(ValueError):continuation_request(state(row))


def test_typed_collect_role_must_agree_with_learned_gati_wire_action():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_typed_collect_choice.json').read_text())
    options=row['bets'][0]['eventdata']['response']['clientData']['Gamble']['Options']
    options['collect']['command'],options['riskList'][0]['command']=options['riskList'][0]['command'],options['collect']['command']
    with pytest.raises(ValueError):continuation_request(state(row))


def test_side_gamble_menu_refuses_target_level_without_risk_request():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    s=state(ROW);s['commands']=['NO_GAMBLE_6','GAMBLE_7_LEFT','GAMBLE_7_RIGHT']
    request=continuation_request(s)
    assert request['cmd']=='NO_GAMBLE_6' and request['amount']=='0' and request['step']=='3'
    s['commands']=['NO_GAMBLE_6','GAMBLE_8_LEFT','GAMBLE_8_RIGHT']
    with pytest.raises(ValueError):continuation_request(s)


def test_current_awarded_spin_count_can_refuse_next_plus_two_target():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    s=state(ROW);s['commands']=['NO_GAMBLE_8','GAMBLE_10']
    s['bets'][-1]['eventdata']={'response':{'clientData':{'clientDatas':[{'freeSpinsAwarded':8,'freeSpinsWon':True}]}}}
    assert continuation_request(s)['cmd']=='NO_GAMBLE_8'
    s['bets'][-1]['eventdata']['response']['clientData']['clientDatas'][0]['freeSpinsAwarded']=6
    with pytest.raises(ValueError):continuation_request(s)


def test_enum_bonus_pick_uses_current_server_index_command_only():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_enum_bonus_choice.json').read_text())
    request=continuation_request(state(row))
    assert request['cmd']==':1' and request['amount']=='0' and request['step']=='2' and request['betid']=='1'
    row['bets'][0]['eventdata']['response']['clientData']['NextRound']['BGData']['Type']=7
    with pytest.raises(ValueError):continuation_request(state(row))


def test_enum_bonus_choice_rejects_unknown_control_mode():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_enum_bonus_choice.json').read_text())
    row['bets'][0]['eventdata']['response']['clientData']['NextRound']['GameMode']=999
    with pytest.raises(ValueError):continuation_request(state(row))


def test_historical_offers_do_not_reopen_a_finished_wager():
    row=deepcopy(ROW);row['status']='Finished'
    row['bets'][0]['betdata']['cmds']=['NO_GAMBLE_8','GAMBLE_10']
    row['bets'][0]['eventdata']['nextCmds']='NO_GAMBLE_8,GAMBLE_10'
    row['bets'][-1]['betdata']['cmds']=[]
    row['bets'][-1]['eventdata']['nextCmds']=''
    s=state(row)
    assert s['terminal'] and s['commands']==[]

def test_current_collect_ignores_earlier_resolved_menu():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=deepcopy(ROW)
    row['bets'][0]['betdata']['cmds']=['NO_GAMBLE_8','GAMBLE_10']
    row['bets'][0]['eventdata']['nextCmds']='NO_GAMBLE_8,GAMBLE_10'
    row['bets'][-1]['betdata']['cmds']=['C']
    row['bets'][-1]['eventdata']['nextCmds']='C'
    assert continuation_request(state(row))['cmd']=='C'


def test_auto_generated_steps_cannot_add_unrequested_charges():
    from tester_spin.providers.yggdrasil.runtime import validate_start,collect_request,validate_transition
    row=deepcopy(ROW);row['bets'][-1]['betamount']='1.00'
    with pytest.raises(ValueError):validate_start(state(row),{'coin':'0.01','coins':'20','amount':'0.20'})
    fixtures=json.loads(Path('tests/fixtures/yggdrasil_demo_contracts.json').read_text())
    before=wager_state(fixtures[0]['rounds'][3]['response']);after=wager_state(fixtures[0]['rounds'][4]['response']);request=collect_request(before)
    extra=deepcopy(after['bets'][-1]);extra['step']=after['max_step']+1;extra['betamount']='1.00'
    after['bets'].append(extra);after['max_step']=extra['step']
    with pytest.raises(ValueError):validate_transition(before,after,request)


def test_classic_wildcard_is_not_an_executable_choice_and_c_is_collect():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_classic_wildcard_collect.json').read_text())
    current=state(row)
    assert current['commands']==['C','*']
    request=continuation_request(current)
    assert request['cmd']=='C' and request['amount']=='0' and request['step']==str(current['max_step']+1)
    for domain in ['*','*,C','C,UNKNOWN']:
        bad=deepcopy(row);bad['bets'][-1]['eventdata']['nextCmds']=domain
        with pytest.raises(ValueError):continuation_request(state(bad))
    bad=deepcopy(row);bad['bets'][0]['betdata']={}
    with pytest.raises(ValueError):continuation_request(state(bad))


@pytest.mark.parametrize('filename,command',[('yggdrasil_prefixed_gamble_menu.json','NG_2_0_0_L_1'),('yggdrasil_awarded_spin_menu.json','FREE_SPINS_7_0')])
def test_sdk_offered_non_risk_selection_uses_same_round_zero_cost(filename,command):
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures',filename).read_text())
    current=state(row);request=continuation_request(current)
    assert request['cmd']==command and request['amount']=='0'
    assert request['step']==str(current['max_step']+1) and request['betid']=='1'


def test_refusal_cannot_cross_gamble_domain_or_award_quantities():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_prefixed_gamble_menu.json').read_text())
    row['bets'][-1]['eventdata']['nextCmds']='NG_2_0_0_L_1,G_3_0_0_L_1'
    with pytest.raises(ValueError):continuation_request(state(row))
    row=json.loads(Path('tests/fixtures/yggdrasil_awarded_spin_menu.json').read_text())
    row['bets'][-1]['eventdata']['response']['clientData']['gambleTriggerFrontEndData']['currentFreeSpinsToAward']=8
    with pytest.raises(ValueError):continuation_request(state(row))


def test_refusal_menu_accepts_initial_level_zero_but_not_negative_level():
    from tester_spin.providers.yggdrasil.runtime import continuation_request
    row=json.loads(Path('tests/fixtures/yggdrasil_prefixed_gamble_menu.json').read_text())
    row['bets'][-1]['eventdata']['response']['clientData']['gambleLevel']=0
    assert continuation_request(state(row))['cmd'].startswith('NG_')
    row['bets'][-1]['eventdata']['response']['clientData']['gambleLevel']=-1
    with pytest.raises(ValueError):continuation_request(state(row))
