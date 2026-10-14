from types import SimpleNamespace
from tester_spin.providers.one_spin4win_purchases import discover_purchase_modes, apply_purchase_coverage

SOURCE = 'var TenLuckySpinsView=function(){this.buyFeatureMult=67;this.useBuyFeature=!0;};'

def test_declared_purchase_is_found_in_matching_game_constructor():
    modes = discover_purchase_modes([SOURCE], 'TenLuckySpins')
    assert len(modes) == 1
    assert modes[0]['kind'] == 'PURCHASE'
    assert modes[0]['cost_multiplier'] == 67
    assert modes[0]['coverage_required'] is True
    assert modes[0]['executable'] is False

def test_shared_buy_ui_or_another_game_does_not_create_purchase():
    assert discover_purchase_modes([SOURCE], 'OtherGame') == []
    assert discover_purchase_modes(['if(Game.game.useBuyFeature){showBuyFeature()}'], 'TenLuckySpins') == []
    assert discover_purchase_modes([SOURCE.replace('!0','!1')], 'TenLuckySpins') == []

def test_base_ok_is_partial_when_purchase_has_not_been_validated():
    result = SimpleNamespace(status='OK', error='', discovered_modes=[{'id':'SPIN'}])
    apply_purchase_coverage(result, discover_purchase_modes([SOURCE,SOURCE], 'TenLuckySpins'))
    assert result.status == 'PARCIAL'
    assert len(result.discovered_modes) == 2
    assert 'compra' in result.error.lower()

def test_purchase_coverage_preserves_transport_errors():
    result = SimpleNamespace(status='ERROR', error='connection failed', discovered_modes=[])
    apply_purchase_coverage(result, discover_purchase_modes([SOURCE], 'TenLuckySpins'))
    assert result.status == 'ERROR'
    assert result.error == 'connection failed'
import json
import threading
from unittest.mock import patch
from tester_spin.models import Game
from tester_spin.providers.one_spin4win import OneSpin4WinProvider

def test_real_provider_downgrades_successful_base_with_purchase(tmp_path):
    provider = OneSpin4WinProvider(tmp_path)
    game = Game(provider='1spin4win', slug='tenluckyspins', name='Ten Lucky Spins', url='https://example.test/?freeplay=true')
    def execute(game, *, timeout_s, attempt_dir):
        (attempt_dir/'runtime-spec.json').write_text(json.dumps({'game_name':'TenLuckySpins', 'purchase_modes':discover_purchase_modes([SOURCE], 'TenLuckySpins')}))
        return True, True, 10.0, 'wss://example.test/games', [], ''
    with patch.object(provider, '_execute_direct_ws_spin', side_effect=execute):
        result = provider.test_game(game, spins=1, timeout_s=1, stop_event=threading.Event(), progress=lambda text:None)
    assert result.successful_spins == 1
    assert result.status == 'PARCIAL'
    assert any(mode['kind']=='PURCHASE' for mode in result.discovered_modes)
def test_server_can_disable_purchase_in_current_session():
    from tester_spin.providers.one_spin4win_purchases import purchase_modes_for_init
    modes = discover_purchase_modes([SOURCE], 'TenLuckySpins')
    assert purchase_modes_for_init(modes, {'type':1,'bf':'f'}) == []
    assert purchase_modes_for_init(modes, {'type':1}) == modes


def test_generic_catalog_launcher_loads_specific_game_client_before_buy_discovery(tmp_path):
    provider = OneSpin4WinProvider(tmp_path)
    url='https://gs.1spin4win.com:10443/gmh5/games.html?game=TenLuckySpins&currency=EUR&config=1&freeplay=true'
    game=Game(provider='1spin4win',slug='tenluckyspins',name='Ten Lucky Spins',url=url)
    calls=[]
    class Response:
        def __init__(self,url,text):self.url=url;self.text=text;self.content=text.encode()
        def raise_for_status(self):pass
    class Session:
        def get(self,url,**kwargs):
            calls.append(url)
            if '/games.html?' in url:return Response(url,'<script src="./games/src/games_000101.js"></script>')
            if '/tenluckyspins.html?' in url:return Response(url,'<script src="/gmh5/tenluckyspins/src/client.js"></script>')
            if '/client.js' in url:return Response(url,SOURCE+'this.gameController.connect("TenLuckySpins","testuser","debug","","01","","");var gameURL="wss://gs.1spin4win.com/games";')
            return Response(url,'')
    with patch.object(provider,'_worker_session',return_value=Session()),patch.object(provider,'_observe_runtime_bootstrap',return_value={'ws_url':'wss://gs.1spin4win.com/games','game_name':'TenLuckySpins','version':'01'}):
        spec=provider._discover_runtime_spec(game,timeout_s=1,attempt_dir=tmp_path)
    assert any('/tenluckyspins.html?' in url for url in calls)
    assert len(spec['purchase_modes']) == 1


