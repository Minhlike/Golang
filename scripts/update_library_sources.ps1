[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [string]$Library,
    [string]$Tier,
    [switch]$FrontierOnly,
    [switch]$CoreOnly,
    [switch]$ForceRehash,
    [switch]$OfflineVerify
)

$ErrorActionPreference = 'Stop'

Write-Host '======================================================================' -ForegroundColor Cyan
Write-Host 'ONLINE GO DEVOPS LIBRARY SOURCE LAB — SYNC CONTROLLER' -ForegroundColor Cyan
Write-Host '======================================================================' -ForegroundColor Cyan

$PythonExe = 'python'
if (-not (Get-Command $PythonExe -ErrorAction SilentlyContinue)) {
    Write-Error 'Python executable not found in PATH.'
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript = Join-Path $ScriptDir 'update_library_sources.py'

$ArgsList = @()
if ($CheckOnly) { $ArgsList += '--check-only' }
if ($Library) { $ArgsList += @('--library', $Library) }
if ($Tier) { $ArgsList += @('--tier', $Tier) }
if ($FrontierOnly) { $ArgsList += '--frontier-only' }
if ($CoreOnly) { $ArgsList += '--core-only' }
if ($ForceRehash) { $ArgsList += '--force-rehash' }
if ($OfflineVerify) { $ArgsList += '--offline-verify' }

& $PythonExe $PyScript @ArgsList
if ($LASTEXITCODE -ne 0) {
    Write-Error ('Update engine failed with exit code ' + $LASTEXITCODE)
    exit $LASTEXITCODE
}
