# Entity Auto-Generation Feature

## Overview

The Broadlink Manager addon now includes automatic entity generation, allowing you to create Home Assistant entities (lights, fans, switches) directly from your learned IR/RF commands.

## Architecture

### Components

1. **StorageManager** (`app/storage_manager.py`)
   - Manages entity metadata in `/config/broadlink_manager/metadata.json`
   - Provides CRUD operations for entity configurations
   - Generates README and setup instructions

2. **EntityDetector** (`app/entity_detector.py`)
   - Pattern matching for command names
   - Auto-detects entity types (light, fan, switch, media_player)
   - Groups commands into logical entities
   - Validates entity configurations

3. **EntityGenerator** (`app/entity_generator.py`)
   - Generates YAML configuration files
   - Creates template lights, fans, and switches
   - Generates helper entities (input_boolean, input_select)
   - Produces setup instructions

### Storage Structure

```
/config/broadlink_manager/
├── README.md              # Auto-generated setup guide
├── metadata.json          # Entity configurations (user data)
├── entities.yaml          # Generated HA entities (auto-generated)
└── helpers.yaml           # Generated helpers (auto-generated)
```

### Metadata Format

```json
{
  "version": 1,
  "entities": {
    "office_ceiling_fan_light": {
      "entity_type": "light",
      "device": "tony_s_office_ceiling_fan",
      "commands": {
        "turn_on": "light_on",
        "turn_off": "light_off"
      },
      "device_id": "e7c20e68cc76d2877b2bfc829f7c8272",
      "enabled": true,
      "friendly_name": "Office Ceiling Fan Light"
    },
    "office_ceiling_fan": {
      "entity_type": "fan",
      "device": "tony_s_office_ceiling_fan",
      "commands": {
        "turn_off": "fan_off",
        "speed_1": "fan_speed_1",
        "speed_2": "fan_speed_2",
        "speed_3": "fan_speed_3",
        "speed_4": "fan_speed_4",
        "speed_5": "fan_speed_5",
        "speed_6": "fan_speed_6",
        "reverse": "fan_reverse"
      },
      "device_id": "e7c20e68cc76d2877b2bfc829f7c8272",
      "speed_count": 6,
      "enabled": true
    }
  },
  "last_generated": "2025-10-06T14:30:00"
}
```

## API Endpoints

### GET /api/entities
Get all configured entities with statistics.

**Response:**
```json
{
  "entities": { /* entity configurations */ },
  "stats": {
    "total_entities": 5,
    "entities_by_type": {
      "light": 3,
      "fan": 2
    },
    "last_generated": "2025-10-06T14:30:00"
  }
}
```

### POST /api/entities
Save or update an entity configuration.

**Request:**
```json
{
  "entity_id": "office_light",
  "entity_data": {
    "entity_type": "light",
    "device": "tony_s_office_ceiling_fan",
    "commands": {
      "turn_on": "light_on",
      "turn_off": "light_off"
    },
    "device_id": "abc123",
    "enabled": true
  }
}
```

### DELETE /api/entities/<entity_id>
Delete an entity configuration.

### POST /api/entities/detect
Auto-detect entities from commands.

**Request:**
```json
{
  "device_name": "tony_s_office_ceiling_fan",
  "commands": {
    "light_on": "scAAArCeB...",
    "light_off": "scCwBLCeB...",
    "fan_speed_1": "scAAArCeB..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "detected_entities": {
    "tony_s_office_ceiling_fan_light": {
      "entity_type": "light",
      "commands": {
        "turn_on": "light_on",
        "turn_off": "light_off"
      },
      "auto_detected": true
    }
  },
  "count": 1
}
```

### POST /api/entities/generate
Generate YAML entity files and automatically reload Home Assistant configuration.

