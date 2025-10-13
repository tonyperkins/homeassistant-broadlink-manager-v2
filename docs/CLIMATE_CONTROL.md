# Climate Control (AC/Heater) with Broadlink

## Important Notice

**Climate entity type is NOT supported** by Broadlink Manager because Home Assistant removed the `template.climate` platform.

## Why Climate Entities Don't Work

Home Assistant no longer supports the `template.climate` platform as of 2024/2025. Attempting to create climate entities will result in this error:

```
ModuleNotFoundError: No module named 'homeassistant.components.template.climate'
```

## Recommended Solution: SmartIR

For IR/RF climate control (AC units, heaters), use the **SmartIR** custom integration:

### What is SmartIR?

SmartIR is a custom component specifically designed for controlling climate devices via IR/RF controllers like Broadlink. It provides:

- ✅ Full climate entity support
- ✅ Temperature control
- ✅ HVAC modes (heat, cool, auto, dry, fan only)
- ✅ Fan speed control
- ✅ Swing mode control
- ✅ Pre-configured device files for hundreds of AC models
- ✅ External temperature sensor support
- ✅ Power monitoring support

### Installation

1. **Install via HACS** (recommended):
   - Open HACS in Home Assistant
   - Go to Integrations
   - Click the 3 dots menu → Custom repositories
   - Add: `https://github.com/smartHomeHub/SmartIR`
   - Category: Integration
   - Click "Install"

2. **Manual Installation**:
   - Download from: https://github.com/smartHomeHub/SmartIR
   - Copy `custom_components/smartir` to your HA `custom_components` folder
   - Restart Home Assistant

### Configuration

1. **Learn IR codes** using Broadlink Manager for your AC unit
2. **Create a device file** or use an existing one from SmartIR's database
3. **Configure in `configuration.yaml`**:

```yaml
# Enable SmartIR
smartir:

# Configure your AC
climate:
  - platform: smartir
    name: Living Room AC
    unique_id: living_room_ac
    device_code: 1000  # Device code from SmartIR database
    controller_data: remote.broadlink_remote  # Your Broadlink entity
    temperature_sensor: sensor.living_room_temperature  # Optional
    humidity_sensor: sensor.living_room_humidity  # Optional
    power_sensor: binary_sensor.living_room_ac_power  # Optional
```

### Finding Device Codes

SmartIR includes a database of pre-configured AC units:
- Browse: https://github.com/smartHomeHub/SmartIR/tree/master/codes/climate
- Search by brand and model
- Download the JSON file if available

### Creating Custom Device Files

If your AC model isn't in the database:

1. **Learn all IR codes** using Broadlink Manager:
   - Power on/off
   - Temperature settings (16-30°C for each mode)
   - HVAC modes (cool, heat, auto, dry, fan_only)
   - Fan speeds (auto, low, medium, high)
   - Swing modes (if applicable)

2. **Create JSON file** in `custom_codes/climate/`:

```json
{
  "manufacturer": "YourBrand",
  "supportedModels": ["Model123"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "minTemperature": 16,
  "maxTemperature": 30,
  "precision": 1,
  "operationModes": ["cool", "heat", "auto", "dry", "fan_only"],
  "fanModes": ["auto", "low", "medium", "high"],
  "commands": {
    "off": "JgBQAAABKJQTERQRFDUVEBQRFBEUERMSEzYUNhMRFDUVNRQ1FDUVNRQ1FBEVNBURExEUERQ1FTUUERM2FBITNhM2EzYUERQRFAAFKQABKEgVAA0FAAAAAAAAAAA=",
    "cool": {
      "16": "...",
      "17": "...",
      ...
    },
    "heat": {
      "16": "...",
      ...
    }
  }
}
```

3. **Reference in configuration**:

```yaml
climate:
  - platform: smartir
    name: My AC
    unique_id: my_ac
    device_code: 9999  # Custom code number
    controller_data: remote.broadlink_remote
```

## Alternative: Use Switches

If you don't want to use SmartIR, you can create **switches** for each AC function:

```yaml
# In Broadlink Manager, create switches like:
- bedroom_ac_cool_18 (Switch)
- bedroom_ac_cool_19 (Switch)
- bedroom_ac_heat_22 (Switch)
- bedroom_ac_fan_high (Switch)
```

Then use these switches in automations or scripts.

## Links

- **SmartIR GitHub**: https://github.com/smartHomeHub/SmartIR
- **SmartIR Climate Codes**: https://github.com/smartHomeHub/SmartIR/tree/master/codes/climate
- **SmartIR Documentation**: https://github.com/smartHomeHub/SmartIR#climate

## Support

For SmartIR-specific questions:
- SmartIR Issues: https://github.com/smartHomeHub/SmartIR/issues
- Home Assistant Community: https://community.home-assistant.io/t/smartir-control-your-climate-tv-and-fan-devices-via-ir-rf-controllers/100798
