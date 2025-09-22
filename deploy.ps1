# Broadlink Manager Add-on Deployment Script for Windows
# This script helps deploy the add-on to Home Assistant via network share or direct path

param(
    [string]$HomeAssistantIP = "homeassistant.local",
    [string]$Username = "",
    [SecureString]$Password,
    [string]$DirectPath = ""
)

Write-Host "🏗️  Deploying Broadlink Manager Add-on..." -ForegroundColor Blue

# Configuration
$AddonName = "broadlink-manager"
$SourceDir = Get-Location

function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Determine the target path based on parameters
if ($DirectPath) {
    # Use direct path if provided
    $AddonPath = Join-Path $DirectPath "local-addons\$AddonName"
    $NetworkPath = $DirectPath
    Write-Status "Using direct path: $DirectPath"
} else {
    # Use network path
    $NetworkPath = "\\$HomeAssistantIP\addons"
    $AddonPath = "$NetworkPath\local-addons\$AddonName"
    Write-Status "Using network path: $NetworkPath"
}

# Test connectivity (skip if using direct path)
function Test-HomeAssistantConnection {
    if ($DirectPath) {
        Write-Status "Using direct path, skipping network connectivity test..."
        return
    }
    
    Write-Status "Testing connection to Home Assistant..."
    
    try {
        $ping = Test-Connection -ComputerName $HomeAssistantIP -Count 1 -Quiet
        if (-not $ping) {
            Write-Error "Cannot reach Home Assistant at $HomeAssistantIP"
            Write-Error "Please check your Home Assistant IP address and network connection"
            exit 1
        }
        Write-Success "Connection to Home Assistant successful"
    }
    catch {
        Write-Error "Network test failed: $($_.Exception.Message)"
        exit 1
    }
}

# Create network drive mapping if needed (skip if using direct path)
function Connect-NetworkShare {
    if ($DirectPath) {
        Write-Status "Using direct path, skipping network share connection..."
        
        # Test if the direct path is accessible
        if (-not (Test-Path $DirectPath)) {
            Write-Error "Cannot access direct path: $DirectPath"
            Write-Error "Please verify the path exists and is accessible"
            exit 1
        }
        
        Write-Success "Direct path accessible: $DirectPath"
        return
    }
    
    Write-Status "Connecting to Home Assistant network share..."
    
    try {
        # Test if we can access the share
        if (Test-Path $NetworkPath) {
            Write-Success "Network share accessible"
            return
        }
        
        # Try to map the network drive
        if ($Username -and $Password) {
            $Credential = New-Object System.Management.Automation.PSCredential($Username, $Password)
            New-PSDrive -Name "HAAddons" -PSProvider FileSystem -Root $NetworkPath -Credential $Credential -Persist
        }
        else {
            # Try without credentials (for Home Assistant OS default setup)
            if (-not (Test-Path $NetworkPath)) {
                Write-Error "Cannot access $NetworkPath"
                Write-Error "You may need to enable Samba add-on in Home Assistant"
                Write-Error "Or provide credentials with -Username and -Password parameters"
                exit 1
            }
        }
        
        Write-Success "Network share connected"
    }
    catch {
        Write-Error "Failed to connect to network share: $($_.Exception.Message)"
        Write-Warning "Make sure the Samba add-on is installed and running in Home Assistant"
        exit 1
    }
}

# Create addon directory
function New-AddonDirectory {
    Write-Status "Creating add-on directory..."
    
    try {
        $LocalAddonsDir = "$NetworkPath\local-addons"
        if (-not (Test-Path $LocalAddonsDir)) {
            New-Item -ItemType Directory -Path $LocalAddonsDir -Force | Out-Null
            Write-Status "Created local-addons directory"
        }
        
        if (Test-Path $AddonPath) {
            Write-Warning "Add-on directory already exists, removing old version..."
            Remove-Item -Path $AddonPath -Recurse -Force
        }
        
        New-Item -ItemType Directory -Path $AddonPath -Force | Out-Null
        Write-Success "Add-on directory created: $AddonPath"
    }
    catch {
        Write-Error "Failed to create add-on directory: $($_.Exception.Message)"
        exit 1
    }
}

