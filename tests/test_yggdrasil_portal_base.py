import json,copy
from pathlib import Path
from tester_spin.providers.yggdrasil.runtime import ordinary_round
F=json.loads((Path(__file__).parent/'fixtures/yggdrasil_portal_base.json').read_text())
def test_current_config_and_neutral_portal_state_prove_base():
 c={**F['constraints'],'portal_definition':F['declared']}
 assert ordinary_round({'bets':[copy.deepcopy(F['bet'])]},c)
def test_active_portal_or_mismatched_declared_reward_is_not_base():
 c={**F['constraints'],'portal_definition':F['declared']}
 for path in ('portalSpinsLeft','portalSpinsAwarded','lastChangeOfWinWays'):
  b=copy.deepcopy(F['bet']);b['eventdata']['response']['clientData']['gameStateAtSpinEnd'][path]=1
  assert not ordinary_round({'bets':[b]},c)
 b=copy.deepcopy(F['bet']);b['eventdata']['response']['clientData']['extraFreeSpins']+=1
 assert not ordinary_round({'bets':[b]},c)
