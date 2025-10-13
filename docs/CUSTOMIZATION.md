# Entity Customization Guide

## Overview

Broadlink Manager supports extensive entity customization through the metadata file. You can customize names, icons, areas, and more - all stored in one place and applied consistently across your Home Assistant installation.

## Customization Fields

### Available Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entity_type` | string | ✅ Yes | Type of HA entity (`light`, `fan`, `switch`, `media_player`) |
| `device` | string | ✅ Yes | Command storage key in Broadlink |
| `broadlink_entity` | string | ✅ Yes | Which Broadlink remote sends commands |
| `area` | string | ✅ Yes | Where the controlled device is located |
| `commands` | object | ✅ Yes | Mapping of actions to learned command names |
| `friendly_name` | string | ✅ Yes | Default display name (auto-generated) |
| `name` | string | ❌ No | Custom display name (overrides `friendly_name`) |
| `icon` | string | ❌ No | Custom MDI icon |
| `enabled` | boolean | ❌ No | Whether to generate this entity (default: `true`) |

## Name Customization

### How It Works

```
Priority: name > friendly_name > entity_id
```

### Example

**Metadata:**
```json
{
  "tony_s_office_ceiling_fan_light": {
    "friendly_name": "Tony's Office Ceiling Fan Light",
    "name": "Office Fan Light"
  }
}
```

**Generated YAML:**
```yaml
light:
  - platform: template
    lights:
      tony_s_office_ceiling_fan_light:
        friendly_name: "Office Fan Light"  # Uses 'name'
```

**In Home Assistant:**
- Entity ID: `light.tony_s_office_ceiling_fan_light`
- Display Name: "Office Fan Light"

### Use Cases

**Shorter Names:**
```json
{
  "friendly_name": "Tony's Office Ceiling Fan Light",
  "name": "Office Fan"
}
```

**Nicknames:**
```json
{
  "friendly_name": "Living Room Ceiling Fan",
  "name": "Big Fan"
}
```

**Abbreviations:**
```json
{
  "friendly_name": "Master Bedroom Ceiling Fan",
  "name": "MB Fan"
}
```

## Icon Customization

### How It Works

Icons are automatically suggested during auto-detection based on entity type and device name. You can override them with any Material Design Icon (MDI).

**Important**: Home Assistant's template platform has limited support for `icon_template`:
- ✅ **Lights**: Full support for `icon_template`
- ✅ **Switches**: Full support for `icon_template`
- ❌ **Fans**: No support - icons must be set via HA entity customization
- ❌ **Media Players**: No support - icons must be set via HA entity customization

For fans and media players, the icon is stored in metadata but must be applied manually via Home Assistant's UI.

### Auto-Suggested Icons

**Lights:**
- `ceiling` → `mdi:ceiling-light`
- `lamp` → `mdi:lamp`
- `floor` → `mdi:floor-lamp`
- `pendant` → `mdi:ceiling-light-outline`
- `wall` → `mdi:wall-sconce`
- Default → `mdi:lightbulb`

**Fans:**
- `ceiling` → `mdi:ceiling-fan`
- `tower` → `mdi:fan`
- Default → `mdi:fan`

**Switches:**
- `outlet` or `plug` → `mdi:power-plug`
- `power` → `mdi:power`
- Default → `mdi:light-switch`

**Media Players:**
- `tv` → `mdi:television`
- `speaker` → `mdi:speaker`
- `receiver` → `mdi:amplifier`
- `projector` → `mdi:projector`
- Default → `mdi:play-box`

### Custom Icons

**Example:**
```json
{
  "living_room_ceiling_fan": {
    "icon": "mdi:ceiling-fan-light"
  }
}
```

**Generated YAML:**
```yaml
fan:
  - platform: template
    fans:
      living_room_ceiling_fan:
        icon_template: "mdi:ceiling-fan-light"
```

### Finding Icons

