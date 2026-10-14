from tester_spin.providers import pragmatic_observed_transitions as rules
from tester_spin.providers.pragmatic_observed_transitions import apply_spin_rule
import pytest

def test_fallen_has_nine_expanding_symbol_choices_and_bounded_index():
    assert hasattr(rules, 'mystery_selection'), 'Missing explicit Book of Fallen symbol-choice handler'
    mystery_selection=rules.mystery_selection
    state={'na':'m','psym':'1~4.00~2,8,14','puri':'1'}
    for ind in range(9):
        choice=mystery_selection(state,'vs10bookfallen',override=str(ind))
        assert choice['domain']==list(map(str,range(9)))
        assert choice['fields']=={'ind':str(ind)}
    with pytest.raises(ValueError): mystery_selection(state,'vs10bookfallen',override='9')
    assert mystery_selection(state,'vs10bookviking') is None
    assert mystery_selection({**state,'na':'s'},'vs10bookfallen') is None
    assert mystery_selection({'na':'m'},'vs10bookfallen') is None

def test_fallen_spin_omits_unsupported_bet_level_but_preserves_purchase():
    fields={'action':'doSpin','symbol':'vs10bookfallen','c':'0.2','l':'10','bl':'0','pur':'1'}
    apply_spin_rule(fields,'vs10bookfallen')
    assert 'bl' not in fields
    assert fields['pur']=='1'


def test_fallen_purchase_uses_client_trigger_information():
    fields={'action':'doSpin','pur':'0','sInfo':'n'}
    apply_spin_rule(fields,'vs10bookfallen')
    assert fields['sInfo']=='t'


def test_fallen_paid_symbol_spin_requires_explicit_choice():
    selection=rules.mystery_selection({'action':'doSpin','pur':'0'},'vs10bookfallen',override='8',purchase=True)
    assert selection['fields']=={'ind':'8'}
    assert 'purchase=0' in selection['branch_signature']


def test_fallen_uncertified_mystery_never_sends_request(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from tester_spin.providers import PragmaticProvider
    bootstrap=SimpleNamespace(symbol='vs10bookfallen',current_response={'na':'m','psym':'bad'},calibration_response={},session=Mock())
    provider=PragmaticProvider(tmp_path)
    with pytest.raises(RuntimeError,match='no certificado'):
        provider._post_and_store(bootstrap,{'action':'doMysteryScatter'},tmp_path,step=1,label='choice',timeout_s=1)
    bootstrap.session.post.assert_not_called()


def test_fallen_natural_choice_in_calibration_finishes_same_session(tmp_path):
    from types import SimpleNamespace
    from unittest.mock import Mock,patch
    from tester_spin.providers import PragmaticProvider
    from tester_spin.providers.pragmatic_live import PragmaticProvider as Live
    provider=PragmaticProvider(tmp_path)
    provider._write_http_bootstrap=Mock()
    boot=SimpleNamespace(symbol='vs10bookfallen',session=Mock(),spin_template={'action':'doSpin'},calibration_response={'na':'m','psym':'1~4.00~2,8,14'})
    provider._post_and_store=Mock(return_value=(200,b'',{'na':'s'},{}))
    with patch('tester_spin.providers.pragmatic.PragmaticProvider._http_bootstrap',return_value=boot):
        result=Live._http_bootstrap(provider,'https://example.invalid','vs10bookfallen',None,1,5)
    assert result is boot
    assert provider._post_and_store.call_args.args[1]['action']=='doMysteryScatter'
    boot.session.close.assert_not_called()
