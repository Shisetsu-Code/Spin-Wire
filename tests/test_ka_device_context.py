import pytest
from tester_spin.providers.ka_gaming.device_context import current_client_identity


@pytest.mark.parametrize('profile,version',[('chrome110','110.0.0.0'),('chrome150','150.0.0.0'),('chrome200','200.0.0.0')])
def test_transport_profile_supplies_version_without_pinning_the_capture(profile,version):
    agent,context=current_client_identity(browser_profile=profile)
    assert 'Windows NT' in agent and 'Chrome/'+version in agent
    assert context=={'dt':'Chrome','dv':version,'do':'Windows'}


def test_explicit_windows_user_agent_and_metadata_are_consistent():
    agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/123.4.5.6 Safari/537.36'
    assert current_client_identity(agent)==(agent,{'dt':'Chrome','dv':'123.4.5.6','do':'Windows'})


def test_unknown_transport_profile_fails_before_signing():
    with pytest.raises(ValueError):current_client_identity(browser_profile='unrecognized')
