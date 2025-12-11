# Template Syntax Migration Guide

## Overview

Broadlink Manager has been updated to use **modern Home Assistant template syntax** (introduced in HA 2021.4) to avoid deprecation warnings and ensure compatibility with future Home Assistant versions.

**Important:** Legacy template syntax will **stop working in Home Assistant 2026.6**.

## What Changed?

### Old Syntax (Legacy - Deprecated)
```yaml
fan:
  - platform: template
    fans:
      office_ceiling_fan:
        unique_id: office_ceiling_fan
        friendly_name: "Office Ceiling Fan"
        speed_count: 6
        # ...

light:
  - platform: template
    lights:
      living_room_light:
        unique_id: living_room_light
        friendly_name: "Living Room Light"
        # ...
```

### New Syntax (Modern - Required)
```yaml
template:
  - fan:
      - unique_id: office_ceiling_fan
        name: "Office Ceiling Fan"
        speed_count: 6
        # ...
  - light:
      - unique_id: living_room_light
        name: "Living Room Light"
        # ...
```

## Key Differences

1. **Top-level key:** `template:` instead of individual `fan:`, `light:`, `switch:`, etc.
2. **No platform key:** No more `platform: template`
3. **No wrapper keys:** No more `fans:`, `lights:`, `switches:` wrappers
4. **Name vs friendly_name:** Uses `name:` instead of `friendly_name:`
5. **List structure:** Each entity type is a list item under `template:`
6. **Template field names changed:**
   - `value_template:` → `state:` (all entity types)
   - `level_template:` → `level:` (light brightness)
   - `temperature_template:` → `temperature:` (light color temp)
   - `percentage_template:` → `percentage:` (fan speed)
   - `direction_template:` → `direction:` (fan direction)
   - `position_template:` → `position:` (cover position)
   - **Exception:** `icon_template:` stays the same (no change)

## Migration Steps

### For New Installations

No action needed! The updated Broadlink Manager automatically generates entities using the modern syntax.

**Minimum Requirements:**
- Home Assistant 2021.4 or newer

### For Existing Users

If you already have entities generated with the old syntax, follow these steps:

#### Option 1: Regenerate Entities (Recommended)

1. **Backup your current configuration:**
   ```bash
   cp /config/broadlink_manager/entities.yaml /config/broadlink_manager/entities.yaml.backup
   cp /config/broadlink_manager/helpers.yaml /config/broadlink_manager/helpers.yaml.backup
   ```

2. **Update Broadlink Manager** to the latest version

3. **Regenerate your entities** in the Broadlink Manager UI:
   - Go to "Managed Devices"
   - Click "Generate Entities" button
   - This will create new files with modern syntax

4. **Update your `configuration.yaml`:**

   **Old:**
   ```yaml
   # Broadlink Manager Entities
   light: !include broadlink_manager/entities.yaml
   fan: !include broadlink_manager/entities.yaml
   switch: !include broadlink_manager/entities.yaml
   media_player: !include broadlink_manager/entities.yaml
   cover: !include broadlink_manager/entities.yaml
   input_boolean: !include broadlink_manager/helpers.yaml
   input_select: !include broadlink_manager/helpers.yaml
   input_number: !include broadlink_manager/helpers.yaml
   ```

   **New:**
   ```yaml
   # Broadlink Manager Entities (Modern Template Syntax - HA 2021.4+)
   template: !include broadlink_manager/entities.yaml
   media_player: !include broadlink_manager/entities.yaml
   input_boolean: !include broadlink_manager/helpers.yaml
   input_select: !include broadlink_manager/helpers.yaml
   input_number: !include broadlink_manager/helpers.yaml
   ```

5. **Check your configuration:**
   - Go to Developer Tools → YAML
   - Click "Check Configuration"
   - Fix any errors if they appear

6. **Restart Home Assistant**

7. **Verify entities work:**
   - Test each entity to ensure commands still work
   - Check that state tracking still functions

#### Option 2: Manual Migration

If you prefer to manually migrate your existing YAML files:

1. **Backup your files** (see Option 1, step 1)

2. **Edit `entities.yaml`:**
   - Remove all `platform: template` lines
   - Remove wrapper keys (`fans:`, `lights:`, `switches:`, `covers:`)
   - Change `friendly_name:` to `name:`
   - Restructure into `template:` list format (see example above)

3. **Update `configuration.yaml`** (see Option 1, step 4)

4. **Check and restart** (see Option 1, steps 5-7)

## Troubleshooting

### Deprecation Warning Still Appears

If you still see the deprecation warning after migration:

1. **Check for other template entities:**
   - Search your entire `/config` folder for `platform: template`
   - You may have other custom template entities using old syntax

2. **Verify configuration.yaml:**
   - Make sure you updated the include statements
   - Ensure you're including the new `entities.yaml` file

3. **Clear cache:**
   ```bash
   rm -rf /config/.storage/core.restore_state
   ```
   Then restart Home Assistant

### Entities Not Appearing

1. **Check configuration:**
   - Developer Tools → YAML → Check Configuration
   - Look for YAML syntax errors

2. **Check logs:**
   - Settings → System → Logs
   - Search for "template" or "broadlink_manager"

3. **Verify file structure:**
   ```yaml
   template:
     - fan:
         - unique_id: ...
   ```
   Note the indentation and list structure

### State Tracking Not Working

Helper entities (`input_boolean`, `input_select`, `input_number`) are unchanged and should continue working. If state tracking fails:

1. **Verify helpers are loaded:**
   - Developer Tools → States
   - Search for `input_boolean.` and `input_select.`

2. **Check helper references:**
   - Entity configs should still reference the same helper entity IDs
   - Example: `input_boolean.office_ceiling_fan_state`

## Timeline

- **HA 2021.4** - Modern template syntax introduced
- **HA 2025.12** - Legacy syntax deprecated (warnings appear)
- **HA 2026.6** - Legacy syntax stops working (breaking change)
- **Broadlink Manager v2.x** - Updated to use modern syntax

## Additional Resources

- [Home Assistant Template Integration Docs](https://www.home-assistant.io/integrations/template/)
- [HA Community: Template Deprecation Discussion](https://community.home-assistant.io/t/deprecation-of-legacy-template-entities-in-2025-12/955562)
- [HA Release 2021.4 Notes](https://www.home-assistant.io/blog/2021/04/07/release-20214/)

## Need Help?

If you encounter issues during migration:

1. Check the [Broadlink Manager GitHub Issues](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues)
2. Post on the [Home Assistant Community Forum](https://community.home-assistant.io/)
3. Include your configuration files (with sensitive data removed) and error logs
