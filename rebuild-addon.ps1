#!/usr/bin/env pwsh
# Quick rebuild script for local add-on development

param(
    [switch]$Restart,  # Just restart (faster, for code changes)
    [switch]$Rebuild,  # Full rebuild (for config/Dockerfile changes)
    [string]$Host = "homeassistant.local"  # Home Assistant hostname
)

$addonSlug = "local_broadlink-manager-v2"

Write-Host "🔧 Broadlink Manager v2 - Development Helper" -ForegroundColor Cyan
Write-Host ""

# Check if we need to use SSH or if ha command is available locally
$useSSH = $true
try {
    $null = Get-Command ha -ErrorAction Stop
    $useSSH = $false
    Write-Host "[INFO] Using local 'ha' command" -ForegroundColor Gray
} catch {
    Write-Host "[INFO] Using SSH to $Host" -ForegroundColor Gray
}

if ($Restart) {
    Write-Host "♻️  Restarting add-on..." -ForegroundColor Yellow
    if ($useSSH) {
        ssh root@$Host "ha addons restart $addonSlug"
    } else {
        ha addons restart $addonSlug
    }
} elseif ($Rebuild) {
    Write-Host "🔨 Rebuilding add-on..." -ForegroundColor Yellow
    if ($useSSH) {
        ssh root@$Host "ha addons rebuild $addonSlug"
    } else {
        ha addons rebuild $addonSlug
    }
} else {
    Write-Host "Usage:" -ForegroundColor Green
    Write-Host "  .\rebuild-addon.ps1 -Restart   # Quick restart (code changes)"
    Write-Host "  .\rebuild-addon.ps1 -Rebuild   # Full rebuild (config/Dockerfile)"
    Write-Host ""
    Write-Host "Defaulting to rebuild..." -ForegroundColor Yellow
    if ($useSSH) {
        ssh root@$Host "ha addons rebuild $addonSlug"
    } else {
        ha addons rebuild $addonSlug
    }
}

Write-Host ""
Write-Host "✅ Done! Check the add-on logs for status." -ForegroundColor Green
