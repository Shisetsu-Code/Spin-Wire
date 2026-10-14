param(
    [string]$Provider = "",
    [string]$WireGuardDir = "",
    [int]$GamesPerIp = 0,
    [int]$Limit = 0
)
$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Falta el entorno Python del programa." }
Push-Location $projectRoot
try {
    $arguments = @("-m", "tester_spin.runtime_entry")
    if (-not $Provider) { $arguments += "--menu" }
    else {
        $arguments += @("run", $Provider, "--limit", "$Limit", "--data-root", (Join-Path $projectRoot "data"))
        if ($WireGuardDir) { $arguments += @("--wg-dir", $WireGuardDir, "--games-per-ip", "$GamesPerIp") }
    }
    & $pythonPath @arguments
} finally { Pop-Location }
