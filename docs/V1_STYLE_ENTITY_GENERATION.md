# V1-Style Entity Generation Implementation Plan

## Overview
Restore v1-style entity generation with state tracking, helpers, and smart features while using the new devices.json structure.

## Key Differences: V1 vs V2

### V1 (Target - Working System)
- **State Tracking**: Uses input_booleans to track device state
- **Smart Entities**: Template entities with value_template reading helpers
- **Multiple Actions**: turn_on/turn_off execute multiple actions (send command + update helper)
- **Command Format**: Uses device/command names (`device: xxx, command: yyy`)
- **Helper Files**: Generates helpers.yaml with input_booleans and input_selects
- **Smart Features**: Fan speed control, direction control, percentage templates
- **Entity Types**: light, switch, fan, media_player, cover

### V2 (Current - Simple System)
- **No State Tracking**: Entities always show as "off"
- **Simple Entities**: Just send raw base64 commands
- **Single Action**: turn_on/turn_off only send command
- **Command Format**: Uses raw base64 data
- **No Helpers**: No helper entities generated
- **No Smart Features**: Each command is a separate entity
- **Entity Types**: Only light, switch, fan

## Implementation Strategy

### Phase 1: Data Structure Analysis
Need to determine entity configuration from devices.json:
- Device has commands (learned IR/RF codes)
- Need to infer entity type from command names
- Need to group commands by logical device

### Phase 2: Helper Generation
Generate helpers.yaml with:
```yaml
input_boolean:
  {device_id}_state:
    name: {Device Name} State
    initial: false

input_select:
  {device_id}_speed:  # For fans
    name: {Device Name} Speed
    options: ['off', '1', '2', '3', '4', '5', '6']
    initial: 'off'
```

### Phase 3: Entity Generation Patterns

#### Light Entity
```yaml
light:
- platform: template
  lights:
    device_name:
      unique_id: device_name
      friendly_name: Device Name
      value_template: "{{ is_state('input_boolean.device_name_state', 'on') }}"
      turn_on:
      - service: remote.send_command
        target:
          entity_id: remote.broadlink_device
        data:
          device: device_name
          command: toggle  # or turn_on
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.device_name_state
      turn_off:
      - service: remote.send_command
        target:
          entity_id: remote.broadlink_device
        data:
          device: device_name
          command: toggle  # or turn_off
      - service: input_boolean.turn_off
        target:
          entity_id: input_boolean.device_name_state
```

#### Fan Entity (with speed control)
```yaml
fan:
- platform: template
  fans:
    device_name:
      unique_id: device_name
      friendly_name: Device Name
      value_template: "{{ is_state('input_boolean.device_name_state', 'on') }}"
      speed_count: 6
      percentage_template: "{% if is_state('input_select.device_name_speed', 'off') %}0{% elif ... %}"
      turn_on:
      - service: remote.send_command
        data:
          device: device_name
          command: fan_speed_3
      - service: input_boolean.turn_on
        target:
          entity_id: input_boolean.device_name_state
      - service: input_select.select_option
        data:
          option: '3'
      turn_off:
      - service: remote.send_command
        data:
          device: device_name
          command: fan_off
      - service: input_boolean.turn_off
      set_percentage:
      - service: input_select.select_option
        data:
          option: "{% if percentage == 0 %}off{% elif ... %}"
      - service: remote.send_command
        data:
          device: device_name
          command: "{% if percentage == 0 %}fan_off{% elif ... %}"
```

### Phase 4: Command Name Inference
Need to detect entity type and commands from learned command names:

**Light Patterns:**
- `toggle`, `turn_on`, `turn_off`
- `brightness_up`, `brightness_down`
- `*_light_*` in name

**Fan Patterns:**
- `fan_speed_1` through `fan_speed_6`
- `fan_off`, `fan_on`
- `fan_reverse`, `fan_forward`

**Switch Patterns:**
- `power`, `on`, `off`
- Simple toggle commands

### Phase 5: Migration Path
1. Keep entity_generator_v2.py as is (rename to entity_generator_v2_simple.py)
2. Create new entity_generator_v2_stateful.py with v1 logic
3. Update web_server.py to use new generator
4. Add configuration option to choose simple vs stateful generation

## Files to Modify
1. `app/entity_generator_v2.py` - Major refactor
2. `app/web_server.py` - Update to use new generator
3. `app/api/entities.py` - May need updates for new structure

## Testing Plan
1. Generate entities for test devices
2. Verify helpers.yaml created correctly
3. Verify entities.yaml has proper structure
4. Verify package.yaml combines both
5. Test in Home Assistant - verify config loads
6. Test entity state tracking works
7. Test fan speed control works

## Rollback Plan
- Keep v2_simple version as backup
- Git commit before major changes
- Can revert to simple generation if needed
