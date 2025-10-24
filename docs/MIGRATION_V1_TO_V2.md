# Migration from v1 to v2 Format

## Overview

Broadlink Manager v2 uses a new data storage format that separates device management into two files:
- **`devices.json`** - New v2 format for all device data
- **`metadata.json`** - Old v1 format (legacy)

## Automatic Migration

The migration happens **automatically** when you start the add-on if it detects:
1. `metadata.json` exists and has entities
2. `devices.json` is empty or missing

### What Gets Migrated

All devices from `metadata.json` are converted to the new format:
- Device ID (extracted from entity_id)
- Device name and friendly name
- Entity type (switch, light, fan, media_player)
- Broadlink entity reference
- Area assignment
- Icon
- Commands
- Enabled status

### Migration Process

1. **On Startup**: The app checks if migration is needed
2. **Automatic Conversion**: Devices are converted from v1 to v2 format
3. **Logging**: Migration results are logged
4. **Notification**: Frontend shows migration status

## Manual Migration

If you need to manually trigger migration:

### Via API

```bash
# Check migration status
curl http://localhost:8099/api/migrate/status

# Run migration
curl -X POST http://localhost:8099/api/migrate/run
```

### Via Frontend

The frontend will show a notification if migration is needed. Simply restart the add-on to trigger automatic migration.

## Migration Status Response

```json
{
  "needs_migration": true,
  "metadata_exists": true,
  "devices_exists": true,
  "metadata_entity_count": 5,
  "devices_count": 0
}
```

## Migration Result

```json
{
  "success": true,
  "message": "Successfully migrated 5 devices from v1 to v2",
  "migrated_devices": [
    "task_light",
    "tealight_candles",
    "neon_rope_2",
    "pac_man",
    "switchbot_fan"
  ],
  "count": 5
}
```

## Troubleshooting

### Devices Not Showing After Reinstall

**Symptom**: After removing and reinstalling the add-on, devices don't appear in the UI.

**Cause**: `devices.json` is empty but `metadata.json` has the old data.

**Solution**: 
1. Restart the add-on - migration will run automatically
2. Check logs for migration messages
3. If migration fails, use the manual API endpoint

### Migration Logs

Look for these log messages:

```
⚠️ Detected v1 data format - running automatic migration...
✅ Successfully migrated 5 devices from v1 to v2
Migrated devices: task_light, tealight_candles, neon_rope_2, pac_man, switchbot_fan
```

### Migration Failed

If migration fails:
1. Check file permissions on `/config/broadlink_manager/`
2. Verify `metadata.json` is valid JSON
3. Check logs for specific error messages
4. Report issue with diagnostics bundle

## Data Format Comparison

### v1 Format (metadata.json)

```json
{
  "version": 1,
  "entities": {
    "switch.task_light": {
      "entity_type": "switch",
      "device": "task_light",
      "broadlink_entity": "remote.broadlink_rm4_pro",
      "area": "Office",
      "friendly_name": "Task Light",
      "commands": {
        "toggle": {
          "type": "reference",
          "value": "Power"
        }
      },
      "enabled": true
    }
  }
}
```

### v2 Format (devices.json)

```json
{
  "task_light": {
    "device_id": "task_light",
    "name": "Task Light",
    "entity_type": "switch",
    "device_type": "broadlink",
    "broadlink_entity": "remote.broadlink_rm4_pro",
    "area": "Office",
    "icon": "",
    "commands": {
      "toggle": {
        "type": "reference",
        "value": "Power"
      }
    },
    "enabled": true,
    "created_at": "2025-10-24T16:38:24.875704",
    "migrated_from_v1": true,
    "original_entity_id": "switch.task_light"
  }
}
```

## Key Differences

1. **Top-level keys**: v2 uses device_id directly (no domain prefix)
2. **device_type field**: v2 adds explicit device_type ("broadlink" or "smartir")
3. **Timestamps**: v2 tracks creation and update times
4. **Migration tracking**: v2 marks migrated devices with `migrated_from_v1: true`

## After Migration

Once migration is complete:
- Devices appear in the frontend
- All commands are preserved
- Area assignments are maintained
- You can continue using the app normally

## Backup

The migration process does NOT delete `metadata.json`. Both files coexist:
- `metadata.json` - Original v1 data (preserved)
- `devices.json` - New v2 data (created by migration)

This provides a safety net in case you need to rollback.

## Support

If you encounter migration issues:
1. Download diagnostics bundle (Settings → Download Diagnostics)
2. Check the logs for error messages
3. Report issue on GitHub with diagnostics attached
