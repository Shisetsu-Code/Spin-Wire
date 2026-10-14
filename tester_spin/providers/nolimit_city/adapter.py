from __future__ import annotations
import json,threading,uuid
from pathlib import Path
from curl_cffi import requests
from tester_spin.models import GameTestResult,utc_now_iso
from tester_spin.providers.base import ProviderAdapter
from .catalog import CODE,CATALOG_URL,FEED_URL,games_from_rows

class NolimitCityProvider(ProviderAdapter):
    key='nolimit_city'
    display_name='Nolimit City'
    catalog_url=CATALOG_URL
    max_test_concurrency=1

    def __init__(self,data_root:Path):
        self.provider_root=Path(data_root)/'providers'/self.key
        self.provider_root.mkdir(parents=True,exist_ok=True)
        self.http=requests.Session(impersonate='chrome')
        self.set_catalog_authority(False,'Catálogo de demos afiliadas: sin autoridad de eliminación')

    def game_dir(self,game):
        if (game.provider!=self.key or not CODE.fullmatch(game.symbol)
                or game.slug!=game.symbol.casefold()):raise ValueError('Nolimit City: identidad inválida')
        path=self.provider_root/game.slug;path.mkdir(parents=True,exist_ok=True)
        return path

    def catalog_record_invalid_reason(self,game):
        try:
            parsed=games_from_rows([{'studio':'Nolimit City','code':game.symbol,'name':game.name,'url':game.url}])[0]
            if game.provider!=self.key or game.slug!=parsed.slug:return 'Nolimit City: identidad inconsistente'
        except ValueError:return 'Nolimit City: fila de catálogo inválida'
        return ''

    def crawl_catalog(self,*,stop_event:threading.Event,progress,max_pages=100,on_game=None):
        self.set_catalog_authority(False,'Feed oficial de demos sin autoridad para borrar juegos')
        if stop_event.is_set():return []
        snapshot=json.loads(Path(__file__).with_name('catalog.json').read_text(encoding='utf-8'))
        games=games_from_rows(snapshot['games'])
        source='snapshot oficial incluido'
        try:
            response=self.http.get(FEED_URL,timeout=30);response.raise_for_status()
            rows=response.json();live=games_from_rows(rows)
            merged={g.symbol:g for g in games};merged.update({g.symbol:g for g in live})
            games=list(merged.values());source=FEED_URL
            (self.provider_root/'catalog.raw.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception as exc:
            progress(f'Nolimit City: usando catálogo oficial guardado ({type(exc).__name__}).')
        found=[]
        for game in sorted(games,key=lambda g:g.name.casefold()):
            if stop_event.is_set():break
            folder=self.game_dir(game)
            metadata={'provider':self.key,'slug':game.slug,'symbol':game.symbol,'name':game.name,
                      'public_url':game.url,'demo_url':game.url,'catalog_source':source,'catalog_updated_at':utc_now_iso()}
            (folder/'game.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
            found.append(game)
            if on_game:on_game(game)
        progress(f'Nolimit City: {len(found)} demos cargadas; protocolo de ejecución pendiente.')
        return found

    def har_artifact_dir(self,game):
        path=self.game_dir(game)/'analysis';path.mkdir(exist_ok=True);return path

    def farm_contract_dir(self,game):return self.game_dir(game)

    def test_game(self,game,*,spins,timeout_s,stop_event,progress):
        requested=max(1,int(spins))
        result=GameTestResult(self.key,game.slug,game.name,game.url,requested,0,requested,'PARCIAL',symbol=game.symbol)
        if stop_event.is_set():
            result.status='CANCELADO';result.error='Ejecución detenida';return result
        folder=self.game_dir(game)/'tests'/(utc_now_iso().replace(':','').replace('+','_')+'-'+uuid.uuid4().hex[:8])
        folder.mkdir(parents=True);result.run_dir=str(folder)
        result.discovered_modes=[{'id':'SPIN','kind':'SPIN','executable':False,'validated':False,
            'coverage_required':True,'required_options':['DOMAIN_UNRESOLVED'],'covered_options':[],
            'reason':'NOLIMIT_PROTOCOL_CAPTURE_REQUIRED'}]
        result.error='Nolimit City: catálogo integrado; faltan primitivas de sesión, opciones, cierre y retorno contrastadas con HAR.'
        result.finished_at=utc_now_iso();progress(result.error)
        return result
