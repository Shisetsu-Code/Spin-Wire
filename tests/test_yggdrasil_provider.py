import json
import threading
from pathlib import Path
import pytest


def provider(tmp_path):
    from tester_spin.providers import YggdrasilProvider
    return YggdrasilProvider(tmp_path)


def har_entry(cmd='BB_2', gameid='10964', url='https://demo.yggdrasilgaming.com/game.web/service?fn=play'):
    return {'request': {'url':url, 'method':'POST', 'postData':{'mimeType':'application/x-www-form-urlencoded',
        'text':f'gameid={gameid}&cmd={cmd}&amount=65&coin=0.1&gameHistorySessionId=SECRET_SESSION&gameHistoryTicketId=SECRET_TICKET&clientinfo=PRIVATE_CLIENT'}},
        'response':{'status':200,'content':{'text':'{"ok":true}'}}}


def test_imported_catalog_is_non_authoritative_and_usable_without_network(tmp_path):
    p=provider(tmp_path)
    class Offline:
        def get(self,*a,**kw):raise OSError('offline')
    p.http=Offline()
    games=p.crawl_catalog(stop_event=threading.Event(),progress=lambda _:None)
    assert len(games)==159
    assert not p.catalog_crawl_authoritative
    assert len({g.slug for g in games})==159
    assert all(g.url.startswith('https://yggdrasilgaming.com/games/') and '#tryit#' not in g.url for g in games)


def test_purchase_capture_is_game_scoped_and_never_proves_base_or_terminal(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/',symbol='10964')
    folder=p.har_artifact_dir(g)
    (folder/'browser.har').write_text(json.dumps({'log':{'entries':[har_entry(),har_entry('BB_5'),har_entry('BB_99','other'),har_entry(url='https://google-analytics.com/game.web/service?fn=play')]}}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='PARCIAL' and result.successful_spins==0
    assert {m['id'] for m in result.discovered_modes}=={'SPIN','BB_2','BB_5'}
    assert not any(m.get('validated') or m.get('executable') for m in result.discovered_modes)
    contract=p.build_farm_contract(g,result)
    exported=json.dumps(contract)
    assert not contract['ready']
    assert all(s not in exported for s in ['SECRET_SESSION','SECRET_TICKET','PRIVATE_CLIENT'])
    assert {m['executor'] for m in contract['modes'] if m['kind']=='PURCHASE'}=={'BB_2','BB_5'}


def test_missing_gameid_does_not_assign_other_games_purchase(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    (p.har_artifact_dir(g)/'mixed.har').write_text(json.dumps({'log':{'entries':[har_entry(),har_entry('BB_5','10965')]}}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert not result.symbol
    assert [m['id'] for m in result.discovered_modes]==['SPIN']


def test_unobserved_base_command_is_never_guessed_or_sent(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    class NoRequests:
        def post(self,*a,**kw):raise AssertionError('No debe inventar giro')
    p.http=NoRequests()
    result=p.test_game(g,spins=3,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='PARCIAL' and result.requested_spins==3 and result.successful_spins==0
    assert all(m['kind']!='PURCHASE' for m in result.discovered_modes)


def test_single_foreign_har_does_not_set_unassociated_gameid(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    (p.har_artifact_dir(g)/'foreign.har').write_text(json.dumps({'log':{'entries':[har_entry()]}}))
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.symbol==''
    assert [m['id'] for m in result.discovered_modes]==['SPIN']


def test_invalid_slug_cannot_escape_provider_directory(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path)
    with pytest.raises(ValueError):p.game_dir(Game('yggdrasil','../../outside','Bad','https://yggdrasilgaming.com/'))


def test_recovery_queue_selects_yggdrasil(tmp_path):
    from tools.run_retry_queue import provider_for
    assert provider_for('yggdrasil',tmp_path).display_name=='Yggdrasil'


def test_official_page_links_runtime_id_and_declares_buy_bonus_without_guessing_commands(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    class Response:
        text='<embed data-iframe-src="https://staticdemo.yggdrasilgaming.com/init/launchClient.html?gameid=10511&amp;org=Demo"><dt>Type</dt><dd>Buy Bonus</dd>'
        def raise_for_status(self):pass
    class HTTP:
        def get(self,*a,**kw):return Response()
    p.http=HTTP()
    p.prepare_test_artifacts(g,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.symbol=='10511'
    assert [m['id'] for m in result.discovered_modes]==['SPIN','BUY_BONUS_UNRESOLVED']
    assert not any(m['executable'] for m in result.discovered_modes)


def test_foreign_launcher_cannot_link_gameid(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    class Response:
        text='<embed data-iframe-src="https://attacker.example/init/launchClient.html?gameid=10511">'
        def raise_for_status(self):pass
    class HTTP:
        def get(self,*a,**kw):return Response()
    p.http=HTTP()
    p.prepare_test_artifacts(g,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert not g.symbol
