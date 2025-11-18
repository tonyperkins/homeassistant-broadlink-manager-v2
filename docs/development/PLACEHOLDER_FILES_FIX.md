# Placeholder Entity Files Fix

## Problem

User reported Home Assistant configuration error:

```
Failed to perform the action homeassistant/reload_all. Cannot quick reload all YAML configurations because the configuration is not valid: Error loading /config/configuration.yaml: in './config/configuration.yaml', line 69, column 24: Unable to read file /config/broadlink_manager/package.yaml
```

**Root Cause**: The `configuration.yaml` references `broadlink_manager/package.yaml` but the file doesn't exist until entities are generated.

## Solution

Added automatic placeholder file creation on startup to prevent this error.

### Implementation

**File**: `app/web_server.py`

**New Method**: `_initialize_entity_files()`

This method:
1. Creates `/config/broadlink_manager/` directory if it doesn't exist
2. Creates placeholder files if they don't exist:
   - `package.yaml` - Empty package file with comment
   - `helpers.yaml` - Empty helpers file with comment
   - `broadlink_manager_entities.yaml` - Empty entities file with comment

**Called During**: Server initialization (after file watcher setup)

### Placeholder Content

Each file contains a comment explaining it will be populated when entities are generated:

```yaml
# Broadlink Manager Package
# This file will be populated when you generate entities
# Settings > Generate Entities to create your device configurations
```

### Benefits

1. **Prevents Configuration Errors**: Home Assistant can load the configuration even if entities haven't been generated yet
2. **Better UX**: Users can add the package reference to `configuration.yaml` before setting up devices
3. **Non-Breaking**: Doesn't interfere with existing entity generation
4. **Safe**: Gracefully handles errors, won't prevent startup if file creation fails

### User Workflow (Before Fix)

1. Add package reference to `configuration.yaml`
2. ❌ Home Assistant fails to reload - file doesn't exist
3. User has to comment out the reference
4. Configure devices
5. Generate entities
6. Uncomment the reference
7. Reload configuration

### User Workflow (After Fix)

1. Add package reference to `configuration.yaml`
2. ✅ Home Assistant reloads successfully - placeholder file exists
3. Configure devices
4. Generate entities - placeholder is replaced with real content
5. Reload configuration

## Files Modified

- `app/web_server.py` - Added `_initialize_entity_files()` method and call during initialization

## Testing

1. Delete `/config/broadlink_manager/package.yaml`
2. Start Broadlink Manager
3. Check logs for: `Created placeholder file: /config/broadlink_manager/package.yaml`
4. Verify file exists with placeholder content
5. Reload Home Assistant configuration - should succeed
6. Generate entities - placeholder should be replaced with real content

## Related Documentation

- `docs/development/PACKAGE_YAML_MISSING_FIX.md` - User-facing troubleshooting guide
- `README.md` - Installation instructions for adding package reference

## Notes

- Placeholder files are only created if they don't exist
- Real entity generation will overwrite placeholders
- Error during placeholder creation is logged but doesn't prevent startup
- Works in both standalone and add-on modes
