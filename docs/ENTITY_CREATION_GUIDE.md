# Entity Creation Guide

## High-Level Overview

Broadlink Manager creates Home Assistant entities (lights, fans, switches, media players) that control your IR/RF devices through Broadlink hardware. This document explains the complete workflow from learning commands to having working entities in Home Assistant.

### Quick Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENTITY CREATION WORKFLOW                      │
└─────────────────────────────────────────────────────────────────┘

1. Learn Commands          2. Store in HA           3. Track in BL Manager
   ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
   │ Press button │   →      │ .storage/    │   →     │ devices.json │
   │ on remote    │          │ broadlink_*  │         │              │
   └──────────────┘          └──────────────┘         └──────────────┘

4. Generate YAML           5. Create Helpers        6. Restart HA
   ┌──────────────┐          ┌──────────────┐         ┌──────────────┐
   │ devices.json │   →      │ helpers.yaml │   →     │ Entities     │
   │ → YAML files │          │ (state track)│         │ Available    │
   └──────────────┘          └──────────────┘         └──────────────┘
```

### Key Concepts

- **Broadlink Device**: Physical IR/RF transmitter (e.g., RM4 Pro) - the hardware that sends signals
- **Controlled Device**: The device you want to control (TV, fan, light) - the target
- **Commands**: IR/RF codes learned from your original remote
- **Device Configuration**: Stored in `devices.json` - defines device settings and entity generation
- **Template Entities**: Home Assistant entities that use the Broadlink remote to send commands
- **Helper Entities**: `input_boolean` entities that track device state (on/off)

---

## The Complete Workflow

### Phase 1: Command Learning

Commands are learned using Home Assistant's Broadlink integration and stored in HA's internal storage.

#### Storage Location
```
/config/.storage/broadlink_remote_<unique_id>_codes
```

#### Storage Format
```json
{
  "version": 1,
  "data": {
    "codes": {
      "living_room_tv": {
        "power_on": "JgBQAAABKZIUEhQ...",
        "power_off": "JgBQAAABKZIUEhQ...",
        "volume_up": "JgBQAAABKZIUEhQ..."
      }
    }
  }
}
```

**Important Notes:**
- Commands are organized by device name (e.g., `living_room_tv`)
- Each command is stored as base64-encoded IR/RF data
- Home Assistant writes to this file with 10-30 second latency
- Multiple Broadlink devices have separate storage files

**Related Documentation:**
- Command learning process: See [ARCHITECTURE.md](ARCHITECTURE.md#2-learning-commands-broadlink-devices)

---

### Phase 2: Device Tracking

Broadlink Manager tracks which devices you want to manage and their commands.

#### Storage Location
```
/config/broadlink_manager/devices.json
```

#### Device Structure
```json
{
  "devices": {
    "living_room_tv": {
      "device_id": "living_room_tv",
      "device_type": "broadlink",
      "device_name": "Living Room TV",
      "broadlink_entity": "remote.kitchen_rm4_pro",
      "area": "Living Room",
      "commands": {
        "power_on": "power_on",
        "power_off": "power_off",
        "volume_up": "volume_up",
        "volume_down": "volume_down"
      },
      "created_at": "2025-10-15T19:30:00Z"
    }
  }
}
```

**Key Fields:**
- `device_id`: Unique identifier matching the device name in Broadlink storage
- `device_type`: Either `broadlink` (IR/RF) or `smartir` (pre-configured codes)
- `broadlink_entity`: Which Broadlink remote will send the commands
- `area`: Where the controlled device is physically located
- `commands`: Available commands for this device

**Related Documentation:**
- Device management: See [ARCHITECTURE.md](ARCHITECTURE.md#data-model)

---

### Phase 3: YAML Generation

Broadlink Manager generates Home Assistant YAML configuration files directly from `devices.json`.

#### Generated Files
```
/config/packages/broadlink_manager/
├── light.yaml
├── fan.yaml
├── switch.yaml
├── media_player.yaml
└── helpers.yaml
```

#### Example: Light Entity

**Input (devices.json):**
```json
{
  "devices": {
    "office_ceiling_fan": {
      "device_id": "office_ceiling_fan",
      "device_type": "broadlink",
      "device_name": "Office Ceiling Fan Light",
      "broadlink_entity": "remote.kitchen_rm4_pro",
      "area": "Office",
      "commands": {
        "light_on": "light_on",
        "light_off": "light_off"
      },
      "entity_type": "light",
      "created_at": "2025-10-15T19:30:00Z"
    }
  }
}
```

**Entity Type Detection:**
- Explicitly set via `entity_type` field in device config
- Or auto-detected from command names (e.g., `light_on` → light entity)
- Or inferred from device name (e.g., "light" in name → light entity)

**Output (light.yaml):**
```yaml
light:
  - platform: template
    lights:
      office_ceiling_fan_light:
        unique_id: office_ceiling_fan_light
        friendly_name: "Office Fan Light"
        icon_template: "mdi:ceiling-fan-light"
        value_template: "{{ is_state('input_boolean.office_ceiling_fan_light_state', 'on') }}"
        turn_on:
          - service: remote.send_command
            target:
              entity_id: remote.kitchen_rm4_pro
            data:
              device: office_ceiling_fan
              command: light_on
          - service: input_boolean.turn_on
            target:
              entity_id: input_boolean.office_ceiling_fan_light_state
        turn_off:
          - service: remote.send_command
            target:
              entity_id: remote.kitchen_rm4_pro
            data:
              device: office_ceiling_fan
              command: light_off
          - service: input_boolean.turn_off
            target:
              entity_id: input_boolean.office_ceiling_fan_light_state
