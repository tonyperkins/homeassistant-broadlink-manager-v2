# Diagnostics System Enhancements

## Overview

Enhanced the diagnostic package system with additional troubleshooting information to help identify and resolve issues more effectively.

## New Sections Added

### 1. **Python Dependencies** ⭐
**Purpose:** Identify version mismatches and missing packages

**Includes:**
- All key dependencies (broadlink, flask, aiohttp, pyyaml, etc.)
- Version numbers for each package
- Total package count

**Example:**
```json
{
  "dependencies": {
    "broadlink": "0.18.3",
    "flask": "3.0.0",
    "aiohttp": "3.9.1",
    "total_packages": 156
  }
}
```

### 2. **Recent Log Entries** ⭐
**Purpose:** Capture recent errors and warnings from application logs

**Includes:**
- Last 20 ERROR entries
- Last 20 WARNING entries
- Log file location
- Included in ZIP as `recent_logs.txt`

**Searches:**
- `/config/broadlink_manager.log`
- `/var/log/broadlink_manager.log`
- `broadlink_manager.log`

### 3. **Home Assistant Connection** ⭐
**Purpose:** Validate HA connectivity and configuration

**Includes:**
- Connection configured status
- HA URL (sanitized)
- Connection test result (success/failed)
- Home Assistant version
- WebSocket connection status

**Example:**
```json
{
  "ha_connection": {
    "configured": true,
    "connection_test": "success",
    "ha_version": "2024.1.0",
    "websocket_connected": true
  }
}
```

### 4. **Broadlink Device Information**
**Purpose:** List discovered Broadlink devices and their usage

**Includes:**
- Count of discovered devices
- Device entity IDs
- Device types (RM4 Pro, RM3 Mini, etc.)
- Command counts per device

### 5. **Environment Variables**
**Purpose:** Validate environment configuration

**Includes:**
- Safe environment variables only (no secrets)
- LOG_LEVEL, WEB_PORT, AUTO_DISCOVER, STORAGE_PATH
- Truncates long values (like PATH)

### 6. **File System Permissions**
**Purpose:** Detect permission issues that cause silent failures

**Includes:**
- Storage path readable/writable
- Config path readable/writable
- HA storage path readable

### 7. **Backup File Status**
**Purpose:** Verify backup system is working

**Includes:**
- Backup file existence
- File sizes
- Age in hours
- Last modified timestamps

**Example:**
```json
{
  "backups": {
    "devices.json.backup": {
      "exists": true,
      "size": 2048,
      "age_hours": 2.5
    }
  }
}
```

### 8. **SmartIR Profile Statistics**
**Purpose:** Track SmartIR usage and profile management

**Includes:**
- Total custom profiles
- Profiles by platform (climate, media_player, etc.)
- Device index file status
- Index last updated timestamp

## Updated ZIP Bundle Contents

The diagnostic ZIP now includes:

1. **diagnostics.json** - Complete diagnostic data (all sections)
2. **README.md** - Markdown summary report
3. **devices_sanitized.json** - Device list with command names only
4. **command_structure.json** - Command metadata (no actual codes)
5. **recent_logs.txt** - Recent errors and warnings ✨ NEW

## Enhanced Markdown Report

The markdown summary now includes:

- ✅ Python dependency versions
- ✅ Home Assistant connection status with version
- ✅ Broadlink device details
- ✅ SmartIR profile statistics
- ✅ Backup file status with ages
- ✅ File system permissions
- ✅ Recent error/warning counts

## API Changes

### Updated Endpoints

All three diagnostic endpoints now accept additional managers:

```python
# Before
collector = DiagnosticsCollector(storage_path, device_manager, storage_manager)

# After
collector = DiagnosticsCollector(
    storage_path, 
    device_manager, 
    storage_manager, 
    area_manager,      # NEW - for HA connection testing
    web_server         # NEW - for future enhancements
)
```

### Endpoints:
- `GET /api/diagnostics` - JSON format
- `GET /api/diagnostics/markdown` - Markdown summary
- `GET /api/diagnostics/download` - ZIP bundle

## Usage

### From UI (Settings Menu)
1. Click gear icon in header
2. Select "Copy Diagnostics" (markdown to clipboard)
3. Or "Download Diagnostics" (ZIP file)

### From API
```bash
# Get JSON
curl http://localhost:8099/api/diagnostics

# Get Markdown
curl http://localhost:8099/api/diagnostics/markdown

# Download ZIP
curl http://localhost:8099/api/diagnostics/download -o diagnostics.zip
```

## Privacy & Security

All diagnostic data is automatically sanitized:

- ✅ No HA tokens or passwords
- ✅ No API keys
- ✅ No IR/RF command codes
- ✅ No sensitive environment variables
- ✅ Partial IP addresses only (if included)
- ✅ Masked MAC addresses (if included)

## Troubleshooting Value

These enhancements help diagnose:

1. **Dependency Issues** - Version mismatches, missing packages
2. **Connection Problems** - HA connectivity, WebSocket failures
3. **Permission Errors** - File system access issues
4. **Configuration Issues** - Environment variable problems
5. **Data Loss** - Backup system failures
6. **Recent Errors** - What went wrong before the issue
7. **Device Discovery** - Broadlink device detection problems
8. **SmartIR Issues** - Profile management and integration status

## Files Modified

- `app/diagnostics.py` - Added 8 new collection methods
- `app/api/devices.py` - Updated all 3 diagnostic endpoints
- `docs/DIAGNOSTICS_ENHANCEMENTS.md` - This documentation

## Future Enhancements (Not Yet Implemented)

- Recent operations log (track user actions)
- YAML validation results
- API endpoint health checks
- Browser/client information (from frontend)
- Troubleshooting hints based on detected issues

## Testing

To test the enhanced diagnostics:

1. Access the app UI
2. Click settings gear → "Download Diagnostics"
3. Extract ZIP and verify all files are present
4. Check README.md includes new sections
5. Verify recent_logs.txt contains log entries (if any)
6. Confirm diagnostics.json has all new sections

## Notes

- Log collection requires log file to exist in standard locations
- HA connection test requires area_manager to be configured
- Broadlink device info requires devices to be registered
- All new sections gracefully handle missing data (no errors)
