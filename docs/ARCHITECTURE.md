# Broadlink Manager Architecture

## Overview

Broadlink Manager creates Home Assistant entities (lights, fans, switches, media players) that are controlled via Broadlink IR/RF devices. This document explains the relationship between Broadlink devices, controlled devices, and areas.

## Key Concepts

### 1. Broadlink Device (Transmitter)
- **What it is**: The physical Broadlink hardware (e.g., RM4 Pro, RM Mini)
- **Location**: Can be anywhere with good IR/RF coverage
- **In Home Assistant**: Appears as `remote.xxx` entity
- **Example**: `remote.kitchen_broadlink` (physically located in Kitchen)

### 2. Controlled Device (Target)
- **What it is**: The actual device being controlled (fan, light, TV, etc.)
- **Location**: Can be in any room
- **In Home Assistant**: Created as template entities (light.xxx, fan.xxx, etc.)
- **Example**: `fan.living_room_ceiling_fan` (physically located in Living Room)

### 3. Area Assignment
- **Purpose**: Organizes entities by the location of the **controlled device**
- **Not related to**: The location of the Broadlink transmitter
- **Example**: A fan in the Living Room is assigned to "Living Room" area, even if controlled by a Broadlink in the Kitchen

## Data Model

### Entity Metadata Structure

```json
{
  "entities": {
    "living_room_ceiling_fan": {
      "entity_type": "fan",
      "device": "living_room_ceiling_fan",
      "broadlink_entity": "remote.kitchen_broadlink",
      "area": "Living Room",
      "commands": {
        "turn_on": "fan_on",
        "turn_off": "fan_off",
        "speed_1": "fan_speed_1",
        "speed_2": "fan_speed_2",
        "speed_3": "fan_speed_3"
      },
      "friendly_name": "Living Room Ceiling Fan",
      "name": "LR Fan",
      "icon": "mdi:ceiling-fan",
      "enabled": true
    }
  }
}
```

### Field Descriptions

| Field | Description | Example |
|-------|-------------|---------|
| `entity_type` | Type of HA entity to create | `fan`, `light`, `switch`, `media_player` |
| `device` | Command storage key in Broadlink | `living_room_ceiling_fan` |
| `broadlink_entity` | Which Broadlink remote sends commands | `remote.kitchen_broadlink` |
| `area` | Where the **controlled device** is located | `Living Room` |
| `commands` | Mapping of actions to learned command names | `{"turn_on": "fan_on"}` |
| `friendly_name` | Default display name (auto-generated) | `Living Room Ceiling Fan` |
| `name` | Custom display name (optional, overrides friendly_name) | `LR Fan` |
| `icon` | Custom MDI icon (optional) | `mdi:ceiling-fan` |
| `enabled` | Whether to generate this entity | `true` or `false` |

## Example Scenarios

### Scenario 1: Single Broadlink, Multiple Rooms

```
Kitchen Broadlink (remote.kitchen_broadlink)
  ├─ Controls: Living Room Fan (area: Living Room)
  ├─ Controls: Bedroom Fan (area: Bedroom)
  └─ Controls: Kitchen Light (area: Kitchen)
```

**Metadata:**
```json
{
  "living_room_fan": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Living Room"
  },
  "bedroom_fan": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Bedroom"
  },
  "kitchen_light": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Kitchen"
  }
}
```

### Scenario 2: Multiple Broadlinks

```
Kitchen Broadlink (remote.kitchen_broadlink)
  ├─ Controls: Living Room TV (area: Living Room)
  └─ Controls: Kitchen Light (area: Kitchen)

Bedroom Broadlink (remote.bedroom_broadlink)
  ├─ Controls: Bedroom Fan (area: Bedroom)
  └─ Controls: Bedroom Light (area: Bedroom)
```

**Metadata:**
```json
{
  "living_room_tv": {
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Living Room"
  },
  "bedroom_fan": {
    "broadlink_entity": "remote.bedroom_broadlink",
    "area": "Bedroom"
  }
}
```

## How It Works

### 1. Learning Commands
1. Commands are learned using a specific Broadlink device
2. Stored in `/config/.storage/broadlink_remote_<unique_id>_codes`
3. Organized by device name (e.g., `living_room_ceiling_fan`)

### 2. Creating Entities
1. User selects which commands to use
2. User specifies:
   - **Broadlink Entity**: Which remote sends the commands
   - **Area**: Where the controlled device is located
3. Entity metadata is saved to `/config/broadlink_manager/metadata.json`

### 3. Generating YAML
1. Generator reads metadata
2. For each entity, creates template configuration
3. Uses `broadlink_entity` field to determine which remote to call
4. Generated entities appear in the specified area

### 4. Generated YAML Example

```yaml
fan:
  - platform: template
    fans:
      living_room_ceiling_fan:
        friendly_name: "Living Room Ceiling Fan"
        turn_on:
          - service: remote.send_command
            target:
              entity_id: remote.kitchen_broadlink  # From broadlink_entity field
            data:
              device: living_room_ceiling_fan
              command: fan_on
```

## Migration from Old Approach

### Old Approach (Area from Name)
- Entity name: `tony_s_office_ceiling_fan`
- Area extracted from name: "Tony's Office"
- **Problem**: Assumes Broadlink is in same area as controlled device

### New Approach (Explicit Assignment)
- Entity name: `tony_s_office_ceiling_fan`
- Area: Explicitly set to "Tony's Office"
- Broadlink: Explicitly set to `remote.kitchen_broadlink`
- **Benefit**: Broadlink can be anywhere; area represents actual device location

### Backward Compatibility
- If `broadlink_entity` is not specified, falls back to default device ID
- Existing entities continue to work
- Can be migrated by adding `broadlink_entity` field to metadata

## Best Practices

1. **Name entities by function and location**: `living_room_ceiling_fan`, not `broadlink_fan_1`
2. **Set area to controlled device location**: Where the fan/light/TV is, not where the Broadlink is
3. **Choose closest Broadlink**: Use the Broadlink with best signal coverage to the target device
4. **Test coverage**: Verify commands work reliably from the chosen Broadlink location
5. **Document your setup**: Note which Broadlink controls which devices in your documentation

## Troubleshooting

### Commands not working
- **Check**: Is the `broadlink_entity` field correct?
- **Check**: Is the Broadlink device online and reachable?
- **Check**: Does the Broadlink have line-of-sight to the target device?

### Entity in wrong area
- **Fix**: Update the `area` field in metadata to the controlled device's location
- **Remember**: Area is for the target device, not the Broadlink

### Want to switch Broadlink devices
- **Fix**: Update the `broadlink_entity` field in metadata
- **Regenerate**: Run entity generation to update YAML files
- **Restart**: Restart Home Assistant to apply changes
