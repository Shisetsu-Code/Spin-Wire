import sys,json,threading,tempfile,copy
from pathlib import Path

from tester_spin.models import Game
from tester_spin.providers.three_oaks.adapter import ThreeOaksProvider
FIXTURES=Path(__file__).parent/'fixtures'
def run_adapter(custom=False):
    base={'context':{'current':'spins','round_finished':True,'actions':['spin'],'spins':{'bet_per_line':10,'lines':25}},'settings':{'lines':[25]},'status':{'code':'OK'}}
    config={'options':{'queue':'fixture','token':'fixture','protocol':'goreel','wl':'demo'},'desktop':{'server_url':'https://betman-demo.head.3oaks.com/betman-demo/gs/unseen/desktop/fixture/demo/','client_url':'https://static.3oaks.com/gs/clients_goreel/unseen/v1/'},'gr':{'static_path':'https://static.3oaks.com/gs/gamerunner/v1/'}}
    sent=[]
    class Response:
        def __init__(self,text='',data=None):self.text=text if data is None else json.dumps(data);self.data=data
        def raise_for_status(self):pass
        def json(self):return self.data
    class HTTP:
        def get(self,url,**kwargs):
            if url.endswith('/play'):return Response('})(window, '+json.dumps(config)+', "url");')
            if url.endswith('init.js'):return Response('window._PROVIDER.game={name:"unseen",use:["protocol","'+('custom_play' if custom else 'ui')+'"]};')
            if url.endswith('gr.js'):return Response((FIXTURES/'three_oaks_shared_runner.js').read_text(encoding='utf-8'))
            return Response('/* current game delegates its spin to the shared runner */')
        def post(self,url,**kwargs):
            payload=json.loads(kwargs['data']);sent.append(payload.get('action'))
            return Response(data={**copy.deepcopy(base),'session_id':'fixture','user':{'huid':'fixture'}})
    with tempfile.TemporaryDirectory() as directory:
        provider=ThreeOaksProvider(Path(directory));provider.http=HTTP()
        result=provider.test_game(Game('3oaks','unseen','Unseen','https://3oaks.com/game/unseen'),spins=1,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
        return result,sent
def test_missing_local_spin_still_certifies_current_shared_runner():
    result,sent=run_adapter()
    assert result.status=='OK',result.error
    assert [a for a in sent if a]==[{'name':'spin','params':{'bet_per_line':10,'lines':25}}]
def test_unknown_custom_play_remains_partial():
    result,sent=run_adapter(custom=True)
    assert result.status=='PARCIAL'
    assert not any(sent)
