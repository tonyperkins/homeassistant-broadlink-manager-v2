# Deployment script for Broadlink Manager Add-on to Home Assistant OS
# This script copies the add-on files to the Home Assistant addons directory

param(
    [switch]$Force  # Skip confirmation prompt
)

# Configuration
$HA_ADDONS_PATH = "\\homeassistant.local\addons\local"
$ADDON_NAME = "broadlink-manager-v2"
$SOURCE_DIR = $PSScriptRoot
$TARGET_DIR = Join-Path $HA_ADDONS_PATH $ADDON_NAME

# Color output functions
function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Banner
Write-Host ""
Write-Host "=======================================================" -ForegroundColor Magenta
Write-Host "  Broadlink Manager v2 (Beta) Deployment Script" -ForegroundColor Magenta
Write-Host "=======================================================" -ForegroundColor Magenta
Write-Host ""

# Validate source directory
if (-not (Test-Path $SOURCE_DIR)) {
    Write-Error-Custom "Source directory not found: $SOURCE_DIR"
    exit 1
}

# Validate Home Assistant addons path
if (-not (Test-Path $HA_ADDONS_PATH)) {
    Write-Error-Custom "Home Assistant addons path not found: $HA_ADDONS_PATH"
    Write-Warning-Custom "Please ensure \\homeassistant.local\addons is accessible"
    Write-Warning-Custom "You may need to map it as a network drive first"
    exit 1
}

Write-Success "Home Assistant addons path found: $HA_ADDONS_PATH"

# Build frontend
Write-Host ""
Write-Info "Building frontend..."
$frontendDir = Join-Path $SOURCE_DIR "frontend"
if (Test-Path $frontendDir) {
    Push-Location $frontendDir
    try {
        Write-Info "Running npm install..."
        npm install --silent 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning-Custom "npm install had warnings, continuing..."
        }
        
        Write-Info "Running npm run build..."
        npm run build
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Frontend build failed!"
            Pop-Location
            exit 1
        }
        Write-Success "Frontend built successfully"
    }
    catch {
        Write-Error-Custom "Error during frontend build: $_"
        Pop-Location
        exit 1
    }
    finally {
        Pop-Location
    }
} else {
    Write-Warning-Custom "Frontend directory not found, skipping build"
}

if (Test-Path $TARGET_DIR) {
    if (-not $Force) {
        Write-Warning-Custom "Target directory already exists: $TARGET_DIR"
        $response = Read-Host "Do you want to overwrite it? (y/N)"
        if ($response -ne "y" -and $response -ne "Y") {
            Write-Info "Deployment cancelled"
            exit 0
        }
    } else {
        Write-Info "Target directory exists, removing (Force mode)..."
    }
    Write-Info "Removing existing directory..."
    Remove-Item -Path $TARGET_DIR -Recurse -Force
    Write-Success "Removed existing directory"
}

Write-Info "Creating target directory: $TARGET_DIR"
New-Item -ItemType Directory -Path $TARGET_DIR -Force | Out-Null
Write-Success "Created target directory"

# Define files and directories to copy (for add-on mode)
$itemsToCopy = @(
    "config.yaml",
    "Dockerfile",
    "run.sh",
    "requirements.txt",
    "apparmor.txt",
    "icon.png",
    "README.md",
    "CHANGELOG.md",
    "app",
    "docs"
)

# Copy files and directories
Write-Host ""
Write-Info "Copying files to target directory..."
Write-Host ""

$copiedCount = 0
$failedCount = 0

foreach ($item in $itemsToCopy) {
    $sourcePath = Join-Path $SOURCE_DIR $item
    $targetPath = Join-Path $TARGET_DIR $item
    
    if (Test-Path $sourcePath) {
        try {
            if (Test-Path $sourcePath -PathType Container) {
                Write-Info "Copying directory: $item"
                Copy-Item -Path $sourcePath -Destination $targetPath -Recurse -Force -Exclude "__pycache__","*.pyc","*.pyo","*.log",".DS_Store"
                Get-ChildItem -Path $targetPath -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
            } else {
                Write-Info "Copying file: $item"
                Copy-Item -Path $sourcePath -Destination $targetPath -Force
            }
            Write-Success "  Copied: $item"
            $copiedCount++
        }
        catch {
            Write-Error-Custom "  Failed to copy $item : $_"
            $failedCount++
        }
    }
    else {
        Write-Warning-Custom "  Not found: $item (skipping)"
    }
}

Write-Host ""
Write-Host "=======================================================" -ForegroundColor Magenta

# Summary
Write-Host ""
Write-Info "Deployment Summary:"
Write-Host "  Files/Directories copied: $copiedCount" -ForegroundColor White
if ($failedCount -gt 0) {
    Write-Host "  Failed: $failedCount" -ForegroundColor Red
}
Write-Host "  Target location: $TARGET_DIR" -ForegroundColor White
Write-Host ""

if ($failedCount -eq 0) {
    Write-Success "Deployment completed successfully!"
    Write-Host ""
    Write-Info "Next Steps:"
    Write-Host "  1. Open Home Assistant web interface" -ForegroundColor White
    Write-Host "  2. Go to Settings -> Add-ons" -ForegroundColor White
    Write-Host "  3. Click Add-on Store (bottom right)" -ForegroundColor White
    Write-Host "  4. Click the three dots in the top right" -ForegroundColor White
    Write-Host "  5. Select Check for updates or refresh the page" -ForegroundColor White
    Write-Host "  6. Look for 'Broadlink Manager v2 (Beta)' in Local add-ons" -ForegroundColor White
    Write-Host "  7. Click Install or Rebuild if already installed" -ForegroundColor White
    Write-Host ""
    Write-Warning-Custom "Note: v2 can run alongside v1 (different slug: broadlink-manager-v2)"
    Write-Warning-Custom "      Both add-ons will share the same /config/broadlink_manager data"
    Write-Host ""
} else {
    Write-Error-Custom "Deployment completed with errors!"
    Write-Warning-Custom "Please check the errors above and try again"
    exit 1
}

Write-Host "=======================================================" -ForegroundColor Magenta
Write-Host ""