Browse all available icons at:
- https://pictogrammers.com/library/mdi/
- https://materialdesignicons.com/

Common patterns:
- `mdi:ceiling-fan`
- `mdi:ceiling-fan-light`
- `mdi:lightbulb`
- `mdi:lamp`
- `mdi:television`
- `mdi:speaker`

## Complete Example

### Metadata File

```json
{
  "version": 1,
  "entities": {
    "tony_s_office_ceiling_fan_light": {
      "entity_type": "light",
      "device": "tony_s_office_ceiling_fan",
      "broadlink_entity": "remote.kitchen_broadlink",
      "area": "Tony's Office",
      "commands": {
        "turn_on": "light_on",
        "turn_off": "light_off"
      },
      "friendly_name": "Tony's Office Ceiling Fan Light",
      "name": "Office Fan Light",
      "icon": "mdi:ceiling-fan-light",
      "enabled": true
    },
    "living_room_tv": {
      "entity_type": "media_player",
      "device": "living_room_tv",
      "broadlink_entity": "remote.living_room_broadlink",
      "area": "Living Room",
      "commands": {
        "turn_on": "power_on",
        "turn_off": "power_off",
        "volume_up": "vol_up",
        "volume_down": "vol_down"
      },
      "friendly_name": "Living Room TV",
      "name": "LR TV",
      "icon": "mdi:television-classic",
      "enabled": true
    },
    "bedroom_fan": {
      "entity_type": "fan",
      "device": "bedroom_ceiling_fan",
      "broadlink_entity": "remote.bedroom_broadlink",
      "area": "Bedroom",
      "commands": {
        "turn_off": "fan_off",
        "speed_1": "fan_speed_1",
        "speed_2": "fan_speed_2",
        "speed_3": "fan_speed_3"
      },
      "friendly_name": "Bedroom Ceiling Fan",
      "icon": "mdi:ceiling-fan",
      "enabled": true
    }
  }
}
```

### Generated YAML

```yaml
light:
  - platform: template
    lights:
      tony_s_office_ceiling_fan_light:
        unique_id: tony_s_office_ceiling_fan_light
        friendly_name: "Office Fan Light"
        icon_template: "mdi:ceiling-fan-light"
        value_template: "{{ is_state('input_boolean.tony_s_office_ceiling_fan_light_state', 'on') }}"
        turn_on:
          - service: remote.send_command
            target:
              entity_id: remote.kitchen_broadlink
            data:
              device: tony_s_office_ceiling_fan
              command: light_on
          - service: input_boolean.turn_on
            target:
              entity_id: input_boolean.tony_s_office_ceiling_fan_light_state
        turn_off:
          - service: remote.send_command
            target:
              entity_id: remote.kitchen_broadlink
            data:
              device: tony_s_office_ceiling_fan
              command: light_off
          - service: input_boolean.turn_off
            target:
              entity_id: input_boolean.tony_s_office_ceiling_fan_light_state

media_player:
  - platform: template
    media_players:
      living_room_tv:
        unique_id: living_room_tv
        friendly_name: "LR TV"
        icon_template: "mdi:television-classic"
        value_template: "{{ is_state('input_boolean.living_room_tv_state', 'on') }}"
        # ... rest of config

fan:
  - platform: template
    fans:
      bedroom_fan:
        unique_id: bedroom_fan
        friendly_name: "Bedroom Ceiling Fan"
        icon_template: "mdi:ceiling-fan"
        value_template: "{{ is_state('input_boolean.bedroom_fan_state', 'on') }}"
        # ... rest of config
```

## Editing Metadata

### Option 1: Via Web Interface (Future)

Future versions will include a web UI for editing these fields.

### Option 2: Direct File Edit

1. **Open metadata file:**
   ```bash
   nano /config/broadlink_manager/metadata.json
   ```

2. **Edit fields:**
   ```json
   {
     "entity_id": {
       "name": "Custom Name",
       "icon": "mdi:custom-icon"
     }
   }
   ```

