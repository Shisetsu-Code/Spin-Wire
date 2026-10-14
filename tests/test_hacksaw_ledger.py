from decimal import Decimal
import pytest
from tester_spin.providers.hacksaw.ledger import RoundLedger, balance, validate_declaration

def reply(status='started', cash='900', win='0', accumulated='0', currency='EUR', rid='round'):
    return {'statusCode':0,'accountBalance':{'currencyCode':currency,'balance':cash},
            'round':{'roundId':rid,'status':status,'possibleActions':[],
                     'events':[{'wa':win,'awa':accumulated,'ba':'0','bc':'0','wc':'0','awc':'0'}]}}

def test_purchase_price_zero_cost_continuations_and_settlement():
    ledger=RoundLedger(Decimal(1000),'EUR','10','10')
    ledger.accept(reply())
    ledger.accept(reply('wfwpc','900','25','25'))
    ledger.accept(reply('completed','925','0','25'))
    assert ledger.proof()['paid_cost']=='100'
    assert ledger.proof()['win']=='25'
    assert ledger.proof()['closed']

@pytest.mark.parametrize('change',[{'cash':'899'},{'currency':'USD'},{'win':'25','accumulated':'24'},{'win':'NaN'},{'rid':''}])
def test_wrong_debit_currency_accumulated_or_identity_fails(change):
    ledger=RoundLedger(Decimal(1000),'EUR','10','10')
    with pytest.raises(ValueError):ledger.accept(reply(**change))

def test_continuation_extra_charge_and_changed_round_fail():
    for changed in [reply('completed','899'),reply('completed','900',rid='other')]:
        ledger=RoundLedger(Decimal(1000),'EUR','10','10');ledger.accept(reply())
        with pytest.raises(ValueError):ledger.accept(changed)

def test_terminal_requires_credited_total_win():
    ledger=RoundLedger(Decimal(1000),'EUR','10','10');ledger.accept(reply('wfwpc','900','25','25'))
    with pytest.raises(ValueError):ledger.accept(reply('completed','900','0','25'))

@pytest.mark.parametrize('value',[True,'NaN','-1','1.5',None])
def test_balance_is_nonnegative_integer_in_current_currency(value):
    with pytest.raises(ValueError):balance({'accountBalance':{'currencyCode':'EUR','balance':value}},'EUR')

@pytest.mark.parametrize('bonuses',[None,[{'bonusGameId':'a','betCostMultiplier':0}],
    [{'bonusGameId':'a','betCostMultiplier':100},{'bonusGameId':'a','betCostMultiplier':200}]])
def test_incomplete_or_conflicting_price_domain_rejected(bonuses):
    with pytest.raises(ValueError):validate_declaration({'bonusGames':bonuses})

def test_nonzero_unmodelled_credit_and_promotion_rejected():
    for field in ['ba','bc','wc','awc']:
        r=reply();r['round']['events'][0][field]='1'
        with pytest.raises(ValueError):RoundLedger(Decimal(1000),'EUR','10','10').accept(r)
    r=reply();r['promotionWin']='100'
    with pytest.raises(ValueError):RoundLedger(Decimal(1000),'EUR','10','10').accept(r)


def test_client_update_balance_false_can_defer_intermediate_balance():
    ledger=RoundLedger(Decimal(1000),'EUR','10','10')
    ledger.accept(reply())
    middle=reply('wfwpc','900','25','25');middle['accountBalance']=None
    ledger.accept(middle)
    ledger.accept(reply('completed','925','0','25'))
    assert ledger.closed and ledger.proof()['balance_observations']==2

@pytest.mark.parametrize('status',['started','completed'])
def test_entry_and_terminal_cannot_omit_balance(status):
    ledger=RoundLedger(Decimal(1000),'EUR','10','10')
    if status=='completed':ledger.accept(reply())
    value=reply(status);value['accountBalance']=None
    with pytest.raises(ValueError):ledger.accept(value)