```

**Output (helpers.yaml):**
```yaml
input_boolean:
  office_ceiling_fan_light_state:
    name: "Office Ceiling Fan Light State"
    icon: mdi:ceiling-fan-light
```

**How It Works:**
1. **Template Entity**: Creates a virtual entity that doesn't directly control hardware
2. **Value Template**: Reads state from helper entity (`input_boolean`)
3. **Turn On Action**: 
   - Sends IR/RF command via Broadlink remote
   - Updates helper entity to "on"
4. **Turn Off Action**:
   - Sends IR/RF command via Broadlink remote
   - Updates helper entity to "off"
5. **State Tracking**: Helper entity maintains state between HA restarts

**Related Documentation:**
- Complete YAML examples: See [CUSTOMIZATION.md](CUSTOMIZATION.md#complete-example)

---

### Phase 4: Home Assistant Integration

After YAML generation, Home Assistant needs to load the new entities.

#### Integration Steps

1. **YAML Files Created**
   ```
   /config/packages/broadlink_manager/
   ```

2. **HA Configuration Includes Packages**
   ```yaml
   # configuration.yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

3. **Restart Home Assistant**
   - HA reads YAML files
   - Creates template entities
   - Creates helper entities
   - Entities appear in UI

4. **Entities Available**
   - Entity ID: `light.office_ceiling_fan_light`
   - Display Name: "Office Fan Light"
   - Area: "Tony's Office"
   - State: Tracked via helper

---

## Entity Types and Command Mappings

Different entity types support different actions and commands.

### Light Entities

**Required Commands:**
- `turn_on` - Turn light on
- `turn_off` - Turn light off

**Optional Commands:**
- `brightness_up` - Increase brightness
- `brightness_down` - Decrease brightness

**Example:**
```json
{
  "entity_type": "light",
  "commands": {
    "turn_on": "light_on",
    "turn_off": "light_off"
  }
}
```

---

### Fan Entities

**Required Commands:**
- `turn_off` - Turn fan off
- `speed_1` - Low speed
- `speed_2` - Medium speed
- `speed_3` - High speed

**Optional Commands:**
- `oscillate_on` - Start oscillation
- `oscillate_off` - Stop oscillation
- `direction_forward` - Forward direction
- `direction_reverse` - Reverse direction

**Example:**
```json
{
  "entity_type": "fan",
  "commands": {
    "turn_off": "fan_off",
    "speed_1": "fan_low",
    "speed_2": "fan_medium",
    "speed_3": "fan_high",
    "oscillate_on": "fan_oscillate_on",
    "oscillate_off": "fan_oscillate_off"
  }
}
```