# Copy files to addon directory
function Copy-AddonFiles {
    Write-Status "Copying add-on files..."
    
    try {
        # Files and directories to copy
        $ItemsToCopy = @(
            "config.yaml",
            "Dockerfile", 
            "run.sh",
            "requirements.txt",
            "app",
            "README.md",
            "CHANGELOG.md",
            "build.yaml",
            "apparmor.txt",
            ".gitignore"
        )
        
        foreach ($Item in $ItemsToCopy) {
            $SourcePath = Join-Path $SourceDir $Item
            if (Test-Path $SourcePath) {
                $DestPath = Join-Path $AddonPath $Item
                Copy-Item -Path $SourcePath -Destination $DestPath -Recurse -Force
                Write-Status "Copied: $Item"
            }
            else {
                Write-Warning "File not found, skipping: $Item"
            }
        }
        
        Write-Success "Files copied successfully"
    }
    catch {
        Write-Error "Failed to copy files: $($_.Exception.Message)"
        exit 1
    }
}

# Validate addon files
function Test-AddonFiles {
    Write-Status "Validating add-on files..."
    
    $RequiredFiles = @(
        "config.yaml",
        "Dockerfile",
        "run.sh", 
        "requirements.txt",
        "app\main.py",
        "app\web_server.py"
    )
    
    $MissingFiles = @()
    foreach ($File in $RequiredFiles) {
        $FilePath = Join-Path $AddonPath $File
        if (-not (Test-Path $FilePath)) {
            $MissingFiles += $File
        }
    }
    
    if ($MissingFiles.Count -gt 0) {
        Write-Error "Missing required files:"
        foreach ($File in $MissingFiles) {
            Write-Error "  - $File"
        }
        exit 1
    }
    
    Write-Success "All required files present"
}

# Main deployment function
function Install-Addon {
    Write-Status "Starting add-on deployment..."
    
    Test-HomeAssistantConnection
    Connect-NetworkShare
    New-AddonDirectory
    Copy-AddonFiles
    Test-AddonFiles
    
    Write-Success "Add-on deployed successfully!"
    Write-Host ""
    Write-Status "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Open Home Assistant web interface (http://$HomeAssistantIP:8123)"
    Write-Host "2. Go to Settings -> Add-ons"
    Write-Host "3. Click 'Add-on Store'"
    Write-Host "4. Click the three dots (...) and select 'Repositories'"
    Write-Host "5. Add repository: /addons/local-addons"
    Write-Host "6. Refresh and install 'Broadlink Manager'"
    Write-Host ""
    Write-Status "The web interface will be available at: http://$HomeAssistantIP:8099"
}

# Show help
function Show-Help {
    Write-Host "Broadlink Manager Add-on Deployment Script"
    Write-Host ""
    Write-Host "Usage: .\deploy.ps1 [-HomeAssistantIP <IP>] [-Username <user>] [-Password <pass>] [-DirectPath <path>]"
    Write-Host ""
    Write-Host "Parameters:"
    Write-Host "  -HomeAssistantIP    Home Assistant IP or hostname (default: homeassistant.local)"
    Write-Host "  -Username          Username for network share (optional)"
    Write-Host "  -Password          SecureString password for network share (optional)"
    Write-Host "  -DirectPath        Direct path to Home Assistant addons directory (bypasses network share)"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\deploy.ps1"
    Write-Host "  .\deploy.ps1 -HomeAssistantIP 192.168.1.100"
    Write-Host "  .\deploy.ps1 -HomeAssistantIP 192.168.1.100 -Username admin -Password (Read-Host -AsSecureString)"
    Write-Host "  .\deploy.ps1 -DirectPath 'C:\config\addons'"
    Write-Host "  .\deploy.ps1 -DirectPath '\\192.168.50.84\config\addons'"
    Write-Host ""
    Write-Host "Prerequisites:"
    Write-Host "  Network Share Method:"
    Write-Host "    - Home Assistant with Samba add-on installed and running"
    Write-Host "    - Network connectivity to Home Assistant"
    Write-Host "  Direct Path Method:"
    Write-Host "    - Already mounted/accessible path to Home Assistant addons directory"
    Write-Host "    - PowerShell execution policy allows script execution"
}

# Main script execution
try {
    if ($args -contains "-help" -or $args -contains "--help" -or $args -contains "-h") {
        Show-Help
        exit 0
    }
    
    Install-Addon
}
catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    exit 1
}
