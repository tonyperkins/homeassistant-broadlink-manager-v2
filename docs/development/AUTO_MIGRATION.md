# Automatic Migration Guide

## Overview

Broadlink Manager includes an **intelligent startup system** that automatically detects your installation type and handles setup accordingly. Whether you're a first-time user, upgrading from a previous version, or migrating from native Broadlink integration, the system adapts to your needs.

## Three User Scenarios

### Scenario 1: First-Time Users 👋

**Who**: Installing Broadlink Manager for the first time, no commands learned yet

**What Happens**:
- System detects no learned commands
- Displays welcome message
- Provides getting started instructions
- No migration needed

**Log Output**:
```
============================================================
👋 WELCOME TO BROADLINK MANAGER!
============================================================
No learned commands found yet
🎯 Get started:
   1. Open the web interface
   2. Select a Broadlink device
   3. Learn IR/RF commands
   4. Auto-generate entities
============================================================
```

### Scenario 2: Existing Broadlink Manager Users 📋

**Who**: Already using Broadlink Manager, have configured entities

**What Happens**:
- System detects existing metadata
- Preserves your configuration
- Skips migration
- Continues normally

**Log Output**:
```
============================================================
📋 EXISTING INSTALLATION DETECTED
============================================================
Found 15 existing entities
No migration needed - your configuration is preserved
============================================================
```

### Scenario 3: Existing Broadlink Users (New to BL Manager) 🎉

**Who**: Have been using Broadlink integration, learned many commands, but new to Broadlink Manager

**What Happens**:
- System discovers all learned commands
- Automatically creates entities
- Associates with Broadlink devices
- Assigns areas
- Ready to generate YAML

**Log Output**:
```
============================================================
✅ AUTOMATIC MIGRATION COMPLETED
============================================================
📊 Migrated: 15 entities
📁 From: 8 devices
🎯 Next steps:
   1. Review entities in the web interface
   2. Adjust areas if needed
   3. Generate YAML entities
   4. Restart Home Assistant
============================================================
```

## How It Works

### On Every Startup

When Broadlink Manager starts, it automatically:

1. **Scans** your Home Assistant storage for Broadlink command files
2. **Discovers** all learned IR/RF commands
3. **Detects** entity types based on command naming patterns
4. **Creates** metadata entries for each detected entity
5. **Associates** entities with their Broadlink devices
6. **Assigns** areas based on Broadlink device locations

### What Happens

```
Startup → Scan Storage → Detect Commands → Create Entities → Ready!
   ↓
Logs show: "✅ Auto-migration completed: Successfully migrated X entities from Y devices"
```

## Migration Process Details

### Step 1: Storage File Discovery

The system looks for files matching:
```
/config/.storage/broadlink_remote_*_codes
```

### Step 2: Command Extraction

For each storage file, it extracts:
- Device names (e.g., `living_room_ceiling_fan`)
- Command names (e.g., `fan_on`, `fan_off`, `fan_speed_1`)
- Command codes (the actual IR/RF data)

### Step 3: Entity Detection

Using intelligent pattern matching, it identifies:

**Lights** - Commands like:
- `light_on`, `light_off`
- `lamp_on`, `lamp_off`
- `light_toggle`

**Fans** - Commands like:
- `fan_speed_1`, `fan_speed_2`, `fan_speed_3`
- `fan_off`, `fan_on`
- `fan_reverse`, `fan_direction`

**Switches** - Commands like:
- `on`, `off`
- `power`, `toggle`

**Media Players** - Commands like:
- `power_on`, `power_off`
- `vol_up`, `vol_down`
- `play`, `pause`, `stop`

### Step 4: Metadata Creation

For each detected entity, creates:

```json
{
  "entity_id": {
    "entity_type": "fan",
    "device": "living_room_ceiling_fan",
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Kitchen",
    "commands": {
      "turn_off": "fan_off",
      "speed_1": "fan_speed_1",
      "speed_2": "fan_speed_2"
    },
    "friendly_name": "Living Room Ceiling Fan",
    "enabled": true,
    "auto_detected": true
  }
}
```

### Step 5: Area Assignment

Initial area assignment uses the Broadlink device's area:
- If Broadlink is in "Kitchen" → entities start in "Kitchen" area
- You can change this later to reflect actual device locations

## After Migration

### What You Get

1. **Metadata File**: `/config/broadlink_manager/metadata.json`
   - Contains all detected entities
   - Ready for customization

2. **Entities Ready**: All entities are configured and ready to generate

3. **Migration Info**: Stored in metadata for reference
   ```json
   {
     "migration": {
       "migrated_at": "2025-10-11T22:30:00",
       "migrated_entities": 15,
       "skipped_devices": 2,
       "errors": 0
     }
   }
   ```

### Next Steps

1. **Review Entities**: Check `/api/entities` to see what was created
2. **Adjust Areas**: Update `area` field for entities in different rooms
3. **Verify Broadlink Assignment**: Ensure `broadlink_entity` is correct
4. **Generate YAML**: Click "Generate Entities" to create HA entities
5. **Restart HA**: Restart Home Assistant to load new entities

## Customization After Migration

### Changing Areas

If a fan is actually in the Living Room but was assigned to Kitchen:

```json
{
  "living_room_ceiling_fan": {
    "broadlink_entity": "remote.kitchen_broadlink",  // Stays the same
    "area": "Living Room"  // Change this
  }
}
```

### Reassigning Broadlink Devices

If you want to use a different Broadlink:

```json
{
  "bedroom_fan": {
    "broadlink_entity": "remote.bedroom_broadlink",  // Change this
    "area": "Bedroom"
  }
}
```

