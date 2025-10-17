# Update documentation screenshots
# Run this whenever you want to refresh all documentation images

Write-Host "Starting Broadlink Manager for screenshots..." -ForegroundColor Cyan

# Start the app in background
$appProcess = Start-Process python -ArgumentList "app/main.py" -PassThru -NoNewWindow

# Wait for app to start
Write-Host "Waiting for app to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Run screenshot tests
Write-Host "Capturing screenshots..." -ForegroundColor Green
pytest tests/e2e/test_documentation_screenshots.py -v -m docs

# Stop the app
Write-Host "Stopping app..." -ForegroundColor Yellow
Stop-Process -Id $appProcess.Id -Force

Write-Host "Screenshots updated in docs/images/screenshots/" -ForegroundColor Green

# Check if directory exists before listing
if (Test-Path "docs/images/screenshots/") {
    Write-Host "Files created:" -ForegroundColor Cyan
    Get-ChildItem docs/images/screenshots/ | Format-Table Name, Length, LastWriteTime
} else {
    Write-Host "No screenshots were created. Check test output for errors." -ForegroundColor Red
}
