"""Standalone desktop entry point: bundled app, existing data, no terminal."""
import json
import os
import sys
from pathlib import Path


def main():
    home = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'Tester-Spin'
    configured = os.environ.get('TESTER_SPIN_DATA_ROOT', '').strip()
    if not configured:
        try:
            configured = json.loads((home/'updater.json').read_text(encoding='utf-8')).get('data_dir', '')
        except (OSError, ValueError, TypeError, AttributeError):
            configured = ''
    data = Path(configured).expanduser().resolve() if configured else home/'data'
    if data.name != 'data':
        raise RuntimeError('La carpeta de datos configurada debe llamarse data.')
    data.mkdir(parents=True, exist_ok=True)
    os.chdir(data.parent)
    os.environ['TESTER_SPIN_APP_HOME'] = str(home)
    browsers = home/'playwright'
    if browsers.is_dir():
        os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(browsers))
    if '--smoke-test' in sys.argv:
        from tester_spin.app_har import HARToolTesterSpinApp
        app = HARToolTesterSpinApp()
        app.withdraw()
        result = {'status':'OK','data_root':str(app.data_root),'providers':[p.key for p in app.registry.all()]}
        (home/'desktop-smoke-test.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
        app.update_idletasks()
        app.destroy()
        return 0
    from run import main as run_main
    return run_main()


if __name__ == '__main__':
    raise SystemExit(main())
