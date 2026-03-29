# 🎯 SmartIR Preset Modes Support

Added comprehensive support for preset modes in SmartIR climate profiles, allowing users to configure special operating modes like Eco, Boost, Sleep, Away, and Comfort.

## ✨ What's New

### Climate Profile Form
- **New "Preset Modes" section** with 6 common preset options:
  - None, Eco, Boost, Sleep, Away, Comfort
- Command count automatically updates to reflect preset combinations

### Command Generation
- Commands include preset mode combinations
- Format: `cool_24_auto_eco` (mode_temp_fan_preset)
- Labels show preset in brackets: `COOL 24°C auto [eco]`

### Profile Generation
- Generated JSON profiles include `presetModes` array
- Fully compatible with SmartIR format specification
- Works seamlessly with Home Assistant SmartIR integration

## 📊 Command Count Impact

**Example:** 4 modes × 15 temps × 4 fan speeds

**Without Presets:**
- Complete: 240 commands (~2 hours)
- Quick: 16 commands (~8 minutes)

**With 3 Presets:**
- Complete: 720 commands (~6 hours) - 3x
- Quick: 48 commands (~24 minutes) - 3x

## 🧪 Testing

1. Create a new climate profile
2. Select 2-3 preset modes in the form
3. Verify command count increases
4. Learn commands (show preset in brackets)
5. Generate JSON (includes `presetModes` array)
6. Import to SmartIR and test in HA

## 📝 User Request

Implemented based on community feedback requesting preset modes support as shown in SmartIR documentation.

## 📚 Documentation

- [Implementation Details](docs/development/PRESET_MODES_IMPLEMENTATION.md)
- [Full Release Notes](RELEASE_NOTES_v0.3.0-alpha.6.md)

## 🚀 Installation

**Docker:**
```bash
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.6
```

**Manual:**
```bash
git checkout v0.3.0-alpha.6
cd frontend && npm install && npm run build
```

## 💬 Feedback

Report issues with "v0.3.0-alpha.6" in the title. Attach generated JSON profiles if relevant.

---

**Full Changelog**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/compare/v0.3.0-alpha.5...v0.3.0-alpha.6
