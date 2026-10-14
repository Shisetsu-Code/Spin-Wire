param(
    [string]$Provider = "",
    [string]$WireGuardDir = "",
    [int]$GamesPerIp = 0,
    [int]$Limit = -1
)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Falta instalar el entorno Python del programa." }
Push-Location $projectRoot
try {
    $providers = (& $pythonPath -m tester_spin.cli providers | ConvertFrom-Json)
    if (-not $Provider) {
        $choices = @($providers.PSObject.Properties)
        for ($index = 0; $index -lt $choices.Count; $index++) {
            Write-Host "$($index + 1). $($choices[$index].Value)"
        }
        $selected = [int](Read-Host "Numero de proveedor")
        if ($selected -lt 1 -or $selected -gt $choices.Count) { throw "Proveedor invalido" }
        $Provider = $choices[$selected - 1].Name
    }
    if (-not $providers.PSObject.Properties[$Provider]) { throw "Proveedor no registrado" }
    if ($Limit -lt 0) { $Limit = [int](Read-Host "Cantidad total de juegos (0 = todos)") }
    if (-not $WireGuardDir) {
        $useVpn = Read-Host "Usar WireGuard? (s/n)"
        if ($useVpn -match "^[sS]$") { $WireGuardDir = Read-Host "Carpeta de archivos .conf exportados"; if ([string]::IsNullOrWhiteSpace($WireGuardDir)) { throw "Seleccionaste WireGuard: falta una carpeta de perfiles. No se ejecutara por red directa." } }
    }
    $arguments = @("-m", "tester_spin.cli", "run", $Provider, "--data-root", (Join-Path $projectRoot "data"), "--limit", "$Limit")
    if ($WireGuardDir) {
        if ($GamesPerIp -le 0) { $GamesPerIp = [int](Read-Host "Cantidad maxima de juegos por IP") }
        $isAdministrator = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdministrator) { throw "Para usar WireGuard, abri este acceso directo como administrador." }
        $arguments += @("--wg-dir", $WireGuardDir, "--games-per-ip", "$GamesPerIp")
    }
    & $pythonPath @arguments
    if ($LASTEXITCODE -ne 0) { Write-Host "Corrida detenida o incompleta. Revisa el resumen y los registros." }
} catch {
    Write-Host $_.Exception.Message
} finally {
    Pop-Location
    Read-Host "Presiona Enter para cerrar"
}
