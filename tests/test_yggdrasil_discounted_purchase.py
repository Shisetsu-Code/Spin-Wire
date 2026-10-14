import json
from copy import deepcopy
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.runtime import configuration, DemoRuntime, Unsupported

DATA=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_discounted_purchase.json").read_text(encoding="utf-8"))

def configured():return configuration(deepcopy(DATA),str(DATA.get("gameid",DATA.get("gameId"))),"EUR")

def test_discount_prices_are_variants_of_one_purchase():
    cfg=configured()
    assert cfg["purchase_variants"]["BUY_A_BONUS"]["BUY_A_BONUS_20"]["discount_percent"]==20
    assert len(cfg["modes"])==4
    assert set(k for k in cfg["modes"] if cfg["mode_kinds"][k]=="PURCHASE")=={"BUY_A_BONUS","MAX_BUY_A_BONUS"}
    assert cfg["wire_modes"]["BUY_A_BONUS_20"]["coinsPerBet"]==1600

@pytest.mark.parametrize("progress,command",[({},"BUY_A_BONUS"),({"0.01000":20},"BUY_A_BONUS_20"),({"0.02000":40},"BUY_A_BONUS")])
def test_current_progress_selects_wire_price(progress,command):
    runtime=DemoRuntime(None,"fixture",5,None,gate=None);runtime.config=configured()
    calls=[]
    def call(fn,body=None,query=None):
        calls.append((fn,body,query));return {"code":0,"data":{"initialized":True,"playerState":{"bonusProgress":progress}}}
    runtime.call=call
    template=runtime.paid_template("BUY_A_BONUS")
    assert calls==[("info",None,{"org":"Demo","currency":"EUR","what":"playerState"})]
    assert template["cmd"]==command
    assert template["amount"]==runtime.config["purchase_variants"]["BUY_A_BONUS"][command]["template"]["amount"]

@pytest.mark.parametrize("progress",[{"0.01000":True},{"0.01000":-10},{"0.01000":100},{"0.01000":15},{"0.01":20},{"0.01000":"20"}])
def test_unrecognized_state_cannot_send_paid_purchase(progress):
    runtime=DemoRuntime(None,"fixture",5,None,gate=None);runtime.config=configured()
    runtime.call=lambda *a,**k:{"code":0,"data":{"initialized":True,"playerState":{"bonusProgress":progress}}}
    with pytest.raises(Unsupported):runtime.paid_template("BUY_A_BONUS")

def test_non_discount_domain_not_folded():
    d=deepcopy(DATA)
    for p in d["cfg"]["props"]:
        if p["prop"]=="Modes":
            modes=json.loads(p["value"]) if isinstance(p["value"],str) else p["value"]
            modes["BUY_A_BONUS_20"]["coinsPerBet"]=1900;p["value"]=modes
    cfg=configuration(d,str(d.get("gameid",d.get("gameId"))),"EUR")
    assert "BUY_A_BONUS_20" in cfg["unresolved"]
    assert "BUY_A_BONUS_20" not in cfg["templates"]

def test_old_price_variants_are_archived_without_losing_sample_quota(tmp_path):
    from tester_spin.models import GameTestResult
    from tester_spin.coverage_history import retain_pending_branches
    from tester_spin.providers.yggdrasil.discounted_purchase import SOURCE
    prior={"id":"BUY_A_BONUS_20","kind":"PURCHASE","coverage_required":True,"required_options":["BUY_A_BONUS_20"],"required_samples":3,"historical_source":"old"}
    (tmp_path/"coverage-history.json").write_text(json.dumps({"provider":"yggdrasil","slug":"fixture","pending":{"BUY_A_BONUS_20":prior,"REAL_OTHER_BUY":dict(prior,id="REAL_OTHER_BUY",required_options=["REAL_OTHER_BUY"])}}))
    result=GameTestResult(provider="yggdrasil",slug="fixture",game_name="Fixture",symbol="fixture",game_url="https://example.test",requested_spins=1,successful_spins=1,failed_spins=0,status="OK")
    result.feature_domains={"purchase":{"complete":True,"source":SOURCE,"options":["BUY_A_BONUS","MAX_BUY_A_BONUS"]}}
    result.discovered_modes=[{"id":"BUY_A_BONUS","kind":"PURCHASE","source":"server.game.cfg.Modes","server_declared":True,"price_variants":configured()["purchase_variants"]["BUY_A_BONUS"],"coverage_required":True,"required_options":["BUY_A_BONUS"],"covered_options":["BUY_A_BONUS"],"required_samples":1,"sample_counts":{"BUY_A_BONUS":1}}]
    retain_pending_branches(tmp_path,result)
    history=json.loads((tmp_path/"coverage-history.json").read_text())
    assert "BUY_A_BONUS_20" not in history["pending"]
    assert "REAL_OTHER_BUY" in history["pending"]
    assert history["pending"]["BUY_A_BONUS"]["required_samples"]==3
    assert history["policy_migrations"][0]["previous"]==prior

def test_subsequent_player_state_has_no_initialized_flag():
    from tester_spin.providers.yggdrasil.discounted_purchase import selected_price
    template,_=selected_price(configured()["purchase_variants"]["BUY_A_BONUS"],{"data":{"playerState":{"bonusProgress":{}}}},"0.01")
    assert template["cmd"]=="BUY_A_BONUS"
