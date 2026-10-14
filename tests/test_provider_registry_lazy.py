import json,subprocess,sys
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]

def test_importing_base_does_not_load_any_provider_or_gui():
 code="import sys,json;from tester_spin.providers.base import ProviderAdapter;print(json.dumps(sorted(m for m in sys.modules if m.startswith('tester_spin.providers.') and m not in ('tester_spin.providers.base','tester_spin.providers.registry'))))"
 out=subprocess.check_output([sys.executable,'-c',code],cwd=ROOT,text=True)
 assert json.loads(out)==[]

def test_loading_one_provider_does_not_construct_or_import_others(tmp_path):
 from tester_spin.providers.registry import create_provider
 code="import sys,json;from pathlib import Path;from tester_spin.providers.registry import create_provider;p=create_provider('nolimit_city',Path(sys.argv[1]));print(json.dumps({'key':p.key,'foreign':[m for m in sys.modules if m.startswith(('tester_spin.providers.hacksaw','tester_spin.providers.pragmatic','tester_spin.providers.yggdrasil'))]}))"
 out=subprocess.check_output([sys.executable,'-c',code,str(tmp_path)],cwd=ROOT,text=True)
 assert json.loads(out)=={'key':'nolimit_city','foreign':[]}
 assert [p.name for p in (tmp_path/'providers').iterdir()]==['nolimit_city']
 with pytest.raises(ValueError):create_provider('nonexistent',tmp_path)

def test_legacy_queue_uses_same_selected_provider_only(tmp_path):
 from tools.run_retry_queue import provider_for
 assert provider_for('hacksaw',tmp_path).key=='hacksaw'
 assert [p.name for p in (tmp_path/'providers').iterdir()]==['hacksaw']

def test_gui_exports_remain_compatible():
 from tester_spin.providers import ProviderRegistry,NolimitCityProvider,HacksawProvider
 assert NolimitCityProvider.key=='nolimit_city' and HacksawProvider.key=='hacksaw'
 assert ProviderRegistry