**Request:**
```json
{
  "device_id": "e7c20e68cc76d2877b2bfc829f7c8272"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Entity files generated successfully. Configuration reloaded successfully.",
  "entities_count": 5,
  "entity_counts": {
    "light": 3,
    "fan": 2
  },
  "files": {
    "entities": "/config/broadlink_manager/entities.yaml",
    "helpers": "/config/broadlink_manager/helpers.yaml"
  },
  "config_reloaded": true,
  "instructions": {
    "step1": "Add to configuration.yaml:",
    "code": "light: !include broadlink_manager/entities.yaml\n...",
    "step2": "Check configuration",
    "step3": "Restart Home Assistant"
  }
}
```

**Note:** This endpoint automatically reloads both the Broadlink integration config entries and the Home Assistant YAML configuration, so new entities appear immediately without manual reload.

### GET /api/entities/types
Get supported entity types and their command roles.

**Response:**
```json
{
  "types": ["light", "fan", "switch", "media_player"],
  "roles": {
    "light": ["turn_on", "turn_off", "toggle"],
    "fan": ["turn_on", "turn_off", "speed_1", "speed_2", ...]
  }
}
```

## Command Naming Conventions

### Lights
- `light_on` / `light_off` - Separate on/off commands
- `light_toggle` - Single toggle command
- `lamp_on` / `lamp_off` - Alternative naming

### Fans
- `fan_speed_1` through `fan_speed_6` - Speed levels
- `fan_off` - Turn off
- `fan_on` - Turn on (optional)
- `fan_reverse` - Reverse direction
- `fan_low`, `fan_medium`, `fan_high` - Named speeds

### Switches
- `on` / `off` - Simple on/off
- `toggle` - Single toggle
- `power` - Power toggle

### Media Players (Coming Soon)
- `power`, `vol_up`, `vol_down`, `mute`
- `play`, `pause`, `stop`
- `ch_up`, `ch_down`

## Entity Types

### Template Light
Generated configuration:
```yaml
light:
  - platform: template
    lights:
      office_light:
        friendly_name: "Office Light"
        value_template: "{{ is_state('input_boolean.office_light_state', 'on') }}"
        turn_on:
          - service: remote.send_command
            target:
              device_id: abc123
            data:
              device: tony_s_office_ceiling_fan
              command: light_on
          - service: input_boolean.turn_on
            target:
              entity_id: input_boolean.office_light_state
        turn_off:
          - service: remote.send_command
            target:
              device_id: abc123
            data:
              device: tony_s_office_ceiling_fan
              command: light_off
          - service: input_boolean.turn_off
            target:
              entity_id: input_boolean.office_light_state
```

### Template Fan
Includes speed control with percentage support and direction control.

**Features:**
- Percentage-based speed control (automatically calculated from speed count)
- Direction control (forward/reverse) - always included
- Optional `fan_off` command (falls back to lowest speed if not available)
- State tracking via input_boolean and input_select helpers

