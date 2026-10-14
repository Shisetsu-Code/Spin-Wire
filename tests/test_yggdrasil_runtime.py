import json
from copy import deepcopy
from pathlib import Path
import pytest

FIXTURES=json.loads(Path(__file__).with_name('fixtures').joinpath('yggdrasil_demo_contracts.json').read_text(encoding='utf-8'))

def test_server_prices_reconstruct_both_bet_formats():
    from tester_spin.providers.yggdrasil.runtime import configuration
    first=configuration(FIXTURES[0]['game'],'10511','EUR')
    second=configuration(FIXTURES[1]['game'],'10945','EUR')
    assert len(first['templates'])==5
    assert first['templates']['BASIC']=={'coin':'0.005','coins':'20','amount':'0.1','lines':'1'*20}
    assert first['templates']['BB_TRAINING']['amount']=='5'
    assert second['templates']['BB_GREEN']=={'coin':'12','coins':'1','amount':'12','cmd':'BB_GREEN'}
    assert len(second['templates'])==6

def test_wager_terminal_requires_settled_bets_and_no_commands():
    from tester_spin.providers.yggdrasil.runtime import wager_state
    pending=FIXTURES[0]['rounds'][0]['response']
    closed=FIXTURES[0]['rounds'][1]['response']
    assert wager_state(pending)['commands']==['C']
    assert not wager_state(pending)['terminal']
    assert wager_state(closed)['terminal']
    malformed=deepcopy(closed);malformed['data']['wager']['bets'][0]['eventdata']={'nextCmds':'UNKNOWN COMMAND'}
    assert not wager_state(malformed)['terminal']
    malformed=deepcopy(closed);malformed['data']['wager']['bets'][0]['status']='PENDING'
    assert not wager_state(malformed)['terminal']

def test_collect_step_uses_last_generated_bet_and_checks_round_identity():
    from tester_spin.providers.yggdrasil.runtime import collect_request, wager_state, validate_transition
    purchase=FIXTURES[0]['rounds'][3]['response']
    state=wager_state(purchase)
    request=collect_request(state)
    assert request=={'cmd':'C','amount':'0','wagerid':'round-3','step':'10','betid':'1'}
    closed=wager_state(FIXTURES[0]['rounds'][4]['response'])
    validate_transition(state,closed,request)
    broken=deepcopy(closed);broken['wagerid']='foreign'
    with pytest.raises(ValueError):validate_transition(state,broken,request)
    broken=deepcopy(closed);broken['max_step']=state['max_step']
    with pytest.raises(ValueError):validate_transition(state,broken,request)

def test_wrong_game_or_unknown_api_cannot_supply_templates():
    from tester_spin.providers.yggdrasil.runtime import configuration
    with pytest.raises(ValueError):configuration(FIXTURES[0]['game'],'999','EUR')
    game=deepcopy(FIXTURES[0]['game']);game['cfg']['props'][0]['value']='unknown'
    with pytest.raises(ValueError):configuration(game,'10511','EUR')

class DemoHTTP:
    def __init__(self, unknown=False, wrong_price=False):
        self.counter=0
        self.pending=None
        self.unknown,self.wrong_price=unknown,wrong_price
    def response(self,value):
        class Response:
            status_code=200
            def json(self):return value
        return Response()
    def get(self,url,params=None,**kw):
        fn=(params or {}).get('fn')
        if fn=='game':
            game=deepcopy(FIXTURES[0]['game'])
            for prop in game['cfg']['props']:
                if prop['prop']=='Modes':
                    prop['value']={'BASIC':{'coinsPerBet':20},'BB_DEATHMATCH_1':{'coinsPerBet':1000}}
                    if self.unknown:prop['value']['SPECIAL_UNKNOWN']={}
            game['orgSettings']['Denoms']='EUR:0.1'
            game['extraOrgSettings']=[{'type':'BB_DEATHMATCH_1','Denoms':'EUR:0.1'}]
            return self.response({'code':0,'data':game})
        if fn=='restore':return self.response({'code':0,'data':{'empty':True}})
        raise AssertionError(fn)
    def post(self,url,params=None,data=None,**kw):
        fn=params['fn']
        if fn=='authenticate':return self.response({'code':0,'data':{'org':'Demo','currency':'EUR','token':'FRESH_TOKEN'}})
        if data.get('cmd')=='C':
            value=deepcopy(FIXTURES[0]['rounds'][6]['response'])
            value['data']['wager']['wagerid']=self.pending
            return self.response(value)
        self.counter+=1
        if data.get('cmd')=='BB_DEATHMATCH_1':
            value=deepcopy(FIXTURES[0]['rounds'][5]['response'])
            self.pending='fresh-'+str(self.counter)
        else:value=deepcopy(FIXTURES[0]['rounds'][2]['response'])
        value['data']['wager']['wagerid']='fresh-'+str(self.counter)
        if self.wrong_price:value['data']['wager']['bets'][0]['betdata']['cashBet']='999'
        return self.response(value)

