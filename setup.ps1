# FASTAptameR3 Python - Setup Script for Windows PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FASTAptameR3 Python - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Backend Setup
Write-Host "[1/2] Setting up Backend..." -ForegroundColor Yellow
Write-Host ""

Set-Location "$scriptDir/backend"

Write-Host "Installing Python dependencies..." -ForegroundColor Green
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Backend dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install backend dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Frontend Setup
Write-Host "[2/2] Setting up Frontend..." -ForegroundColor Yellow
Write-Host ""

Set-Location "$scriptDir/web"

Write-Host "Installing Node.js dependencies..." -ForegroundColor Green
npm install

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Frontend dependencies installed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to install frontend dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the application:" -ForegroundColor White
Write-Host "  1. Backend:  cd backend && uvicorn main:app --reload --port 8000" -ForegroundColor White
Write-Host "  2. Frontend: cd web && npm start" -ForegroundColor White
Write-Host ""
Write-Host "Then open http://localhost:4200 in your browser" -ForegroundColor White
Write-Host ""

Set-Location $scriptDir
