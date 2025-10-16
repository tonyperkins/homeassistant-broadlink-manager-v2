# Using Non-Broadlink Remotes with SmartIR

## Overview

As of this update, Broadlink Manager now supports using **any Home Assistant remote entity** as a controller for SmartIR devices, not just Broadlink remotes. This means you can use SmartIR climate profiles with:

- ✅ **Broadlink** remotes (RM4 Pro, RM Mini, etc.)
- ✅ **Xiaomi/Aqara** IR remotes
- ✅ **Harmony Hub**
- ✅ **ESPHome** IR blasters
- ✅ Any custom integration that implements the `remote` platform

## Why This Matters

Previously, the application incorrectly tried to resolve IP addresses for SmartIR controllers, which only worked with Broadlink devices. Now it correctly uses entity IDs, which is the standard Home Assistant approach.

### What Changed

**Before (Broken):**
```yaml
climate:
  - platform: smartir
    name: Living Room AC
    device_code: 1000
    controller_data: 192.168.1.100  # ❌ IP address - only worked with Broadlink
```

**After (Fixed):**
```yaml
climate:
  - platform: smartir
    name: Living Room AC
    device_code: 1000
    controller_data: remote.xiaomi_ir_remote  # ✅ Entity ID - works with any remote
```

## Use Cases

### Scenario 1: User Has Xiaomi Remote Only

You have a Xiaomi IR remote but no Broadlink device. You want to use SmartIR climate profiles:

1. **Create SmartIR Device** in Broadlink Manager
2. **Select Entity Type**: Climate
3. **Choose Controller**: `remote.xiaomi_ir_remote`
4. **Select Device Code**: Browse SmartIR codes (e.g., 1080 for your AC model)
5. **Add Sensors** (optional): Temperature and humidity sensors
6. **Generate Entities**: Creates proper SmartIR YAML configuration

**Generated YAML:**
```yaml
climate:
  - platform: smartir
    name: Bedroom AC
    unique_id: bedroom_ac
    device_code: 1080
    controller_data: remote.xiaomi_ir_remote
    temperature_sensor: sensor.bedroom_temperature
    humidity_sensor: sensor.bedroom_humidity
```

### Scenario 2: Harmony Hub for TV Control

You have a Harmony Hub and want to control your TV using SmartIR media player profiles:

1. **Create SmartIR Device**
2. **Entity Type**: Media Player
3. **Controller**: `remote.harmony_hub`
4. **Device Code**: Select TV model code
5. **Power Sensor** (optional): `binary_sensor.tv_power`

**Generated YAML:**
```yaml
media_player:
  - platform: smartir
    name: Living Room TV
    unique_id: living_room_tv
    device_code: 1500
    controller_data: remote.harmony_hub
    power_sensor: binary_sensor.tv_power
```

### Scenario 3: Mixed Controllers

You can use different remote types for different devices:

- Broadlink RM4 Pro for bedroom AC
- Xiaomi IR remote for living room AC
- Harmony Hub for media room TV

Each device can have its own controller entity. The system handles all of them correctly.

## What Works and What Doesn't

### ✅ Works with Non-Broadlink Remotes

| Feature | Status | Notes |
|---------|--------|-------|
| **Send Commands** | ✅ Yes | Uses standard `remote.send_command` service |
| **Test Commands** | ✅ Yes | Works with any remote entity |
| **SmartIR Profiles** | ✅ Yes | All SmartIR device codes work |
| **Entity Generation** | ✅ Yes | Creates proper YAML configuration |
| **Multiple Controllers** | ✅ Yes | Mix and match different remote types |

### ❌ Doesn't Work with Non-Broadlink Remotes

| Feature | Status | Notes |
|---------|--------|-------|
| **Learn Commands** | ❌ No | `remote.learn_command` is Broadlink-specific |
| **Delete Commands** | ❌ No | Command storage is Broadlink-specific |

### Why Learning Doesn't Work

The `remote.learn_command` service is **Broadlink-specific**. Other remotes either:

1. **Use pre-programmed codes** (Xiaomi, Harmony Hub) - no learning needed
2. **Have their own learning mechanism** (ESPHome has its own tools)

**This is expected behavior.** SmartIR is designed to use pre-configured device profiles, so learning isn't necessary. You select a device code from the SmartIR database instead.

## How to Use

### Step 1: Ensure Your Remote is in Home Assistant

Make sure your remote entity appears in Home Assistant:
- Check **Developer Tools** → **States**
- Look for entities starting with `remote.`
- Examples: `remote.xiaomi_ir_remote`, `remote.harmony_hub`, `remote.broadlink_rm4_pro`

