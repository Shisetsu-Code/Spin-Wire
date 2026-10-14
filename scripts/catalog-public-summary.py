"""Safe Actions report for catalog-only providers; never claims game tests."""
import argparse,json
from pathlib import Path
from tester_spin.storage import Storage
from tester_spin.cli import write_json

parser=argparse.ArgumentParser()
parser.add_argument('provider');parser.add_argument('--data-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
games=Storage(args.data_root/'tester-spin.sqlite3').list_games(args.provider)
write_json(args.output,{'provider':args.provider,'catalog_games':len(games),'execution_supported':False,'attempted':0,'reason':'CATALOG_ONLY','statuses':{}})