MODERN_BUY_CLIENT = """
class BasicSlotView {constructor(){this.sideBetPercent=this.sideBet=0;this.buyFeaturePlayIndex=this.sideBetPlayIndex=this.buyFeatureToPlayActionIndex=this.sideBetToPlayActionIndex=this.extraAnimationState=0;}
confirmBuyFeature(){0==this.buyFeatureToPlayActionIndex?this.sideBet=2:this.buyFeaturePlayIndex=this.buyFeatureToPlayActionIndex;}}
class SlotNetworkController {play(a,b,c){if(Game.game.useBuyFeature&&0<Game.game.sideBetPercent){var e=0;0<Game.game.buyFeaturePlayIndex?(e=Game.game.buyFeaturePlayIndex,Game.game.buyFeaturePlayIndex=0):0<Game.game.sideBet&&0<Game.game.sideBetPlayIndex&&(e=Game.game.sideBetPlayIndex);0<e&&(d={type:"1",data:""+a+","+b+","+c+","+e.toString()})}else d=(Game.game.sideBet-1).toString();this.sendData("A/u2"+JSON.stringify(d));}}
class FixtureBuyView extends BasicSlotView {constructor(){super();this.sideBetToPlayActionIndex=1;this.buyFeatureToPlayActionIndex=3;this.buyFeatureMult=56;this.useBuyFeature=!0;this.sideBet=1;this.sideBetPercent=3;}}
"""

def test_modern_class_purchase_uses_configured_buy_selector_not_side_bet():
    modes=discover_purchase_modes([MODERN_BUY_CLIENT],'FixtureBuy')
    assert len(modes)==1
    assert modes[0]['cost_multiplier']==56
    assert modes[0]['feature_selector']==3
    assert modes[0]['executable'] is True

def test_buy_support_in_shared_class_does_not_enable_normal_game():
    source=MODERN_BUY_CLIENT+'class FixtureNormalView extends BasicSlotView {constructor(){super();this.sideBet=1;}showHelp(){this.useBuyFeature=true;}}'
    assert discover_purchase_modes([source],'FixtureNormal')==[]

def test_effective_disabled_constructor_does_not_count_earlier_enable():
    source='var FixtureNormalView=function(){this.useBuyFeature=true;this.useBuyFeature=false;};'
    assert discover_purchase_modes([source],'FixtureNormal')==[]

def test_nested_callback_enable_is_not_constructor_purchase_configuration():
    source='var FixtureNormalView=function(){this.help=function(){this.useBuyFeature=true;};};'
    assert discover_purchase_modes([source],'FixtureNormal')==[]


def test_nested_class_constructor_does_not_enable_outer_game():
    source='class FixtureNormalView extends BasicSlotView {help(){class Inner extends BasicSlotView {constructor(){super();this.useBuyFeature=true;}}}}'
    assert discover_purchase_modes([source],'FixtureNormal')==[]

def test_concise_arrow_callback_does_not_enable_purchase():
    source='var FixtureNormalView=function(){BasicSlotView.call(this);this.help=()=>this.useBuyFeature=true;};'
    assert discover_purchase_modes([source],'FixtureNormal')==[]

def test_selector_certificate_cannot_come_from_comment_or_other_method():
    source=MODERN_BUY_CLIENT.replace('play(a,b,c){','fake(a,b,c){')
    source+='class SlotNetworkController {play(a,b,c){this.sendData("ordinary");}}'
    modes=discover_purchase_modes([source],'FixtureBuy')
    assert len(modes)==1
    assert modes[0]['executable'] is False
    assert modes[0]['feature_selector'] is None


def test_parenthesized_arrow_expression_does_not_enable_purchase():
    source='var FixtureNormalView=function(){BasicSlotView.call(this);this.help=()=> callback(0,this.useBuyFeature=true,1);};'
    assert discover_purchase_modes([source],'FixtureNormal')==[]


def test_chained_constructor_values_enable_configured_purchase():
    source=MODERN_BUY_CLIENT.replace('this.sideBet=1;this.sideBetPercent=3;','this.sideBetPercent=this.sideBet=this.sideBetToPlayActionIndex=1;')
    modes=discover_purchase_modes([source],'FixtureBuy')
    assert modes[0]['executable'] is True
    assert modes[0]['feature_selector']==3

