# Migration Fix - Devices Not Showing After Migration

## Issue

Users upgrading from v1 to v2 (version 0.3.0-alpha.2) experienced successful migration logs showing "Successfully migrated 5 entities from 5 devices", but the web UI showed "0 devices" in the Managed Devices section.

## Root Cause

The migration system was creating entities in the **legacy v1 system** (`metadata.json`) but the **v2 UI expects devices** in the new `devices.json` file.

**Migration Flow (Before Fix):**
```
Broadlink Storage → Entity Detector → metadata.json (v1 legacy)
                                          ↓
                                    UI shows 0 devices ❌
```

**Expected Flow (After Fix):**
```
Broadlink Storage → Entity Detector → metadata.json (v1 legacy)
                                   → devices.json (v2 system)
                                          ↓
                                    UI shows devices ✅
```

## Technical Details

### Before Fix

`migration_manager.py` only saved to `metadata.json`:

```python
for entity_id, entity_data in detected_entities.items():
    self.storage.save_entity(entity_id, entity_data)  # Only saves to metadata.json
    migrated_entities[entity_id] = entity_data
```

### After Fix

`migration_manager.py` now saves to **both** systems:

```python
for entity_id, entity_data in detected_entities.items():
    # Save to metadata.json (legacy system)
    self.storage.save_entity(entity_id, entity_data)
    
    # Create device in devices.json (v2 system)
    device_id = entity_data.get('device', device_name)
    device_data_v2 = {
        'name': entity_data.get('friendly_name', device_name),
        'entity_type': entity_data.get('entity_type', 'switch'),
        'device_type': 'broadlink',
        'broadlink_entity': entity_data.get('broadlink_entity', broadlink_entity),
        'area': entity_data.get('area', area_name),
        'commands': entity_data.get('commands', {})
    }
    
    # Create device in devices.json
    self.device_manager.create_device(device_id, device_data_v2)
```

## Files Modified

1. **app/migration_manager.py**
   - Added `device_manager` parameter to `__init__()`
   - Updated `_perform_migration()` to create devices in `devices.json`
   - Logs now show: `Migrated entity: {entity_id} -> device: {device_id}`

2. **app/web_server.py**
   - Updated `MigrationManager` initialization to pass `device_manager`

## User Impact

### For New Migrations (After Fix)

Users upgrading from v1 will now see:
- ✅ Devices appear in "Managed Devices" section
- ✅ Commands are visible and functional
- ✅ All device metadata preserved
- ✅ Both legacy and v2 systems populated

### For Users Already Migrated (Before Fix)

If you already ran migration and saw "0 devices", you have two options:

#### Option 1: Re-run Migration (Recommended)

1. **Backup your data:**
   ```bash
   cd /config/broadlink_manager
   cp devices.json devices.json.backup
   cp metadata.json metadata.json.backup
   ```

2. **Clear devices.json to trigger re-migration:**
   ```bash
   echo '{}' > /config/broadlink_manager/devices.json
   ```

3. **Restart the add-on** - Migration will detect existing metadata and re-populate devices.json

#### Option 2: Manual Sync (If Available)

If a sync endpoint is available in the UI:
1. Open Broadlink Manager web interface
2. Click "Sync Commands" button in Managed Devices section
3. Devices should appear

## Verification

After fix is applied, check logs for:

```
INFO - Migration complete: Successfully migrated 5 entities from 5 devices
INFO - Migrated entity: switch.bedroom_tv -> device: bedroom_tv
INFO - Migrated entity: switch.living_room_fan -> device: living_room_fan
...
```

And verify in UI:
- Managed Devices shows correct device count
- Device cards display with commands
- Commands are clickable and functional

## Prevention

This fix ensures:
- ✅ Migration creates devices in both legacy and v2 systems
- ✅ Backward compatibility maintained
- ✅ Future migrations will work correctly
- ✅ No data loss during migration

## Related Issues

- GitHub Issue: [Link to issue when created]
- Version Affected: 0.3.0-alpha.2
- Version Fixed: 0.3.0-alpha.3 (pending)

## Testing

To test the fix:

1. **Setup test environment with v1 devices**
2. **Clear migration state:**
   ```bash
   rm /config/broadlink_manager/metadata.json
   rm /config/broadlink_manager/devices.json
   ```
3. **Start add-on** - Should trigger migration
4. **Verify:**
   - Logs show "Migrated entity: X -> device: Y"
   - UI shows correct device count
   - Commands are visible and functional
   - Both metadata.json and devices.json populated

## Notes

- Migration is **non-destructive** - original Broadlink storage files are never modified
- Both `metadata.json` and `devices.json` are backed up automatically before writes
- Migration only runs once (skipped if metadata already exists)
- Force migration endpoint available for re-running if needed
