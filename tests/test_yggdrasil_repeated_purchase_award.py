import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import configuration,continuation_request,Unsupported
B=json.loads((Path(__file__).parent/'fixtures/yggdrasil_repeated_purchase_award.json').read_text(encoding='utf-8'))
def config():
 data={'gameid':'fixture','cfg':{'props':[{'prop':'ApiVersion','value':'2.6.0'},{'prop':'Modes','value':{'BASIC':{'coinsPerBet':1},'BUYBONUS':{'coinsPerBet':1}}},{'prop':'Config','value':{'initialBoard':[[1,1,1]]*6}}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.2'},'extraOrgSettings':[{'type':'BUYBONUS','Denoms':'EUR:20'}]}
 return configuration(data,'fixture','EUR')['ordinary_constraints']
def state():return {'commands':['BUYBONUS','GAMBLE'],'bets':[deepcopy(B)],'terminal':False,'wagerid':'fixture-round','max_step':1,'root_step':1}
def test_awarded_purchase_is_continued_without_new_stake():
 request=continuation_request(state(),config())
 assert request=={'cmd':'BUYBONUS','type':'bonus','amount':'0','wagerid':'fixture-round','step':'2','betid':'1'}
@pytest.mark.parametrize('change',['no_award','no_buy','price','command','schema','missing_quote'])
def test_unproved_purchase_continuation_stays_partial(change):
 s=state();c=config();b=s['bets'][0]
 if change=='no_award':b['eventdata']['playerState']['freespinsRemaining']=0
 elif change=='no_buy':b['eventdata']['playerState']['buyBonus']=False
 elif change=='price':b['betamount']='21'
 elif change=='command':s['commands'].append('OTHER')
 elif change=='schema':b['eventdata']['response']['clientData']['unknown']=True
 else:c.pop('purchase_quotes',None)
 with pytest.raises(Unsupported):continuation_request(s,c)


def active_state():
 s=state();s['bets']=[json.loads((Path(__file__).parent/'fixtures/yggdrasil_purchased_spin.json').read_text(encoding='utf-8'))];s['commands']=['BUYBONUS'];s['max_step']=2
 return s

def test_active_purchase_continues_current_awarded_counter():
 req=continuation_request(active_state(),config())
 assert req=={'cmd':'BUYBONUS','type':'bonus','amount':'0','wagerid':'fixture-round','step':'3','betid':'1'}

@pytest.mark.parametrize('change',['count','initial_count','accrual'])
def test_purchased_transition_rejects_counter_or_cash_inconsistency(change):
 from tester_spin.providers.yggdrasil.runtime import validate_transition
 before=state();after=active_state();b=after['bets'][0]
 if change=='count':b['eventdata']['playerState']['freespinsRemaining']=6
 elif change=='initial_count':b['eventdata']['initialPlayerState']['freespinsRemaining']=7
 else:b['eventdata']['accWa']='1.00';b['betdata']['accWa']='1.00'
 with pytest.raises(Unsupported):validate_transition(before,after,continuation_request(before,config()),config())

def test_actual_purchased_transition_conserves_counter_and_cash():
 from tester_spin.providers.yggdrasil.runtime import validate_transition
 before=state();after=active_state()
 validate_transition(before,after,continuation_request(before,config()),config())


def test_paid_cascade_may_keep_returned_column_height_after_growth():
 from tester_spin.providers.yggdrasil.repeated_purchase_award import active_spin
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_purchased_height_plateau.json').read_text(encoding='utf-8'))
 assert active_spin(bet,config())
 frames=bet['eventdata']['response']['clientData']['boards']
 frames[-1]['board'][0].pop()
 frames[-1]['total_ways']=__import__('math').prod(map(len,frames[-1]['board']))
 bet['eventdata']['playerState']['heights']=list(map(len,frames[-1]['board']))
 assert not active_spin(bet,config())


def test_purchased_cascade_uses_returned_multiplier_progress_and_already_paid_cash():
 from tester_spin.providers.yggdrasil.repeated_purchase_award import active_spin
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_purchased_multipliers.json').read_text(encoding='utf-8'))
 assert active_spin(bet,config())
 bet['eventdata']['response']['cashWin']='3.28'
 assert not active_spin(bet,config())

@pytest.mark.parametrize('change',['jump','final'])
def test_unexplained_multiplier_progress_is_rejected(change):
 from tester_spin.providers.yggdrasil.repeated_purchase_award import active_spin
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_purchased_multipliers.json').read_text(encoding='utf-8'))
 if change=='jump':bet['eventdata']['response']['clientData']['boards'][0]['multiplier']=100
 else:bet['eventdata']['playerState']['multiplier']=100
 assert not active_spin(bet,config())
