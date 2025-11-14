# Preset Modes Implementation for SmartIR Climate Entities

## Overview

Added support for `presetModes` in SmartIR climate profiles, allowing users to configure special operating modes like Eco, Boost, Sleep, Away, and Comfort.

## User Request

A user requested the ability to include preset modes in climate entities, referencing the SmartIR documentation which shows:

```json
{
  "operationModes": ["auto", "heat", "cool", "heat_cool", "fan_only", "dry"],
  "presetModes": ["none", "eco", "hi_power"],
  "fanModes": ["low", "mid", "high", "auto"],
  "swingModes": ["off", "", "high", "auto"]
}
```

## Implementation

### 1. Frontend Form (`ClimateProfileForm.vue`)

**Added preset modes section** with checkboxes for common preset options:
- None
- Eco (energy-saving mode)
- Boost (high-power/turbo mode)
- Sleep (quiet night mode)
- Away (vacation/absence mode)
- Comfort (optimal comfort mode)

**Updated command calculations** to include preset modes in the total command count for both Quick and Complete learning modes.

**Changes:**
- Added `presetModes: []` to default config object
- Added `selectedPresetModesCount` computed property
- Updated `quickModeCommands` and `completeModeCommands` to multiply by preset mode count
- Updated command breakdown text to mention preset modes

### 2. Profile Builder (`SmartIRProfileBuilder.vue`)

**Added preset modes to JSON generation:**
```javascript
// Add preset modes if configured
if (profile.config.presetModes && profile.config.presetModes.length > 0) {
  json.presetModes = profile.config.presetModes
}
```

**Added inference function** to detect preset modes from existing command keys:
```javascript
function inferPresetModesFromCommands(commands) {
  const presetModes = new Set()
  const commandKeys = Object.keys(commands)
  
  // Check for preset mode patterns
  if (commandKeys.some(k => k.includes('none'))) presetModes.add('none')
  if (commandKeys.some(k => k.includes('eco'))) presetModes.add('eco')
  if (commandKeys.some(k => k.includes('boost'))) presetModes.add('boost')
  if (commandKeys.some(k => k.includes('sleep'))) presetModes.add('sleep')
  if (commandKeys.some(k => k.includes('away'))) presetModes.add('away')
  if (commandKeys.some(k => k.includes('comfort'))) presetModes.add('comfort')
  
  return Array.from(presetModes)
}
```

**Updated profile loading** to infer and include preset modes when editing existing profiles.

### 3. Command Learning Wizard (`CommandLearningWizard.vue`)

**Updated command generation** to create combinations including preset modes:

```javascript
// Generate commands for each mode/temp/fan/swing/preset combination
const swingList = swingModes.length > 0 ? swingModes : [null]
swingList.forEach(swingMode => {
  const presetList = presetModes.length > 0 ? presetModes : [null]
  presetList.forEach(presetMode => {
    // Build key and label
    let key = `${mode}_${temp}_${fanMode}`
    let label = `${mode.toUpperCase()} ${temp}°C ${fanMode}`
    
    if (swingMode) {
      key += `_${swingMode}`
      label += ` ${swingMode}`
    }
    
    if (presetMode) {
      key += `_${presetMode}`
      label += ` [${presetMode}]`
    }
    
    list.push({ key, label, description, ... })
  })
})
```

**Command key format:**
- Without preset: `cool_24_auto`
- With preset: `cool_24_auto_eco`
- With swing and preset: `cool_24_auto_vertical_eco`

**Label format:**
- Without preset: `COOL 24°C auto`
- With preset: `COOL 24°C auto [eco]`

## Backend Changes

**None required.** The backend already passes through profile data as-is to SmartIR. The SmartIR integration natively supports `presetModes` in the JSON profile format.

## Command Count Impact

Preset modes multiply the total number of commands to learn:

**Example with 4 modes, 15 temps, 4 fan speeds:**
- Without presets: 4 × 15 × 4 = 240 commands
- With 3 presets: 4 × 15 × 4 × 3 = 720 commands

**Quick Mode** (one representative temperature):
- Without presets: 4 × 1 × 4 = 16 commands
- With 3 presets: 4 × 1 × 4 × 3 = 48 commands

## SmartIR Compatibility

The generated JSON profile follows the SmartIR format exactly:

```json
{
  "manufacturer": "Daikin",
  "supportedModels": ["FTXS25CVMA"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "minTemperature": 16,
  "maxTemperature": 30,
  "precision": 1,
  "operationModes": ["auto", "heat", "cool", "dry"],
  "fanModes": ["auto", "low", "medium", "high"],
  "swingModes": ["off", "vertical"],
  "presetModes": ["none", "eco", "boost"],
  "commands": {
    "off": "...",
    "cool_24_auto_none": "...",
    "cool_24_auto_eco": "...",
    "cool_24_auto_boost": "..."
  }
}
```

## User Experience

1. **Profile Creation:**
   - User selects which preset modes their device supports
   - Command count automatically updates to reflect preset combinations
   - Learning wizard generates commands for all preset mode combinations

2. **Command Learning:**
   - Each command shows the preset mode in brackets: `COOL 24°C auto [eco]`
   - User learns IR codes for each preset mode combination
   - Progress bar tracks completion across all combinations

3. **Profile Generation:**
   - Generated JSON includes `presetModes` array
   - Commands are keyed with preset mode suffix
   - SmartIR integration automatically exposes preset mode selector in HA

## Testing Recommendations

1. **Create new climate profile** with preset modes selected
2. **Verify command count** increases correctly with preset modes
3. **Learn commands** for at least one preset mode combination
4. **Generate JSON** and verify `presetModes` field is present
5. **Import to SmartIR** and verify preset mode selector appears in HA
6. **Test preset switching** in Home Assistant UI

## Files Modified

1. `frontend/src/components/smartir/ClimateProfileForm.vue`
   - Added preset modes UI section
   - Updated command count calculations
   - Added presetModes to config object

2. `frontend/src/components/smartir/SmartIRProfileBuilder.vue`
   - Added presetModes to JSON generation
   - Added inferPresetModesFromCommands function
   - Updated profile loading to include preset modes

3. `frontend/src/components/smartir/CommandLearningWizard.vue`
   - Updated command generation to include preset mode combinations
   - Updated command keys and labels to show preset modes

## Complexity

**Low** - The implementation follows the existing pattern for `swingModes`:
- Same UI pattern (checkbox grid)
- Same JSON generation pattern (conditional inclusion)
- Same command generation pattern (nested loops)
- No backend changes required

## Estimated Effort

- Implementation: 1 hour
- Testing: 30 minutes
- Documentation: 30 minutes
- **Total: 2 hours**
