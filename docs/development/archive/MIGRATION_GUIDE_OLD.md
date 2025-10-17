# Migration Guide: Explicit Broadlink Device Assignment

## Automatic Migration for Existing Users

**Good news!** If you're an existing user with learned commands, Broadlink Manager will **automatically migrate** your setup on first startup.

### How Automatic Migration Works

1. **On First Startup**: The add-on checks if you have existing learned commands
2. **Auto-Detection**: Discovers all commands in your Broadlink storage files
3. **Entity Creation**: Automatically creates metadata and entities based on command patterns
4. **Area Assignment**: Uses the Broadlink device's area for initial assignment
5. **Ready to Use**: Entities are immediately available for generation

### What Gets Migrated

- ✅ All learned IR/RF commands from all Broadlink devices
- ✅ Automatic entity type detection (lights, fans, switches, media players)
- ✅ Area assignments based on Broadlink device location
- ✅ Broadlink device associations
- ✅ Command mappings

### Manual Migration Control

If you need more control, use these API endpoints:

**Check Migration Status:**
```bash
GET /api/migration/status
```

**Force Re-migration:**
```bash
POST /api/migration/force
{
  "overwrite": false  // Set to true to replace existing entities
}
```

## What Changed?

Previously, the system assumed that the area in an entity's name (e.g., `tony_s_office_ceiling_fan`) indicated where the Broadlink device was located. This caused issues when a Broadlink device in one area (e.g., Kitchen) controlled devices in other areas (e.g., Living Room, Bedroom).

**New approach**: Each entity explicitly specifies which Broadlink device transmits its commands, separate from the area where the controlled device is located.

## Changes Summary

### 1. Entity Metadata Structure
**New field added**: `broadlink_entity`

```json
{
  "living_room_ceiling_fan": {
    "entity_type": "fan",
    "device": "living_room_ceiling_fan",
    "broadlink_entity": "remote.kitchen_broadlink",  // NEW!
    "area": "Living Room",
    "commands": {...}
  }
}
```

### 2. Code Changes

#### `entity_detector.py`
- Added `broadlink_entity` parameter to `group_commands_by_entity()`
- Entities now store which Broadlink device will transmit their commands

#### `entity_generator.py`
- Constructor now accepts optional `broadlink_device_id` (for backward compatibility)
- Each entity uses its own `broadlink_entity` field instead of global device ID
- Falls back to default device ID if `broadlink_entity` not specified

#### `web_server.py`
- `/api/entities/detect` endpoint now accepts `broadlink_entity` parameter
- `/api/entities/generate` endpoint no longer requires `device_id` (optional for backward compatibility)

#### `storage_manager.py`
- Updated README to document the new structure

## Backward Compatibility

✅ **Existing entities continue to work**
- If `broadlink_entity` is not specified, system uses the default device ID
- No breaking changes to existing functionality

## Migration Steps

### For Existing Users

1. **No immediate action required** - existing entities will continue working
2. **To take advantage of new features**:
   - Edit entity metadata in `/config/broadlink_manager/metadata.json`
   - Add `broadlink_entity` field to each entity
   - Specify which Broadlink remote should send commands
   - Regenerate entity YAML files

### Example Migration

**Before:**
```json
{
  "living_room_fan": {
    "entity_type": "fan",
    "device": "living_room_ceiling_fan",
    "area": "Living Room",
    "commands": {...}
  }
}
```

**After:**
```json
{
  "living_room_fan": {
    "entity_type": "fan",
    "device": "living_room_ceiling_fan",
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Living Room",
    "commands": {...}
  }
}
```

## Benefits

1. **Flexibility**: One Broadlink can control devices in multiple areas
2. **Clarity**: Explicit assignment removes ambiguity
3. **Scalability**: Easy to reassign commands to different Broadlink devices
4. **Correctness**: Area represents where the controlled device is, not where the transmitter is

## Use Cases

### Use Case 1: Central Broadlink
You have one Broadlink in a central location controlling devices throughout your home:

```json
{
  "living_room_tv": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Living Room"
  },
  "bedroom_fan": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Bedroom"
  },
  "office_light": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Office"
  }
}
```

### Use Case 2: Multiple Broadlinks
You have multiple Broadlink devices, each controlling nearby devices:

```json
{
  "living_room_tv": {
    "broadlink_entity": "remote.living_room_broadlink",
    "area": "Living Room"
  },
  "bedroom_fan": {
    "broadlink_entity": "remote.bedroom_broadlink",
    "area": "Bedroom"
  }
}
```

### Use Case 3: Reassigning Devices
You move a Broadlink device or want to use a different one:

**Before:**
```json
{
  "living_room_tv": {
    "broadlink_entity": "remote.old_broadlink",
    "area": "Living Room"
  }
}
```

**After:**
```json
{
  "living_room_tv": {
    "broadlink_entity": "remote.new_broadlink",  // Just change this field
    "area": "Living Room"
  }
}
```

Then regenerate YAML and restart Home Assistant.

## Testing

After migration:

1. **Verify entities load**: Check Home Assistant logs for errors
2. **Test commands**: Ensure all entities still respond to commands
3. **Check areas**: Verify entities appear in correct areas in HA UI
4. **Test reassignment**: Try changing `broadlink_entity` for one entity to verify flexibility

## Troubleshooting

### Entity not working after migration
- **Check**: Is `broadlink_entity` field correct?
- **Check**: Is the Broadlink device online?
- **Fix**: Verify entity ID format (e.g., `remote.kitchen_broadlink`)

### Missing broadlink_entity field
- **Symptom**: Error logs about missing broadlink_entity
- **Fix**: Add `broadlink_entity` field to entity metadata
- **Or**: Provide default `device_id` when calling EntityGenerator

### Entity in wrong area
- **Check**: `area` field should be where the controlled device is located
- **Not**: Where the Broadlink transmitter is located

## Questions?

See the [Architecture Guide](docs/ARCHITECTURE.md) for detailed explanation of the new structure.
