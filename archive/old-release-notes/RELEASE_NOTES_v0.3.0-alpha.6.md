# Release Notes - v0.3.0-alpha.6

**Release Date:** November 12, 2025  
**Type:** Alpha Release (Testing)

## 🎯 What's New

### SmartIR Preset Modes Support

Added comprehensive support for preset modes in SmartIR climate profiles, allowing users to configure special operating modes like Eco, Boost, Sleep, Away, and Comfort.

## ✨ Features Added

### Climate Profile Form
- **New "Preset Modes" section** with 6 common preset options:
  - None (default/normal operation)
  - Eco (energy-saving mode)
  - Boost (high-power/turbo mode)
  - Sleep (quiet night mode)
  - Away (vacation/absence mode)
  - Comfort (optimal comfort mode)

### Command Generation
- Commands now include preset mode combinations
- **Command key format:** `cool_24_auto_eco` (mode_temp_fan_preset)
- **Command label format:** `COOL 24°C auto [eco]` (preset shown in brackets)
- Command count automatically updates to reflect preset combinations

### Profile Generation
- Generated JSON profiles include `presetModes` array
- Follows SmartIR format specification exactly
- Compatible with existing SmartIR Home Assistant integration

### Profile Loading
- Automatic inference of preset modes from existing command keys
- Seamless editing of profiles with preset modes

## 📊 Impact on Command Count

Preset modes multiply the total number of commands to learn:

**Example Configuration:**
- 4 HVAC modes (auto, cool, heat, dry)
- 15 temperatures (16-30°C)
- 4 fan speeds (auto, low, medium, high)

**Without Presets:**
- Complete Mode: 240 commands (~2 hours)
- Quick Mode: 16 commands (~8 minutes)

**With 3 Presets (none, eco, boost):**
- Complete Mode: 720 commands (~6 hours) - 3x multiplier
- Quick Mode: 48 commands (~24 minutes) - 3x multiplier

## 🔧 Technical Details

### Files Modified
1. `frontend/src/components/smartir/ClimateProfileForm.vue`
   - Added preset modes UI section
   - Updated command count calculations

2. `frontend/src/components/smartir/SmartIRProfileBuilder.vue`
   - Added `presetModes` to JSON generation
   - Added `inferPresetModesFromCommands()` function

3. `frontend/src/components/smartir/CommandLearningWizard.vue`
   - Updated command generation for preset combinations
   - Enhanced command keys and labels

### SmartIR Compatibility

Generated profiles follow the official SmartIR format:

```json
{
  "manufacturer": "Daikin",
  "supportedModels": ["FTXS25CVMA"],
  "operationModes": ["auto", "heat", "cool", "dry"],
  "fanModes": ["auto", "low", "medium", "high"],
  "presetModes": ["none", "eco", "boost"],
  "commands": {
    "off": "...",
    "cool_24_auto_none": "...",
    "cool_24_auto_eco": "...",
    "cool_24_auto_boost": "..."
  }
}
```

## 🧪 Testing Instructions

### For Alpha Testers

1. **Create a new climate profile:**
   - Navigate to SmartIR Profile Builder
   - Select Platform: Climate
   - Configure basic settings (manufacturer, model, temps, modes)

2. **Configure preset modes:**
   - Scroll to "Preset Modes (Optional)" section
   - Select 2-3 preset modes (e.g., none, eco, boost)
   - Verify command count increases (should multiply by preset count)

3. **Learn commands:**
   - Proceed to command learning
   - Verify commands show preset in brackets: `[eco]`, `[boost]`
   - Learn at least one command per preset mode

4. **Generate profile:**
   - Complete the wizard
   - Download/view the generated JSON
   - Verify `presetModes` array is present
   - Verify command keys include preset suffix

5. **Test in Home Assistant:**
   - Import the profile to SmartIR
   - Verify preset mode selector appears in HA UI
   - Test switching between preset modes

### Expected Behavior

✅ **Success Indicators:**
- Preset modes section visible in form
- Command count multiplies when presets selected
- Commands show preset in brackets
- JSON includes `presetModes` array
- Preset mode selector appears in HA

❌ **Issues to Report:**
- Preset modes not visible
- Command count doesn't change
- JSON missing `presetModes`
- Errors during command learning
- Preset selector missing in HA

## 📝 User Request

This feature was implemented based on user feedback:

> "Is it possible to include the preset modes in the climate entity? I've copy-pasted this code from the documentation on GitHub showing `presetModes: ["none", "eco", "hi_power"]`"

The implementation follows the SmartIR documentation and format specification exactly.

## 🐛 Known Issues

None at this time.

## 📚 Documentation

- Implementation details: `docs/development/PRESET_MODES_IMPLEMENTATION.md`
- SmartIR format: https://github.com/smartHomeHub/SmartIR/blob/master/docs/CODES_SYNTAX.md

## 🚀 Installation

### Docker (Recommended)
```bash
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.6
```

### Manual
```bash
git checkout v0.3.0-alpha.6
cd frontend && npm install && npm run build
cd ../app && pip install -r requirements.txt
python main.py
```

## 💬 Feedback

Please report any issues or feedback:
- GitHub Issues: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues
- Include "v0.3.0-alpha.6" in the issue title
- Attach generated JSON profiles if relevant

## 🙏 Credits

Thanks to the community member who requested this feature and provided the SmartIR documentation reference!

---

**Previous Release:** [v0.3.0-alpha.5](RELEASE_NOTES_v0.3.0-alpha.5.md)  
**Next Release:** TBD
