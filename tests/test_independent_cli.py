import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def cli(*args):return subprocess.run([sys.executable,'-m','tester_spin.cli',*args],cwd=ROOT,text=True,capture_output=True)

def test_provider_listing_works_without_gui():
 r=cli('providers');assert r.returncode==0,r.stderr
 values=json.loads(r.stdout)
 assert 'nolimit_city' in values and 'hacksaw' in values and len(values)==11

def test_invalid_quota_rejected_before_loading_catalog_or_network(tmp_path):
 r=cli('run','nolimit_city','--data-root',str(tmp_path),'--wg-dir',str(tmp_path),'--games-per-ip','0')
 assert r.returncode!=0 and not (tmp_path/'tester-spin.sqlite3').exists()

def test_dry_run_has_no_network_or_results_and_selects_only_one_provider(tmp_path):
 from tester_spin.storage import Storage
 from tester_spin.models import Game
 db=Storage(tmp_path/'tester-spin.sqlite3')
 db.upsert_games([Game('nolimit_city','example','Example','https://playin.com/embed/v1/demo/Example',symbol='Example')])
 r=cli('run','nolimit_city','--data-root',str(tmp_path),'--dry-run','--limit','1')
 assert r.returncode==0,r.stderr
 report=json.loads(r.stdout)
 assert report['selected_games']==['example']
 assert not db.latest_results()
 assert not (tmp_path/'providers'/'hacksaw').exists()
