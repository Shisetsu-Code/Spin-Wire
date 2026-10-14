import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import wager_state,validate_start,ordinary_round
ROW=json.loads(Path('tests/fixtures/yggdrasil_classic_wire.json').read_text())
def state(row):return wager_state({'code':0,'data':{'wager':row}})
TEMPLATE={'coin':'0.004','coins':'25','amount':'0.1','lines':'1'*25}
def test_classic_echoed_bet_and_flat_base_outcome_are_recognized():
    validate_start(state(ROW),TEMPLATE)
    assert ordinary_round(state(ROW))
def test_missing_purchase_ack_or_wrong_bet_is_not_accepted():
    with pytest.raises(ValueError):validate_start(state(ROW),{**TEMPLATE,'cmd':'BB1'})
    row=deepcopy(ROW);row['bets'][0]['betdata']['nCoins']=1
    with pytest.raises(ValueError):validate_start(state(row),TEMPLATE)
def test_unknown_pending_state_or_invalid_collection_blocks_base():
    for key,value in [('choice',{'available':[1,2]}),('freeSpins',True),('cardsCollection',{'pending':True})]:
        row=deepcopy(ROW);row['bets'][0]['eventdata'][key]=value
        assert not ordinary_round(state(row))


def test_classic_zero_cost_collect_preserves_line_wager_and_currency():
    from tester_spin.providers.yggdrasil.runtime import collect_request,validate_transition
    rows=json.loads(Path('tests/fixtures/yggdrasil_classic_collect.json').read_text());before,after=map(state,rows)
    request=collect_request(before)
    validate_transition(before,after,request)
    for field,value in [('betamount','0.10'),('betcurrency','USD')]:
        row=deepcopy(rows[1]);row['bets'][0][field]=value
        with pytest.raises(ValueError):validate_transition(before,state(row),request)


def test_flat_movement_rejects_malformed_board_without_raising():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=deepcopy(ROW['bets'][0]['eventdata'])
    ed['reels']=None
    ed['spinData']={'featuresOutputs':{'movingSymbol':{'positionBefore':{'reel':0,'row':0},'positionAfter':{'reel':0,'row':0}}},'multiplier':1}
    assert not ordinary_flat_event(ed)

def test_classic_start_rejects_foreign_currency_and_nonfinite_stake():
    for field,value in [('betcurrency','USD'),('betamount','NaN')]:
        row=deepcopy(ROW);row['bets'][0][field]=value
        with pytest.raises(ValueError):validate_start(state(row),TEMPLATE)

def test_classic_empty_cmd_can_echo_initial_balance_without_leaking_it():
    from tester_spin.providers.yggdrasil.classic_wire import echoed_base_bet
    row={'betamount':'0.2','betcurrency':'EUR','betdata':{'coin':'0.01','cmd':'','ncoins':20,'accC':0,'accWa':'0','initialBalance':'1000'}}
    assert echoed_base_bet(row,{'coin':'0.01','coins':'20','amount':'0.2'})
    row['betdata']['initialBalance']='NaN'
    assert not echoed_base_bet(row,{'coin':'0.01','coins':'20','amount':'0.2'})

def test_classic_ncoins_echo_proves_current_basic_stake_without_line_echo():
    from tester_spin.providers.yggdrasil.classic_wire import echoed_base_bet
    row={'betamount':'0.1','betcurrency':'EUR','betdata':{'coin':'0.002','cmd':'','ncoins':50,'accC':0,'accWa':'0','initialBalance':'1000'}}
    template={'coin':'0.002','coins':'50','amount':'0.1','lines':'1'*65}
    assert echoed_base_bet(row,template)
    row['betdata']['ncoins']=49
    assert not echoed_base_bet(row,template)

def test_compact_ncoins_wager_collect_preserves_stake_reference():
    from tester_spin.providers.yggdrasil.runtime import collect_request,validate_transition
    rows=json.loads(Path('tests/fixtures/yggdrasil_classic_collect.json').read_text());before,after=map(state,rows)
    root=before['bets'][0];old=root['betdata']
    root['betdata']={'cmd':'','coin':old['coin'],'ncoins':old['nCoins'],'accWa':'0','accC':0,'initialBalance':'1000'}
    request=collect_request(before)
    validate_transition(before,after,request)
    after['bets'][0]['betdata']['nCoins']=1
    with pytest.raises(ValueError):validate_transition(before,after,request)


def test_winning_compact_echo_allows_only_collect_command_metadata():
    from tester_spin.providers.yggdrasil.classic_wire import echoed_base_bet
    row={'betamount':'0.1','betcurrency':'EUR','betdata':{'coin':'0.002','cmd':'','ncoins':50,'accC':20,'accWa':'0.04','cmds':'C'}}
    template={'coin':'0.002','coins':'50','amount':'0.1','lines':'1'*65}
    assert echoed_base_bet(row,template)
    for commands in ['BUY_A_BONUS','C,*',['C','Finished'],{'cmd':'C'}]:
        row['betdata']['cmds']=commands
        assert not echoed_base_bet(row,template)