def test_chained_sidebet_is_separate_from_purchase():
    from tester_spin.providers.one_spin4win_purchases import discover_antebet_modes
    source=MODERN_BUY_CLIENT.replace('this.sideBet=1;this.sideBetPercent=3;','this.sideBetPercent=this.sideBet=this.sideBetToPlayActionIndex=1;')
    source=source.replace('confirmBuyFeature(){','toggleSideBet(){this.sideBet=2;this.sideBetPlayIndex=this.sideBetToPlayActionIndex;}getSidebetValue(){return a+Math.round(a*this.sideBetPercent);}confirmBuyFeature(){')
    modes=discover_antebet_modes([source],'FixtureBuy')
    assert len(modes)==1
    assert modes[0]['kind']=='ANTE_BET'
    assert modes[0]['feature_selector']==1
    assert modes[0]['cost_multiplier']==2
    assert modes[0]['feature_selector']!=discover_purchase_modes([source],'FixtureBuy')[0]['feature_selector']


def test_antebet_executes_regular_result_without_requiring_buy_bonus(tmp_path):
    from unittest.mock import patch
    import json
    from tester_spin.models import Game
    from tester_spin.providers.one_spin4win import OneSpin4WinProvider
    class WS:
        def __init__(self):self.sent=[];self.responses=iter([json.dumps({'type':1,'l':27,'b3':0}),json.dumps({'type':3,'st':0,'l':27,'b3':0})])
        def send(self,s):self.sent.append(s)
        def recv(self):return next(self.responses)
        def settimeout(self,t):pass
        def close(self):pass
    ws=WS();p=OneSpin4WinProvider(tmp_path)
    spec={'ws_url':'wss://example.invalid/games','game_name':'FixtureBuy','version':'01','wallet':'','currency':'EUR','purchase_modes':[],'antebet_modes':[{'id':'D1_ANTE_BET','executable':True,'feature_selector':1}]}
    with patch.object(p,'_discover_runtime_spec',return_value=spec),patch.object(p,'_open_websocket',return_value=ws),patch('tester_spin.providers.one_spin4win.audit_enabled',return_value=False):
        result=p._execute_direct_ws_spin(Game('1spin4win','fixture','Fixture','https://example.invalid'),timeout_s=1,attempt_dir=tmp_path,feature_selector=1,feature_kind='ANTE_BET')
    assert result[0] and result[1],result
    sends=[x for x in result[4] if x.get('direction')=='sent' and x.get('classification')!='init']
    assert sends[0]['classification']=='antebet'
    assert sends[0]['spin_shape']['variant']=='side_bet'
    assert any('27,0,0,1' in x for x in ws.sent)


def test_equal_buy_and_sidebet_selectors_are_not_certified_as_antebet():
    from tester_spin.providers.one_spin4win_purchases import discover_antebet_modes
    source=MODERN_BUY_CLIENT.replace('this.sideBetToPlayActionIndex=1;','this.sideBetToPlayActionIndex=3;')
    source=source.replace('confirmBuyFeature(){','toggleSideBet(){this.sideBetPlayIndex=this.sideBetToPlayActionIndex;}getSidebetValue(){return a+Math.round(a*this.sideBetPercent);}confirmBuyFeature(){')
    assert discover_antebet_modes([source],'FixtureBuy')==[]

def test_provider_schedules_and_reports_one_purchase_and_one_antebet(tmp_path):
    import json,threading
    from unittest.mock import patch
    from tester_spin.models import Game
    from tester_spin.providers.one_spin4win import OneSpin4WinProvider
    from tester_spin.feature_summary import feature_summary
    p=OneSpin4WinProvider(tmp_path);calls=[]
    modes=[{'id':'D1_BUY_FEATURE','kind':'PURCHASE','executable':True,'feature_selector':3,'observed':True,'coverage_required':True}, {'id':'D1_ANTE_BET','kind':'ANTE_BET','executable':True,'feature_selector':1,'observed':True,'coverage_required':True}]
    def execute(game,*,attempt_dir,**kwargs):
        calls.append(kwargs)
        (attempt_dir/'runtime-spec.json').write_text(json.dumps({'game_name':'FixtureBuy','purchase_modes':modes[:1],'antebet_modes':modes[1:]}))
        return True,True,1,'wss://example.invalid',[],''
    with patch.object(p,'_execute_direct_ws_spin',side_effect=execute):
        result=p.test_game(Game('1spin4win','fixture','Fixture','https://example.invalid'),spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda s:None)
    assert result.status=='OK'
    assert [a.mode_kind for a in result.attempts]==['SPIN','PURCHASE','ANTE_BET']
    assert calls[-1]['feature_selector']==1 and calls[-1]['feature_kind']=='ANTE_BET'
    summary=feature_summary(result.to_dict())
    assert 'Cantidad: 1' in summary and 'Antebets: S' in summary
