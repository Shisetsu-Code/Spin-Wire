import sys
from pathlib import Path

from tester_spin.providers.three_oaks.code_primitives import runner_spin_contract
FIXTURE=(Path(__file__).parent/'fixtures'/'three_oaks_shared_runner.js').read_text(encoding='utf-8')
INIT='window._PROVIDER.game={name:"fixture",use:["protocol","ui"]};'
def test_parenthesized_forwarder_keeps_certified_normal_spin():
    source=FIXTURE.replace('.on(function(e){return s.A.game.play(e.data)})','.on((function(e){return s.A.game.play(e.data)}))')
    profile=runner_spin_contract(source,INIT)
    assert profile is not None
    assert profile['spin_route']=='shared-runner-button'
    assert profile['spin_params']==['bet_per_line','lines']
def test_parenthesized_forwarder_does_not_override_custom_play():
    source=FIXTURE.replace('.on(function(e){return s.A.game.play(e.data)})','.on((function(e){return s.A.game.play(e.data)}))')
    assert runner_spin_contract(source,INIT.replace('"ui"','"custom_play"')) is None
def test_bound_forwarder_with_preassigned_event_is_not_certified():
    source=FIXTURE.replace('.on(function(e){return s.A.game.play(e.data)})','.on((function(e){return s.A.game.play(e.data)}).bind(null,{data:{action:{name:"buy_spin",params:{}}}}))')
    assert runner_spin_contract(source,INIT) is None
def test_immediately_invoked_forwarder_is_not_certified():
    source=FIXTURE.replace('.on(function(e){return s.A.game.play(e.data)})','.on((function(e){return s.A.game.play(e.data)})(anotherEvent))')
    assert runner_spin_contract(source,INIT) is None
