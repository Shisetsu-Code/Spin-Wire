import threading
from unittest.mock import MagicMock
from tester_spin.models import Game
from tester_spin.providers.ka_gaming.runtime import refresh_signing_profile
from test_ka_rmp_execution import CLIENT


def test_refresh_reads_current_launcher_instead_of_stale_cached_build(tmp_path):
    old=tmp_path/'runtime';old.mkdir();(old/'game.min.2070.js').write_text(CLIENT)
    current=CLIENT.replace('2070','2071').replace('I9e','H9e').replace('w4d','v4d').replace('PXh','NXh')
    http=MagicMock()
    http.get.side_effect=[MagicMock(status_code=200,text='script.src="game.min.2071.js"'),MagicMock(status_code=200,text=current)]
    game=Game('ka_gaming','example','Example','https://gamesdemo.kaga88.com/?g=Example&p=demo')
    profile=refresh_signing_profile(game,http=http,root=tmp_path,timeout_s=1,stop_event=threading.Event(),progress=lambda _:None)
    assert profile[:2]==('2071','1.0.266 (2071)')
    assert http.get.call_count==2
    assert http.get.call_args.args[0].endswith('game.min.2071.js')
