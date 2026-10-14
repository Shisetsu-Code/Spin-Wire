import json
from pathlib import Path
from copy import deepcopy
import pytest
from tester_spin.providers.yggdrasil.runtime import ordinary_round
DATA=json.loads(Path('tests/fixtures/yggdrasil_outcome_families.json').read_text())
def ordinary(cd):
    # These fixtures classify DTO grammar, not a paid wager. BBG execution
    # separately requires its actual envelope and current server definition.
    from tester_spin.providers.yggdrasil.bbg_cascades import ordinary_dto
    from tester_spin.providers.yggdrasil.base_game_state import ordinary_closed_flags
    if ordinary_dto(cd):return ordinary_closed_flags(cd)
    return ordinary_round({'bets':[{'eventdata':{'response':{'clientData':cd}}}]})
@pytest.mark.parametrize('key',DATA)
def test_observed_ordinary_families(key):assert ordinary(DATA[key])
@pytest.mark.parametrize('key',DATA)
def test_unknown_control_is_not_ignored(key):
    cd=deepcopy(DATA[key]);cd['pendingChoices']=[1,2]
    assert not ordinary(cd)
def test_advertised_free_spins_are_not_ordinary():
    cd=deepcopy(DATA['structured_no_award']);cd['freeSpinsAwarded']=8
    assert not ordinary(cd)
def test_collection_award_is_not_ordinary():
    cd=deepcopy(DATA['persistent_collectibles']);cd['collections']['userWonFreespins']=True
    assert not ordinary(cd)
def test_symbol_animation_requires_rectangular_unique_positions():
    cd=deepcopy(DATA['symbol_actions']);cd['actions'][1]['symbols'].append(cd['actions'][1]['symbols'][0])
    assert not ordinary(cd)

@pytest.mark.parametrize('name', ['MAX_BUY_A_BONUS','SUPER_BUY_BONUS','BUYBONUS','BUYMAXBONUS'])
def test_explicit_purchase_mode_names(name):
    from tester_spin.providers.yggdrasil.protocol import mode_kind
    assert mode_kind(name)=='PURCHASE'
@pytest.mark.parametrize('name',['GOLDENBET','GOLDEN_BET_WILD'])
def test_explicit_golden_bet_mode_names(name):
    from tester_spin.providers.yggdrasil.protocol import mode_kind
    assert mode_kind(name)=='ANTE_BET'
@pytest.mark.parametrize('name',['GB','BONUS1','BUYER','MAX_BUY_A_BONUS_PENDING','GOLDEN_BET_CHOICE'])
def test_unknown_mode_names_are_not_inferred(name):
    from tester_spin.providers.yggdrasil.protocol import mode_kind
    assert mode_kind(name)=='UNKNOWN_FEATURE'

@pytest.mark.parametrize('field,value',[('finished',False),('nextActions',['Spin','Choose']),('gameModeSet','FreeGame0'),('finalGrid',[[True]])])
def test_numeric_grid_does_not_prove_pending_or_bonus(field,value):
    cd=deepcopy(DATA['numeric_grid']);cd[field]=value
    assert not ordinary(cd)

def test_jackpot_collection_pending_payload_is_not_ignored():
    cd=deepcopy(DATA['jackpot_collections']);first=next(iter(cd['collections'].values()));first['choices']=[1,2]
    assert not ordinary(cd)

@pytest.mark.parametrize('field,value',[('goldenBet',True),('freeSpinsAwarded',5),('gigabloxData',[{'choices':[1,2]}])])
def test_block_board_does_not_ignore_extra_controls(field,value):
    cd=deepcopy(DATA['block_board_modified']);cd[field]=value
    assert not ordinary(cd)

def test_numeric_tiny_positive_win_is_not_zero():
    cd=deepcopy(DATA['numeric_grid']);cd['currentWinnings']='1e-1000'
    assert not ordinary(cd)
def test_block_invalid_columns_return_unknown_without_raising():
    cd=deepcopy(DATA['block_board']);cd['gigabloxData'][0]['columns']=[{}]
    assert not ordinary(cd)

def test_multiplier_counter_is_not_a_generic_pending_counter():
    cd=deepcopy(DATA['typed_multiplier_counters'])
    counter=next(a for a in cd['actions'] if a['$type']=='ActionGame_SetCounterBoard')
    counter['name']='PendingChoices0'
    assert not ordinary(cd)

@pytest.mark.parametrize('field,value',[('gameMode','FREE_GAME'),('freeSpinsLeft',1),('respin',True),('lastRespin',False)])
def test_multiplier_base_does_not_accept_bonus_or_respin(field,value):
    cd=deepcopy(DATA['multiplier_base']);cd[field]=value
    assert not ordinary(cd)

def test_numeric_bonus_flags_do_not_hide_awarded_free_spins():
    cd=deepcopy(DATA['numeric_bonus_flags']);cd['bonusData']['freespinsAwarded']=7
    assert not ordinary(cd)
def test_named_multiplier_counter_does_not_hide_unknown_counter():
    cd=deepcopy(DATA['named_multiplier_counter']);cd['actions'][0]['counters'][0]['name']='pendingChoices'
    assert not ordinary(cd)

@pytest.mark.parametrize('field,value',[('RoundType',2),('GameMode',1),('Count',1)])
def test_enum_round_requires_regular_zero_mode_without_pending_count(field,value):
    cd=deepcopy(DATA['enum_regular_round']);cd['Round']['Info'][field]=value
    assert not ordinary(cd)
def test_enum_round_unknown_trigger_event_is_not_discarded():
    cd=deepcopy(DATA['enum_regular_round']);cd['Round']['VISData']['Events'].append({'Type':80,'FreeSpins':10})
    assert not ordinary(cd)

