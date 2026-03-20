# Color Temperature Variant Lights

## Overview

Broadlink Manager automatically detects and creates multiple light entities for devices with color temperature variants. This is common in LED lights with adjustable color temperature (CCT lights) that have multiple preset buttons.

## How It Works

### Automatic Detection

When you have a light with multiple color temperature commands and a shared off button, the system automatically:

1. **Detects the pattern** - Multiple color temp commands + shared `turn_off`
2. **Creates a master light** - Main entity for dashboard control
3. **Creates variant lights** - Individual entities for each color temperature
4. **Shares state tracking** - All entities synchronized via shared helper

### Example Device

**Remote buttons:**
- Cool White (5000K-6500K)
- Warm White (2700K-3000K)  
- Daylight/Natural (4000K-4500K)
- OFF (single button)

**Commands learned:**
- `cold` - Turns on in cool white
- `warm` - Turns on in warm white
- `mid_tone` - Turns on in daylight/natural
- `turn_off` - Turns off regardless of color

**Generated entities:**
```yaml
light.bedroom_light           # Master light (uses mid_tone)
light.bedroom_light_cold      # Cool white variant
light.bedroom_light_warm      # Warm white variant
light.bedroom_light_mid_tone  # Daylight variant
```

## Learning Commands

### Step 1: Create Device

1. Go to **Managed Devices** → **Add Device**
2. Select your Broadlink remote device
3. Enter device name (e.g., "Bedroom Light")
4. Select entity type: **Light**
5. Click **Create Device**

### Step 2: Learn Color Temperature Commands

For each color temperature button on your remote:

1. Click the **Learn Commands** button on your device card
2. Select **"Custom command..."** from the dropdown
3. Enter command name:
   - `warm` - For warm white button
   - `cold` - For cool white button
   - `mid_tone` - For middle/natural white button
   - `daylight` - Alternative for natural white
4. Select command type (usually **IR**)
5. Click **Start Learning**
6. Press the corresponding button on your remote
7. Repeat for each color temperature

### Step 3: Learn Turn Off Command

1. Click **Learn Commands** again
2. Select **"turn_off"** from suggested commands
3. Click **Start Learning**
4. Press the OFF button on your remote

### Step 4: Generate Entities

1. Click **Generate Entities** button
2. The system automatically detects the color temp pattern
3. Master light + variant lights are created
4. Reload Home Assistant configuration

## Supported Command Names

The system recognizes these color temperature command names:

**Warm tones:**
- `warm`
- `warm_white`
- `warm_tone`
- `soft`
- `soft_white`

**Cool tones:**
- `cold`
- `cool`
- `cool_white`
- `cold_white`
- `cool_tone`

**Neutral/Middle tones:**
- `mid`
- `mid_tone`
- `mid_white`
- `middle`
- `neutral`
- `natural`
- `daylight`
- `day`

**Note:** You need at least 2 color temperature commands + `turn_off` for the pattern to be detected.

## Master Light Behavior

The master light entity (`light.bedroom_light`) provides:

### Turn On
- Sends the **default color temperature** command (prefers `mid_tone`, `neutral`, or first alphabetically)
- Updates shared state to ON
- All variant lights show as ON

### Turn Off
- Sends the `turn_off` command
- Updates shared state to OFF
- All variant lights show as OFF

### State Tracking
- Shows **ON** if ANY variant is currently on
- Shows **OFF** only when all variants are off
- Perfect for dashboard toggle buttons!

## Variant Light Behavior

Each variant light entity (e.g., `light.bedroom_light_warm`) provides:

### Turn On
- Sends the specific color temperature command (`warm`, `cold`, etc.)
- Updates shared state to ON
- Master light shows as ON

### Turn Off
- Sends the shared `turn_off` command
- Updates shared state to OFF
- Master light shows as OFF

### State Tracking
- Shares the same state helper as master light
- Synchronized state across all variants

## Use Cases

### 1. Dashboard Toggle Button

Use the master light for a simple on/off toggle:

```yaml
type: button
entity: light.bedroom_light
name: Bedroom Light
tap_action:
  action: toggle
```

**Behavior:**
- Press once → Turns on (default color temp)
- Press again → Turns off
- Works regardless of which variant was last used!

### 2. Time-Based Color Temperature

Create automations to change color temp based on time of day:

```yaml
automation:
  - alias: "Bedroom Light - Morning Cool"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom_light_cold
        
  - alias: "Bedroom Light - Evening Warm"
    trigger:
      - platform: time
        at: "19:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.bedroom_light_warm
```

**Behavior:**
- Morning automation turns on cool white
- Evening automation turns on warm white
- Dashboard toggle button works for both!

### 3. Scene-Based Control

Include different variants in different scenes:

```yaml
scene:
  - name: "Work Mode"
    entities:
      light.bedroom_light_cold: on
      
  - name: "Relax Mode"
    entities:
      light.bedroom_light_warm: on
```

### 4. Manual Color Temperature Selection

Add buttons to manually select color temperature:

```yaml
type: horizontal-stack
cards:
  - type: button
    entity: light.bedroom_light_warm
    name: Warm
    icon: mdi:weather-sunset
  - type: button
    entity: light.bedroom_light_mid_tone
    name: Natural
    icon: mdi:white-balance-sunny
  - type: button
    entity: light.bedroom_light_cold
    name: Cool
    icon: mdi:weather-sunny
```

## Troubleshooting

### Variants Not Created

**Problem:** Only master light created, no variants

**Solution:** Check that you have:
- At least 2 color temperature commands
- A `turn_off` command
- Command names match supported patterns (see list above)

### State Not Synchronized

**Problem:** Master light doesn't show ON when variant is on

**Solution:**
- Regenerate entities
- Reload Home Assistant configuration
- Check that all entities share the same state helper: `input_boolean.{device_name}_state`

### Commands Not Recognized

**Problem:** Color temp commands created as buttons instead of lights

**Solution:**
- Use recognized command names from the supported list
- Or rename commands to match patterns (e.g., `warm_white` → `warm`)
- Regenerate entities

## Technical Details

### Shared State Helper

All variant lights share a single `input_boolean` helper:

```yaml
input_boolean:
  bedroom_light_state:
    name: Bedroom Light State
    initial: false
```

This ensures:
- Turning on ANY variant → Helper turns ON
- Turning off ANY variant → Helper turns OFF
- Master light reflects combined state

### Entity Naming Convention

- **Master light:** `light.{device_name}`
- **Variant lights:** `light.{device_name}_{variant_name}`
- **State helper:** `input_boolean.{device_name}_state`

Example:
- Master: `light.bedroom_light`
- Variants: `light.bedroom_light_warm`, `light.bedroom_light_cold`
- Helper: `input_boolean.bedroom_light_state`

## Backward Compatibility

This feature is **100% backward compatible**:

- Existing devices continue working unchanged
- Pattern detection only activates when color temp variants are found
- Standard light generation used for devices without variants
- No breaking changes to existing configurations

## Related Features

- **Brightness Control:** Only the master light supports brightness commands (if available)
- **Custom Commands:** Commands not matching patterns still create buttons
- **SmartIR Integration:** Not applicable to SmartIR devices (they use code files)
