# Release Notes: v0.3.0-alpha.5

**Release Date**: November 6, 2025  
**Type**: Bug Fix Release  
**Status**: Alpha

---

## 🎯 Overview

This release fixes the area sync 404 error that occurred when creating new devices before entity generation.

---

## 🐛 Bug Fixes

### Area Sync: 404 Error for Newly Created Devices

**Problem:**
- Area sync endpoint returned 404 when entity not found in HA registry
- ERROR/WARNING logs appeared for normal behavior (new devices before entity generation)
- Entity not found is EXPECTED for devices created before entity generation

**Changes:**

1. **app/api/devices.py** - sync-area endpoint now returns 200 success with pending flag
   - Changed `success: false` to `success: true`
   - Changed HTTP 404 to 200
   - Added `pending: true` flag to indicate sync will happen after entity generation
   - Updated message to clarify this is normal behavior
   - Changed log level from WARNING to INFO

2. **app/area_manager.py** - Reduced error logging for expected conditions
   - WebSocket `not_found` errors now log at DEBUG level (not ERROR)
   - `get_entity_details` not found now logs at DEBUG level (not WARNING)
   - Only actual errors are logged as ERROR

3. **Removed unused storage variable** in devices.py (flake8 cleanup)

**Impact:**
- No more ERROR/WARNING logs for normal new device creation
- Clear 200 response indicates success with pending sync
- Area syncs automatically after entity generation and HA restart
- Better UX - users understand this is expected behavior

---

## 📝 Changes

### Fixed
- **Area Sync**: Endpoint now returns 200 success instead of 404 when entity doesn't exist yet
  - This is normal for newly created devices before entity generation
  - Added `pending: true` flag to response
  - Reduced error logging to DEBUG level for expected conditions
  - Area will sync automatically after entity generation and HA restart

### Changed
- **Logging**: Reduced noise in logs for expected "not found" conditions
  - WebSocket not_found errors: ERROR → DEBUG
  - Entity not found warnings: WARNING → DEBUG
  - Only actual errors are logged as ERROR

### Removed
- **Code Cleanup**: Removed unused `storage` variable in devices.py

---

## 🧪 Testing

### Test Results
- ✅ Device creation works without errors
- ✅ No ERROR/WARNING logs for normal behavior
- ✅ Area sync returns 200 with pending flag
- ✅ Area syncs correctly after entity generation

### Verification Steps
1. Create a new device in Broadlink Manager
2. Check logs - should see INFO level logs, no errors
3. Generate entities and restart HA
4. Area should sync automatically

---

## 📦 Installation

### Home Assistant Add-on Store
1. Navigate to **Settings** → **Add-ons** → **Add-on Store**
2. Find **Broadlink Manager v2 (Alpha)**
3. Click **Update** to upgrade to v0.3.0-alpha.5

### Manual Installation
```bash
cd /config/addons/homeassistant-broadlink-manager-v2
git pull
git checkout v0.3.0-alpha.5
```

---

## 🔄 Upgrade Instructions

### Automatic Upgrade
No special steps required. The fix is backward compatible and will work automatically after updating.

---

## 🔍 Verification

After updating, verify the fix:

1. **Create a new device**: Should complete without errors
2. **Check logs**: No ERROR or WARNING messages for area sync
3. **Generate entities**: Area should sync after entity generation
4. **Check device card**: Area should appear after HA restart

---

## 📚 Documentation

- **Bug Fix Details**: `docs/development/BUG_FIX_AREA_SYNC_404_ERROR.md`
- **Changelog**: `CHANGELOG.md`

---

## 🐛 Known Issues

None

---

## 🔗 Links

- **GitHub Release**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v0.3.0-alpha.5
- **Issue Tracker**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues

---

## 💬 Feedback

If you encounter any issues with this release, please:
1. Check the logs for detailed error messages
2. Generate diagnostics via Settings → Copy Diagnostics
3. Report issues on GitHub with diagnostics attached

---

## 🙏 Credits

Thanks to the alpha testers for reporting issues and helping improve the app!

---

**Previous Release**: [v0.3.0-alpha.4](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v0.3.0-alpha.4)  
**Next Release**: TBD
