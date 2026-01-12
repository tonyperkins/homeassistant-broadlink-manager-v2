# Using Broadlink Manager Commands in Automations and Dashboards

This guide shows you how to use commands learned in Broadlink Manager within Home Assistant automations and Lovelace dashboards.

## 📋 Table of Contents

- [Understanding Command Storage](#understanding-command-storage)
- [Automation Examples](#automation-examples)
- [Dashboard Examples](#dashboard-examples)
- [Finding Device and Command Names](#finding-your-device-and-command-names)
- [Auto-Generate Entities (Recommended)](#auto-generate-entities-recommended)
- [Troubleshooting](#troubleshooting)

---

## Understanding Command Storage

When you learn commands in Broadlink Manager, they're stored in Home Assistant's Broadlink integration storage files (`.storage/broadlink_remote_*_codes`). You can use them in two ways:

1. **Direct Command Calls** - Use `remote.send_command` service (simple, works immediately)
2. **Auto-Generated Entities** - Let Broadlink Manager create proper entities (recommended for complex setups)

---

## Automation Examples

### Example 1: Basic Command Execution

Turn on a device using a learned command:

```yaml
automation:
  - alias: "Turn On MiniSplit Heat in Morning"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: numeric_state
        entity_id: sensor.bedroom_temperature
        below: 20
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4  # Your Broadlink device entity ID
        data:
          device: MiniSplit Heat On      # Device name from Broadlink Manager
          command: MiniSplit Heat On Command  # Command name you learned
```

**Key Points:**
- `entity_id`: Your Broadlink remote entity (find in Settings → Devices & Services → Broadlink)
- `device`: The device name shown in Broadlink Manager
- `command`: The exact command name you learned (case-sensitive)

### Example 2: Button-Triggered Command

Trigger a command when a button is pressed:

```yaml
automation:
  - alias: "Toggle MiniSplit with Button"
    trigger:
      - platform: state
        entity_id: binary_sensor.bedroom_button
        to: "on"
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4
        data:
          device: MiniSplit
          command: toggle
```

### Example 3: Multiple Commands in Sequence

Execute multiple commands with delays:

```yaml
automation:
  - alias: "Movie Mode"
    trigger:
      - platform: state
        entity_id: input_boolean.movie_mode
        to: "on"
    action:
      # Turn off lights
      - service: remote.send_command
        target:
          entity_id: remote.living_room_rm4
        data:
          device: Living Room Lights
          command: light_off
      
      # Wait 1 second
      - delay: "00:00:01"
      
      # Turn on TV
      - service: remote.send_command
        target:
          entity_id: remote.living_room_rm4
        data:
          device: TV
          command: power_on
      
      # Wait 2 seconds
      - delay: "00:00:02"
      
      # Set TV to HDMI 1
      - service: remote.send_command
        target:
          entity_id: remote.living_room_rm4
        data:
          device: TV
          command: hdmi_1
```

### Example 4: Temperature-Based Control

Control AC based on temperature:

```yaml
automation:
  - alias: "Auto Climate Control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bedroom_temperature
        above: 25
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4
        data:
          device: AC
          command: cool_on
  
  - alias: "Turn Off AC When Cool"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bedroom_temperature
        below: 22
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4
        data:
          device: AC
          command: power_off
```

### Example 5: Time-Based Fan Speed

Change fan speed throughout the day:

```yaml
automation:
  - alias: "Fan Speed - Morning"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4
        data:
          device: Ceiling Fan
          command: fan_speed_1
  
  - alias: "Fan Speed - Afternoon"
    trigger:
      - platform: time
        at: "14:00:00"
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4
        data:
          device: Ceiling Fan
          command: fan_speed_3
  
  - alias: "Fan Speed - Night"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: remote.send_command
        target:
          entity_id: remote.bedroom_rm4
        data:
          device: Ceiling Fan
          command: fan_off
```

### Example 6: Presence-Based Automation

Turn on lights when someone arrives home:

```yaml
automation:
  - alias: "Welcome Home Lights"
    trigger:
      - platform: state
        entity_id: person.john
        to: "home"
    condition:
      - condition: sun
        after: sunset
    action:
      - service: remote.send_command
        target:
          entity_id: remote.living_room_rm4
        data:
          device: Living Room Lights
          command: light_on
```

---

## Dashboard Examples

### Example 1: Simple Button Card

Add a single button to your dashboard:

```yaml
type: button
name: MiniSplit Heat On
icon: mdi:heat-wave
tap_action:
  action: call-service
  service: remote.send_command
  service_data:
    entity_id: remote.bedroom_rm4
    device: MiniSplit Heat On
    command: MiniSplit Heat On Command
```

### Example 2: Entities Card with Multiple Commands

Create a card with multiple control buttons:

```yaml
type: entities
title: MiniSplit Controls
entities:
  - type: button
    name: Heat On
    icon: mdi:heat-wave
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit Heat On
        command: MiniSplit Heat On Command
  
  - type: button
    name: Cool On
    icon: mdi:snowflake
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit
        command: cool_on
  
  - type: button
    name: Heat Off
    icon: mdi:power-off
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit Heat Off
        command: MiniSplit Heat Off Command
```

### Example 3: Horizontal Stack Buttons

Create a row of buttons:

```yaml
type: horizontal-stack
cards:
  - type: button
    name: Heat
    icon: mdi:heat-wave
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit
        command: heat_on
  
  - type: button
    name: Cool
    icon: mdi:snowflake
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit
        command: cool_on
  
  - type: button
    name: Fan
    icon: mdi:fan
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit
        command: fan_only
  
  - type: button
    name: Off
    icon: mdi:power-off
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.bedroom_rm4
        device: MiniSplit
        command: power_off
```

### Example 4: Grid Card Layout

Create a grid of device controls:

```yaml
type: grid
columns: 3
square: false
cards:
  - type: button
    name: TV Power
    icon: mdi:television
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: power
  
  - type: button
    name: Volume Up
    icon: mdi:volume-plus
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: volume_up
  
  - type: button
    name: Volume Down
    icon: mdi:volume-minus
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: volume_down
  
  - type: button
    name: HDMI 1
    icon: mdi:hdmi-port
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: hdmi_1
  
  - type: button
    name: HDMI 2
    icon: mdi:hdmi-port
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: hdmi_2
  
  - type: button
    name: Netflix
    icon: mdi:netflix
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: netflix
```

### Example 5: Conditional Card (Show Only When Home)

Show controls only when someone is home:

```yaml
type: conditional
conditions:
  - entity: person.john
    state: home
card:
  type: entities
  title: Welcome Home Controls
  entities:
    - type: button
      name: Living Room Lights On
      icon: mdi:lightbulb
      tap_action:
        action: call-service
        service: remote.send_command
        service_data:
          entity_id: remote.living_room_rm4
          device: Living Room Lights
          command: light_on
    
    - type: button
      name: TV On
      icon: mdi:television
      tap_action:
        action: call-service
        service: remote.send_command
        service_data:
          entity_id: remote.living_room_rm4
          device: TV
          command: power_on
```

### Example 6: Picture Elements Card (Remote Control)

Create a visual remote control:

```yaml
type: picture-elements
image: /local/images/tv_remote_background.png
elements:
  - type: icon
    icon: mdi:power
    style:
      top: 10%
      left: 50%
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: power
  
  - type: icon
    icon: mdi:chevron-up
    style:
      top: 30%
      left: 50%
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: up
  
  - type: icon
    icon: mdi:chevron-down
    style:
      top: 50%
      left: 50%
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: down
  
  - type: icon
    icon: mdi:chevron-left
    style:
      top: 40%
      left: 35%
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: left
  
  - type: icon
    icon: mdi:chevron-right
    style:
      top: 40%
      left: 65%
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: right
  
  - type: icon
    icon: mdi:checkbox-blank-circle
    style:
      top: 40%
      left: 50%
    tap_action:
      action: call-service
      service: remote.send_command
      service_data:
        entity_id: remote.living_room_rm4
        device: TV
        command: ok
```

---

## Finding Your Device and Command Names

### Method 1: Check Broadlink Manager UI

1. Open Broadlink Manager at `http://homeassistant.local:8099`
2. Look at your device cards - the device name is shown at the top
3. Click on a device to see all learned commands
4. Use these exact names in your automations (they are case-sensitive)

### Method 2: Check Storage Files

Commands are stored in `.storage/broadlink_remote_*_codes` files. You can view them using the File Editor add-on:

**File Location:**
```
/config/.storage/broadlink_remote_XXXX_codes
```

**File Structure:**
```json
{
  "MiniSplit Heat On": {
    "MiniSplit Heat On Command": "JgBQAAABKZIUEhQ...",
    "another_command": "JgBQAAABKZIUEhQ..."
  },
  "Living Room TV": {
    "power": "JgBQAAABKZIUEhQ...",
    "volume_up": "JgBQAAABKZIUEhQ...",
    "volume_down": "JgBQAAABKZIUEhQ..."
  }
}
```

The first level is the **device name**, and the second level contains **command names**.

### Method 3: Use Developer Tools

1. Go to **Developer Tools** → **Services**
2. Select `remote.send_command`
3. Choose your Broadlink remote entity
4. Try different device and command names
5. Click "Call Service" to test

---

## Auto-Generate Entities (Recommended)

Instead of manually creating automations for every command, let Broadlink Manager auto-generate proper Home Assistant entities. This gives you native entities like `light.bedroom_light`, `fan.living_room_fan`, etc.

### Step 1: Use Descriptive Command Names

When learning commands, use these naming patterns for automatic entity detection:

**For Lights:**
- `light_on`
- `light_off`
- `light_toggle`

**For Fans:**
- `fan_speed_1`
- `fan_speed_2`
- `fan_speed_3`
- `fan_speed_4` (up to 6 speeds supported)
- `fan_off` (optional)
- `fan_reverse` (optional)

**For Switches:**
- `on`
- `off`
- `toggle`
- `power`

**For Media Players:**
- `power`
- `volume_up`
- `volume_down`
- `mute`
- `play`
- `pause`

### Step 2: Generate Entities in Broadlink Manager

1. Open Broadlink Manager web interface
2. Click on your device card
3. Click the **"Generate Entities"** button
4. The system will auto-detect entity types based on command names
5. Review the generated configuration
6. Generated files will be saved to `/config/broadlink_manager/`

### Step 3: Add to Home Assistant Configuration

Add this to your `configuration.yaml`:

```yaml
homeassistant:
  packages:
    broadlink_manager: !include broadlink_manager/package.yaml
```

### Step 4: Restart Home Assistant

After restarting, you'll have proper entities that can be used like any other Home Assistant entity:

**In Automations:**
```yaml
automation:
  - alias: "Turn on bedroom light at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom_light
```

**In Dashboards:**
```yaml
type: entities
title: Bedroom Controls
entities:
  - light.bedroom_light
  - fan.bedroom_fan
  - switch.tv_power
```

**Benefits of Auto-Generated Entities:**
- ✅ Native Home Assistant entities (lights, fans, switches)
- ✅ Work with voice assistants (Alexa, Google Home)
- ✅ Appear in standard entity cards
- ✅ Support state tracking with helper entities
- ✅ Percentage-based fan speed control
- ✅ Proper icons and device classes

---

## Troubleshooting

### Commands Not Working?

#### 1. Check Broadlink Remote Entity ID

Make sure you're using the correct entity ID for your Broadlink device:

- Go to **Settings** → **Devices & Services** → **Broadlink**
- Find your device and note its entity ID
- Should look like `remote.bedroom_rm4`, `remote.living_room_rm_mini`, etc.

#### 2. Verify Device and Command Names

Names must match **exactly** (case-sensitive):

**❌ Wrong:**
```yaml
device: minisplit heat on
command: heat on
```

**✅ Correct:**
```yaml
device: MiniSplit Heat On
command: MiniSplit Heat On Command
```

#### 3. Test in Developer Tools

1. Go to **Developer Tools** → **Services**
2. Select `remote.send_command`
3. Fill in the service data:
   ```yaml
   entity_id: remote.bedroom_rm4
   device: MiniSplit Heat On
   command: MiniSplit Heat On Command
   ```
4. Click **"Call Service"** to test
5. If it works here but not in automation, check your automation syntax

#### 4. Check Logs

**Broadlink Manager Logs:**
- Go to **Settings** → **Add-ons** → **Broadlink Manager** → **Logs**
- Look for errors related to command execution

**Home Assistant Logs:**
- Go to **Settings** → **System** → **Logs**
- Filter for "broadlink" or "remote"
- Look for error messages

#### 5. Enable Debug Logging

For more detailed logs, enable debug mode:

**In Broadlink Manager:**
Edit the add-on configuration:
```yaml
log_level: debug
```

**In Home Assistant:**
Add to `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
    homeassistant.components.broadlink: debug
    custom_components.broadlink_manager: debug
```

Restart and check logs again.

### Common Issues

#### Issue: "Device not found"

**Cause:** Device name doesn't match what's stored in Broadlink integration.

**Solution:** 
- Check exact device name in Broadlink Manager UI
- Verify spelling and capitalization
- Check `.storage/broadlink_remote_*_codes` file

#### Issue: "Command not found"

**Cause:** Command name doesn't match what's stored.

**Solution:**
- Check exact command name in Broadlink Manager
- Verify spelling and capitalization
- Re-learn the command if necessary

#### Issue: Command sends but device doesn't respond

**Cause:** 
- Device is out of range
- IR/RF interference
- Device is off or in wrong mode
- Command was learned incorrectly

**Solution:**
- Move Broadlink device closer to target device
- Re-learn the command
- Test with original remote to verify device is working
- Check for IR/RF interference from other devices

#### Issue: Delay between commands needed

**Cause:** Some devices need time to process commands.

**Solution:** Add delays between commands:
```yaml
action:
  - service: remote.send_command
    data:
      entity_id: remote.bedroom_rm4
      device: TV
      command: power_on
  
  - delay: "00:00:02"  # Wait 2 seconds
  
  - service: remote.send_command
    data:
      entity_id: remote.bedroom_rm4
      device: TV
      command: hdmi_1
```

#### Issue: Entity generation not working

**Cause:** Command names don't follow naming conventions.

**Solution:**
- Use proper naming patterns (see [Auto-Generate Entities](#auto-generate-entities-recommended))
- Example: `light_on`, `light_off`, `fan_speed_1`, etc.
- Re-learn commands with correct names
- Regenerate entities

---

## Additional Resources

### Documentation
- **[Broadlink Manager README](../README.md)** - Main documentation
- **[API Reference](API.md)** - Complete REST API documentation
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Entity Generation Guide](ENTITY_GENERATION.md)** - Technical details on entity auto-generation
- **[Architecture Guide](ARCHITECTURE.md)** - Understanding the system architecture

### Community
- **[GitHub Repository](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2)** - Source code and issues
- **[Reddit Announcement](https://www.reddit.com/r/homeassistant/comments/1o1q3kf/release_broadlink_manager_addon_a_modern_web_ui/)** - Community discussion
- **[GitHub Discussions](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/discussions)** - Ask questions and share tips

### Home Assistant Resources
- **[Home Assistant Automations](https://www.home-assistant.io/docs/automation/)** - Official automation documentation
- **[Lovelace UI](https://www.home-assistant.io/lovelace/)** - Dashboard configuration
- **[Broadlink Integration](https://www.home-assistant.io/integrations/broadlink/)** - Official Broadlink integration docs

---

## Quick Reference

### Basic Service Call Structure

```yaml
service: remote.send_command
target:
  entity_id: remote.YOUR_BROADLINK_ENTITY
data:
  device: YOUR_DEVICE_NAME
  command: YOUR_COMMAND_NAME
```

### Common Icon Names

Use these MDI icons in your dashboard cards:

- **Climate:** `mdi:heat-wave`, `mdi:snowflake`, `mdi:fan`, `mdi:air-conditioner`
- **Lights:** `mdi:lightbulb`, `mdi:lightbulb-on`, `mdi:lightbulb-off`, `mdi:lamp`
- **TV/Media:** `mdi:television`, `mdi:remote`, `mdi:play`, `mdi:pause`, `mdi:stop`
- **Power:** `mdi:power`, `mdi:power-on`, `mdi:power-off`, `mdi:power-cycle`
- **Volume:** `mdi:volume-plus`, `mdi:volume-minus`, `mdi:volume-mute`
- **Navigation:** `mdi:chevron-up`, `mdi:chevron-down`, `mdi:chevron-left`, `mdi:chevron-right`
- **HDMI:** `mdi:hdmi-port`, `mdi:video-input-hdmi`

Browse all icons at: https://pictogrammers.com/library/mdi/

---

## Need More Help?

If you're still having trouble:

1. **Check the logs** - Enable debug logging and look for specific errors
2. **Test in Developer Tools** - Verify commands work manually first
3. **Open an issue** - [GitHub Issues](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues)
4. **Join the discussion** - [GitHub Discussions](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/discussions)
5. **Ask the community** - [Reddit r/homeassistant](https://www.reddit.com/r/homeassistant/)

When asking for help, include:
- Broadlink Manager version
- Home Assistant version
- Broadlink device model
- Exact error messages from logs
- Your automation/dashboard YAML (remove sensitive data)

---

**Happy Automating! 🎉**
