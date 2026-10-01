import importlib.util
import json
import threading
from pathlib import Path
import pytest


def api():
    assert importlib.util.find_spec('tester_spin.providers.three_oaks') is not None, 'Falta el proveedor Three Oaks'
    from tester_spin.providers.three_oaks.adapter import ThreeOaksProvider
    from tester_spin.providers.three_oaks.catalog import games_from_page, launcher_config, family_map
    from tester_spin.providers.three_oaks.runtime import discover_modes, base_terminal, play_fields, checked_response
    return ThreeOaksProvider, games_from_page, launcher_config, family_map, discover_modes, base_terminal, play_fields, checked_response


def test_catalog_keeps_native_names_and_ignores_non_game_rows():
    _, parse, *_ = api()
    games = parse({'data': {'items': [{'name':'3_superpower_diamonds','title_text':'3 SuperPower Diamonds','has_page':True,'main_logo_file':'/media/diamond.jpg'}, {'name':'hidden','title_text':'Hidden','has_page':False}], 'total_pages':2}})
    assert [(g.provider,g.slug,g.symbol,g.name,g.url,g.thumbnail_url) for g in games] == [('3oaks','3_superpower_diamonds','3_superpower_diamonds','3 SuperPower Diamonds','https://3oaks.com/game/3_superpower_diamonds','https://3oaks.com/media/diamond.jpg')]


def test_catalog_rejects_bad_slug_before_a_directory_can_be_written():
    _, parse, *_ = api()
    with pytest.raises(ValueError):
        parse({'data':{'items':[{'name':'../escape','title_text':'Bad','has_page':True}],'total_pages':1}})


def test_launcher_is_parsed_as_json_without_executing_javascript():
    _, _, parse, families, *_ = api()
    config={'options':{'token':'secret','queue':'queue','protocol':'goreel','wl':'demo'},'desktop':{'server_url':'//betman-demo.head.3oaks.com/betman-demo/gs/demo/desktop/{QUEUE}/demo/','client_url':'https://static.3oaks.com/gs/clients_enjoy/demo/v1/'},'available_games':[{'name':'demo','client_url':'https://static.3oaks.com/gs/clients_enjoy/demo/v1/'}]}
    assert families(parse('})(window, '+json.dumps(config)+', "url");')) == {'demo':'enjoy'}
    with pytest.raises(ValueError):parse('})(window, getSecret(), "url");')


def initial():
    return {'context':{'current':'spins','round_finished':True,'actions':['spin','buy_spin'],'available_buy_bonus':[1,2],'spins':{'bet_per_line':10,'lines':25}},'settings':{'bets':[2,10],'lines':[25],'bet_factor':[10],'buy_bonus_prices':{'1':100,'2':300}}}


def test_only_server_advertised_purchases_become_candidates():
    *_, discover, terminal, play, check = api()
    modes=discover(initial(),'enjoy',True)
    assert [m['id'] for m in modes] == ['SPIN','PURCHASE_1','PURCHASE_2']
    assert modes[1]['request_options']['selected_mode'] == 1
    assert modes[2]['feature_multiplier'] == 300
    assert not any(m['validated'] for m in modes)
    assert play(initial(),'buy_spin',2)['action'] == {'name':'buy_spin','params':{'bet_per_line':10,'lines':25,'bet_factor':10,'selected_mode':2}}
    with pytest.raises(ValueError): play(initial(),'buy_spin',3)


def test_unknown_family_does_not_inherit_the_enjoy_purchase_serializer():
    *_, discover, terminal, play, check = api()
    modes=discover(initial(),'unseen',False)
    assert len(modes)==3
    assert all(not m['executable'] for m in modes)


def test_terminal_requires_explicit_completed_base_round():
    *_, discover, terminal, play, check = api()
    assert terminal(initial())
    assert not terminal({'context':{'actions':['spin'],'current':'spins'}})
    assert not terminal({'context':{'actions':['respin'],'current':'bonus','round_finished':True}})


def test_http_200_server_error_is_not_a_success():
    *_, check = api()
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'status':{'code':'SERVER_ERROR','type':'crit'},'context':{'round_finished':True}}
    with pytest.raises(ValueError,match='SERVER_ERROR'):check(Response())


def test_partial_catalog_never_becomes_authoritative(tmp_path):
    Provider,*_ = api()
    provider=Provider(tmp_path)
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'data':{'items':[{'name':'one','title_text':'One','has_page':True}],'total_pages':2}}
    class HTTP:
        def get(self,url,**kwargs):return Response()
    provider.http=HTTP()
    games=provider.crawl_catalog(stop_event=threading.Event(),progress=lambda _:None,max_pages=1)
    assert len(games)==1
    assert not provider.catalog_crawl_authoritative


