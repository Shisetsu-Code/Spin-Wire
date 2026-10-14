from tester_spin.providers.pragmatic_observed_transitions import bonus_transition

def test_second_bonus_after_completed_menu():
    state={'na':'b','g':'{bg_0:{bgid:"0",bgt:"69",ch_h:"0~0",ch_k:"fs_0,fs_1",ch_v:"0,1",end:"1",rw:"0.00"},bg_1:{bgid:"1",bgt:"69",end:"0",rw:"0.00"}}'}
    choice=bonus_transition(state)
    assert choice is not None
    assert choice['fields']=={'ind':'0'}
    assert choice['domain']==['0']

def test_second_bonus_requires_observed_identity():
    state={'na':'b','g':'{bg_1:{bgid:"2",bgt:"69",end:"0",rw:"0.00"}}'}
    assert bonus_transition(state) is None


def test_range_pick_uses_only_hidden_positions():
    state={'na':'b','g':'{b:{ask:"0",bgid:"0",bgt:"69",ch_h:"0~0,0~4",ch_k:"pck",ch_v:"0:7",end:"0",level:"2",lifes:"1",rw:"0.00",rw_c:"0",status:"1,0,0,0,2,0,0,0",wi:"4",wins:"1,0,0,0,1,0,0,0",wins_mask:"B,h,h,h,C,h,h,h"}}'}
    choice=bonus_transition(state,override='1')
    assert choice is not None
    assert choice['fields']=={'ind':'1'}
    assert choice['domain']==['1','2','3','5','6','7']
    for old,new in [('0:7','0:8'),('lifes:"1"','lifes:"9"'),('B,h,h,h,C','h,h,h,h,C'),('0~0,0~4','0~4,0~0')]:
        assert bonus_transition({**state,'g':state['g'].replace(old,new)}) is None

def test_range_pick_accepts_multiple_remaining_picks():
    state={'na':'b','g':'{b:{ask:"0",bgid:"0",bgt:"69",ch_k:"pck",ch_v:"0:7",end:"0",level:"0",lifes:"3",rw:"0.00",rw_c:"0",status:"0,0,0,0,0,0,0,0",wins:"0,0,0,0,0,0,0,0",wins_mask:"h,h,h,h,h,h,h,h"}}'}
    assert bonus_transition(state)['domain']==list(map(str,range(8)))


def test_lucky_lightning_observed_automatic_respin():
    from tester_spin.providers.pragmatic_observed_transitions import automatic_fs_respin
    state={'na':'s','rs':'mc','rs_p':'0','rs_c':'1','rs_m':'1','fs':'2','fsmax':'10'}
    assert automatic_fs_respin(state,symbol='vswayslight')
    assert not automatic_fs_respin(state,symbol='unknown')
    for change in [{'rs_c':'2'},{'rs_p':'1'},{'trail':'sr~2'},{'rs_t':'1'}]:
        assert not automatic_fs_respin({**state,**change},symbol='vswayslight')


def test_yum_automatic_respins_require_observed_stages():
    from tester_spin.providers.pragmatic_observed_transitions import automatic_fs_respin
    for played in ['0','1']:
        assert automatic_fs_respin({'na':'s','rs':'mc','rs_p':played,'rs_c':'1','rs_m':'1'},symbol='vswaysyumyum')
    assert not automatic_fs_respin({'na':'s','rs':'mc','rs_p':'2','rs_c':'1','rs_m':'1'},symbol='vswaysyumyum')


def test_observed_respin_rejects_present_malformed_tumble_amount():
    from tester_spin.providers.pragmatic_observed_transitions import automatic_fs_respin
    for symbol in ['vswayslight','vswaysyumyum']:
        state={'na':'s','rs':'mc','rs_p':'0','rs_c':'1','rs_m':'1','tmb_win':'invalid'}
        assert not automatic_fs_respin(state,symbol=symbol)
