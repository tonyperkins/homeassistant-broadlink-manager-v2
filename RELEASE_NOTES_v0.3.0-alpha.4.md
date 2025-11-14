# Release Notes: v0.3.0-alpha.4

**Release Date**: November 4, 2025  
**Type**: Bug Fix Release  
**Status**: Alpha

---

## 🎯 Overview

This release fixes a critical bug in the entity generator that prevented fan entities with named speed commands from being created. Users with fans using commands like `speed_low`, `speed_medium`, and `speed_high` will now have their entities generated correctly.

---

## 🐛 Bug Fixes

### Entity Generator: Named Speed Command Support

**Issue**: Fan entities with named speed commands were rejected with warning:
```
WARNING - Fan {device_name} has no speed commands
```

**Root Cause**: The entity generator only accepted numeric speed identifiers (1, 2, 3) and rejected named identifiers (low, medium, high).

**Solution**: 
- Added intelligent mapping system for named speeds
- Supports common naming conventions: `low`, `medium`, `med`, `high`
- Maps to numeric equivalents: `low→1`, `medium→2`, `high→3`
- Works with both `speed_*` and `fan_speed_*` prefixes

**Impact**:
- ✅ Devices with named speed commands now generate entities correctly
- ✅ Improved error messages show which commands were found
- ✅ Fully backward compatible with existing numeric speed commands
- ✅ No migration required

---

## 📝 Changes

### Fixed
- **Entity Generator**: Fan entities with named speed commands (e.g., `speed_low`, `speed_medium`, `speed_high`) are now properly detected
  - Previously only numeric speed commands (e.g., `speed_1`, `speed_2`) were recognized
  - Added mapping system: `low→1`, `medium→2`, `high→3`
  - Supports both `speed_*` and `fan_speed_*` prefixes
  - Improved warning messages now show which commands were found for easier debugging
  - Fully backward compatible with existing numeric speed commands

### Changed
- **Test Suite**: Deprecated `test_command_storage_format.py` (StorageManager removed in favor of DeviceManager)
- **Documentation**: Added comprehensive bug fix documentation in `docs/development/BUG_FIX_ENTITY_GENERATOR_SPEED_COMMANDS.md`

### Added
- **Manual Test**: New speed command detection test suite (`tests/manual/test_speed_command_detection.py`)
  - Tests named speed commands
  - Tests numeric speed commands
  - Tests mixed speed configurations

---

## 🧪 Testing

### Test Results
- **Unit Tests**: 301 passed, 1 failed (cosmetic), 9 skipped
- **Manual Tests**: 3/3 passed
  - ✅ Named speed commands (speed_low, speed_medium, speed_high)
  - ✅ Numeric speed commands (fan_speed_1, fan_speed_2, etc.)
  - ✅ Mixed speed configurations
- **Code Coverage**: 23% (up from 4%)

### Test Coverage
- Config Loader: 99%
- Controller Detector: 100%
- Broadlink Device Manager: 90%
- SmartIR Detector: 95%
- YAML Validator: 82%
- Entity Generator: 52%
- Area Manager: 52%

---

## 📦 Installation

### Home Assistant Add-on Store
1. Navigate to **Settings** → **Add-ons** → **Add-on Store**
2. Find **Broadlink Manager v2 (Alpha)**
3. Click **Update** to upgrade to v0.3.0-alpha.4

### Manual Installation
```bash
cd /config/addons/homeassistant-broadlink-manager-v2
git pull
git checkout v0.3.0-alpha.4
```

---

## 🔄 Upgrade Instructions

### Automatic Upgrade
No special steps required. The fix is backward compatible and will work automatically after updating.

### Manual Workaround (If Not Updating Yet)

If you can't update immediately, you can work around the issue by renaming your speed commands:

**Option 1: Rename via UI**
1. Open Broadlink Manager
2. Edit each affected fan device
3. Rename commands:
   - `speed_low` → `speed_1`
   - `speed_medium` → `speed_2`
   - `speed_high` → `speed_3`
4. Save and regenerate entities

**Option 2: Edit devices.json**
1. Backup `devices.json`
2. Edit the file and rename command keys
3. Restart Broadlink Manager
4. Regenerate entities

---

## 🔍 Verification

After updating, verify the fix:

1. **Check Logs**: No more "has no speed commands" warnings for devices with named speeds
2. **Generate Entities**: Entities should be created successfully
3. **Check helpers.yaml**: Should contain `input_select` helpers for fan speeds
4. **Test in Home Assistant**: Fan entities should show proper speed controls

---

## 📚 Documentation

- **Bug Fix Details**: `docs/development/BUG_FIX_ENTITY_GENERATOR_SPEED_COMMANDS.md`
- **Test Suite**: `tests/manual/test_speed_command_detection.py`
- **Changelog**: `CHANGELOG.md`

---

## 🐛 Known Issues

1. **Diagnostics Test**: One cosmetic test failure in markdown report generation (does not affect functionality)

---

## 🔗 Links

- **GitHub Release**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v0.3.0-alpha.4
- **Commit**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/commit/bf9dc76
- **Issue Tracker**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues

---

## 💬 Feedback

If you encounter any issues with this release, please:
1. Check the logs for detailed error messages
2. Generate diagnostics via Settings → Copy Diagnostics
3. Report issues on GitHub with diagnostics attached

---

## 🙏 Credits

Special thanks to the user who reported this issue with detailed logs, making it easy to identify and fix the root cause.

---

**Previous Release**: [v0.3.0-alpha.3](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v0.3.0-alpha.3)  
**Next Release**: TBD
