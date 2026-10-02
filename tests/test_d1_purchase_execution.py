import pytest
from contextlib import nullcontext
from tester_spin.return_to_base import audit_scope
import json
from pathlib import Path
from unittest.mock import patch
from tester_spin.providers.one_spin4win import OneSpin4WinProvider
from tester_spin.models import Game

@pytest.mark.parametrize("audited,malformed", [(False,False),(True,False),(False,True)])
def test_purchase_replays_har_once_then_free_spins_stop_at_settled_state12(tmp_path, audited, malformed):
    provider=OneSpin4WinProvider(tmp_path)
    game=Game(provider='1spin4win',slug='tenluckyspins',name='Ten Lucky Spins',url='https://example.test/?freeplay=true')
    records=json.loads(Path(__file__).with_name('fixtures').joinpath('d1_ten_lucky_purchase.json').read_text())
    received=[x['payload'] for x in records if x['direction']=='received']
    if malformed:
        received[15].pop('b9')
    class WS:
        def __init__(self):
            self.messages=[json.dumps({'type':1,'l':10,'b3':0,'bs':'1,2','b':10000,'st':3})]+[json.dumps(x) for x in received]
            self.sent=[]
        def send(self,data):self.sent.append(data)
        def recv(self):return self.messages.pop(0)
        def close(self):pass
    ws=WS()
    spec={'ws_url':'wss://example.test/games','game_name':'TenLuckySpins','version':'01','wallet':'1','currency':'EUR','origin':'https://example.test','purchase_modes':[{'id':'D1_BUY_FEATURE','kind':'PURCHASE','feature_selector':1,'executable':True,'cost_multiplier':67}]}
    with patch.object(provider,'_discover_runtime_spec',return_value=spec),patch.object(provider,'_open_websocket',return_value=ws),(audit_scope() if audited else nullcontext()):
        result=provider._execute_direct_ws_spin(game,timeout_s=1,attempt_dir=tmp_path,feature_selector=1)
    assert result[0] and result[1] == (not malformed)
    if malformed:
        assert "contadores incompletos" in result[-1]
    plays=[json.loads(x[x.index('{'):]) for x in ws.sent if x.startswith('A/u2') and json.loads(x[x.index('{'):]).get('type')=='1']
    assert plays[0]['data']=='10,0,0,1'
    assert len(plays)==(18 if audited else 16)
    assert all(x['data']=='10,0,0' for x in plays[1:])
    assert len(ws.messages)==(3 if audited else 5) # Five manual paid spins in the HAR must not be consumed as free continuations.
import threading

def test_batch_executes_purchase_and_normal_as_separate_modes(tmp_path):
    provider=OneSpin4WinProvider(tmp_path)
    game=Game(provider='1spin4win',slug='tenluckyspins',name='Ten Lucky Spins',url='https://example.test/?freeplay=true')
    calls=[]
    def execute(game, *,timeout_s,attempt_dir,feature_selector=None):
        calls.append(feature_selector)
        (attempt_dir/'runtime-spec.json').write_text(json.dumps({'game_name':'TenLuckySpins','purchase_modes':[{'id':'D1_BUY_FEATURE','kind':'PURCHASE','feature_selector':1,'executable':True,'validated':False}]}))
        return True,True,10,'wss://example.test',[],''
    with patch.object(provider,'_execute_direct_ws_spin',side_effect=execute):
        result=provider.test_game(game,spins=2,timeout_s=1,stop_event=threading.Event(),progress=lambda text:None)
    assert calls==[None,None,1,1]
    assert [x.mode_kind for x in result.attempts]==['SPIN','SPIN','PURCHASE','PURCHASE']
    assert result.status=='OK'
    assert next(x for x in result.discovered_modes if x['id']=='D1_BUY_FEATURE')['validated'] is True

def test_failed_purchase_cannot_be_hidden_by_successful_normal_spin(tmp_path):
    provider=OneSpin4WinProvider(tmp_path)
    game=Game(provider='1spin4win',slug='tenluckyspins',name='Ten Lucky Spins',url='https://example.test/?freeplay=true')
    def execute(game, *,timeout_s,attempt_dir,feature_selector=None):
        (attempt_dir/'runtime-spec.json').write_text(json.dumps({'game_name':'TenLuckySpins','purchase_modes':[{'id':'D1_BUY_FEATURE','kind':'PURCHASE','feature_selector':1,'executable':True,'validated':False}]}))
        return True,feature_selector is None,10,'wss://example.test',[],'' if feature_selector is None else 'rejected purchase'
    with patch.object(provider,'_execute_direct_ws_spin',side_effect=execute):
        result=provider.test_game(game,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda text:None)
    assert result.status=='PARCIAL'
    assert result.attempts[0].terminal
    assert result.attempts[1].mode_kind=='PURCHASE'
    assert not next(x for x in result.discovered_modes if x['id']=='D1_BUY_FEATURE')['validated']


def test_purchase_success_does_not_validate_unresolved_normal_mode(tmp_path):
    provider=OneSpin4WinProvider(tmp_path)
    game=Game(provider='1spin4win',slug='tenluckyspins',name='Ten Lucky Spins',url='https://example.test/?freeplay=true')
    def execute(game, *,timeout_s,attempt_dir,feature_selector=None):
        (attempt_dir/'runtime-spec.json').write_text(json.dumps({'game_name':'TenLuckySpins','purchase_modes':[{'id':'D1_BUY_FEATURE','kind':'PURCHASE','feature_selector':1,'executable':True,'validated':False}]}))
        return True,feature_selector is not None,10,'wss://example.test',[],'' if feature_selector is not None else 'unresolved normal'
    with patch.object(provider,'_execute_direct_ws_spin',side_effect=execute):
        result=provider.test_game(game,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda text:None)
    assert not next(x for x in result.discovered_modes if x['id']=='SPIN')['spin_validated']
