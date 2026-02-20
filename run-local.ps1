# Local development runner for the Analytics Lambda server
# Activates the Python virtual environment, loads environment variables,
# and starts the local Lambda invocation server on port 9001.
#
# Usage: .\run-local.ps1
#
# Run this in a separate terminal BEFORE starting the backend API.
# The Spring Boot backend will forward analytics requests to this server
# when LAMBDA_ENDPOINT_URL=http://localhost:9001 is set.

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CPSC Analytics - Local Lambda Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1 | Select-Object -First 1
    Write-Host "[OK] $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] Python is not installed or not in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# Check for .env.local and create template if missing
if (-not (Test-Path .env.local)) {
    Write-Host "[!] .env.local not found. Creating template..." -ForegroundColor Yellow
    @"
AWS_PROFILE=cpsc-devops
AWS_REGION=us-east-1
ENVIRONMENT=devl
LOCAL_REPORTS_DIR=./reports
"@ | Out-File -FilePath .env.local -Encoding UTF8
    Write-Host "[OK] Created .env.local template" -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "IMPORTANT: Configure your environment" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Yellow
    Write-Host "Please edit .env.local with your AWS credentials." -ForegroundColor White
    Write-Host "Then run this script again." -ForegroundColor White
    Write-Host ""
    Write-Host "Default values have been set:" -ForegroundColor Cyan
    Write-Host "  AWS_PROFILE=cpsc-devops" -ForegroundColor Gray
    Write-Host "  AWS_REGION=us-east-1" -ForegroundColor Gray
    Write-Host "  ENVIRONMENT=devl" -ForegroundColor Gray
    Write-Host "  LOCAL_REPORTS_DIR=./reports" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

# Load environment variables from .env.local
Get-Content .env.local | ForEach-Object {
    if ($_ -match '^([^=]+)=(.*)$') {
        $name = $matches[1]
        $value = $matches[2]
        Set-Item -Path "env:$name" -Value $value
        Write-Host "Set $name" -ForegroundColor Green
    }
}
Write-Host "Environment variables loaded from .env.local" -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
$venvActivate = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "[OK] Activating virtual environment..." -ForegroundColor Green
    & $venvActivate
} else {
    Write-Host "[!] Virtual environment not found at .\venv" -ForegroundColor Yellow
    Write-Host "    Create it and install dependencies:" -ForegroundColor Yellow
    Write-Host "      python -m venv venv" -ForegroundColor White
    Write-Host "      .\venv\Scripts\Activate.ps1" -ForegroundColor White
    Write-Host "      pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    Write-Host "Attempting to run without virtual environment..." -ForegroundColor Yellow
}
Write-Host ""

Write-Host "[i] Starting local Lambda server on http://localhost:9001" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Route: POST /2015-03-31/functions/{functionName}/invocations" -ForegroundColor Gray
Write-Host "  cpsc-analytics-generate-* -> analytics_handler.handler" -ForegroundColor Gray
Write-Host "  cpsc-analytics-report-*   -> report_handler.handler" -ForegroundColor Gray
Write-Host ""
Write-Host "The Spring Boot backend (cpsc-backend-api) will route analytics" -ForegroundColor White
Write-Host "requests here when LAMBDA_ENDPOINT_URL=http://localhost:9001." -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C to stop." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python local_lambda_server.py --port 9001 --log-level INFO
