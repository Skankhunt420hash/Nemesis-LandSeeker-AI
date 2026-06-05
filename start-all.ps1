$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$backend = Join-Path $root "backend"
$frontend = Join-Path $root "frontend"
$python = Join-Path $backend ".venv\Scripts\python.exe"
$npmCmd = "C:\Program Files\nodejs\npm.cmd"

if (-not (Test-Path $python)) {
    throw "Backend venv fehlt. Bitte zuerst das Backend einrichten."
}

if (-not (Test-Path $npmCmd)) {
    throw "npm wurde nicht gefunden. Bitte Node.js installieren."
}

Write-Host "Baue Frontend fuer App-Modus..." -ForegroundColor Cyan
Push-Location $frontend
if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    & $npmCmd install
}
& $npmCmd run build
Pop-Location

Write-Host "Starte API und Celery Worker..." -ForegroundColor Cyan

$api = Start-Job -Name "LandSeekerAPI" -ScriptBlock {
    param($backend, $python)
    Set-Location $backend
    $env:USE_CELERY = "1"
    & $python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
} -ArgumentList $backend, $python

$worker = Start-Job -Name "LandSeekerWorker" -ScriptBlock {
    param($backend, $python)
    Set-Location $backend
    & $python -m celery -A app.tasks worker --loglevel=info --pool=solo
} -ArgumentList $backend, $python

Start-Sleep -Seconds 5

$health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
$localIps = Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } | Select-Object -ExpandProperty IPAddress -Unique

Write-Host ""
Write-Host "LandSeeker AI laeuft." -ForegroundColor Green
Write-Host "Lokal:  http://127.0.0.1:8000"
foreach ($ip in $localIps) {
    Write-Host "Handy:  http://$ip`:8000"
}
Write-Host "Celery: $($health.celery_enabled)"
Write-Host ""
Write-Host "Zum Beenden dieses Fensters offen lassen und mit Ctrl+C abbrechen." -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 3
        if ($api.State -match "Failed|Completed|Stopped" -or $worker.State -match "Failed|Completed|Stopped") {
            throw "API oder Worker wurde beendet."
        }
    }
}
finally {
    Stop-Job -Job $api, $worker -ErrorAction SilentlyContinue
    Remove-Job -Job $api, $worker -Force -ErrorAction SilentlyContinue
}
