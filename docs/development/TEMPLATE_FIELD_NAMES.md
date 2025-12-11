# Modern Template Syntax Field Names Reference

## Overview

This document provides a complete reference for the field name changes between legacy and modern Home Assistant template syntax.

**Source:** [Home Assistant Template Integration Documentation](https://www.home-assistant.io/integrations/template/)

## Universal Changes (All Entity Types)

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `friendly_name:` | `name:` | Entity display name |
| `value_template:` | `state:` | Template for entity state |
| `icon_template:` | `icon_template:` | **No change** - Still uses `icon_template:` |

## Fan Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | On/off state template |
| `percentage_template:` | `percentage:` | Speed percentage template |
| `direction_template:` | `direction:` | Direction template (forward/reverse) |
| `oscillating_template:` | `oscillating:` | Oscillation state template |
| `preset_mode_template:` | `preset_mode:` | Preset mode template |

**Example:**
```yaml
# Legacy
fan:
  - platform: template
    fans:
      bedroom_fan:
        friendly_name: "Bedroom Fan"
        value_template: "{{ is_state('input_boolean.fan_state', 'on') }}"
        percentage_template: "{{ states('input_number.fan_speed') | int }}"
        direction_template: "{{ states('input_select.fan_direction') }}"

# Modern
template:
  - fan:
      - name: "Bedroom Fan"
        state: "{{ is_state('input_boolean.fan_state', 'on') }}"
        percentage: "{{ states('input_number.fan_speed') | int }}"
        direction: "{{ states('input_select.fan_direction') }}"
```

## Light Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | On/off state template |
| `level_template:` | `level:` | Brightness level template |
| `temperature_template:` | `temperature:` | Color temperature template |
| `color_template:` | `hs:` | HS color template |
| `effect_template:` | `effect:` | Effect template |
| `effect_list_template:` | `effect_list:` | Effect list template |
| `white_value_template:` | ❌ Removed | No longer supported |
| `rgb_template:` | `rgb:` | RGB color template |
| `rgbw_template:` | `rgbw:` | RGBW color template |
| `rgbww_template:` | `rgbww:` | RGBWW color template |

**Example:**
```yaml
# Legacy
light:
  - platform: template
    lights:
      living_room_light:
        friendly_name: "Living Room Light"
        value_template: "{{ is_state('input_boolean.light_state', 'on') }}"
        level_template: "{{ states('input_number.brightness') | int }}"
        temperature_template: "{{ states('input_number.color_temp') | int }}"

# Modern
template:
  - light:
      - name: "Living Room Light"
        state: "{{ is_state('input_boolean.light_state', 'on') }}"
        level: "{{ states('input_number.brightness') | int }}"
        temperature: "{{ states('input_number.color_temp') | int }}"
```

## Switch Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | On/off state template |

**Example:**
```yaml
# Legacy
switch:
  - platform: template
    switches:
      garage_door:
        friendly_name: "Garage Door"
        value_template: "{{ is_state('binary_sensor.garage', 'on') }}"

# Modern
template:
  - switch:
      - name: "Garage Door"
        state: "{{ is_state('binary_sensor.garage', 'on') }}"
```

## Cover Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | Open/closed state template |
| `position_template:` | `position:` | Position template (0-100) |
| `tilt_template:` | `tilt:` | Tilt position template (0-100) |

**Example:**
```yaml
# Legacy
cover:
  - platform: template
    covers:
      garage_door:
        friendly_name: "Garage Door"
        value_template: "{{ is_state('sensor.garage', 'open') }}"
        position_template: "{{ states('input_number.position') | int }}"

# Modern
template:
  - cover:
      - name: "Garage Door"
        state: "{{ is_state('sensor.garage', 'open') }}"
        position: "{{ states('input_number.position') | int }}"
```

## Binary Sensor Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | Binary state template (true/false) |

**Example:**
```yaml
# Legacy
binary_sensor:
  - platform: template
    sensors:
      motion_detected:
        friendly_name: "Motion Detected"
        value_template: "{{ is_state('sensor.motion', 'on') }}"

# Modern
template:
  - binary_sensor:
      - name: "Motion Detected"
        state: "{{ is_state('sensor.motion', 'on') }}"
```

## Sensor Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | Sensor value template |
| `attribute_templates:` | `attributes:` | Attribute templates |

**Example:**
```yaml
# Legacy
sensor:
  - platform: template
    sensors:
      temperature:
        friendly_name: "Temperature"
        value_template: "{{ states('sensor.temp') | float }}"
        unit_of_measurement: "°C"

# Modern
template:
  - sensor:
      - name: "Temperature"
        state: "{{ states('sensor.temp') | float }}"
        unit_of_measurement: "°C"
```

## Lock Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | Locked/unlocked state template |

## Vacuum Entity

| Legacy Field | Modern Field | Description |
|-------------|--------------|-------------|
| `value_template:` | `state:` | Vacuum state template |
| `battery_level_template:` | `battery_level:` | Battery level template |
| `fan_speed_template:` | `fan_speed:` | Fan speed template |

## Important Notes

### Fields That Did NOT Change

- `icon_template:` - Still uses `_template` suffix
- `availability_template:` - Still uses `_template` suffix  
- `unique_id:` - No change
- Action fields (`turn_on:`, `turn_off:`, `set_level:`, etc.) - No change

### Common Patterns

1. **State templates:** All `value_template:` → `state:`
2. **Attribute templates:** Most `*_template:` → Remove `_template` suffix
3. **Name field:** `friendly_name:` → `name:`
4. **Icon exception:** `icon_template:` stays the same

### Validation

To validate your templates match modern syntax:
1. Check Home Assistant logs for deprecation warnings
2. Use Developer Tools → YAML → Check Configuration
3. Verify no `platform: template` entries
4. Confirm all templates use `template:` top-level key

## Migration Checklist

- [ ] Replace `platform: template` with `template:` structure
- [ ] Change `friendly_name:` to `name:`
- [ ] Change `value_template:` to `state:`
- [ ] Change `*_template:` fields (except `icon_template` and `availability_template`)
- [ ] Update `configuration.yaml` includes
- [ ] Test configuration with Check Configuration
- [ ] Restart Home Assistant
- [ ] Verify entities work correctly

## References

- [Home Assistant Template Integration](https://www.home-assistant.io/integrations/template/)
- [Template Deprecation Discussion](https://community.home-assistant.io/t/deprecation-of-legacy-template-entities-in-2025-12/955562)
- [HA 2021.4 Release Notes](https://www.home-assistant.io/blog/2021/04/07/release-20214/)
