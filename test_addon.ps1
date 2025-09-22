# Test script to check if add-on is detected by Home Assistant Supervisor
param(
    [string]$HomeAssistantIP = "192.168.50.84"
)

Write-Host "Testing add-on detection..." -ForegroundColor Blue

# Check if the directory structure is correct
Write-Host "Checking directory structure..." -ForegroundColor Cyan

$AddonPath = "H:\addons\local-addons\broadlink-manager"
$RequiredFiles = @("config.yaml", "Dockerfile", "run.sh", "requirements.txt")

foreach ($file in $RequiredFiles) {
    $filePath = Join-Path $AddonPath $file
    if (Test-Path $filePath) {
        Write-Host "Found: $file" -ForegroundColor Green
    } else {
        Write-Host "Missing: $file" -ForegroundColor Red
    }
}

# Check config.yaml content
$configPath = Join-Path $AddonPath "config.yaml"
if (Test-Path $configPath) {
    Write-Host "Checking config.yaml content..." -ForegroundColor Cyan
    $configContent = Get-Content $configPath -Raw
    
    # Check for required fields
    $requiredFields = @("name:", "version:", "slug:", "description:")
    foreach ($field in $requiredFields) {
        if ($configContent -match $field) {
            Write-Host "Found required field: $field" -ForegroundColor Green
        } else {
            Write-Host "Missing required field: $field" -ForegroundColor Red
        }
    }
    
    # Show first few lines of config
    Write-Host "Config.yaml preview:" -ForegroundColor Cyan
    Get-Content $configPath | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
}

Write-Host ""
Write-Host "Next steps to try:" -ForegroundColor Yellow
Write-Host "1. Restart Home Assistant Supervisor service" -ForegroundColor White
Write-Host "2. Try accessing: http://$HomeAssistantIP`:8123/hassio/addon/local_broadlink_manager" -ForegroundColor White
Write-Host "3. Check Home Assistant Core logs (not just Supervisor)" -ForegroundColor White
Write-Host "4. Try creating a simple test add-on first" -ForegroundColor White
