#!/usr/bin/env pwsh
# Simple reminder script for rebuilding local add-on

Write-Host "🔧 Broadlink Manager v2 - Rebuild Reminder" -ForegroundColor Cyan
Write-Host ""
Write-Host "After running .\deploy-to-haos.ps1, you need to rebuild the add-on:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1: Via Home Assistant UI" -ForegroundColor Green
Write-Host "  1. Go to Settings → Add-ons → Broadlink Manager v2" 
Write-Host "  2. Click ⋮ (three dots) → Rebuild"
Write-Host ""
Write-Host "Option 2: Via SSH/Terminal" -ForegroundColor Green
Write-Host "  ssh root@homeassistant.local"
Write-Host "  ha addons rebuild local_broadlink-manager-v2"
Write-Host ""
Write-Host "💡 Tip: For code-only changes, use Restart instead of Rebuild (faster)" -ForegroundColor Cyan
Write-Host ""
