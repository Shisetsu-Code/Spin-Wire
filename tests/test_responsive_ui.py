from tester_spin.responsive_ui import flow_positions

def test_wrapping_keeps_each_control_inside_container():
    boxes,height=flow_positions([(220,26),(220,26),(180,28),(180,28)],450,gap=8)
    assert boxes[0][1]==boxes[1][1]
    assert boxes[2][1]>boxes[0][1]
    assert all(x>=0 and y>=0 and x+w<=450 and y+h<=height for x,y,w,h in boxes)

def test_wide_control_is_constrained_and_layout_can_expand_again():
    small,height=flow_positions([(600,30),(100,30)],300,gap=8)
    large,_=flow_positions([(600,30),(100,30)],900,gap=8)
    assert small[0][2]==300
    assert small[1][1]>0
    assert large[1][1]==0

def test_empty_layout_has_no_phantom_row():
    assert flow_positions([],500)==([],0)