**Generated Features:**
- Speed control (percentage-based)
- Preset modes (Low, Medium, High)
- Oscillation toggle
- Direction control (if commands provided)

---

### Switch Entities

**Required Commands:**
- `turn_on` - Turn switch on
- `turn_off` - Turn switch off

**Example:**
```json
{
  "entity_type": "switch",
  "commands": {
    "turn_on": "power_on",
    "turn_off": "power_off"
  }
}
```

---

### Media Player Entities

**Required Commands:**
- `turn_on` - Power on
- `turn_off` - Power off

**Optional Commands:**
- `volume_up` - Increase volume
- `volume_down` - Decrease volume
- `mute` - Toggle mute
- `source_hdmi1` - Switch to HDMI 1
- `source_hdmi2` - Switch to HDMI 2
- (etc.)

**Example:**
```json
{
  "entity_type": "media_player",
  "commands": {
    "turn_on": "power_on",
    "turn_off": "power_off",
    "volume_up": "vol_up",
    "volume_down": "vol_down",
    "mute": "mute_toggle",
    "source_hdmi1": "input_hdmi1",
    "source_hdmi2": "input_hdmi2"
  }
}
```

**Generated Features:**
- Power control
- Volume control
- Source selection (if source commands provided)
- Mute toggle

---

## Relationship Diagrams

### Data Flow: Command to Entity

```
┌─────────────────────────────────────────────────────────────────────┐
│                         COMMAND LEARNING                             │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Home Assistant Storage   │
                    │ .storage/broadlink_*     │
                    │                          │
                    │ {                        │
                    │   "living_room_tv": {    │
                    │     "power_on": "JgB..." │
                    │   }                      │
                    │ }                        │
                    └──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DEVICE TRACKING                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Broadlink Manager        │
                    │ devices.json             │
                    │                          │
                    │ {                        │
                    │   "living_room_tv": {    │
                    │     "device_type": "..." │
                    │     "entity_type": "..." │
                    │     "commands": {...}    │
                    │   }                      │
                    │ }                        │
                    └──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      YAML GENERATION                                 │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Generated YAML Files     │
                    │ packages/broadlink_*/    │
                    │                          │
                    │ - media_player.yaml      │
                    │ - helpers.yaml           │
                    └──────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      HOME ASSISTANT                                  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ Working Entity           │
                    │ media_player.            │
                    │   living_room_tv         │
                    └──────────────────────────┘
```

### Entity Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HOME ASSISTANT ENTITY                             │
│                  media_player.living_room_tv                         │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌────────────────────┐      ┌────────────────────┐
        │ Template Entity    │      │ Helper Entity      │
        │ (Virtual)          │      │ (State Storage)    │
        │                    │      │                    │
        │ - turn_on action   │◄─────│ input_boolean.     │
        │ - turn_off action  │      │   living_room_tv_  │
        │ - value_template   │      │   state            │
        └────────────────────┘      └────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │ Broadlink Remote   │
        │ remote.kitchen_    │
        │   rm4_pro          │
        │                    │
        │ - send_command     │
        └────────────────────┘
                    │
                    ▼
        ┌────────────────────┐
        │ Physical Device    │
        │ (TV, Fan, etc.)    │
        └────────────────────┘
```

---

## Configuration Relationships

### Broadlink Entity Selection

The `broadlink_entity` field determines which physical Broadlink device sends the commands.

**Example Scenario:**
```
Kitchen Broadlink (remote.kitchen_rm4_pro)
  ├─ Controls: Living Room TV (area: Living Room)
  ├─ Controls: Bedroom Fan (area: Bedroom)
  └─ Controls: Kitchen Light (area: Kitchen)
