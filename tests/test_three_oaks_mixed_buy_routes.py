from pathlib import Path
from tester_spin.providers.three_oaks.client_contracts import client_contract
root=Path(__file__).parent/'fixtures'
def source():return (root/'three_oaks_mixed_buy_routes.js').read_text(encoding='utf-8')
def test_known_finite_route_survives_unresolved_alternative():
 profile=client_contract(source(),data={'context':{'available_buy_bonus':[1,2,3]}})
 assert profile['purchase_modes']==[1,2,3]
 assert profile['purchase_selector_type']=='number'
def test_unresolved_route_does_not_extend_known_ui_domain():
 profile=client_contract(source(),data={'context':{'available_buy_bonus':[1,2,3,4]}})
 assert profile['purchase_modes']==[1,2,3]
 assert 4 not in profile['purchase_ui_modes']
def test_no_finite_route_means_the_mixed_contract_remains_pending():
 profile=client_contract(source().replace('[0,1,2].includes(t)','allowed(t)'),data={'context':{'available_buy_bonus':[1,2,3]}})
 assert profile['purchase_modes']==[]

def test_all_accepted_har_actions_match_the_composed_contract():
 import copy,json
 from tester_spin.providers.three_oaks.runtime import play_fields,continuation_fields
 steps=json.loads((root/'three_oaks_mixed_buy_rounds.json').read_text(encoding='utf-8'))
 before=steps[0]['context'];settings={};profile=client_contract(source(),data={'context':before})
 purchases=[]
 for step in steps:
  settings=step['settings'] or settings
  data={'context':copy.deepcopy(before),'settings':settings};action=step['action']
  if action['name'] in ('spin','buy_spin'):
   # These values come from the captured UI controls, which the user changed between spins.
   data['context'][data['context']['current']].update({k:v for k,v in action['params'].items() if k in ('bet_per_line','lines')})
   actual=play_fields(data,action['name'],action['params'].get('selected_mode'),client_profile=profile)
   if action['name']=='buy_spin':purchases.append(action['params']['selected_mode'])
  else:actual=continuation_fields(data,game_slug='unseen',family='kendoo',client_profile=profile)
  assert actual and actual['action']==action
  before=step['context']
 assert sorted(purchases)==[1,2,3]
 assert before['round_finished'] and before['current']=='spins'
