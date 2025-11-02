# RF Remote Dashboard Setup Guide

## Overview

For RF remotes with step-based controls (brightness up/down, cooler/warmer), the default Home Assistant light slider doesn't work well. This guide shows how to configure your dashboard with buttons that directly call the RF commands.

## The Problem

RF remotes like your workbench lamp remote have:
- ☀️+ / ☀️- buttons (brightness up/down)
- 🌡️+ / 🌡️- buttons (cooler/warmer)
- Preset buttons (bright, dim, etc.)

Home Assistant's light entity shows a **slider** that expects to jump to a specific brightness level, but RF remotes can only **step up or down**. The slider won't work properly.

## The Solution

Add custom buttons to your dashboard that directly call the RF commands. You have two options:

### Option 1: Button Card (Recommended)

Use the built-in button card to create a custom control panel:

```yaml
type: vertical-stack
cards:
  # Main light control
  - type: light
    entity: light.tony_s_office_workbench_lamp
    name: Workbench Lamp
    
  # Brightness controls
  - type: horizontal-stack
    cards:
      - type: button
        name: Brighter
        icon: mdi:brightness-5
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: brightness_up
      - type: button
        name: Dimmer
        icon: mdi:brightness-4
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: brightness_down
  
  # Color temperature controls
  - type: horizontal-stack
    cards:
      - type: button
        name: Warmer
        icon: mdi:weather-sunny
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: warmer
      - type: button
        name: Cooler
        icon: mdi:snowflake
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: cooler
  
  # Preset buttons
  - type: horizontal-stack
    cards:
      - type: button
        name: Bright
        icon: mdi:brightness-7
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: bright
      - type: button
        name: Dim
        icon: mdi:brightness-3
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: dim
```

### Option 2: Custom Button Card (Advanced)

If you have the [custom button card](https://github.com/custom-cards/button-card) installed via HACS, you can create a more compact layout:

```yaml
type: custom:button-card
entity: light.tony_s_office_workbench_lamp
name: Workbench Lamp
show_state: true
tap_action:
  action: toggle
custom_fields:
  brightness:
    card:
      type: horizontal-stack
      cards:
        - type: custom:button-card
          icon: mdi:brightness-5
          name: Brighter
          tap_action:
            action: call-service
            service: remote.send_command
            service_data:
              entity_id: remote.tony_s_office_rm4_pro
              device: tony_s_office_workbench_lamp
              command: brightness_up
        - type: custom:button-card
          icon: mdi:brightness-4
          name: Dimmer
          tap_action:
            action: call-service
            service: remote.send_command
            service_data:
              entity_id: remote.tony_s_office_rm4_pro
              device: tony_s_office_workbench_lamp
              command: brightness_down
  color_temp:
    card:
      type: horizontal-stack
      cards:
        - type: custom:button-card
          icon: mdi:weather-sunny
          name: Warmer
          tap_action:
            action: call-service
            service: remote.send_command
            service_data:
              entity_id: remote.tony_s_office_rm4_pro
              device: tony_s_office_workbench_lamp
              command: warmer
        - type: custom:button-card
          icon: mdi:snowflake
          name: Cooler
          tap_action:
            action: call-service
            service: remote.send_command
            service_data:
              entity_id: remote.tony_s_office_rm4_pro
              device: tony_s_office_workbench_lamp
              command: cooler
```

### Option 3: Scripts (Most Flexible)

Create scripts for each command, then add them as buttons:

**scripts.yaml:**
```yaml
workbench_lamp_brighter:
  alias: Workbench Lamp Brighter
  icon: mdi:brightness-5
  sequence:
    - service: remote.send_command
      target:
        entity_id: remote.tony_s_office_rm4_pro
      data:
        device: tony_s_office_workbench_lamp
        command: brightness_up

workbench_lamp_dimmer:
  alias: Workbench Lamp Dimmer
  icon: mdi:brightness-4
  sequence:
    - service: remote.send_command
      target:
        entity_id: remote.tony_s_office_rm4_pro
      data:
        device: tony_s_office_workbench_lamp
        command: brightness_down

workbench_lamp_warmer:
  alias: Workbench Lamp Warmer
  icon: mdi:weather-sunny
  sequence:
    - service: remote.send_command
      target:
        entity_id: remote.tony_s_office_rm4_pro
      data:
        device: tony_s_office_workbench_lamp
        command: warmer

workbench_lamp_cooler:
  alias: Workbench Lamp Cooler
  icon: mdi:snowflake
  sequence:
    - service: remote.send_command
      target:
        entity_id: remote.tony_s_office_rm4_pro
      data:
        device: tony_s_office_workbench_lamp
        command: cooler
```

**Dashboard:**
```yaml
type: entities
entities:
  - entity: light.tony_s_office_workbench_lamp
  - type: buttons
    entities:
      - entity: script.workbench_lamp_brighter
      - entity: script.workbench_lamp_dimmer
      - entity: script.workbench_lamp_warmer
      - entity: script.workbench_lamp_cooler
```

## Quick Copy-Paste Example

Here's a ready-to-use card you can paste directly into your dashboard:

```yaml
type: vertical-stack
cards:
  - type: entities
    entities:
      - entity: light.tony_s_office_workbench_lamp
        name: Workbench Lamp
  - type: grid
    columns: 2
    square: false
    cards:
      - type: button
        name: Brighter
        icon: mdi:brightness-5
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: brightness_up
      - type: button
        name: Dimmer
        icon: mdi:brightness-4
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: brightness_down
      - type: button
        name: Warmer
        icon: mdi:weather-sunny
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: warmer
      - type: button
        name: Cooler
        icon: mdi:snowflake
        tap_action:
          action: call-service
          service: remote.send_command
          target:
            entity_id: remote.tony_s_office_rm4_pro
          data:
            device: tony_s_office_workbench_lamp
            command: cooler
```

## How to Add to Dashboard

1. Open your Home Assistant dashboard
2. Click the three dots (⋮) in the top right
3. Click "Edit Dashboard"
4. Click "+ Add Card" at the bottom
5. Scroll down and click "Manual" at the bottom
6. Paste one of the YAML examples above
7. Click "Save"

## Icon Reference

Common icons for RF remote buttons:

| Command | Icon | Description |
|---------|------|-------------|
| brightness_up | `mdi:brightness-5` | Brighter |
| brightness_down | `mdi:brightness-4` | Dimmer |
| bright | `mdi:brightness-7` | Full bright |
| dim | `mdi:brightness-3` | Low brightness |
| warmer | `mdi:weather-sunny` | Warm white |
| cooler | `mdi:snowflake` | Cool white |
| toggle | `mdi:power` | On/Off |

## Tips

1. **Test commands first**: Use the Broadlink Manager web interface to test each command before adding to dashboard
2. **Group related controls**: Keep brightness and color temp buttons together
3. **Use descriptive names**: "Brighter" is clearer than "Up"
4. **Consider scenes**: For frequently used settings, create scenes instead of multiple button presses

## Future Enhancement Idea

If you want the entity generator to automatically create these scripts, we could add:
- A device configuration option: `control_type: "step_based"` vs `control_type: "absolute"`
- Auto-generate helper scripts for step-based controls
- Add metadata to indicate which commands are available

Let me know if you'd like me to implement this!
