#!/usr/bin/env pwsh
# Deploy to TEST Supervised instance (192.168.50.169) via SSH
# This script deploys to the TEST instance ONLY, not production

param(
    [switch]$SkipBuild = $false,
    [switch]$AutoRebuild = $false,
    [string]$TestHost = "192.168.50.168"
)

$ErrorActionPreference = "Stop"

$TEST_HOST = $TestHost
$ADDON_SLUG = "1ed199ed_broadlink-manager-v2"
$REMOTE_PATH = "/addons/git/1ed199ed"

Write-Host "[TEST] Deploying to TEST Instance via SSH" -ForegroundColor Cyan
Write-Host "Target: $TEST_HOST" -ForegroundColor Yellow
Write-Host ""

# Step 1: Build frontend (unless skipped)
if (-not $SkipBuild) {
    Write-Host "[BUILD] Building frontend..." -ForegroundColor Green
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
    Write-Host "[SKIP] Skipping frontend build" -ForegroundColor Yellow
}

# Step 2: Check SSH connectivity
Write-Host ""
Write-Host "[SSH] Testing SSH connection..." -ForegroundColor Green
ssh -o ConnectTimeout=5 -o BatchMode=yes root@$TEST_HOST "echo OK" 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Cannot connect to $TEST_HOST via SSH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please ensure:" -ForegroundColor Yellow
    Write-Host "1. SSH is enabled on the test instance" -ForegroundColor White
    Write-Host "2. You have SSH key authentication set up, or" -ForegroundColor White
    Write-Host "3. Run manually: ssh root@$TEST_HOST" -ForegroundColor White
    exit 1
}
Write-Host "[SUCCESS] SSH connection OK" -ForegroundColor Green

# Step 3: Create temporary archive
Write-Host ""
Write-Host "[ARCHIVE] Creating deployment archive..." -ForegroundColor Green
$tempArchive = [System.IO.Path]::GetTempFileName() + ".tar.gz"

# Create list of files to include
$filesToInclude = @(
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

# Use tar to create archive (Windows 10+ has tar built-in)
tar -czf $tempArchive $filesToInclude 2>&1 | Out-Null

if (-not (Test-Path $tempArchive)) {
    Write-Host "[ERROR] Failed to create archive" -ForegroundColor Red
    exit 1
}

Write-Host "[SUCCESS] Archive created: $tempArchive" -ForegroundColor Green

# Step 4: Copy to test instance
Write-Host ""
Write-Host "[UPLOAD] Uploading to test instance..." -ForegroundColor Green
scp $tempArchive root@${TEST_HOST}:/tmp/addon.tar.gz
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to upload archive" -ForegroundColor Red
    Remove-Item $tempArchive -Force
    exit 1
}

# Step 5: Extract on remote
Write-Host "[EXTRACT] Extracting files on test instance..." -ForegroundColor Green
$extractCmd = "mkdir -p $REMOTE_PATH && cd $REMOTE_PATH && tar -xzf /tmp/addon.tar.gz && rm /tmp/addon.tar.gz && echo Files extracted successfully"
ssh root@$TEST_HOST $extractCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to extract files" -ForegroundColor Red
    Remove-Item $tempArchive -Force
    exit 1
}

# Cleanup local temp file
Remove-Item $tempArchive -Force

Write-Host "[SUCCESS] Files deployed to test instance" -ForegroundColor Green

# Step 6: Rebuild add-on (if requested)
if ($AutoRebuild) {
    Write-Host ""
    Write-Host "[REBUILD] Rebuilding add-on..." -ForegroundColor Green
    ssh root@$TEST_HOST "ha addons rebuild $ADDON_SLUG"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Add-on rebuilt successfully" -ForegroundColor Green
        Write-Host ""
        Write-Host "To start the add-on:" -ForegroundColor Cyan
        Write-Host "  ssh root@$TEST_HOST" -ForegroundColor Yellow
        Write-Host "  ha addons start $ADDON_SLUG" -ForegroundColor Yellow
    } else {
        Write-Host "[ERROR] Add-on rebuild failed" -ForegroundColor Red
    }
} else {
    # Step 7: Instructions
    Write-Host ""
    Write-Host "[SUCCESS] Deployment complete!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. SSH to test instance:" -ForegroundColor White
    Write-Host "   ssh root@$TEST_HOST" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "2. Rebuild the add-on:" -ForegroundColor White
    Write-Host "   ha addons rebuild $ADDON_SLUG" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "3. Start the add-on:" -ForegroundColor White
    Write-Host "   ha addons start $ADDON_SLUG" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or run with -AutoRebuild to rebuild automatically:" -ForegroundColor Cyan
    Write-Host "   .\deploy-to-test-ssh.ps1 -AutoRebuild" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or via Web UI:" -ForegroundColor Cyan
    Write-Host "  http://$TEST_HOST:8123" -ForegroundColor White
    Write-Host "  Settings > Add-ons > Broadlink Manager v2 > Rebuild" -ForegroundColor White
}

Write-Host ""
