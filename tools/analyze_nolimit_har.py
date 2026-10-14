"""Decode a supplied Nolimit City HAR offline; never replay its session."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tester_spin.providers.nolimit_city.protocol import decode_capture,analyze_messages

def main():
    parser=argparse.ArgumentParser(description='Analizar apuestas Nolimit City de un HAR con WebSocket, sin ejecutar jugadas.')
    parser.add_argument('har',type=Path)
    parser.add_argument('--output',type=Path,help='Guardar solo el informe, sin claves ni mensajes de sesión.')
    args=parser.parse_args()
    try:
        document=json.loads(args.har.read_text(encoding='utf-8-sig'))
        report=analyze_messages(decode_capture(document))
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(1,f'No se pudo interpretar la captura: {exc}\n')
    output=json.dumps(report,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(output+'\n',encoding='utf-8')
    print(output)
    return 0

if __name__=='__main__':raise SystemExit(main())