def test_adapter_executes_current_modes_and_confirms_return(tmp_path):
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    import threading
    p=YggdrasilProvider(tmp_path);p.request_gate=None;p.http=DemoHTTP()
    g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10511')
    (p.game_dir(g)/'game.json').write_text(json.dumps({'symbol':g.symbol,'identifier_source':g.url}))
    result=p.test_game(g,spins=2,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='OK',result.error
    assert result.successful_spins==4 and result.failed_spins==0
    assert len([m for m in result.discovered_modes if m['kind']=='PURCHASE'])==1
    assert all(a.terminal for a in result.attempts)
    p.finalize_test_result(result,progress=lambda _:None)
    assert result.status=='OK',result.error
    contract=p.build_farm_contract(g,result)
    assert contract['ready'],contract['unresolved']
    exported=json.dumps(contract)
    assert 'FRESH_TOKEN' not in exported
    assert all('FRESH_TOKEN' not in file.read_text() for file in Path(result.run_dir).rglob('*.json'))

def test_unknown_server_mode_stays_partial_after_supported_modes_execute(tmp_path):
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    import threading
    p=YggdrasilProvider(tmp_path);p.request_gate=None;p.http=DemoHTTP(unknown=True)
    g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10511')
    (p.game_dir(g)/'game.json').write_text(json.dumps({'symbol':g.symbol,'identifier_source':g.url}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='PARCIAL' and result.successful_spins==2
    assert 'SPECIAL_UNKNOWN' in result.error

def test_wrong_server_price_never_proves_execution(tmp_path):
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    import threading
    runtime=DemoRuntime(DemoHTTP(wrong_price=True),'10511',1,threading.Event(),gate=None)
    config=runtime.bootstrap()
    with pytest.raises(ValueError):runtime.round(config['templates']['BASIC'],tmp_path)


def test_collect_cannot_discard_pending_bets_or_malformed_command_containers():
    from tester_spin.providers.yggdrasil.runtime import collect_request,wager_state
    value=deepcopy(FIXTURES[0]['rounds'][3]['response'])
    value['data']['wager']['bets'][0]['status']='PENDING'
    with pytest.raises(ValueError):collect_request(wager_state(value))
    value=deepcopy(FIXTURES[0]['rounds'][1]['response'])
    value['data']['wager']['bets'][0]['eventdata']=['C']
    with pytest.raises(ValueError):wager_state(value)


def test_action_stream_base_markers_require_normal_mode_not_just_animation_end():
    from tester_spin.providers.yggdrasil.runtime import wager_state,ordinary_round
    value=deepcopy(FIXTURES[0]['rounds'][2]['response'])
    cd={'isFinished':True,'actions':[{'$type':'ActionGame_PresentModeStart','modeName':'BaseGame'},{'$type':'ActionGame_NewSpin'},{'$type':'ActionGame_FeatureHappened','featureIdentifier':'spin'},{'$type':'ActionGame_PresentModeWin'}]}
    value['data']['wager']['bets'][0]['eventdata']['response']['clientData']=cd
    assert ordinary_round(wager_state(value))
    cd['actions'][0]['modeName']='BB_BonusGreen'
    assert not ordinary_round(wager_state(value))
    cd['actions']=[]
    assert not ordinary_round(wager_state(value))
    cd.clear();cd['featuresUsed']=[]
    assert not ordinary_round(wager_state(value))


def test_uncertain_paid_request_stops_without_proving_or_repeating_it(tmp_path):
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    import threading
    class UncertainHTTP(DemoHTTP):
        def post(self,url,params=None,data=None,**kw):
            if params['fn']=='play':raise OSError('connection lost after request')
            return super().post(url,params=params,data=data,**kw)
    p=YggdrasilProvider(tmp_path);p.request_gate=None;p.http=UncertainHTTP()
    g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10511')
    (p.game_dir(g)/'game.json').write_text(json.dumps({'symbol':g.symbol,'identifier_source':g.url}))
    result=p.test_game(g,spins=3,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='ERROR' and result.successful_spins==0
    assert len(result.attempts)==1
    assert not any(m.get('validated') for m in result.discovered_modes)


def test_unknown_continuation_stays_review_required_in_return_proof(tmp_path):
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    import threading
    class UnknownHTTP(DemoHTTP):
        def post(self,url,params=None,data=None,**kw):
            response=super().post(url,params=params,data=data,**kw)
            if params['fn']=='play' and self.counter==2:
                value=response.json();value['data']['wager']['status']='Pending'
                value['data']['wager']['bets'][0]['eventdata']['nextCmds']='UNPROVEN_SELECT'
            return response
    p=YggdrasilProvider(tmp_path);p.request_gate=None;p.http=UnknownHTTP()
    g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10511')
    (p.game_dir(g)/'game.json').write_text(json.dumps({'symbol':g.symbol,'identifier_source':g.url}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='PARCIAL' and result.successful_spins==0
    assert 'REVIEW_REQUIRED' in result.error and 'UNPROVEN_SELECT' in result.error


def test_collect_reply_with_different_paid_price_is_not_a_valid_transition():
    from tester_spin.providers.yggdrasil.runtime import wager_state,collect_request,validate_transition
    before=wager_state(FIXTURES[0]['rounds'][3]['response'])
    after=wager_state(deepcopy(FIXTURES[0]['rounds'][4]['response']))
    after['bets'][0]['betdata']['cashBet']='100000'
    with pytest.raises(ValueError):validate_transition(before,after,collect_request(before))


def test_authoritative_domain_resolves_old_passive_placeholder_without_erasing_history(tmp_path):
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    from tester_spin.coverage_history import retain_pending_branches
    import threading
    p=YggdrasilProvider(tmp_path);p.request_gate=None;p.http=DemoHTTP()
    g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10511')
    folder=p.game_dir(g)
    (folder/'game.json').write_text(json.dumps({'symbol':g.symbol,'identifier_source':g.url}))
    old={'id':'BUY_BONUS_UNRESOLVED','kind':'UNKNOWN_FEATURE','coverage_required':True,'executable':False,'required_options':['DOMAIN_UNRESOLVED'],'covered_options':[],'required_samples':1,'historical_source':'old-run','reason':'PURCHASE_COMMAND_CAPTURE_REQUIRED'}
    (folder/'coverage-history.json').write_text(json.dumps({'schema':'tester-spin/coverage-history/v1','provider':g.provider,'slug':g.slug,'pending':{'BUY_BONUS_UNRESOLVED':old},'policy_migrations':[]}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    retain_pending_branches(folder,result)
    p.finalize_test_result(result,progress=lambda _:None)
    assert result.status=='OK',result.error
    assert json.loads((folder/'coverage-history.json').read_text())['pending']['BUY_BONUS_UNRESOLVED']['historical_source']=='old-run'


def test_return_transport_failure_is_error_not_an_unknown_domain(tmp_path):
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    import threading
    class BrokenReturn(DemoHTTP):
        def post(self,url,params=None,data=None,**kw):
            if params['fn']=='play' and self.counter==1:raise OSError('probe transport failure')
            return super().post(url,params=params,data=data,**kw)
    p=YggdrasilProvider(tmp_path);p.request_gate=None;p.http=BrokenReturn()
    g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10511')
    (p.game_dir(g)/'game.json').write_text(json.dumps({'symbol':g.symbol,'identifier_source':g.url}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='ERROR' and result.successful_spins==0


def test_request_budget_spaces_calls_and_honors_rate_limit_cooldown():
    from tester_spin.providers.yggdrasil.limits import RequestGate
    class Clock:
        now=0.0
        def __call__(self):return self.now
    class Event:
        def is_set(self):return False
        def wait(self,seconds):clock.now+=seconds;return False
    clock=Clock();gate=RequestGate(clock=clock, interval_s=1.0);event=Event()
    gate.acquire(event);gate.acquire(event)
    assert clock.now>=1.0
    gate.cooldown('8')
    gate.acquire(event)
    assert clock.now>=9.0


def test_server_cooldown_longer_than_timeout_does_not_hang_next_game():
    from tester_spin.providers.yggdrasil.limits import RequestGate
    import threading
    clock=lambda:10.0
    gate=RequestGate(clock=clock)
    gate.cooldown('3600')
    with pytest.raises(TimeoutError):gate.acquire(threading.Event(),max_wait_s=25)


def test_demo_runtime_captures_full_unknown_actions(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime
    class UnknownActionsHTTP:
        def post(self,*args,**kwargs):
            return DemoHTTP().response({'code':0,'data':{'actions':[{'NewAction':{'Options':['left','right']}}]}})
    path=tmp_path/'analysis'/'http.har'
    runtime=DemoRuntime(UnknownActionsHTTP(),'10511',1,threading.Event(),gate=None,capture_path=path)
    runtime.call('play',{'amount':'0.1'})
    entry=json.loads(path.read_text())['log']['entries'][0]
    assert json.loads(entry['response']['content']['text'])['data']['actions'][0]['NewAction']['Options']==['left','right']


def test_classic_modes_and_coin_domain_can_prove_contract_without_version_label():
    from tester_spin.providers.yggdrasil.runtime import configuration
    game={'gameid':'synthetic','cfg':{'props':[{'prop':'Modes','value':{'BASIC':{'coinsPerBet':2}}},{'prop':'CoinsPerBet','value':[2]},{'prop':'Paylines','value':[[0,0,0],[1,1,1]]}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.05'}}
    result=configuration(game,'synthetic','EUR')
    assert result['templates']['BASIC']=={'coin':'0.05','coins':'2','amount':'0.1','lines':'11'}
    game['cfg']['props'][1]['value']=[3]
    with pytest.raises(ValueError):configuration(game,'synthetic','EUR')


def typed_game():return json.loads(Path('tests/fixtures/yggdrasil_typed_betting_modes.json').read_text())
def test_typed_betting_modes_supply_command_roles_and_prices():
    from tester_spin.providers.yggdrasil.runtime import configuration
    config=configuration(typed_game(),'12345','EUR')
    assert not config['unresolved']
    assert config['mode_kinds']=={'BASIC':'SPIN','GB':'ANTE_BET','BB_1':'PURCHASE','BB_0':'PURCHASE'}
    assert config['templates']['GB']['cmd']=='GB'
    assert config['templates']['GB']['amount']=='0.15'
@pytest.mark.parametrize('change',['duplicate','wrong_coins','missing','unknown_type'])
def test_typed_declarations_cannot_be_guessed_or_conflict(change):
    from tester_spin.providers.yggdrasil.runtime import configuration
    game=typed_game();typed=game['cfg']['props'][-1]['value']['bettingModes']
    if change=='duplicate':typed.append(deepcopy(typed[1]))
    elif change=='wrong_coins':typed[1]['coinsPerBet']=999
    elif change=='missing':typed.pop(1)
    else:typed[1]['type']='UNLEARNED'
    try:config=configuration(game,'12345','EUR')
    except ValueError:return
    assert 'GB' not in config['templates']
    assert 'GB' in config['unresolved']

def test_server_cooldown_survives_a_new_executor(tmp_path):
    from tester_spin.providers.yggdrasil.limits import RequestGate
    import threading,json
    path=tmp_path/'server-cooldown.json'
    one=RequestGate(clock=lambda:10,wall_clock=lambda:100,cooldown_path=path)
    one.cooldown('3600')
    two=RequestGate(clock=lambda:20,wall_clock=lambda:200,cooldown_path=path)
    with pytest.raises(TimeoutError):two.acquire(threading.Event(),max_wait_s=25)
    assert json.loads(path.read_text())=={'retry_at':3700}

def test_expired_persistent_cooldown_does_not_block(tmp_path):
    from tester_spin.providers.yggdrasil.limits import RequestGate
    import threading
    path=tmp_path/'server-cooldown.json';path.write_text('{"retry_at":100}')
    gate=RequestGate(clock=lambda:10,wall_clock=lambda:101,cooldown_path=path)
    gate.acquire(threading.Event(),max_wait_s=1)

def definition_game(multiplier=1.5,ante_denom='0.15'):
    return {'gameid':'12345','cfg':{'props':[{'prop':'ApiVersion','value':'2.6.0'},{'prop':'Config','value':{'definition':{'bonusBetMultiplier':multiplier}}},{'prop':'Modes','value':{'BASIC':{'coinsPerBet':1},'ANTE_BET':{'coinsPerBet':1}}}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.1'},'extraOrgSettings':[{'type':'ANTE_BET','Denoms':'EUR:'+ante_denom}]}

def test_definition_ante_domain_cross_checks_server_multiplier_and_price():
    from tester_spin.providers.yggdrasil.runtime import configuration
    cfg=configuration(definition_game(),'12345','EUR')
    assert cfg['mode_kinds']['ANTE_BET']=='ANTE_BET' and cfg['templates']['ANTE_BET']['amount']=='0.15'

@pytest.mark.parametrize('multiplier,denom',[(None,'0.15'),(1.5,'0.2'),(0,'0.15')])
def test_definition_ante_does_not_guess_a_missing_or_inconsistent_multiplier(multiplier,denom):
    from tester_spin.providers.yggdrasil.runtime import configuration
    cfg=configuration(definition_game(multiplier,denom),'12345','EUR')
    assert 'ANTE_BET' in cfg['unresolved'] and 'ANTE_BET' not in cfg['templates']

def test_pacing_is_shared_with_another_process_gate(tmp_path):
    from tester_spin.providers.yggdrasil.limits import RequestGate
    import threading
    path=tmp_path/'server-cooldown.json'
    one=RequestGate(clock=lambda:10,wall_clock=lambda:100,cooldown_path=path)
    one.acquire(threading.Event(),max_wait_s=1)
    two=RequestGate(clock=lambda:20,wall_clock=lambda:101,cooldown_path=path)
    with pytest.raises(TimeoutError):two.acquire(threading.Event(),max_wait_s=1)

def _persist_cooldown_in_process(path,delay,start):
    from tester_spin.providers.yggdrasil.limits import RequestGate
    gate=RequestGate(wall_clock=lambda:100,cooldown_path=path)
    start.wait(10)
    for _ in range(10):gate.cooldown(delay)

def test_parallel_process_cooldowns_cannot_shorten_retry_after(tmp_path):
    import multiprocessing as mp,json
    context=mp.get_context('spawn');start=context.Barrier(3)
    path=tmp_path/'cooldown.json'
    workers=[context.Process(target=_persist_cooldown_in_process,args=(path,delay,start)) for delay in ('3600','60')]
    for worker in workers:worker.start()
    start.wait(10)
    for worker in workers:
        worker.join(15)
        assert worker.exitcode==0
    assert json.loads(path.read_text())['retry_at']==3700

def test_provider_pause_is_checked_before_preparation_or_http(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.adapter import YggdrasilProvider
    from tester_spin.models import Game
    from tester_spin.scheduler import run_game_tests
    provider=YggdrasilProvider(tmp_path/'data');provider.request_gate.cooldown('3600')
    prepared=[];results=[];messages=[];stop=threading.Event()
    provider.prepare_test_artifacts=lambda *a,**kw:prepared.append(True)
    game=Game('yggdrasil','fixture-game','Fixture','https://yggdrasilgaming.com/games/fixture-game/',last_status='OK')
    run_game_tests(provider,[game],concurrency=1,spins_per_game=1,delay_between_starts_s=0,timeout_s=25,stop_event=stop,progress=messages.append,on_result=results.append)
    assert stop.is_set() and not prepared and not results and game.last_status=='OK'
    assert any('429' in message for message in messages)


@pytest.mark.parametrize('value',[2,3,True,0,'bad'])
def test_classic_scalar_coin_domain_must_match_basic(value):
    from tester_spin.providers.yggdrasil.runtime import configuration
    game={'gameid':'synthetic','cfg':{'props':[{'prop':'Modes','value':{'BASIC':{'coinsPerBet':2}}},{'prop':'CoinsPerBet','value':value}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.05'}}
    if type(value) is int and value==2:
        assert configuration(game,'synthetic','EUR')['templates']['BASIC']['amount']=='0.1'
    else:
        with pytest.raises(ValueError):configuration(game,'synthetic','EUR')


def test_legacy_line_quantity_is_per_line_and_not_total_coins(tmp_path):
    import threading
    from tester_spin.providers.yggdrasil.runtime import DemoRuntime,validate_start
    root={'step':1,'status':'RESULTED','betamount':'0.20','betcurrency':'EUR','betdata':{'lines':'1'*20,'coin':'0.01','nCoins':1,'cheat':None,'clientData':None},'eventdata':{}}
    template={'coin':'0.01','coins':'20','amount':'0.20','lines':'1'*20}
    validate_start({'bets':[root]},template,classic_line_quantity=True)
    bad=deepcopy(root);bad['betdata']['nCoins']=20
    with pytest.raises(ValueError):validate_start({'bets':[bad]},template,classic_line_quantity=True)
    runtime=DemoRuntime(None,'fixture',1,threading.Event(),gate=None)
    runtime.config={'classic_line_quantity':True}
    sent=[]
    def call(fn,body):
        sent.append(body)
        return {'code':0,'data':{'wager':{'wagerid':'fixture-round','status':'Finished','bets':[root]}}}
    runtime.call=call
    runtime.round(template,tmp_path)
    assert 'coins' not in sent[0]
    assert sent[0]['lines']==template['lines'] and sent[0]['amount']==template['amount']


def test_legacy_line_serializer_requires_geometry_without_coin_domain():
    from tester_spin.providers.yggdrasil.runtime import configuration
    game={'gameid':'synthetic','cfg':{'props':[{'prop':'Modes','value':{'BASIC':{'coinsPerBet':2}}},{'prop':'Paylines','value':[[0,0,0],[1,1,1]]}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.05'}}
    assert configuration(game,'synthetic','EUR')['classic_line_quantity'] is True
    game['cfg']['props'].append({'prop':'CoinsPerBet','value':[2]})
    assert configuration(game,'synthetic','EUR')['classic_line_quantity'] is False

def test_scalar_classic_price_uses_one_coin_per_line():
    from tester_spin.providers.yggdrasil.runtime import configuration
    d=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_classic_scalar_lines.json").read_text(encoding="utf-8"))
    cfg=configuration(d,str(d.get("gameid",d.get("gameId"))),"EUR")
    assert cfg["classic_line_quantity"] is True
    assert cfg["templates"]["BASIC"]["amount"]=="0.2"

def test_api_27_current_modes_keep_same_price_contract():
    from tester_spin.providers.yggdrasil.runtime import configuration,number
    d=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_api_27.json").read_text(encoding="utf-8"))
    cfg=configuration(d,str(d.get("gameid",d.get("gameId"))),"EUR")
    assert cfg["api_version"]=="2.7.0"
    assert not cfg["unresolved"]
    assert set(cfg["modes"])=={"BASIC"}
    t=cfg["templates"]["BASIC"]
    assert number(t["amount"])==number(t["coin"])*number(t["coins"])

def test_unknown_closed_base_response_stops_return_probe_once(tmp_path):
 import threading
 from tester_spin.providers.yggdrasil.runtime import DemoRuntime
 from tester_spin.return_to_base import verify_return_to_base
 class Reply:
  status_code=200
  headers={}
  def __init__(self,value):self.value=value;self.text=json.dumps(value)
  def json(self):return self.value
 class HTTP:
  def __init__(self):self.calls=0
  def post(self,*args,**kwargs):
   self.calls+=1
   bet={'step':1,'betamount':'0.1','betcurrency':'EUR','wonamount':'0','status':'RESULTED','betdata':{'coin':'0.01','cashBet':'0.1','cmd':'BASE_SPIN','accC':0,'accWa':'0'},'eventdata':{'response':{'clientData':{'unlearnedOutput':{}}}}}
   return Reply({'code':0,'data':{'wager':{'wagerid':'fixture-'+str(self.calls),'status':'Finished','bets':[bet]}}})
 http=HTTP();runtime=DemoRuntime(http,'fixture',1,threading.Event(),gate=None,capture_path=tmp_path/'http.har');runtime.config={'ordinary_constraints':{'basic_coin':'0.01','basic_amount':'0.1'}}
 template={'coin':'0.01','coins':'10','amount':'0.1'}
 proof=verify_return_to_base(tmp_path,lambda directory:runtime.round(template,directory),stop_event=threading.Event())
 assert proof['status']=='REVIEW_REQUIRED'
 assert http.calls==1
 assert (tmp_path/'http.har').exists()
 assert proof['probes'][0]['reason']=='UNRECOGNIZED_CLOSED_OUTCOME'
