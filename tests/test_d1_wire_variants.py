from tester_spin.providers.one_spin4win_purchases import classify_spin_message, purchase_response_evidence

def test_wire_shape_distinguishes_normal_and_unidentified_feature():
    assert classify_spin_message({'type':'1','data':'10,0,0'})['variant'] == 'normal'
    assert classify_spin_message({'type':'1','data':'10,0,0,1'})['variant'] == 'feature_variant'
    assert classify_spin_message({'type':'1','data':'10,0,0,1'}, purchase_selectors={1})['variant'] == 'bonus_buy'
    assert classify_spin_message({'type':'1','data':'10,0,0,2'}, side_bet_selectors={2})['variant'] == 'side_bet'
    assert classify_spin_message({'type':'2','data':'10,0,0,1'}) is None
    assert classify_spin_message({'type':'1','data':'10,0,0,1,2'}) is None
    assert classify_spin_message({'type':'1','data':'10,0,0,nan'}) is None

def test_response_evidence_requires_state_counter_and_verified_cost():
    buy = classify_spin_message({'type':'1','data':'10,0,0,1'}, purchase_selectors={1})
    response = {'type':3,'st':5,'b8':0,'b9':15,'b10':0,'b11':0}
    evidence = purchase_response_evidence(buy,response,base_bet=2, cost_multiplier=67,observed_debit=134)
    assert evidence['purchase_accepted'] is True
    assert evidence['terminal'] is False
    assert evidence['bonus_spins'] == 15
    assert not purchase_response_evidence(buy,response,base_bet=2,cost_multiplier=67)['purchase_accepted']
    assert not purchase_response_evidence(buy,response,base_bet=2,cost_multiplier=67,observed_debit=2)['purchase_accepted']
    assert not purchase_response_evidence(buy,{'type':3,'st':0},base_bet=2,cost_multiplier=67,observed_debit=134)['purchase_accepted']
    variant = classify_spin_message({'type':'1','data':'10,0,0,1'})
    assert not purchase_response_evidence(variant,response,base_bet=2,cost_multiplier=67,observed_debit=134)['purchase_accepted']