**Generated configuration:**
```yaml
fan:
  - platform: template
    fans:
      office_ceiling_fan:
        friendly_name: "Office Ceiling Fan"
        value_template: "{{ is_state('input_boolean.office_ceiling_fan_state', 'on') }}"
        speed_count: 6
        percentage_template: |
          {%- if is_state('input_select.office_ceiling_fan_speed', 'off') -%}
            0
          {%- elif is_state('input_select.office_ceiling_fan_speed', '1') -%}
            16
          {%- elif is_state('input_select.office_ceiling_fan_speed', '2') -%}
            33
          ...
          {%- endif -%}
        direction_template: "{{ states('input_select.office_ceiling_fan_direction') }}"
        turn_on:
          - service: remote.send_command
            target:
              entity_id: remote.broadlink_rm4_pro
            data:
              device: office_ceiling_fan
              command: fan_speed_3  # Default to medium speed
          - service: input_boolean.turn_on
            target:
              entity_id: input_boolean.office_ceiling_fan_state
          - service: input_select.select_option
            target:
              entity_id: input_select.office_ceiling_fan_speed
            data:
              option: '3'
        turn_off:
          - service: remote.send_command
            target:
              entity_id: remote.broadlink_rm4_pro
            data:
              device: office_ceiling_fan
              command: fan_off  # Uses fan_off if available, otherwise lowest speed
          - service: input_boolean.turn_off
            target:
              entity_id: input_boolean.office_ceiling_fan_state
          - service: input_select.select_option
            target:
              entity_id: input_select.office_ceiling_fan_speed
            data:
              option: 'off'
        set_percentage:
          - service: input_select.select_option
            target:
              entity_id: input_select.office_ceiling_fan_speed
            data:
              option: "{% if percentage == 0 %}off{% elif percentage <= 16 %}1..."
          - service: remote.send_command
            target:
              entity_id: remote.broadlink_rm4_pro
            data:
              device: office_ceiling_fan
              command: "{% if percentage == 0 %}fan_off{% elif percentage <= 16 %}fan_speed_1..."
        set_direction:
          - service: remote.send_command  # Only included if fan_reverse command exists
            target:
              entity_id: remote.broadlink_rm4_pro
            data:
              device: office_ceiling_fan
              command: fan_reverse
          - service: input_select.select_option
            target:
              entity_id: input_select.office_ceiling_fan_direction
            data:
              option: "{% if direction == 'forward' %}reverse{% else %}forward{% endif %}"
```

**Required Helper Entities:**
```yaml
input_boolean:
  office_ceiling_fan_state:
    name: "Office Ceiling Fan State"
    initial: off

input_select:
  office_ceiling_fan_speed:
    name: "Office Ceiling Fan Speed"
    options:
      - 'off'
      - '1'
      - '2'
      - '3'
      - '4'
      - '5'
      - '6'
    initial: 'off'
  
  office_ceiling_fan_direction:
    name: "Office Ceiling Fan Direction"
    options:
      - 'forward'
      - 'reverse'
    initial: 'forward'
```

### Template Switch
Similar to light but simpler (no brightness control).

## UI Integration (To Be Implemented)

The UI will include:

1. **Entity Configuration Tab**
   - View all configured entities
   - Edit entity settings
   - Enable/disable entities

2. **Auto-Detection**
   - Scan learned commands
   - Suggest entity configurations
   - One-click entity creation

3. **Generation Interface**
   - Preview generated YAML
   - Generate button with progress
   - Setup instructions display

4. **Command Assignment**
   - Drag-and-drop command assignment
   - Visual entity builder
   - Command role selection

## Testing

### Manual Testing Steps

1. Learn commands with proper naming:
   ```
   tony_s_office_ceiling_fan.light_on
   tony_s_office_ceiling_fan.light_off
   tony_s_office_ceiling_fan.fan_speed_1
   ```

2. Test auto-detection:
   ```bash
   curl -X POST http://localhost:8099/api/entities/detect \
     -H "Content-Type: application/json" \
     -d '{
       "device_name": "tony_s_office_ceiling_fan",
       "commands": {
         "light_on": "...",
         "light_off": "..."
       }
     }'
   ```

3. Save entity:
   ```bash
   curl -X POST http://localhost:8099/api/entities \
     -H "Content-Type: application/json" \
     -d '{
       "entity_id": "office_light",
       "entity_data": { ... }
     }'
   ```

4. Generate YAML:
   ```bash
   curl -X POST http://localhost:8099/api/entities/generate \
     -H "Content-Type: application/json" \
     -d '{"device_id": "abc123"}'
   ```

5. Check generated files:
   ```bash
   ls -la /config/broadlink_manager/
   cat /config/broadlink_manager/entities.yaml
   ```

## Future Enhancements

- [ ] Media player entity support
- [ ] Climate entity support (AC units)
- [ ] Cover entity support (blinds, curtains)
- [ ] Entity templates/presets
- [ ] Bulk entity generation
- [ ] Entity import/export
- [ ] Visual entity editor in UI
- [ ] Real-time YAML preview
- [ ] Entity testing before generation
- [ ] Backup/restore entity configurations
