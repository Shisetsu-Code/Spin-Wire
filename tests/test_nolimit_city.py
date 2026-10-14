import json,threading
import pytest
from tester_spin.providers.nolimit_city.catalog import games_from_rows
from tester_spin.providers.nolimit_city import NolimitCityProvider

def row(code='ExampleSlot',studio='Nolimit City'):
    return {'name':'Example Slot','code':code,'studio':studio,'url':'https://playin.com/embed/v1/demo/'+code}

def test_catalog_filters_studio_and_preserves_launch_identity():
    games=games_from_rows([row(),row('OtherStudio','Red Tiger')])
    assert len(games)==1
    assert games[0].provider=='nolimit_city' and games[0].slug=='exampleslot'
    assert games[0].symbol=='ExampleSlot'
    assert games[0].url=='https://playin.com/embed/v1/demo/ExampleSlot'
    assert games[0].last_status=='PENDIENTE'

@pytest.mark.parametrize('mutation',[{'code':'../escape'},{'url':'https://attacker.example/embed/v1/demo/ExampleSlot'},
    {'url':'https://playin.com/embed/v1/demo/Different'},{'url':'https://playin.com/embed/v1/demo/ExampleSlot?token=private'},{'name':''}])
def test_invalid_or_mismatched_launch_record_rejected(mutation):
    with pytest.raises(ValueError):games_from_rows([{**row(),**mutation}])

def test_case_collision_and_duplicate_ids_rejected():
    for values in [[row(),row()],[row(),row('exampleslot')]]:
        with pytest.raises(ValueError):games_from_rows(values)

def test_empty_or_foreign_catalog_is_not_authority_for_zero():
    for value in [[],[row(studio='NetEnt')],{},None]:
        with pytest.raises(ValueError):games_from_rows(value)

def test_live_and_offline_catalog_never_delete_existing_rows(tmp_path):
    provider=NolimitCityProvider(tmp_path)
    class Response:
        def raise_for_status(self):pass
        def json(self):return [row()]
    class HTTP:
        def get(self,*a,**kw):return Response()
    provider.http=HTTP()
    games=provider.crawl_catalog(stop_event=threading.Event(),progress=lambda _:None)
    assert any(g.symbol=='ExampleSlot' for g in games)
    assert not provider.catalog_crawl_authoritative
    assert provider.game_dir(games[0]).is_dir()
    class Offline:
        def get(self,*a,**kw):raise OSError('offline')
    provider.http=Offline()
    assert provider.crawl_catalog(stop_event=threading.Event(),progress=lambda _:None)
    assert not provider.catalog_crawl_authoritative

def test_unlearned_protocol_never_claims_ok_or_zero_purchases(tmp_path,monkeypatch):
    from tester_spin.providers.nolimit_city.runtime import Unlearned
    class UnsupportedSession:
        def open(self,*args):raise Unlearned('Nolimit City: bootstrap desconocido')
        def close(self):pass
    monkeypatch.setattr('tester_spin.providers.nolimit_city.adapter.NolimitSession',UnsupportedSession)
    provider=NolimitCityProvider(tmp_path);game=games_from_rows([row()])[0]
    result=provider.test_game(game,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='PARCIAL' and result.successful_spins==0
    assert not result.feature_domains
    assert not provider.build_farm_contract(game,result)['ready']

def test_provider_can_be_selected_by_batch_registry(tmp_path):
    from tools.run_retry_queue import provider_for
    assert provider_for('nolimit_city',tmp_path).display_name=='Nolimit City'
