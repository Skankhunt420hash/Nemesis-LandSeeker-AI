$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontend = Join-Path $root "frontend"
$npmCmd = "C:\Program Files\nodejs\npm.cmd"

if (-not (Test-Path $npmCmd)) {
    throw "npm wurde nicht gefunden. Bitte Node.js installieren."
}

Push-Location $frontend
try {
    if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
        & $npmCmd install
    }

    & $npmCmd run native:build

    Write-Host ""
    Write-Host "Android-Projekt vorbereitet." -ForegroundColor Green
    Write-Host "Naechster Schritt: npm run native:open"
    Write-Host "Dann in Android Studio APK oder AAB bauen."
}
finally {
    Pop-Location
}
