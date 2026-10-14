from tester_spin.providers.pragmatic_observed_transitions import observed_spin_fields, apply_spin_rule
from tester_spin.providers.pragmatic_modes import discover_modes

def test_ra_osiris_keeps_stake_scale_separate_from_wire_lines():
    assert observed_spin_fields('vs15raos')=={'l':'15','ind':'0'}
    init={'l':'10','sc':'0.2,0.4','bls':'10,20','c':'0.2'}
    catalog=discover_modes(init,symbol='vs15raos')
    assert catalog.base_scale==10 and catalog.base_bet==2
    fields={'action':'doSpin','l':'10','c':'0.2','bl':'0'}
    apply_spin_rule(fields,'vs15raos')
    assert fields=={'action':'doSpin','l':'15','c':'0.2','bl':'0','ind':'0'}

def test_zeus_250_uses_observed_olympus_selector():
    assert observed_spin_fields('vs15zeushadseq')=={'l':'15','ind':'1'}

def test_champions_transmits_observed_team_selection_without_bl():
    fields={'action':'doSpin','l':'25','c':'0.08','bl':'0','sInfo':'n'}
    apply_spin_rule(fields,'vs25champ')
    assert fields=={'action':'doSpin','l':'25','c':'0.08','sInfo':'n','prg_i':'7'}
