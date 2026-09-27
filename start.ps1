# Sets up (if needed) and runs the whole app as a single process.
# Usage: right-click this file -> "Run with PowerShell", or from a terminal: .\start.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "== Backend: setting up virtual environment ==" -ForegroundColor Cyan
Set-Location "$root\backend"
if (-not (Test-Path "venv")) {
    python -m venv venv
}
& ".\venv\Scripts\Activate.ps1"
pip install -q -r requirements.txt

Write-Host "== Frontend: installing dependencies ==" -ForegroundColor Cyan
Set-Location "$root\frontend"
if (-not (Test-Path "node_modules")) {
    npm install
}

Write-Host "== Frontend: building ==" -ForegroundColor Cyan
npm run build

Write-Host "== Starting server on http://localhost:5000 ==" -ForegroundColor Green
Set-Location "$root\backend"
python run.py
