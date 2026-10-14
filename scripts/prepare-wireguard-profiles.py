"""Materialize a GitHub Secret in a private runner temp directory, never print it."""
import argparse,json,os,re,sys
from pathlib import Path

def materialize(secret,output):
    values=json.loads(secret)
    if not isinstance(values,dict) or not values or len(values)>100:raise ValueError('Perfiles inválidos')
    if any(not isinstance(k,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,60}',k) or not isinstance(v,str) or len(v)>100_000 for k,v in values.items()):
        raise ValueError('Nombres o perfiles inválidos')
    output=Path(output)
    if output.exists() and any(output.iterdir()):raise ValueError('La carpeta de destino debe estar vacía')
    output.mkdir(parents=True,exist_ok=True);output.chmod(0o700)
    for name,content in values.items():
        descriptor=os.open(output/(name+'.conf'),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(descriptor,'w',encoding='utf-8') as target:target.write(content)
    return len(values)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    try:count=materialize(os.environ.pop('WG_CONFIGS_JSON',''),args.output)
    except Exception:print('Falta WG_CONFIGS_JSON válido en los Secrets del repositorio.',file=sys.stderr);raise SystemExit(2)
    print('Perfiles privados preparados: '+str(count))
