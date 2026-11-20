# SE3002 Software Quality Engineering - Database Reset Script (PowerShell)
# Purges transient order mutations and restores the database to identical seeded state
# Empirically verifies reset idempotency via dual execution.

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "SE3002 SQE Pretix Reset: Restoring State to Clean Seed" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$PythonBin = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $PythonBin)) {
    $PythonBin = "python"
}

$ResetPy = Join-Path $ScriptDir "reset.py"
& $PythonBin $ResetPy --verify-idempotency

if ($LASTEXITCODE -ne 0) {
    Write-Error "Reset failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "`nSystem state reset and idempotency successfully verified." -ForegroundColor Green