@pytest.mark.parametrize('win',[[1,15,'100000000000000'],[1,3,'100000000000000','0.09',9],[4,10,'100000000000000','0.02',10,'0.02'],[8,12,'100000000000000','0.06',{'waysAmount':1,'oakIndex':3,'coinsPerWay':12,'cashPerWay':'0.06','icon':'HIGH_4'}]])
def test_known_classic_win_vectors_and_collect_signal(win):
    from tester_spin.providers.yggdrasil.classic_wire import classic_win
    assert classic_win(win,15)
    bad=deepcopy(win);bad[2]='1'*14
    assert not classic_win(bad,15)
    bad=deepcopy(win);bad[0]=True
    assert not classic_win(bad,15)

def test_flat_base_outcome_accepts_only_collect_as_optional_command():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=deepcopy(ROW['bets'][0]['eventdata']);ed['nextCmds']='C'
    assert ordinary_flat_event(ed)
    ed['nextCmds']='BUY_A_BONUS'
    assert not ordinary_flat_event(ed)


def test_neutral_sticky_multiplier_does_not_mean_pending_feature():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_neutral_sticky_multiplier.json').read_text())
    assert ordinary_flat_event(event)
    for key,value in [('grandTotal',1),('multiplier',2),('multiplier',True),('unknownAward',0)]:
        bad=deepcopy(event);bad[key]=value
        assert not ordinary_flat_event(bad)


def test_empty_heads_do_not_create_a_free_spin_round():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_neutral_heads.json').read_text())
    assert ordinary_flat_event(event)
    for key,value in [('blueHeadsAfter',1),('fsBetAmount','0.2'),('ReelSetConfig',[1,1,1,1,1]),('unknown',0)]:
        bad=deepcopy(event);bad[key]=value
        assert not ordinary_flat_event(bad)


def test_unawarded_jackpot_display_is_bound_to_current_currency_and_stake():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_neutral_jackpot_display.json').read_text())
    constraints={'currency':'EUR','basic_amount':'0.2'}
    assert not ordinary_flat_event(event)
    assert ordinary_flat_event(event,constraints)
    for key,value in [('accWaWithJackpot','1'),('betAmountCache','0.4'),('unknownAward',0)]:
        bad=deepcopy(event);bad[key]=value
        assert not ordinary_flat_event(bad,constraints)
    bad=deepcopy(event);bad['jackpot']['currency']='USD'
    assert not ordinary_flat_event(bad,constraints)


def test_three_field_blocks_are_bounded_rendering_metadata():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_lucky_neko_geometry.json').read_text())
    assert ordinary_flat_event(event)
    for key,value in [('blockSize',99),('reelIndex',99),('startRow',99),('pending',False)]:
        bad=deepcopy(event);bad['blockDetails'][0][key]=value
        assert not ordinary_flat_event(bad)


def test_split_and_synced_reels_match_declared_way_geometry():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_syncronite_geometry.json').read_text())
    assert ordinary_flat_event(event)
    for damage in ['ways','reel','rows','command']:
        bad=deepcopy(event)
        if damage=='ways':bad['winWays']+=1
        elif damage=='reel':bad['syncedReelsDetail']['startReelIndex']=99
        elif damage=='rows':bad['splitzDetail']['reelIndexesToRevealedRowsCounts']['99']=5
        else:bad['freeSpinsAwarded']=1
        assert not ordinary_flat_event(bad)


def test_complete_board_can_omit_strip_stop_offsets():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_nullable_stops.json').read_text())
    assert ordinary_flat_event(event)
    for value in [[],True,'unknown',[-1]*5]:
        bad=deepcopy(event);bad['rpos']=value
        assert not ordinary_flat_event(bad)
    bad=deepcopy(event);bad['unknownContinuation']='C'
    assert not ordinary_flat_event(bad)


def test_alternate_base_reel_series_remain_base_only():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_block_alternate_base_reels.json').read_text())
    assert ordinary_flat_event(event)
    bad=deepcopy(event);bad['reelDetails']['0']['reelName']='freeReels2'
    assert not ordinary_flat_event(bad)


def test_initial_collectable_win_has_no_double_already_in_progress():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_optional_collect_board.json').read_text())
    assert ordinary_flat_event(event,{"basic_coin":"0.01"})
    for key,value in [('doubleCount',2),('doubleAmount','999'),('superBet',True),('nextCmds','C,UNKNOWN')]:
        bad=deepcopy(event);bad[key]=value
        assert not ordinary_flat_event(bad,{"basic_coin":"0.01"})


def test_unawarded_feature_lists_and_identity_symbol_map_are_base():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_unawarded_features.json').read_text())
    assert ordinary_flat_event(event,{"basic_coin":"0.004"})
    for key,value in [('initialFreeSpins',1),('remainingFeatures',['unknown']),('goldenbet',True),('awardFromTwoScatters',{})]:
        bad=deepcopy(event);bad[key]=value
        assert not ordinary_flat_event(bad,{"basic_coin":"0.004"})
    bad=deepcopy(event);bad['iconMapping']['Wild']='Freespin'
    assert not ordinary_flat_event(bad,{"basic_coin":"0.004"})