### Step 2: Create SmartIR Device in Broadlink Manager

1. Open Broadlink Manager web interface
2. Click **"Add Device"**
3. Select **Device Type**: SmartIR
4. Choose **Entity Type**: Climate, Media Player, Fan, or Light
5. **Controller Device**: Select your remote entity (any type)
6. **Device Code**: Browse SmartIR codes or enter manually
7. Add optional sensors (temperature, humidity, power)
8. Click **"Save"**

### Step 3: Generate Entities

1. Click **"Generate Entities"** button
2. Review the generated YAML files in `/config/smartir/`
3. Restart Home Assistant to load the new entities

### Step 4: Verify in Home Assistant

After restart, your SmartIR entities should appear:
- Climate entities: `climate.bedroom_ac`
- Media players: `media_player.living_room_tv`
- Fans: `fan.living_room_fan`

## Technical Details

### Controller Data Format

SmartIR's `controller_data` field accepts:

1. **Entity ID** (recommended): `remote.any_remote_entity`
2. **IP Address** (legacy, Broadlink only): `192.168.1.100`
3. **Entity ID with port** (advanced): `remote.custom_remote:8000`

The fix ensures we always use **entity IDs**, which is the standard HA approach.

### Code Changes

**File**: `app/smartir_yaml_generator.py`

**What Changed**:
- Removed IP address resolution logic
- Changed `controller_data` to use entity ID directly
- Made `broadlink_devices` parameter optional (deprecated)
- Updated documentation to reflect support for any remote type

**Backward Compatibility**:
- Existing Broadlink configurations continue to work
- Old method `_get_controller_ip()` is deprecated but kept for compatibility
- No breaking changes to existing setups

## Troubleshooting

### "Controller device not found"

**Problem**: Selected remote entity doesn't exist in Home Assistant

**Solution**:
1. Check **Developer Tools** → **States** for the entity
2. Ensure the integration is loaded (Xiaomi, Harmony, etc.)
3. Restart Home Assistant if you just added the integration

### "Commands not working"

**Problem**: SmartIR device doesn't respond to commands

**Solution**:
1. Verify the remote entity works: Test it manually in Developer Tools
2. Check the device code is correct for your device model
3. Ensure the remote has line-of-sight to the device
4. Check Home Assistant logs for errors

### "Can't learn commands"

**Expected**: Learning is not supported with non-Broadlink remotes

**Solution**: Use SmartIR device codes instead. SmartIR has a database of 1000+ pre-configured device profiles. You don't need to learn commands.

## Examples

### Complete Climate Configuration

```yaml
climate:
  - platform: smartir
    name: Master Bedroom AC
    unique_id: master_bedroom_ac
    device_code: 1080
    controller_data: remote.xiaomi_ir_remote
    temperature_sensor: sensor.bedroom_temperature
    humidity_sensor: sensor.bedroom_humidity
    power_sensor: binary_sensor.ac_power
```

### Complete Media Player Configuration

```yaml
media_player:
  - platform: smartir
    name: Living Room TV
    unique_id: living_room_tv
    device_code: 1500
    controller_data: remote.harmony_hub
    power_sensor: binary_sensor.tv_power
```

### Multiple Devices with Different Controllers

```yaml
climate:
  # Bedroom AC with Broadlink
  - platform: smartir
    name: Bedroom AC
    unique_id: bedroom_ac
    device_code: 1080
    controller_data: remote.broadlink_rm4_pro
    temperature_sensor: sensor.bedroom_temp
  
  # Living Room AC with Xiaomi
  - platform: smartir
    name: Living Room AC
    unique_id: living_room_ac
    device_code: 1000
    controller_data: remote.xiaomi_ir_remote
    temperature_sensor: sensor.living_room_temp

media_player:
  # TV with Harmony Hub
  - platform: smartir
    name: Media Room TV
    unique_id: media_room_tv
    device_code: 1500
    controller_data: remote.harmony_hub
```

## Resources

- **SmartIR GitHub**: https://github.com/smartHomeHub/SmartIR
- **SmartIR Device Codes**: Browse codes in Broadlink Manager UI
- **Home Assistant Remote Platform**: https://www.home-assistant.io/integrations/remote/

## Summary

✅ **SmartIR now works with any Home Assistant remote entity**
✅ **No Broadlink device required for SmartIR functionality**
✅ **Use pre-configured device profiles from SmartIR database**
✅ **Mix and match different remote types in the same setup**
❌ **Learning commands requires Broadlink (but not needed for SmartIR)**

This change makes Broadlink Manager more flexible and accessible to users with different IR remote hardware!