3. **Regenerate YAML:**
   - Via web interface: Click "Generate Entities"
   - Via API: `POST /api/entities/generate`

4. **Restart Home Assistant**

### Option 3: Via API (Advanced)

```bash
# Update entity
POST /api/entities
{
  "entity_id": "living_room_fan",
  "entity_data": {
    "name": "LR Fan",
    "icon": "mdi:ceiling-fan-light",
    ...
  }
}

# Regenerate YAML
POST /api/entities/generate
```

## Customization vs HA Entity Registry

### Two Places for Customizations

**Broadlink Manager Metadata** (Source of Truth):
- Stored in `/config/broadlink_manager/metadata.json`
- Applied when generating YAML
- Survives regeneration
- Recommended for persistent customizations

**HA Entity Registry** (UI Overrides):
- Stored in `/config/.storage/core.entity_registry`
- Set via HA UI (Settings → Entities)
- Overrides YAML values
- Survives YAML regeneration
- Not in your "source of truth"

### Recommendation

**For persistent, version-controlled customizations:**
→ Edit Broadlink Manager metadata

**For quick, temporary changes:**
→ Edit via HA UI

## Migration from HA UI Customizations

If you've customized entities via HA UI and want to move them to metadata:

1. **Check current values in HA:**
   - Settings → Devices & Services → Entities
   - Note custom names and icons

2. **Update metadata:**
   ```json
   {
     "entity_id": {
       "name": "Value from HA UI",
       "icon": "Icon from HA UI"
     }
   }
   ```

3. **Regenerate and restart:**
   - Generate YAML
   - Restart HA
   - Values now match

4. **Optional: Clear HA customizations:**
   - In HA UI, reset name/icon to default
   - Your metadata values will be used

## Best Practices

### Naming

✅ **Do:**
- Use clear, descriptive names
- Be consistent across similar devices
- Consider voice assistant pronunciation
- Keep it short but meaningful

❌ **Don't:**
- Use special characters
- Make names too long
- Use ambiguous abbreviations
- Duplicate names across entities

### Icons

✅ **Do:**
- Choose icons that match device function
- Use consistent icon styles
- Test icons in HA UI
- Consider dashboard appearance

❌ **Don't:**
- Use unrelated icons
- Change icons frequently
- Use deprecated icons

### Organization

✅ **Do:**
- Document your customizations
- Use version control for metadata
- Backup metadata before major changes
- Test changes before applying widely

❌ **Don't:**
- Edit generated YAML files directly
- Skip regeneration after metadata changes
- Forget to restart HA after regeneration

## Troubleshooting

### Custom name not showing

**Check:**
1. Is `name` field set in metadata?
2. Did you regenerate YAML after editing?
3. Did you restart Home Assistant?
4. Is there an override in HA entity registry?

**Solution:**
```bash
# Verify metadata
cat /config/broadlink_manager/metadata.json | grep -A 5 "entity_id"

# Regenerate
POST /api/entities/generate

# Restart HA
```

### Custom icon not appearing

**Check:**
1. Is icon name correct? (must start with `mdi:`)
2. Does the icon exist? (check materialdesignicons.com)
3. Did you regenerate YAML?
4. Did you restart HA?

**Solution:**
```json
{
  "icon": "mdi:ceiling-fan"  // Correct format
}
```

### Changes reverted after regeneration

**Cause:** Editing generated YAML instead of metadata

**Solution:** Always edit metadata, then regenerate

## Summary

- **Name customization**: Use `name` field to override `friendly_name`
- **Icon customization**: Use `icon` field with MDI icon names
- **Auto-suggestions**: Icons suggested during auto-detection
- **Priority**: Metadata → YAML → HA Entity Registry
- **Best practice**: Edit metadata, not generated files
- **Workflow**: Edit metadata → Regenerate → Restart HA

Happy customizing! 🎨
