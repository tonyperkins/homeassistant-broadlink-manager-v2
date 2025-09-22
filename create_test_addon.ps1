# Create a minimal test add-on to verify local add-on detection works
param(
    [string]$DirectPath = "H:\addons"
)

Write-Host "🧪 Creating minimal test add-on..." -ForegroundColor Blue

$TestAddonPath = Join-Path $DirectPath "local-addons\test-addon"

# Create directory
New-Item -ItemType Directory -Path $TestAddonPath -Force | Out-Null

# Create minimal config.yaml
$minimalConfig = @"
name: Test Add-on
version: "1.0.0"
slug: test_addon
description: Minimal test add-on
arch:
  - amd64
startup: application
boot: manual
init: false
"@

$minimalConfig | Out-File -FilePath (Join-Path $TestAddonPath "config.yaml") -Encoding UTF8

# Create minimal Dockerfile
$minimalDockerfile = @"
ARG BUILD_FROM
FROM `$BUILD_FROM

RUN echo "Test add-on container"

CMD ["echo", "Hello from test add-on"]
"@

$minimalDockerfile | Out-File -FilePath (Join-Path $TestAddonPath "Dockerfile") -Encoding UTF8

Write-Host "[SUCCESS] Created minimal test add-on at: $TestAddonPath" -ForegroundColor Green
Write-Host "[INFO] Check if 'Test Add-on' appears in Home Assistant add-on store" -ForegroundColor Cyan
Write-Host "[INFO] If it doesn't appear, the issue is with local add-on detection in general" -ForegroundColor Yellow