@pytest.mark.parametrize('name',['BB','BONUSBUY','BONUSBUY3','BUYRFS','BUYSFS','BUY_WHEEL','BUY_REVEAL'])
def test_explicit_legacy_purchase_command_families(name):
    from tester_spin.providers.yggdrasil.protocol import mode_kind
    assert mode_kind(name)=='PURCHASE'

def test_event_free_spin_state_blocks_client_ordinary_board():
    assert not ordinary_round({'bets':[{'eventdata':{'freeSpins':True,'response':{'clientData':DATA['structured_no_award']}}}]})

def test_multiplier_board_does_not_accept_ante_or_pending_respin():
    cd=deepcopy(DATA['multiplier_board_flags']);cd['goldenBet']=True
    assert not ordinary(cd)
    cd=deepcopy(DATA['multiplier_board_flags']);cd.update(respinAwarded=True,positionShifts=[])
    assert not ordinary(cd)

def test_direct_jackpot_event_uses_same_typed_collection_primitive():
    assert ordinary_round({'bets':[{'eventdata':DATA['classic_jackpot_collections']}]})

def test_malformed_win_direction_is_rejected_without_exception():
    from tester_spin.providers.yggdrasil.named_actions import ordinary_named_actions
    cd={"actions":[{"name":"showWinResults","type":"regular","isOverWinCap":False,"wins":[{"value":{"cash":0,"coins":0},"multiplier":1,"positions":[{"column":0,"row":0}],"symbol":"A","oak":1,"paylineIndex":0,"direction":[]}]}]}
    assert not ordinary_named_actions(cd)

@pytest.mark.parametrize('key,field,value',[('classic_football-glory','gloryAfterSpin',{'HIGH_1':{'amount':1,'gathered':1,'coinsSum':'0'}}),('classic_dr_fortuno','jackpotInfo',{'secondsToGuaranteedFallout':0,'jackpotValue':'2','clockIsTicking':True,'operatorHasDailyJackpot':True}),('classic_joker-millions','currentSticky',1),('classic_rainbow-ryan','usedReels',[0,0,0,0,0,0])])
def test_classic_extension_does_not_hide_pending_feature(key,field,value):
    cd=deepcopy(DATA[key]);cd[field]=value
    assert not ordinary(cd)

@pytest.mark.parametrize('name',['awardSpins','finishSpins','makeChoice','unknownControl'])
def test_presentation_schema_does_not_hide_feature_controls(name):
    cd=deepcopy(DATA['named_wild-stack-frenzy']);cd['actions'].append({'name':name})
    assert not ordinary(cd)

@pytest.mark.parametrize('value',[[],{},None,1])
def test_malformed_action_name_is_rejected(value):
    from tester_spin.providers.yggdrasil.named_actions import ordinary_named_actions
    assert not ordinary_named_actions({'actions':[{'name':value}]})

@pytest.mark.parametrize('field,value',[('isRespin',True),('isRespinAwarded',True),('isFreeSpinsAwarded',True),('accumulatedFreeSpinCoins',1),('wonCoins',1),('wtw',[[1,2,3]])])
def test_flat_multiplier_preserves_unknown_bonus_or_win(field,value):
    cd=deepcopy(DATA['flat_multiplier_multifly']);cd[field]=value
    assert not ordinary(cd)

def test_no_feature_label_cannot_hide_unknown_control_fields():
    assert not ordinary({'featuresUsed':['noFeature'],'pendingChoice':[1,2]})

def test_rage_ordinary_requires_current_server_threshold():
    from tester_spin.providers.yggdrasil.runtime import ordinary_round
    data=json.loads(Path('tests/fixtures/yggdrasil_rage_progress.json').read_text())
    state={'bets':[{'eventdata':{'response':{'clientData':data['clientData']}}}]}
    assert not ordinary_round(state)
    assert not ordinary_round(state,{'rage_trigger':'50'})
    assert ordinary_round(state,data['constraints'])

@pytest.mark.parametrize('value',[[],{},None,1])
def test_malformed_typed_action_name_is_rejected(value):
    from tester_spin.providers.yggdrasil.balanced_features import ordinary_balanced_features
    assert not ordinary_balanced_features({'actions':[{'$type':value}],'isFinished':True})

@pytest.mark.parametrize('key,field,value',[('neutral_royal-family','newItems',['WILD']*5),('neutral_pumpkin-smash','pumpkinsAmount',1),('neutral_sunny-shores','stickyA','1'*25),('neutral_temple-stacks','splitzContainers',[{}]),('neutral_valley-of-the-gods-2','tokens',[{}]),('neutral_pirates-smugglers-paradise','currentMode','FREESPIN')])
def test_neutral_metadata_does_not_hide_a_feature(key,field,value):
    cd=deepcopy(DATA[key]);cd[field]=value
    assert not ordinary(cd)

@pytest.mark.parametrize('field,value',[('spinsRemainingTotal',1),('additionalSpinsAwarded',1),('addedWilds',[{}]),('hiddenSelection',[1,2])])
def test_gati_does_not_hide_an_active_feature(field,value):
    cd=deepcopy(DATA['gati_gigagong-gigablox']);cd['Spin'][0]['spinEvent'][field]=value
    assert not ordinary(cd)

def test_gati_does_not_claim_active_gamble_is_ordinary():
    cd=deepcopy(DATA['gati_giganimals-gigablox']);cd['Gamble']['Options']['riskList']=[{}]
    assert not ordinary(cd)

def test_bbg_metadata_alone_does_not_prove_paid_ordinary_round():
    assert not ordinary_round({'bets':[{'eventdata':{'response':{'clientData':DATA['closed_flags_florageddon']}}}]})
