from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from tester_spin.app_current import CurrentTesterSpinApp
from tester_spin.providers.ka_gaming.limits import REQUEST_GATE


def test_active_application_applies_operation_delay_before_starting_workers():
    app=SimpleNamespace(_worker=None)
    for name,value in [('concurrency','1'),('spins','1'),('delay','0'),('timeout','30'),('operation_delay','0,5')]:
        setattr(app,name+'_var',MagicMock())
        getattr(app,name+'_var').get.return_value=value
    provider=MagicMock(key='ka_gaming',display_name='KA Gaming')
    provider.effective_test_concurrency.return_value=1
    app._provider=lambda:provider
    for name in ['_set_busy','status_var','progress','_append_log','storage','_events','_execution_backend']:
        setattr(app,name,MagicMock())
    try:
        with patch('tester_spin.app_current.threading.Thread'):
            CurrentTesterSpinApp._start_tests(app,[])
        assert REQUEST_GATE.min_interval_s==.5
    finally:
        REQUEST_GATE.configure_delay(0)
