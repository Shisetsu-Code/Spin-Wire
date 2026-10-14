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


def test_normal_spin_without_cmd_and_collect_without_coin_are_not_lost():
    from tester_spin.providers.yggdrasil.protocol import play_records, discovered_modes
    spin = har_entry()
    spin['request']['postData']['text'] = 'gameid=10964&amount=2&coin=0.1'
    spin['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {
        'status': 'Pending', 'bets': [{'step': 1, 'betdata': {'cmds': ['C']},
                                    'eventdata': {'nextCmds': 'C'}}]}}})
    collect = har_entry()
    collect['request']['postData']['text'] = 'gameid=10964&cmd=C&amount=0&step=2&betid=1'
    collect['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {
        'status': 'Finished', 'bets': [{'step': 2, 'status': 'RESULTED', 'betdata': {'cmd': 'C'}, 'eventdata': None}]}}})
    records = play_records({'log': {'entries': [spin, collect]}})
    assert len(records) == 2
    assert records[0]['cmd'] == ''
    assert records[0]['next_commands'] == ['C']
    assert not records[0]['terminal_captured']
    assert records[1]['terminal_captured']
    modes = discovered_modes(records, '10964')
    assert [m['id'] for m in modes] == ['SPIN', 'C']
    assert modes[1]['kind'] == 'CONTINUATION'
    assert not modes[1]['coverage_required']
    assert not any(m.get('executable') for m in modes)


def test_animation_finished_is_not_a_settled_wager():
    from tester_spin.providers.yggdrasil.protocol import play_records
    entry = har_entry()
    entry['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {
        'status': 'Pending', 'bets': [{'step': 1, 'betdata': {'cmds': ['C']},
        'eventdata': {'response': {'clientData': {'isFinished': True}}}}]}}})
    row = play_records({'log': {'entries': [entry]}})[0]
    assert row['terminal_captured'] is False


def test_http_failure_does_not_confirm_terminal():
    from tester_spin.providers.yggdrasil.protocol import play_records
    entry = har_entry()
    entry['response']['status'] = 500
    entry['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {'status': 'Finished', 'bets': [{'status': 'RESULTED'}]}}})
    assert not play_records({'log': {'entries': [entry]}})[0]['terminal_captured']


def test_unknown_next_command_blocks_terminal_evidence():
    from tester_spin.providers.yggdrasil.protocol import play_records
    entry = har_entry()
    entry['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {
        'status': 'Finished', 'bets': [{'status': 'RESULTED', 'eventdata': {'nextCmds': 'UNSUPPORTED COMMAND'}}]}}})
    assert not play_records({'log': {'entries': [entry]}})[0]['terminal_captured']


def test_mode_aggregates_later_terminal_capture():
    from tester_spin.providers.yggdrasil.protocol import play_records, discovered_modes
    pending, finished = har_entry(), har_entry()
    pending['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {
        'status': 'Pending', 'bets': [{'status': 'RESULTED'}]}}})
    finished['response']['content']['text'] = json.dumps({'code': 0, 'data': {'wager': {
        'status': 'Finished', 'bets': [{'status': 'RESULTED'}]}}})
    rows = play_records({'log': {'entries': [pending, finished]}})
    assert discovered_modes(rows, '10964')[1]['terminal_captured'] is True


def test_numeric_client_launcher_links_official_game_identity(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    class Response:
        text='<embed data-iframe-src="https://staticdemo.yggdrasilgaming.com/10945/index.html?gameid=10945&amp;org=Demo&amp;appsrv=https://demo.yggdrasilgaming.com">'
        def raise_for_status(self):pass
    class HTTP:
        def get(self,*a,**kw):return Response()
    p.http=HTTP()
    p.prepare_test_artifacts(g,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert g.symbol=='10945'


def test_official_pff_launcher_links_identity_without_authorizing_a_session(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    class Response:
        text='<embed data-iframe-src="https://staticpff.yggdrasilgaming.com/init/launchClient.html?gameid=10304">'
        def raise_for_status(self):pass
    class HTTP:
        def get(self,*a,**kw):return Response()
    p.http=HTTP()
    p.prepare_test_artifacts(g,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert g.symbol=='10304'
    assert p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None).status=='PARCIAL'


def test_numeric_launcher_trims_page_whitespace_with_matching_path(tmp_path):
    from tester_spin.models import Game
    p=provider(tmp_path);g=Game('yggdrasil','example','Example','https://yggdrasilgaming.com/games/example/')
    class Response:
        text='<embed data-iframe-src="https://staticdemo.yggdrasilgaming.com/10945/index.html?gameid=%2010945%20&amp;org=Demo&amp;appsrv=https://demo.yggdrasilgaming.com">'
        def raise_for_status(self):pass
    class HTTP:
        def get(self,*a,**kw):return Response()
    p.http=HTTP()
    p.prepare_test_artifacts(g,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert g.symbol=='10945'
