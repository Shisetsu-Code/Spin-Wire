import importlib.util,json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]

def test_public_report_is_allowlisted_and_does_not_publish_network_or_sessions():
 from tester_spin.cli import public_report
 report={'provider':'nolimit_city','attempted':1,'pending':0,'reason':'COMPLETED','results':[{'provider':'nolimit_city','slug':'example','status':'OK'}],
  'ip_counts':{'203.0.113.1':1},'private_config':'PrivateKey=secret','future_private_field':{'extPlayerKey':'secret'}}
 safe=public_report(report)
 assert safe=={'provider':'nolimit_city','attempted':1,'pending':0,'reason':'COMPLETED','results':report['results']}
 assert 'secret' not in json.dumps(safe) and '203.0.113.1' not in json.dumps(safe)

def test_workflow_is_manual_selects_one_provider_and_uploads_only_summary():
 path=ROOT/'.github/workflows/provider-run.yml'
 assert path.is_file()
 text=path.read_text(encoding='utf-8')
 assert 'workflow_dispatch:' in text and 'WG_CONFIGS_JSON' in text
 assert 'cancel-in-progress: false' in text
 assert 'path: public-summary.json' in text
 assert 'path: data' not in text and 'path: **' not in text
 assert 'env:' in text and '--games-per-ip' in text

def test_installed_entry_point_and_catalog_data_are_packaged():
 import tomllib
 project=tomllib.loads((ROOT/'pyproject.toml').read_text(encoding='utf-8'))
 assert project['project']['scripts']['tester-spin']=='tester_spin.cli:main'
 assert project['tool']['setuptools']['package-data']['*']==['*.json','*.js','*.html','*.txt']

def test_profile_materialization_does_not_print_secret_or_allow_path_escape(tmp_path,capsys):
 spec=importlib.util.spec_from_file_location('profile_prep',ROOT/'scripts/prepare-wireguard-profiles.py')
 assert spec and spec.loader
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 profile='[Interface]\nPrivateKey = private-value\nAddress = 10.0.0.2/32\n[Peer]\nPublicKey = public-value\nEndpoint = vpn.example:51820\nAllowedIPs = 0.0.0.0/0, ::/0\n'
 with pytest.raises(ValueError):module.materialize(json.dumps({'../outside':profile}),tmp_path/'unsafe')
 assert not (tmp_path/'outside.conf').exists()
 output=tmp_path/'valid';module.materialize(json.dumps({'profile1':profile}),output)
 assert (output/'profile1.conf').read_text(encoding='utf-8')==profile
 assert 'private-value' not in capsys.readouterr().out
