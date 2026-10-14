import json
import pytest
from tester_spin.providers.hacksaw.return_check import check_return

def test_return_requires_two_new_closed_paid_basic_rounds(tmp_path):
    requests=[];account=1000
    def send(payload):
        nonlocal account
        requests.append(payload);account-=10
        return {'statusCode':0,'accountBalance':{'currencyCode':'EUR','balance':str(account)},
            'round':{'roundId':str(len(requests)),'status':'completed','possibleActions':[],
                     'events':[{'etn':'reveal','wa':'0','awa':'0','ba':'0','bc':'0','wc':'0','awc':'0','c':{}}]}}
    proof=check_return(send,tmp_path,before=1000,stake='10',currency='EUR')
    assert proof['status']=='CONFIRMED' and proof['consecutive_base']==2
    assert len(requests)==2
    assert all(r['bets']==[{'betAmount':'10'}] for r in requests)
    assert all('buyBonus' not in r['bets'][0] for r in requests)

def test_completed_with_wrong_cash_cannot_confirm_return(tmp_path):
    def send(payload):return {'statusCode':0,'accountBalance':{'currencyCode':'EUR','balance':'1000'},
        'round':{'roundId':'r','status':'completed','possibleActions':[],'events':[]}}
    proof=check_return(send,tmp_path,before=1000,stake='10',currency='EUR')
    assert proof['status']=='ERROR' and proof['consecutive_base']==0

def test_natural_feature_round_does_not_count_as_base(tmp_path):
    count=0;cash=1000
    def send(payload):
        nonlocal count,cash
        count+=1;cash-=10
        event={'etn':'feature_enter' if count==1 else 'reveal','wa':'0','awa':'0','ba':'0','bc':'0','wc':'0','awc':'0','c':{}}
        return {'statusCode':0,'accountBalance':{'currencyCode':'EUR','balance':str(cash)},
            'round':{'roundId':str(count),'status':'completed','possibleActions':[],'events':[event]}}
    proof=check_return(send,tmp_path,before=1000,stake='10',currency='EUR')
    assert proof['status']=='CONFIRMED' and count==3


def test_repeated_round_identity_cannot_prove_two_new_rounds(tmp_path):
    cash=1000
    def send(payload):
        nonlocal cash
        cash-=10
        return {'statusCode':0,'accountBalance':{'currencyCode':'EUR','balance':str(cash)},
            'round':{'roundId':'same','status':'completed','possibleActions':[],'events':[]}}
    proof=check_return(send,tmp_path,before=1000,stake='10',currency='EUR')
    assert proof['status']=='ERROR' and proof['consecutive_base']==1
