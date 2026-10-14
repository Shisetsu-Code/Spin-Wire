import copy,json
from pathlib import Path
import pytest
from tester_spin.providers.yggdrasil.runtime import ordinary_round
ROWS=json.loads((Path(__file__).parent/'fixtures/yggdrasil_round_family.json').read_text())
@pytest.mark.parametrize('row',ROWS,ids=lambda r:r['slug']+('-active' if r['active'] else '-base'))
def test_common_round_contract_distinguishes_base_and_award(row):
 b=copy.deepcopy(row['bet']);c={'basic_amount':b['betdata']['cashBet'],'basic_coin':b['betdata']['coin'],'sdk_mode_profile':'sdk.dynamicModes/defaultBuy/excludedGolden/v1'}
 assert ordinary_round({'bets':[b]},c) is (not row['active'])
def test_unacknowledged_award_or_money_mismatch_never_proves_base():
 row=next(v for v in ROWS if not v['active']);b=copy.deepcopy(row['bet']);c={'basic_amount':b['betdata']['cashBet'],'basic_coin':b['betdata']['coin'],'sdk_mode_profile':'sdk.dynamicModes/defaultBuy/excludedGolden/v1'}
 b['eventdata']['response']['clientData']['Completed']=False
 assert not ordinary_round({'bets':[b]},c)
 b=copy.deepcopy(row['bet']);b['eventdata']['response']['cashWin']='999'
 assert not ordinary_round({'bets':[b]},c)

def test_one_based_line_and_saved_bet_grid_are_metadata():
 row=next(v for v in ROWS if v['slug']=='bloody-pesos' and v['bet']['eventdata']['response']['clientData']['Round']['VISData']['Prizes']);b=copy.deepcopy(row['bet']);cd=b['eventdata']['response']['clientData'];cd['Round']['VISData']['Prizes'][0]['Line']=cd['Bet']['Lines']
 event=next(v for v in cd['Round']['VISData']['Events'] if v['Type']==201)
 next(iter(event['StatesPerBet'].values()))['LastGrid'][0][0]+=1
 c={'basic_amount':b['betdata']['cashBet'],'basic_coin':b['betdata']['coin'],'sdk_mode_profile':'sdk.dynamicModes/defaultBuy/excludedGolden/v1'}
 assert ordinary_round({'bets':[b]},c)
def test_symbol_display_uses_flat_index():
 row=next(v for v in ROWS if v['slug']=='your-own-island' and not v['active']);b=copy.deepcopy(row['bet']);vis=b['eventdata']['response']['clientData']['Round']['VISData'];event=next(v for v in vis['Events'] if v['Type']==302);event['SymbolsInfo']=[[sum(map(len,vis['Grids'][0]))-1,0,600,30]]
 c={'basic_amount':b['betdata']['cashBet'],'basic_coin':b['betdata']['coin'],'sdk_mode_profile':'sdk.dynamicModes/defaultBuy/excludedGolden/v1'}
 assert ordinary_round({'bets':[b]},c)
 event['SymbolsInfo'][0][0]+=1
 assert not ordinary_round({'bets':[b]},c)