### Disabling Entities

If you don't want certain entities:

```json
{
  "unwanted_device": {
    "enabled": false  // Set to false
  }
}
```

## Migration Scenarios

### Scenario 1: Fresh Install with Existing Commands

**Situation**: You've been using Broadlink integration for months, learned many commands, but never used Broadlink Manager.

**What Happens**:
1. Install Broadlink Manager
2. Start the add-on
3. Automatic migration runs
4. All commands are discovered and entities created
5. Ready to generate YAML

**Result**: Instant setup with all your existing commands!

### Scenario 2: Multiple Broadlink Devices

**Situation**: You have 3 Broadlink devices in different rooms, each with learned commands.

**What Happens**:
1. Migration scans all 3 storage files
2. Creates entities for each device's commands
3. Associates entities with correct Broadlink device
4. Assigns initial areas based on Broadlink locations

**Result**: All devices migrated, properly associated!

### Scenario 3: Hundreds of Commands

**Situation**: You have extensive command libraries across multiple devices.

**What Happens**:
1. Migration processes all commands
2. Groups them by device name
3. Detects entity types automatically
4. Creates metadata for valid entities
5. Skips commands that don't match patterns

**Result**: Organized entity structure from your command library!

## Checking Migration Status

### Via API

```bash
# Get migration status
curl http://homeassistant.local:8099/api/migration/status

# Response:
{
  "has_metadata": true,
  "entity_count": 15,
  "migration_performed": true,
  "migration_info": {
    "migrated_at": "2025-10-11T22:30:00",
    "migrated_entities": 15,
    "skipped_devices": 2
  }
}
```

### Via Logs

Check add-on logs for:
```
✅ Auto-migration completed: Successfully migrated 15 entities from 8 devices
```

Or:
```
ℹ️ Migration not needed: Metadata already exists
```

## Manual Migration

### When to Use

- Migration didn't run automatically
- You want to re-scan for new commands
- You want to overwrite existing metadata

### Force Migration

**Without Overwrite** (adds new entities only):
```bash
POST /api/migration/force
{
  "overwrite": false
}
```

**With Overwrite** (replaces all entities):
```bash
POST /api/migration/force
{
  "overwrite": true
}
```

### Via Web Interface

Future versions will include a "Re-scan Commands" button in the UI.

## Troubleshooting

### Migration Didn't Run

**Check**:
1. Are there learned commands? Check `/config/.storage/broadlink_remote_*_codes`
2. Do you have Broadlink devices configured in HA?
3. Check add-on logs for errors

**Solution**: Trigger manual migration via `/api/migration/check`

### No Entities Created

**Possible Reasons**:
1. Command names don't match detection patterns
2. Commands are incomplete (e.g., only `fan_on` without `fan_off`)
3. Storage files are empty or corrupted

**Solution**: 
- Check command naming conventions
- Ensure commands follow patterns (see Entity Detection section)
- Manually create entities via web interface

### Wrong Areas Assigned

**Reason**: Initial area comes from Broadlink device location

**Solution**: Edit metadata to update `area` field to actual device location

### Entities Disabled

**Reason**: Auto-detected entities are enabled by default

**Solution**: Check `enabled` field in metadata, set to `true`

## Command Naming Best Practices

For best auto-detection results:

### Lights
```
✅ light_on, light_off
✅ lamp_on, lamp_off
✅ light_toggle
❌ turn_light_on (won't detect)
```

### Fans
```
✅ fan_speed_1, fan_speed_2, fan_speed_3
✅ fan_off, fan_on
✅ fan_reverse
❌ speed1 (won't detect)
```

### Switches
```
✅ on, off
✅ power, toggle
✅ power_on, power_off
```

### Media Players
```
✅ vol_up, vol_down
✅ play, pause, stop
✅ ch_up, ch_down
```

## Migration Data Structure

### Metadata File Location
```
/config/broadlink_manager/metadata.json
```

### Structure
```json
{
  "version": 1,
  "entities": {
    "entity_id": {
      "entity_type": "fan",
      "device": "device_name",
      "broadlink_entity": "remote.xxx",
      "area": "Area Name",
      "commands": {...},
      "friendly_name": "Display Name",
      "enabled": true,
      "auto_detected": true
    }
  },
  "migration": {
    "migrated_at": "2025-10-11T22:30:00",
    "migrated_entities": 15,
    "skipped_devices": 2,
    "errors": 0,
    "broadlink_devices": 3
  },
  "last_generated": null
}
```

## FAQ

### Q: Will migration overwrite my manual configurations?
**A**: No. If metadata already exists, automatic migration is skipped.

### Q: Can I re-run migration after adding new commands?
**A**: Yes. Use force migration with `overwrite: false` to add new entities only.

### Q: What if my command names don't match the patterns?
**A**: You can manually create entities via the web interface or edit metadata directly.

### Q: Can I customize entity names after migration?
**A**: Yes. Edit the `friendly_name` field in metadata and regenerate.

### Q: Will migration affect my existing HA entities?
**A**: No. Migration only creates metadata. You control when to generate actual HA entities.

### Q: What happens to commands that don't match any pattern?
**A**: They're skipped during migration but remain in your Broadlink storage. You can manually create entities for them later.

## Support

If you encounter issues with automatic migration:

1. Check add-on logs for error messages
2. Verify your command naming follows patterns
3. Try manual migration via API
4. Report issues on GitHub with:
   - Add-on logs
   - Sample command names
   - Number of Broadlink devices
   - Number of learned commands
