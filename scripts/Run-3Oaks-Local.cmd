@echo off
setlocal EnableExtensions
cd /d "%~dp0.."
set "PYTHONUTF8=1"
set "PYTHONUNBUFFERED=1"
set "TESTER_SPIN_PUBLISH_RESULTS=0"
set "TESTER_SPIN_3OAKS_DATA_ROOT=%CD%\data"
set "TESTER_SPIN_3OAKS_OUT=%CD%\test-evidence\3oaks-local"

if not exist ".venv\Scripts\python.exe" (
    echo [3 Oaks] Creando entorno Python...
    py -3 -m venv ".venv"
    if errorlevel 1 goto preparation_error
)

echo [3 Oaks] Preparando dependencias...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto preparation_error

if /I "%~1"=="all" goto full
if /I "%~1"=="smoke" goto smoke
echo.
echo Uso: scripts\Run-3Oaks-Local.cmd smoke ^| all
echo   smoke: 777 Fruity Coins, Lady Fortune, 15 Dragon Pearls
echo   all: catalogo completo, juegos secuenciales, compras y bonos
exit /b 2

:smoke
echo [3 Oaks] Probando los 3 juegos corregidos...
".venv\Scripts\python.exe" -m tools.three_oaks_full_sweep --catalog-source live --budget-seconds 900 --base-spins 2 --natural-spins 24 --slugs 777_fruity_coins lady_fortune 15_dragon_pearls
goto done

:full
echo [3 Oaks] Ejecutando catalogo completo, un juego por vez...
".venv\Scripts\python.exe" -m tools.three_oaks_full_sweep --catalog-source live --budget-seconds 5400 --base-spins 2 --natural-spins 24
goto done

:preparation_error
echo [3 Oaks] ERROR de instalacion. Revisar Python/py y la salida anterior.
exit /b 1

:done
set "RESULT=%ERRORLEVEL%"
echo.
echo [3 Oaks] Estado de proceso: %RESULT%
echo [3 Oaks] Resumen: test-evidence\3oaks-local\summary.json
echo [3 Oaks] Evidencia privada local: data\three-oaks-full-sweep
exit /b %RESULT%
