import pytest
import json,threading
from unittest.mock import MagicMock
from tester_spin.models import Game
from tester_spin.providers.ka_gaming.adapter import KAGamingProvider
from test_ka_rmp_execution import CLIENT

def test_har_purchase_is_scoped_and_contains_no_session(tmp_path):
    from tester_spin.providers.ka_gaming.evidence import purchase_modes_from_har
    p=tmp_path/'capture.har'
    p.write_text(json.dumps({'log':{'entries':[{'request':{'method':'POST','url':'https://rmpdemo.kaga88.com/kaga/command/spin','postData':{'text':json.dumps({'gn':'JadeQuest','sid':'secret','sel':40,'cps':1,'atb':0,'dn':.01,'pos':[1]})}}}]}}))
    modes=purchase_modes_from_har(p,'JadeQuest')
    assert len(modes)==1 and modes[0]['pos']==[1] and not modes[0]['validated']
    assert 'secret' not in json.dumps(modes)
    assert purchase_modes_from_har(p,'OtherGame')==[]

@pytest.mark.parametrize('unknown', [None, {'rf':1}, {'mb':True}, {'as':[{'choice':1}]}, {'acb':0,'fsr':0}])
def test_imported_purchase_runs_free_games_without_rebuying(tmp_path,unknown):
    p=KAGamingProvider(tmp_path);cache=p.provider_root/'runtime';cache.mkdir();(cache/'game.min.2070.js').write_text(CLIENT)
    g=Game('ka_gaming','jadequest','JadeQuest','https://gamesdemo.kaga88.com/?g=JadeQuest&p=demo',symbol='JadeQuest')
    folder=p.provider_root/g.slug;folder.mkdir();(folder/'purchase_modes.json').write_text(json.dumps([{'id':'BUY_POS_1','kind':'PURCHASE','pos':[1],'source':'manual-har','observed':True,'validated':False,'coverage_required':True}]))
    calls=[];rest={'sel':40,'cps':1,'atb':0,'dn':.01,'fs':False,'rf':0,'acb':0,'fsr':0}
    states=iter([{**rest,'acb':1,'fsr':1,'pos':[1],**(unknown or {})},{**rest,'fs':True,'acb':1,'fsr':0},rest])
    def post(url,**kwargs):
        body=json.loads(kwargs['data']);calls.append(body)
        if url.endswith('startGame'):value={'e':False,'ec':0,'un':'new','si':'session','sgr':{'lsd':rest}}
        elif url.endswith('endSession'):value={'e':False,'ec':0}
        else:value={'e':False,'ec':0,'md':rest if len(calls)==2 else next(states)}
        r=MagicMock(text=json.dumps(value));r.json.return_value=value;return r
    p.http=MagicMock();p.http.post.side_effect=post
    p.http.get.side_effect=[MagicMock(status_code=200,text='script.src="game.min.2070.js"'),MagicMock(status_code=200,text=CLIENT)]
    result=p.test_game(g,spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    if unknown:
        assert result.status=='PARCIAL'
        assert len(result.attempts)==2 and result.attempts[1].wire_steps==1
        assert not next(m for m in result.discovered_modes if m['id']=='BUY_POS_1')['validated']
        return
    assert result.status=='OK',result.error
    assert len(result.attempts)==2 and result.attempts[1].wire_steps==3
    assert sum('pos' in b for b in calls)==1
    assert next(m for m in result.discovered_modes if m['id']=='BUY_POS_1')['validated']

def test_catalog_purchase_uses_provider_candidate_without_claiming_validation(tmp_path):
    p=KAGamingProvider(tmp_path)
    g=Game('ka_gaming','hotcoinbf','HotCoinBF','https://gamesdemo.kaga88.com/?g=HotCoinBF&p=demo',symbol='HotCoinBF')
    p._catalog_modes['hotcoinbf']=[{'id':'SPIN','kind':'SLOTS'},{'id':'BONUS_PURCHASE','kind':'BONUS_PURCHASE'}]
    modes=p._discovered_modes(g)
    buy=next(m for m in modes if m['id']=='BUY_POS_1')
    assert buy['source']=='provider-family-candidate' and buy['pos']==[1]
    assert not buy['validated'] and buy['coverage_required']


def test_old_catalog_buy_flag_does_not_make_nonpurchase_game_buyable(tmp_path):
    p=KAGamingProvider(tmp_path)
    game=Game('ka_gaming','dragonslegend','DragonsLegend','https://gamesdemo.kaga88.com/?g=DragonsLegend&p=demo',symbol='DragonsLegend')
    p._catalog_modes[game.slug]=[{'id':'SPIN'},{'id':'BONUS_PURCHASE'},{'id':'FREE_GAMES','coverage_required':False}]
    modes=p._discovered_modes(game)
    assert not any(m['id'] in {'BONUS_PURCHASE','BUY_POS_1'} for m in modes)
    assert any(m['id']=='FREE_GAMES' for m in modes)


def test_ares_natural_free_games_complete_without_a_purchase(tmp_path):
    from pathlib import Path
    from tester_spin.providers.ka_gaming.runtime import run_rmp_game
    fixture=json.loads((Path(__file__).parent/'fixtures/ka_ares_natural_free_games.json').read_text(encoding='utf-8'))
    responses=[{'e':False,'ec':0,'un':'demo','si':'session','sgr':{'lsd':fixture['initial']}}]
    responses += [{'e':False,'ec':0,'md':state} for state in fixture['responses']]
    responses += [{'e':False,'ec':0}]
    calls=[]
    def post(url,**kwargs):
        calls.append(json.loads(kwargs['data']))
        value=responses.pop(0)
        response=MagicMock(status_code=200,text=json.dumps(value));response.json.return_value=value
        return response
    http=MagicMock();http.post.side_effect=post
    game=Game('ka_gaming','ares','Ares','https://gamesdemo.kaga88.com/?g=Ares&p=demo',symbol='Ares')
    result=run_rmp_game(game,http=http,root=tmp_path,profile=('2070','version','literal'),
        modes=[{'id':'SPIN'}],spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='OK',result.error
    assert result.successful_spins==1 and len(result.attempts)==1
    assert result.attempts[0].wire_steps==17
    assert not any('pos' in body for body in calls)
    assert len(calls)==19


def test_tattooist_har_purchase_finishes_despite_retrigger_and_zero_remaining(tmp_path):
    from pathlib import Path
    from tester_spin.providers.ka_gaming.runtime import run_rmp_game
    fixture=json.loads((Path(__file__).parent/'fixtures/ka_tattooist_purchase.json').read_text(encoding='utf-8'))
    rest=fixture['initial']
    responses=[{'e':False,'ec':0,'un':'demo','si':'session','sgr':{'lsd':rest}},{'e':False,'ec':0,'md':rest}]
    responses += [{'e':False,'ec':0,'md':state} for state in fixture['responses']]
    responses += [{'e':False,'ec':0}]
    calls=[]
    def post(url,**kwargs):
        calls.append(json.loads(kwargs['data']));value=responses.pop(0)
        response=MagicMock(status_code=200,text=json.dumps(value));response.json.return_value=value
        return response
    http=MagicMock();http.post.side_effect=post
    game=Game('ka_gaming','thenaughtytattooist','Tattooist','https://gamesdemo.kaga88.com/?g=TheNaughtyTattooist&p=demo',symbol='TheNaughtyTattooist')
    modes=[{'id':'SPIN'},{'id':'BUY_POS_1','kind':'PURCHASE','pos':[1],'source':'manual-har','coverage_required':True}]
    result=run_rmp_game(game,http=http,root=tmp_path,profile=('2071','version','literal'),modes=modes,
        spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert result.status=='OK',result.error
    assert result.attempts[-1].terminal
    assert result.attempts[-1].wire_steps==len(fixture['responses'])
    assert sum('pos' in b for b in calls)==1