```

**Key Points:**
- One Broadlink can control devices in multiple rooms
- Choose the Broadlink with best signal coverage to the target device
- The Broadlink's location doesn't determine the entity's area
- Multiple entities can use the same Broadlink

**Related Documentation:**
- Area assignment: See [ARCHITECTURE.md](ARCHITECTURE.md#3-area-assignment)

---

### Area Assignment

The `area` field determines where the entity appears in Home Assistant's area organization.

**Important:**
- Area refers to where the **controlled device** is located
- NOT where the Broadlink transmitter is located

**Example:**
```json
{
  "bedroom_fan": {
    "broadlink_entity": "remote.kitchen_rm4_pro",
    "area": "Bedroom"
  }
}
```

This creates an entity in the "Bedroom" area, even though the Broadlink is in the Kitchen.

---

### Command Name Mapping

Commands in `devices.json` reference learned command names in Broadlink storage.

**Broadlink Storage:**
```json
{
  "living_room_tv": {
    "samsung_power": "JgBQAAAB...",
    "samsung_vol_up": "JgBQAAAB...",
    "samsung_vol_down": "JgBQAAAB..."
  }
}
```

**devices.json:**
```json
{
  "devices": {
    "living_room_tv": {
      "device_id": "living_room_tv",
      "device_type": "broadlink",
      "commands": {
        "samsung_power": "samsung_power",
        "samsung_vol_up": "samsung_vol_up",
        "samsung_vol_down": "samsung_vol_down"
      }
    }
  }
}
```

**Generated YAML:**
```yaml
turn_on:
  - service: remote.send_command
    data:
      device: living_room_tv
      command: samsung_power
```

**Key Points:**
- Left side: HA action name (standardized)
- Right side: Learned command name (your choice)
- Same command can be mapped to multiple actions (e.g., toggle power)

---

## Workflow Examples

### Example 1: Creating a Light Entity

**Step 1: Learn Commands**
```
Device Name: office_ceiling_fan
Commands:
  - light_on
  - light_off
```

**Step 2: Device Tracked Automatically**
```json
{
  "devices": {
    "office_ceiling_fan": {
      "device_id": "office_ceiling_fan",
      "device_type": "broadlink",
      "device_name": "Office Ceiling Fan",
      "broadlink_entity": "remote.kitchen_rm4_pro",
      "area": "Office",
      "commands": {
        "light_on": "light_on",
        "light_off": "light_off"
      },
      "entity_type": "light",
      "created_at": "2025-10-15T19:30:00Z"
    }
  }
}
```

**Step 3: Generate YAML**
- Click "Generate Entities" in Broadlink Manager
- Entity type auto-detected from commands or explicitly set
- Files created in `/config/packages/broadlink_manager/`

**Step 4: Restart Home Assistant**
- Entity appears as `light.office_ceiling_fan`
- Display name: "Office Ceiling Fan"
- Area: "Office"

---

### Example 2: Creating a Fan with Speed Control

**Step 1: Learn Commands**
```
Device Name: bedroom_ceiling_fan
Commands:
  - fan_off
  - fan_low
  - fan_medium
  - fan_high
  - fan_oscillate_on
  - fan_oscillate_off
```

**Step 2: Device Configuration in devices.json**
```json
{
  "devices": {
    "bedroom_ceiling_fan": {
      "device_id": "bedroom_ceiling_fan",
      "device_type": "broadlink",
      "device_name": "Bedroom Ceiling Fan",
      "broadlink_entity": "remote.bedroom_rm4_pro",
      "area": "Bedroom",
      "commands": {
        "fan_off": "fan_off",
        "fan_low": "fan_low",
        "fan_medium": "fan_medium",
        "fan_high": "fan_high",
        "fan_oscillate_on": "fan_oscillate_on",
        "fan_oscillate_off": "fan_oscillate_off"
      },
      "entity_type": "fan",
      "created_at": "2025-10-15T19:30:00Z"
    }
  }
}
```

**Step 3: Generated Features**
- Speed control: Low (33%), Medium (66%), High (100%)
- Preset modes: "Low", "Medium", "High"
- Oscillation toggle
- State tracking via helper entity

---

## Troubleshooting

### Entity Not Appearing

**Check:**
1. Is the device configured in `devices.json`?
2. Did you regenerate YAML after adding the device?
3. Did you restart Home Assistant?
4. Check HA logs for YAML errors

**Solution:**
```bash
# Verify device configuration
cat /config/broadlink_manager/devices.json

# Regenerate YAML via Broadlink Manager UI
# Click "Generate Entities" button

# Check generated files
ls -la /config/packages/broadlink_manager/

