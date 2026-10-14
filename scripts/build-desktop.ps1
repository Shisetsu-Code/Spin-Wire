param(
    [string]$Python = "python",
    [string]$DistPath = ""
)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
if (-not $DistPath) { $DistPath = Join-Path $root "dist\desktop" }
$build = Join-Path $root "build\desktop"
New-Item -ItemType Directory -Path $build -Force | Out-Null
& $Python -m PyInstaller --noconfirm --onefile --windowed --name "Tester-Spin" `
    --paths $root --distpath $DistPath --workpath $build --specpath $build `
    --icon (Join-Path $root "tester_spin\assets\tester-spin.ico") `
    --add-data "$(Join-Path $root 'tester_spin\assets');tester_spin/assets" `
    --collect-data tester_spin.providers --collect-submodules tester_spin.providers --collect-all playwright --collect-all curl_cffi (Join-Path $root "desktop.py")
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el ejecutable." }
Write-Host "Ejecutable completo: $(Join-Path $DistPath 'Tester-Spin.exe')"
