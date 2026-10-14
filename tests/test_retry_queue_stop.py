import threading
from types import SimpleNamespace
from unittest.mock import patch

def test_provider_stop_prevents_next_isolated_worker(monkeypatch):
    import tools.run_retry_queue as queue
    games=[SimpleNamespace(last_status='PENDIENTE',slug=str(i),name=str(i),provider='ka_gaming') for i in range(2)]
    shared=threading.Event();starts=[]
    class Process:
        exitcode=0
        def __init__(self,target,args):self.args=args
        def start(self):
            starts.append(self.args)
            if len(self.args)>5:self.args[-1].set()
        def join(self,*args):pass
        def is_alive(self):return False
    context=SimpleNamespace(Event=lambda:shared,Process=Process)
    from pathlib import Path
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    monkeypatch.setattr(queue.mp,'get_context',lambda _:context)
    monkeypatch.setattr(queue,'provider_for',lambda *args:SimpleNamespace(key='ka_gaming'))
    monkeypatch.setattr(queue.sys,'argv',['run_retry_queue','ka_gaming','--statuses','PENDIENTE'])
    with patch('tester_spin.storage.Storage',return_value=SimpleNamespace(list_games=lambda _:games)):
        assert queue.main()==0
    assert len(starts)==1


def test_rate_rejection_sets_shared_stop_after_recording(monkeypatch):
    from pathlib import Path
    import tools.run_retry_queue as queue
    shared=threading.Event();recorded=[]
    game=SimpleNamespace(name='synthetic')
    monkeypatch.setattr(queue,'provider_for',lambda *args:SimpleNamespace(key='synthetic'))
    result=SimpleNamespace(error='Yggdrasil: HTTP 429 en authenticate; petición no reintentada')
    def scheduler(*args,**kwargs):kwargs['on_result'](result)
    with patch('tester_spin.storage.Storage',return_value=SimpleNamespace(record_result=recorded.append)),patch('tester_spin.scheduler.run_game_tests',scheduler):
        queue._run_one(str(Path(__file__).resolve().parents[1]),'synthetic',game,1,1,shared)
    assert recorded==[result]
    assert shared.is_set()
