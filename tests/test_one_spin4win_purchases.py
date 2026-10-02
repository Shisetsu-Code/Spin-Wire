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