def test_positive_coin_only_win_requires_current_stake_basis():
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    event=json.loads(Path('tests/fixtures/yggdrasil_classic_optional_collect_board.json').read_text())
    assert not ordinary_flat_event(event)
    assert not ordinary_flat_event(event,{'basic_coin':'0.02'})
    bad=deepcopy(event);bad['accC']+=1
    assert not ordinary_flat_event(bad,{'basic_coin':'0.01'})

def test_level_progress_is_ordinary_only_without_award_or_level_change():
    import json
    from pathlib import Path
    from copy import deepcopy
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_level_progress.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed)
    for field,value in [("levelIncreased",True),("lastBet",0),("superMode",True),("currentLevel",2),("mysteryWin",1),("spinsMade",0),("gridSnapshot","1"*20)]:
        bad=deepcopy(ed);bad["gameState"][field]=value
        assert not ordinary_flat_event(bad),field
    bad=deepcopy(ed);bad["gameState"]["unknownCommand"]="PLAY"
    assert not ordinary_flat_event(bad)

def test_rectangular_symbol_is_geometry_not_a_bonus():
    import json
    from pathlib import Path
    from copy import deepcopy
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_rectangular_symbol.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed)
    for field,value in [("start",-1),("end",999),("sym",""),("start",True)]:
        bad=deepcopy(ed);bad["blox"][field]=value
        assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["reelSet"]="FreeSpinsReels"
    assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["bonusAwarded"]=True
    assert not ordinary_flat_event(bad)

def test_rectangular_reel_name_must_be_string():
    import json
    from pathlib import Path
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_rectangular_symbol.json").read_text(encoding="utf-8"))
    ed["reelSet"]=[]
    assert not ordinary_flat_event(ed)

def test_selected_bet_and_gathered_wins_are_persistent_progress():
    import json
    from pathlib import Path
    from copy import deepcopy
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_level_progress_win.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed,{"basic_coin":"0.01"})
    bad=deepcopy(ed);bad["gameState"]["coinsWon"]+=1
    assert not ordinary_flat_event(bad,{"basic_coin":"0.01"})
    bad=deepcopy(ed);bad["gameState"]["levelIncreased"]=True
    assert not ordinary_flat_event(bad,{"basic_coin":"0.01"})

def test_symbol_replacement_is_bound_to_final_board():
    import json
    from pathlib import Path
    from copy import deepcopy
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_symbol_replacement.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed)
    for replacement in ({"999":"HIGH_3"},{"-1":"HIGH_3"},{"16":True},{"16":"FOREIGN_ICON"},{"016":"HIGH_3"}):
        bad=deepcopy(ed);bad["replaceIcons"]=replacement
        assert not ordinary_flat_event(bad)

def test_multiplier_accumulator_does_not_award_a_bonus_by_itself():
    import json
    from pathlib import Path
    from copy import deepcopy
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_level_progress.json").read_text(encoding="utf-8"))
    ed["gameState"]["currentMultiplier"]=3
    assert ordinary_flat_event(ed)
    bad=deepcopy(ed);bad["gameState"]["currentMultiplier"]=True
    assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["previousGameState"]["currentMultiplier"]=4
    assert not ordinary_flat_event(bad)

def test_empty_shards_and_quoted_jackpot_values_are_not_awards():
    import json
    from pathlib import Path
    from copy import deepcopy
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_empty_shards.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed)
    bad=deepcopy(ed);bad["shardCounter"]["count"][0]=1
    assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["shardCounter"]["a"][0][0]=1
    assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["jpPlayerValue1"]="-1"
    assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["shardsAwarded"]="S1"
    assert not ordinary_flat_event(bad)

def test_empty_shards_need_positive_advertised_jackpot_prices():
    import json
    from pathlib import Path
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_empty_shards.json").read_text(encoding="utf-8"))
    ed["jpValue1"]=ed["jpPlayerValue1"]=0
    assert not ordinary_flat_event(ed)

def test_split_symbols_and_display_prizes_have_typed_geometry():
    import json
    from copy import deepcopy
    from pathlib import Path
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_split_symbol_values.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed)
    for field,value in (("column",99),("symbolsCount",True),("symbol","FOREIGN")):
        bad=deepcopy(ed);bad["splitFields"][0][field]=value;assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["allBonusAmountsInMoney"]["CONTINUE"]="1"
    assert not ordinary_flat_event(bad)

def test_empty_feature_data_with_unchanged_jackpots_is_base():
    import json
    from copy import deepcopy
    from pathlib import Path
    from tester_spin.providers.yggdrasil.classic_wire import ordinary_flat_event
    ed=json.loads(Path(__file__).with_name("fixtures").joinpath("yggdrasil_inactive_jackpot_features.json").read_text(encoding="utf-8"))
    assert ordinary_flat_event(ed)
    bad=deepcopy(ed);bad["spinData"]["featuresData"]={"scattersFreeSpins":{"gameMode":"FREE_SPINS"}}
    assert not ordinary_flat_event(bad)
    bad=deepcopy(ed);bad["spinData"]["bonusWon"]["cash"]="1"
    assert not ordinary_flat_event(bad)
