import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import ordinary_round,configuration

FIXTURE=json.loads((Path(__file__).parent/'fixtures/yggdrasil_growing_ways.json').read_text(encoding='utf-8'))
def constraints():
 data={'gameid':'fixture','cfg':{'props':[{'prop':'ApiVersion','value':'2.6.0'},{'prop':'Modes','value':{'BASIC':{'coinsPerBet':1}}},{'prop':'Config','value':{'initialBoard':FIXTURE['initialBoard']}}]},'orgSettings':{'type':'BASIC','Denoms':'EUR:0.20'}}
 return configuration(data,'fixture','EUR')['ordinary_constraints']

@pytest.mark.parametrize('bet',FIXTURE['bets'])
def test_real_closed_growing_ways_are_ordinary(bet):
 assert ordinary_round({'bets':[bet]},constraints())

@pytest.mark.parametrize('change',['bonus','free','cash','ways','position','shift','unknown','price','missing_geometry'])
def test_unproved_state_price_geometry_or_cash_is_not_ordinary(change):
 bet=deepcopy(next(b for b in FIXTURE['bets'] if len(b['eventdata']['response']['clientData']['boards'])>1));ed=bet['eventdata'];cd=ed['response']['clientData'];cfg=constraints()
 if change=='bonus':cd['bonusTriggered']=True
 elif change=='free':ed['playerState']['freespinsRemaining']=8
 elif change=='cash':ed['response']['cashWin']='0.37'
 elif change=='ways':cd['boards'][0]['total_ways']+=1
 elif change=='position':cd['boards'][0]['winningRows'][0]['positions'][0]['row']=99
 elif change=='shift':cd['boards'][1]['board'][1][0]=4095
 elif change=='unknown':cd['unknownEffect']=True
 elif change=='price':bet['betamount']='0.40'
 else:cfg.pop('growing_ways_geometry',None)
 assert not ordinary_round({'bets':[bet]},cfg)


def test_current_base_round_can_clear_previous_purchase_flag():
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_after_purchase_base.json').read_text(encoding='utf-8'))
 assert ordinary_round({'bets':[bet]},constraints())
 bet['eventdata']['playerState']['buyBonus']=True
 assert not ordinary_round({'bets':[bet]},constraints())


def test_base_cascade_can_announce_multipliers_without_awarding_bonus():
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_base_returned_multipliers.json').read_text(encoding='utf-8'))
 assert ordinary_round({'bets':[bet]},constraints())
 bet['eventdata']['response']['clientData']['boards'][1]['multiplier']=50
 assert not ordinary_round({'bets':[bet]},constraints())


def test_base_clears_previous_bonus_multiplier_and_heights():
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_base_clears_previous_geometry.json').read_text(encoding='utf-8'))
 assert ordinary_round({'bets':[bet]},constraints())
 bet['eventdata']['initialPlayerState']['freespinsRemaining']=1
 assert not ordinary_round({'bets':[bet]},constraints())