def test_cancelled_run_does_not_send_requests(tmp_path):
    Provider,*_=api()
    from tester_spin.models import Game
    provider=Provider(tmp_path);event=threading.Event();event.set()
    class HTTP:
        def get(self,*a,**k):raise AssertionError('No debe conectar al cancelar')
    provider.http=HTTP()
    result=provider.test_game(Game('3oaks','one','One','https://3oaks.com/game/one',symbol='one'),spins=1,timeout_s=1,stop_event=event,progress=lambda _:None)
    assert result.status=='PARCIAL' and result.successful_spins==0

def test_recovery_queue_can_select_the_new_provider(tmp_path):
    from tools.run_retry_queue import provider_for
    assert provider_for('3oaks',tmp_path).display_name == '3 Oaks Gaming'


def test_real_server_error_envelope_remains_failed_and_exports_no_session(tmp_path):
    Provider,*_=api()
    from tester_spin.models import Game
    config={'options':{'token':'demo-private-token','queue':'private-queue','protocol':'goreel','wl':'demo','lang':'en','vendor':'ENJOY'},'desktop':{'server_url':'//betman-demo.head.3oaks.com/betman-demo/gs/demo/desktop/{QUEUE}/demo/','client_url':'https://static.3oaks.com/gs/clients_enjoy/demo/v1/'}}
    class Response:
        def __init__(self,data=None,text=None):self._data=data;self.text=json.dumps(data) if text is None else text
        def raise_for_status(self):pass
        def json(self):return self._data
    responses=iter([{'session_id':'private-session','user':{'huid':'private-user'},'status':{'code':'OK'}}, {'session_id':'private-session','status':{'code':'OK'},**initial()}, {'command':'play','status':{'code':'SERVER_ERROR','type':'crit'},'context':initial()['context']}])
    class HTTP:
        def get(self,url,**kwargs):
            if url.endswith('/play'):return Response(text='})(window, '+json.dumps(config)+', "url");')
            return Response(text='setActionHandler(bn.SPIN bet_per_line bet_factor t.selected_mode=e bn.BUY_SPIN')
        def post(self,*args,**kwargs):return Response(next(responses))
    provider=Provider(tmp_path);provider.http=HTTP();game=Game('3oaks','demo','Demo','https://3oaks.com/game/demo',symbol='demo')
    result=provider.test_game(game,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='ERROR' and result.successful_spins==0
    assert len(result.discovered_modes)==3 and not any(m.get('validated') for m in result.discovered_modes)
    assert 'SERVER_ERROR' in result.error
    assert (Path(result.run_dir)/'attempt-001'/'002-play.response.raw.json').is_file()
    contract=provider.build_farm_contract(game,result)
    exported=json.dumps(contract)
    assert not contract['ready']
    assert all(secret not in exported for secret in ['private-session','private-user','private-queue','demo-private-token'])

def test_multiple_rounds_keep_independent_samples_and_purchase_selectors(tmp_path):
    Provider,*_=api()
    from tester_spin.models import Game
    from tester_spin.sample_catalog import build_sample_catalog
    config={'options':{'token':'fake-token','queue':'fake-queue','protocol':'goreel','wl':'demo','lang':'en','vendor':'ENJOY'},'desktop':{'server_url':'//betman-demo.head.3oaks.com/betman-demo/gs/demo/desktop/{QUEUE}/demo/','client_url':'https://static.3oaks.com/gs/clients_enjoy/demo/v1/'}}
    class Response:
        def __init__(self,data=None,text=None):self._data=data;self.text=json.dumps(data) if text is None else text
        def raise_for_status(self):pass
        def json(self):return self._data
    class HTTP:
        def get(self,url,**kwargs):
            if url.endswith('/play'):return Response(text='})(window, '+json.dumps(config)+', "url");')
            return Response(text='setActionHandler(bn.SPIN bet_per_line bet_factor t.selected_mode=e bn.BUY_SPIN')
        def post(self,url,**kwargs):
            body=json.loads(kwargs['data'])
            if body['command']=='login':return Response({'session_id':'fake-session','user':{'huid':'fake-user'},'status':{'code':'OK'}})
            return Response({'command':body['command'],'session_id':'fake-session','status':{'code':'OK'},**initial()})
    provider=Provider(tmp_path);provider.http=HTTP();game=Game('3oaks','demo','Demo','https://3oaks.com/game/demo',symbol='demo')
    result=provider.test_game(game,spins=2,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    samples=build_sample_catalog(result)
    assert len(result.attempts)==4 and samples['observed_paths_sampled']
    assert {g['mode_id'] for g in samples['groups']}=={'SPIN','PURCHASE_1','PURCHASE_2'}
    contract=provider.build_farm_contract(game,result)
    modes={m['id']:m for m in contract['modes']}
    assert modes['PURCHASE_1']['options']['selected_mode']==1
    assert modes['PURCHASE_2']['options']['selected_mode']==2
    assert all(m['executor']=='play' for m in modes.values())
    provider.finalize_test_result(result,progress=lambda _:None)
    assert result.status=='OK', result.error
