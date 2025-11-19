# Quick test script for Coatsy's "No Entities Configured" issue
# This creates a test device with an empty broadlink_entity field

Write-Host "🔧 Setting up test environment for Coatsy's issue..." -ForegroundColor Cyan
Write-Host ""

# Setup paths
$testDir = "C:\temp\broadlink_test"
$devicesFile = "$testDir\broadlink_manager\devices.json"

# Clean up previous test
if (Test-Path $testDir) {
    Write-Host "🧹 Cleaning up previous test..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $testDir -ErrorAction SilentlyContinue
}

# Create directory
Write-Host "📁 Creating test directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "$testDir\broadlink_manager" | Out-Null

# Create test device with empty broadlink_entity (THIS IS THE BUG!)
Write-Host "📝 Creating test device with empty broadlink_entity..." -ForegroundColor Yellow

$deviceJson = @"
{
  "living_room_test_fan": {
    "name": "Living Room Test Fan",
    "entity_type": "fan",
    "device_type": "broadlink",
    "area": "Living Room",
    "icon": "mdi:fan",
    "broadlink_entity": "",
    "enabled": true,
    "commands": {
      "speed_low": {
        "data": "JgBQAAABKJIUEhQ5FBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FDkUEhQSFBIUEhQSFBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FAANBQ==",
        "type": "rf"
      },
      "speed_medium": {
        "data": "JgBQAAABKZIUEhQ5FBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FDkUEhQSFBIUEhQSFBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FAANBQ==",
        "type": "rf"
      },
      "speed_high": {
        "data": "JgBQAAABKpIUEhQ5FBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FDkUEhQSFBIUEhQSFBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FAANBQ==",
        "type": "rf"
      },
      "fan_off": {
        "data": "JgBQAAABK5IUEhQ5FBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FDkUEhQSFBIUEhQSFBIUEhQSFBIUEhQ5FDkUORQ5FDkUORQ5FAANBQ==",
        "type": "rf"
      }
    }
  }
}
"@

# Write JSON
$deviceJson | Set-Content $devicesFile -Encoding UTF8

Write-Host ""
Write-Host "✅ Test environment created!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 Test device location: $devicesFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔍 Device details:" -ForegroundColor Cyan
Write-Host "   - Name: Living Room Test Fan"
Write-Host "   - Type: Fan (Broadlink)"
Write-Host "   - Commands: 4 (speed_low, speed_medium, speed_high, fan_off)"
Write-Host "   - broadlink_entity: '' (EMPTY - This is the bug!)" -ForegroundColor Red
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1️⃣  Set environment variables:" -ForegroundColor White
Write-Host "   `$env:CONFIG_PATH = '$testDir'" -ForegroundColor Gray
Write-Host "   `$env:HA_URL = 'http://localhost:8123'" -ForegroundColor Gray
Write-Host "   `$env:HA_TOKEN = 'your_long_lived_access_token'" -ForegroundColor Gray
Write-Host ""
Write-Host "2️⃣  Start the app:" -ForegroundColor White
Write-Host "   python app/main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "3️⃣  Open browser:" -ForegroundColor White
Write-Host "   http://localhost:8099" -ForegroundColor Gray
Write-Host ""
Write-Host "4️⃣  Try to generate entities:" -ForegroundColor White
Write-Host "   Settings (⚙️) → Generate Entities" -ForegroundColor Gray
Write-Host ""
Write-Host "✅ Expected result:" -ForegroundColor Green
Write-Host "   Error: 'The following device(s) are missing a Broadlink remote entity: Living Room Test Fan'"
Write-Host ""
Write-Host "🔧 To fix (testing the solution):" -ForegroundColor Yellow
Write-Host "   1. Edit the device"
Write-Host "   2. Select a Broadlink remote from dropdown"
Write-Host "   3. Save"
Write-Host "   4. Try generating entities again"
Write-Host "   5. Should succeed!"
Write-Host ""
Write-Host "📊 To view device data:" -ForegroundColor Cyan
Write-Host "   Get-Content '$devicesFile' | ConvertFrom-Json | ConvertTo-Json -Depth 10" -ForegroundColor Gray
Write-Host ""
Write-Host "🎯 Ready to test!" -ForegroundColor Green
