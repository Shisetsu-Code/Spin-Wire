import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import ordinary_round
BETS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_side_ledgers.json').read_text(encoding='utf-8'))
CONSTRAINTS={'currency':'EUR','basic_amount':'0.20','basic_coin':'0.01'}
@pytest.mark.parametrize('bet',BETS)
def test_base_rounds_conserve_both_sides_and_total(bet):
 assert ordinary_round({'bets':[bet]},CONSTRAINTS)
@pytest.mark.parametrize('change',['price','root_cash','side_coins','event_cash','coordinate','hidden','award','unknown'])
def test_unproved_price_award_effect_or_ledger_is_rejected(change):
 bet=deepcopy(BETS[0]);ed=bet['eventdata'];response=ed['response'];cd=response['clientData'];reels=cd['rounds'][0]['reels']
 if change=='price':bet['betamount']='0.21'
 elif change=='root_cash':response['cashWin']='0.09'
 elif change=='side_coins':reels['winRight']=9
 elif change=='event_cash':reels['eventsRight'][0]['winCash']=0.09
 elif change=='coordinate':reels['eventsRight'][0]['coords'][0]['x']=99
 elif change=='hidden':reels['hidden']=[1]
 elif change=='award':ed['boostData']['isWinFreeSpins']=True
 else:reels['unknownEffect']=True
 assert not ordinary_round({'bets':[bet]},CONSTRAINTS)


@pytest.mark.parametrize('change',['replacement','persistent','unreported_board'])
def test_hidden_reveals_must_explain_the_exact_returned_board(change):
 bet=deepcopy(next(b for b in BETS if b['eventdata']['response']['clientData']['rounds'][0]['reels']['hidden']))
 reels=bet['eventdata']['response']['clientData']['rounds'][0]['reels']
 if change=='replacement':reels['hidden'][0]['changeTo']='UNDECLARED_REPLACEMENT'
 elif change=='persistent':reels['hidden'][0]['persistent']=True
 else:reels['positions'][0][0]='UNEXPLAINED_CHANGE'
 assert not ordinary_round({'bets':[bet]},CONSTRAINTS)


def test_current_paid_round_can_retain_explained_winning_reveals_until_collect():
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_side_winning_persistence.json').read_text(encoding='utf-8'))
 assert ordinary_round({'bets':[bet]},CONSTRAINTS)
 bet['eventdata']['response']['clientData']['rounds'][0]['reels']['hidden'][0]['persistent']='yes'
 assert not ordinary_round({'bets':[bet]},CONSTRAINTS)


@pytest.mark.parametrize('change',['missing_respin','carryover','accrual'])
def test_paid_respin_sequence_must_preserve_retained_symbols_and_close(change):
 bet=json.loads((Path(__file__).parent/'fixtures/yggdrasil_side_winning_persistence.json').read_text(encoding='utf-8'))
 frames=bet['eventdata']['response']['clientData']['rounds']
 if change=='missing_respin':frames.pop()
 elif change=='carryover':
  hidden=frames[-1]['reels']['hidden'][0];hidden['changeTo']='WRONG'
  frames[-1]['reels']['positions'][hidden['x']][hidden['y']]='WRONG'
 else:frames[-1]['reels']['winSum']=0.03
 assert not ordinary_round({'bets':[bet]},CONSTRAINTS)
