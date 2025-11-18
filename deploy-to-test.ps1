#!/usr/bin/env pwsh
# Deploy to TEST Supervised instance (192.168.50.169)
# This script deploys to the TEST instance ONLY, not production

param(
    [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

$TEST_HOST = "192.168.50.169"
$TEST_SHARE = "\\$TEST_HOST\addons"
$ADDON_NAME = "broadlink-manager-v2"

Write-Host "🧪 Deploying to TEST Instance" -ForegroundColor Cyan
Write-Host "Target: $TEST_HOST" -ForegroundColor Yellow
Write-Host ""

# Step 1: Build frontend (unless skipped)
if (-not $SkipBuild) {
    Write-Host "📦 Building frontend..." -ForegroundColor Green
    Push-Location frontend
    try {
        npm run build
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend build failed"
        }
        Write-Host "[SUCCESS] Frontend built successfully" -ForegroundColor Green
    }
    finally {
        Pop-Location
    }
} else {
    Write-Host "⏭️  Skipping frontend build" -ForegroundColor Yellow
}

# Step 2: Check if test instance is accessible
Write-Host ""
Write-Host "🔍 Checking test instance accessibility..." -ForegroundColor Green
if (-not (Test-Path $TEST_SHARE)) {
    Write-Host "[ERROR] Cannot access $TEST_SHARE" -ForegroundColor Red
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "1. Map network drive: net use Z: $TEST_SHARE /user:root" -ForegroundColor White
    Write-Host "2. Or use SSH method (see below)" -ForegroundColor White
    Write-Host ""
    Write-Host "SSH Alternative:" -ForegroundColor Cyan
    Write-Host "  scp -r . root@${TEST_HOST}:/addons/local/$ADDON_NAME" -ForegroundColor White
    Write-Host "  ssh root@$TEST_HOST" -ForegroundColor White
    Write-Host "  ha addons rebuild local_$ADDON_NAME" -ForegroundColor White
    exit 1
}

# Step 3: Deploy files
$TARGET_DIR = "$TEST_SHARE\local\$ADDON_NAME"
Write-Host "📁 Target directory: $TARGET_DIR" -ForegroundColor Green

if (Test-Path $TARGET_DIR) {
    Write-Host "[WARNING] Target directory already exists: $TARGET_DIR" -ForegroundColor Yellow
    $response = Read-Host "Do you want to overwrite it? (y/N)"
    if ($response -ne "y") {
        Write-Host "Deployment cancelled" -ForegroundColor Red
        exit 1
    }
    Write-Host "Removing existing directory..." -ForegroundColor Yellow
    Remove-Item -Path $TARGET_DIR -Recurse -Force
}

Write-Host "Copying files to test instance..." -ForegroundColor Green
New-Item -ItemType Directory -Path $TARGET_DIR -Force | Out-Null

# Copy essential files
$filesToCopy = @(
    "app",
    "config.yaml",
    "Dockerfile",
    "run.sh",
    "apparmor.txt",
    "requirements.txt",
    "smartir_device_index.json",
    "CHANGELOG.md",
    "README.md",
    "icon.png"
)

foreach ($item in $filesToCopy) {
    if (Test-Path $item) {
        Write-Host "  Copying $item..." -ForegroundColor Gray
        Copy-Item -Path $item -Destination $TARGET_DIR -Recurse -Force
    }
}

Write-Host "[SUCCESS] Files copied to test instance" -ForegroundColor Green

# Step 4: Instructions for rebuild
Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. SSH to test instance:" -ForegroundColor White
Write-Host "   ssh root@$TEST_HOST" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Rebuild the add-on:" -ForegroundColor White
Write-Host "   ha addons rebuild local_$ADDON_NAME" -ForegroundColor Yellow
Write-Host ""
Write-Host "3. Start the add-on:" -ForegroundColor White
Write-Host "   ha addons start local_$ADDON_NAME" -ForegroundColor Yellow
Write-Host ""
Write-Host "Or via Web UI:" -ForegroundColor Cyan
Write-Host "  http://$TEST_HOST:8123" -ForegroundColor White
Write-Host "  Settings > Add-ons > Broadlink Manager v2 > Rebuild" -ForegroundColor White
Write-Host ""
