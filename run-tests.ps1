# Run tests with proper virtual environment activation
# Usage: .\run-tests.ps1

Write-Host "Running Broadlink Manager Tests..." -ForegroundColor Cyan
Write-Host ""

# Activate virtual environment
$venvPath = ".\venv\Scripts\Activate.ps1"
if (Test-Path $venvPath) {
    Write-Host "✓ Activating virtual environment..." -ForegroundColor Green
    & $venvPath
} else {
    Write-Host "✗ Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "  Please create it first: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Running new unit tests..." -ForegroundColor Cyan
Write-Host ""

# Run new test files
Write-Host "1. Testing BroadlinkDeviceManager..." -ForegroundColor Yellow
python -m pytest tests/unit/test_broadlink_device_manager.py -v

Write-Host ""
Write-Host "2. Testing SmartIRCodeService..." -ForegroundColor Yellow
python -m pytest tests/unit/test_smartir_code_service.py -v

Write-Host ""
Write-Host "3. Running all unit tests..." -ForegroundColor Yellow
python -m pytest tests/unit/ -v --tb=short

Write-Host ""
Write-Host "Tests complete!" -ForegroundColor Green
