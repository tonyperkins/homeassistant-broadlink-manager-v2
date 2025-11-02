# Light Brightness and Color Temperature Support

## Overview

Enhanced the entity generator to support brightness and color temperature control for light entities with RF/IR commands.

## Changes Made

### 1. Entity Generator Updates (`app/entity_generator.py`)

#### Light Command Detection
Added detection for brightness and color temperature commands:
- **Brightness commands**: `brightness_up`, `brightness_down`, `bright`, `dim`
- **Color temperature commands**: `cooler`, `warmer`

#### Template Light Configuration
Enhanced `_generate_light()` method to:
- Add `level_template` for brightness tracking
- Add `temperature_template` for color temperature tracking
- Generate `set_level` action for brightness control
- Generate `set_temperature` action for color temperature control

#### Brightness Control Logic
- Supports two patterns:
  1. `brightness_up` + `brightness_down` - Step-based control
  2. `bright` + `dim` - Preset brightness levels
- Uses Jinja2 templates to compare current vs target brightness
- Sends appropriate command based on direction (up/down)
- Updates `input_number.{entity_id}_brightness` helper

#### Color Temperature Control Logic
- Supports `cooler` + `warmer` commands
- Uses Jinja2 templates to compare current vs target temperature
- Sends appropriate command based on direction (cooler/warmer)
- Updates `input_number.{entity_id}_color_temp` helper

### 2. Helper Generation Updates

Enhanced `_build_helpers_yaml()` to generate input_number helpers for lights:

#### Brightness Helper
```yaml
input_number:
  {entity_id}_brightness:
    name: "{Display Name} Brightness"
    min: 0
    max: 100
    step: 1
    initial: 50
    unit_of_measurement: "%"
```

#### Color Temperature Helper
```yaml
input_number:
  {entity_id}_color_temp:
    name: "{Display Name} Color Temperature"
    min: 153    # Warm white (6500K)
    max: 500    # Cool white (2000K)
    step: 1
    initial: 326  # Mid-range (~3000K)
    unit_of_measurement: "mireds"
```

## Example Generated Configuration

### Light with Brightness and Color Temperature

**Device Commands:**
- `toggle`
- `brightness_up`
- `brightness_down`
- `cooler`
- `warmer`

**Generated Light Entity:**
```yaml
light:
  - platform: template
    lights:
      tony_s_office_workbench_lamp:
        unique_id: tony_s_office_workbench_lamp
        friendly_name: Tony's Office Workbench Lamp
        value_template: "{{ is_state('input_boolean.tony_s_office_workbench_lamp_state', 'on') }}"
        level_template: "{{ states('input_number.tony_s_office_workbench_lamp_brightness') | int }}"
        temperature_template: "{{ states('input_number.tony_s_office_workbench_lamp_color_temp') | int }}"
        icon_template: mdi:lamp
        turn_on:
          - service: remote.send_command
            target:
              entity_id: remote.tony_s_office_rm4_pro
            data:
              command: "b64:..."
          - service: input_boolean.turn_on
            target:
              entity_id: input_boolean.tony_s_office_workbench_lamp_state
        turn_off:
          - service: remote.send_command
            target:
              entity_id: remote.tony_s_office_rm4_pro
            data:
              command: "b64:..."
          - service: input_boolean.turn_off
            target:
              entity_id: input_boolean.tony_s_office_workbench_lamp_state
        set_level:
          - service: remote.send_command
            target:
              entity_id: remote.tony_s_office_rm4_pro
            data:
              command: >
                {% if brightness > states('input_number.tony_s_office_workbench_lamp_brightness') | int %}
                  b64:...  # brightness_up command
                {% else %}
                  b64:...  # brightness_down command
                {% endif %}
          - service: input_number.set_value
            target:
              entity_id: input_number.tony_s_office_workbench_lamp_brightness
            data:
              value: "{{ brightness }}"
        set_temperature:
          - service: remote.send_command
            target:
              entity_id: remote.tony_s_office_rm4_pro
            data:
              command: >
                {% if temperature < states('input_number.tony_s_office_workbench_lamp_color_temp') | int %}
                  b64:...  # cooler command
                {% else %}
                  b64:...  # warmer command
                {% endif %}
          - service: input_number.set_value
            target:
              entity_id: input_number.tony_s_office_workbench_lamp_color_temp
            data:
              value: "{{ temperature }}"
```

**Generated Helpers:**
```yaml
input_boolean:
  tony_s_office_workbench_lamp_state:
    name: Tony's Office Workbench Lamp State
    initial: false

input_number:
  tony_s_office_workbench_lamp_brightness:
    name: Tony's Office Workbench Lamp Brightness
    min: 0
    max: 100
    step: 1
    initial: 50
    unit_of_measurement: "%"
  
  tony_s_office_workbench_lamp_color_temp:
    name: Tony's Office Workbench Lamp Color Temperature
    min: 153
    max: 500
    step: 1
    initial: 326
    unit_of_measurement: "mireds"
```

## Home Assistant UI Integration

With these changes, light entities will now show:
- ✅ On/Off toggle
- ✅ Brightness slider (0-100%)
- ✅ Color temperature slider (warm to cool)
- ✅ Proper state tracking

## Command Patterns Supported

### Brightness Patterns
1. **Step-based**: `brightness_up` + `brightness_down`
   - Incremental brightness adjustment
   - Sends multiple commands to reach target
   
2. **Preset-based**: `bright` + `dim`
   - Switches between preset brightness levels
   - Single command per adjustment

### Color Temperature Patterns
- `cooler` - Shift toward cool white (higher mireds)
- `warmer` - Shift toward warm white (lower mireds)

## Backward Compatibility

- Lights without brightness/color temp commands work as before
- Only generates helpers for features that have commands
- Existing light entities continue to function normally

## Testing Recommendations

1. **Basic On/Off**: Verify toggle functionality works
2. **Brightness Control**: Test brightness slider in HA UI
3. **Color Temperature**: Test color temp slider in HA UI
4. **State Persistence**: Verify helpers maintain state across restarts
5. **Multiple Adjustments**: Test multiple brightness/temp changes in sequence

## Future Enhancements

- Support for discrete brightness levels (e.g., `brightness_25`, `brightness_50`, `brightness_75`, `brightness_100`)
- RGB color control for RGB-capable lights
- Effects/scenes support
- Transition duration support

## Files Modified

- `app/entity_generator.py` - Enhanced light generation and helper creation

## Related Documentation

- [Entity Generator Architecture](ARCHITECTURE_ANALYSIS.md)
- [Helper Entities Guide](../HELPERS.md)
- [Template Light Platform](https://www.home-assistant.io/integrations/light.template/)