# Restart HA and check logs
```

---

### Commands Not Working

**Check:**
1. Is the `broadlink_entity` correct?
2. Is the Broadlink device online?
3. Is the `device` name correct (matches Broadlink storage)?
4. Is the `command` name correct (matches learned command)?

**Solution:**
```bash
# Test command manually
service: remote.send_command
target:
  entity_id: remote.kitchen_rm4_pro
data:
  device: office_ceiling_fan
  command: light_on
```

**Related Documentation:**
- Troubleshooting guide: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

### Entity State Not Updating

**Check:**
1. Is the helper entity created?
2. Is the helper entity being updated in turn_on/turn_off actions?
3. Check helper entity state in HA Developer Tools

**Solution:**
```bash
# Check helper exists
ls /config/packages/broadlink_manager/helpers.yaml

# Verify helper state
Developer Tools → States → input_boolean.entity_name_state

# Manually toggle helper
service: input_boolean.toggle
target:
  entity_id: input_boolean.office_ceiling_fan_light_state
```

---

### Wrong Area Assignment

**Check:**
1. Is the `area` field set correctly in `devices.json`?
2. Did you regenerate YAML after changing area?
3. Did you restart HA?

**Solution:**
Edit the device in `devices.json`:
```json
{
  "devices": {
    "device_id": {
      "area": "Correct Room Name"
    }
  }
}
```

Then regenerate YAML and restart HA.

---

## Best Practices

### Naming Conventions

**Device Names (Broadlink Storage):**
- Use lowercase with underscores
- Be descriptive and unique
- Example: `living_room_tv`, `bedroom_ceiling_fan`

**Entity IDs (Metadata):**
- Use lowercase with underscores
- Include room and device type
- Example: `living_room_tv`, `bedroom_ceiling_fan_light`

**Display Names:**
- Use Title Case
- Be concise but clear
- Example: "Living Room TV", "Bedroom Fan Light"

---

### Command Organization

**Group Related Commands:**
```json
{
  "living_room_tv": {
    "power_on": "...",
    "power_off": "...",
    "vol_up": "...",
    "vol_down": "...",
    "hdmi1": "...",
    "hdmi2": "..."
  }
}
```

**Use Descriptive Command Names:**
- ✅ `fan_speed_low`, `fan_speed_medium`, `fan_speed_high`
- ❌ `cmd1`, `cmd2`, `cmd3`

---

### Device Configuration Management

**Version Control:**
- Keep `devices.json` in version control
- Document changes in commit messages
- Backup before major changes

**Testing:**
- Test commands before generating entities
- Verify Broadlink coverage for each device
- Test entity actions after generation

**Documentation:**
- Document device configurations and command mappings
- Note any special requirements
- Keep track of which Broadlink controls which devices

---

## Related Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Overall system architecture and data model
- **[CUSTOMIZATION.md](CUSTOMIZATION.md)** - Entity customization options and examples
- **[AUTOMATION_EXAMPLES.md](AUTOMATION_EXAMPLES.md)** - Using entities in automations
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[API.md](API.md)** - API endpoints for entity generation

---

## Summary

Entity creation in Broadlink Manager v2 follows a streamlined pipeline:

1. **Learn Commands** → Stored in HA's Broadlink storage (`.storage/broadlink_remote_*_codes`)
2. **Track Devices** → Automatically synced to `devices.json` with device configuration
3. **Generate YAML** → Template entities and helpers created directly from `devices.json`
4. **Restart HA** → Entities become available

Each step builds on the previous one, with clear separation between:
- **Command Storage** (Home Assistant's responsibility)
- **Device Management** (Broadlink Manager tracks in `devices.json`)
- **YAML Generation** (Automated by Broadlink Manager from device config)
- **Entity Creation** (Home Assistant reads generated YAML)

**Key Points:**
- All device configuration is in `devices.json` - single source of truth
- Entity type is auto-detected from commands or explicitly set in device config
- No separate metadata file needed - everything is in the device configuration
- Automatic command sync keeps `devices.json` in sync with Broadlink storage

This streamlined approach allows for flexible configuration, easy troubleshooting, and maintainable smart home setups.
