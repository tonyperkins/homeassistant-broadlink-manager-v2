# SmartIR Integration Roadmap

## Vision

Transform Broadlink Manager into an all-in-one IR/RF management solution by integrating with SmartIR. This would eliminate the tedious manual workflow of learning codes, creating JSON files, and writing YAML configuration.

## Current State

- ✅ Broadlink Manager can learn individual IR/RF codes
- ✅ Has full `/config` directory access
- ✅ Can write files to Home Assistant configuration
- ❌ Users must manually create SmartIR JSON files
- ❌ Users must manually write YAML configuration
- ❌ No structured workflow for complete device profiles

## Proposed Solution

### Phase 1: SmartIR Code Set Builder UI

**Goal**: Replace ad-hoc code learning with structured device profile creation.

#### Features

1. **New Section in UI**: "Create SmartIR Device Profile"
   - Button: "Create New SmartIR Device"
   - Prominent placement in main interface

2. **Device Type Selection**
   - Climate (AC/Heater)
   - Media Player (TV/Stereo)
   - Fan

3. **Structured Learning Form**
   
   **For Climate Devices:**
   ```
   Device Information:
   - Manufacturer: [text input]
   - Model(s): [text input, comma-separated]
   - Min Temperature: [number, default 16]
   - Max Temperature: [number, default 30]
   
   Commands:
   ┌─────────────────────────────────────┐
   │ Power Off          [Learn IR] [✓]   │
   │ Cool - 16°C        [Learn IR] [ ]   │
   │ Cool - 17°C        [Learn IR] [ ]   │
   │ Cool - 18°C        [Learn IR] [ ]   │
   │ ...                                  │
   │ Heat - 16°C        [Learn IR] [ ]   │
   │ Heat - 17°C        [Learn IR] [ ]   │
   │ ...                                  │
   │ Fan Mode - Auto    [Learn IR] [ ]   │
   │ Fan Mode - Low     [Learn IR] [ ]   │
   │ Fan Mode - Medium  [Learn IR] [ ]   │
   │ Fan Mode - High    [Learn IR] [ ]   │
   │ Swing - On         [Learn IR] [ ]   │
   │ Swing - Off        [Learn IR] [ ]   │
   └─────────────────────────────────────┘
   
   Progress: 15/45 commands learned
   [Save Draft] [Generate SmartIR File]
   ```

   **For Media Players:**
   ```
   Device Information:
   - Manufacturer: [text input]
   - Model(s): [text input]
   
   Commands:
   ┌─────────────────────────────────────┐
   │ Power On/Off       [Learn IR] [✓]   │
   │ Volume Up          [Learn IR] [✓]   │
   │ Volume Down        [Learn IR] [✓]   │
   │ Mute               [Learn IR] [ ]   │
   │ Source - HDMI1     [Learn IR] [ ]   │
   │ Source - HDMI2     [Learn IR] [ ]   │
   │ Channel Up         [Learn IR] [ ]   │
   │ Channel Down       [Learn IR] [ ]   │
   │ ...                                  │
   └─────────────────────────────────────┘
   ```

4. **Guided Learning Process**
   - Click "Learn IR" button
   - UI enters learning mode (same as current functionality)
   - User presses button on physical remote
   - Code captured and field marked as complete ✓
   - Auto-advances to next command (optional)
   - Can skip optional commands
   - Can re-learn any command

5. **Draft Saving**
   - Save progress to metadata.json
   - Resume later without losing work
   - Multiple draft profiles supported

#### Technical Implementation

**New Files:**
- `app/smartir_builder.py` - Core logic for SmartIR profile building
- `app/templates/smartir_builder.html` - UI for device profile creation

**Data Structure (in metadata.json):**
```json
{
  "smartir_drafts": {
    "draft_001": {
      "device_type": "climate",
      "manufacturer": "Daikin",
      "models": ["Model123", "Model456"],
      "min_temp": 16,
      "max_temp": 30,
      "commands_learned": {
        "off": "JgBQAAA...",
        "cool_16": "JgBQAAA...",
        "cool_17": "JgBQAAA...",
        "heat_20": "JgBQAAA..."
      },
      "created": "2025-10-13T12:00:00",
      "modified": "2025-10-13T12:30:00"
    }
  }
}
```

### Phase 2: SmartIR File Writer

**Goal**: Automatically generate and place SmartIR JSON files.

#### Features

1. **Code Validation**
   - Check all required commands are learned
   - Validate Base64 encoding
   - Warn about missing optional commands
   - Suggest completing common command sets

2. **JSON Assembly**
   - Build SmartIR-compliant JSON structure
   - Proper formatting and encoding
   - Include all metadata

3. **Device Code Assignment**
   - Scan `/config/custom_components/smartir/codes/{type}/`
   - Find unused device code (start at 10000 for custom)
   - Avoid conflicts with existing files
   - Allow manual override

4. **Automatic File Placement**
   ```
   /config/custom_components/smartir/codes/climate/10001.json
   /config/custom_components/smartir/codes/media_player/10002.json
   /config/custom_components/smartir/codes/fan/10003.json
   ```

5. **Safety Checks**
   - Verify SmartIR is installed
   - Check directory permissions
   - Backup existing file if overwriting
   - Validate JSON before writing

#### SmartIR JSON Format

**Climate Example:**
```json
{
  "manufacturer": "Daikin",
  "supportedModels": ["Model123", "Model456"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "minTemperature": 16,
  "maxTemperature": 30,
  "precision": 1,
  "operationModes": ["cool", "heat", "auto", "dry", "fan_only"],
  "fanModes": ["auto", "low", "medium", "high"],
  "swingModes": ["on", "off"],
  "commands": {
    "off": "JgBQAAABKJQT...",
    "cool": {
      "16": "JgBQAAABKZEW...",
      "17": "JgBQAAABKZEW...",
      "18": "JgBQAAABKZEW..."
    },
    "heat": {
      "16": "JgBQAAABKZEW...",
      "17": "JgBQAAABKZEW..."
    },
    "auto": {
      "16": "JgBQAAABKZEW..."
    }
  }
}
```

**Media Player Example:**
```json
{
  "manufacturer": "Samsung",
  "supportedModels": ["UE55"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "commands": {
    "power": "JgBQAAABKJQT...",
    "volumeUp": "JgBQAAABKZEW...",
    "volumeDown": "JgBQAAABKZEW...",
    "mute": "JgBQAAABKZEW...",
    "source": "JgBQAAABKZEW...",
    "channelUp": "JgBQAAABKZEW...",
    "channelDown": "JgBQAAABKZEW..."
  }
}
```

#### Technical Implementation

**New Methods in `smartir_builder.py`:**
```python
def validate_commands(device_type: str, commands: dict) -> dict:
    """Validate learned commands are complete and valid"""
    
def find_available_device_code(device_type: str) -> int:
    """Find next available device code number"""
    
def build_smartir_json(device_type: str, profile_data: dict) -> dict:
    """Build SmartIR-compliant JSON structure"""
    
def write_smartir_file(device_type: str, device_code: int, json_data: dict) -> bool:
    """Write JSON file to SmartIR directory"""
    
def check_smartir_installed() -> bool:
    """Check if SmartIR is installed"""
```

### Phase 3: Configuration Helper

**Goal**: Generate ready-to-use YAML configuration.

#### Features

1. **Success Dialog**
   ```
   ✅ SmartIR Device Profile Created!
   
   Device Code: 10001
   Location: /config/custom_components/smartir/codes/climate/10001.json
   
   📋 Configuration YAML (click to copy):
   ┌─────────────────────────────────────────────────────┐
   │ # Add this to your configuration.yaml               │
   │ climate:                                            │
   │   - platform: smartir                               │
   │     name: Living Room AC                            │
   │     unique_id: living_room_ac                       │
   │     device_code: 10001                              │
   │     controller_data: remote.broadlink_rm4_mini      │
   │     temperature_sensor: sensor.living_room_temp     │
   │     humidity_sensor: sensor.living_room_humidity    │
   │     power_sensor: binary_sensor.living_room_ac_power│
   └─────────────────────────────────────────────────────┘
   
   [Copy to Clipboard] [Download YAML File]
   
   📝 Next Steps:
   1. Copy the YAML above
   2. Paste into your configuration.yaml
   3. Adjust entity names to match your setup
   4. Restart Home Assistant
   5. Your device will appear as a climate entity!
   
   [View in SmartIR] [Create Another Device] [Done]
   ```

2. **Smart Defaults**
   - Pre-fill controller_data with user's Broadlink entity
   - Suggest entity names based on device info
   - Include optional sensors with comments
   - Link to available temperature sensors

3. **YAML File Download**
   - Generate complete YAML snippet
   - Download as `smartir_config_10001.yaml`
   - Include comments and examples

4. **Integration with HA**
   - Option to add to package file automatically
   - Create `/config/packages/smartir_devices.yaml` if needed
   - Append new device configuration
   - Trigger config reload (if safe)

#### Technical Implementation

**New Methods:**
```python
def generate_yaml_config(device_type: str, device_code: int, profile_data: dict) -> str:
    """Generate YAML configuration snippet"""
    
def get_available_sensors() -> dict:
    """Query HA API for available temperature/humidity sensors"""
    
def write_to_package_file(yaml_config: str) -> bool:
    """Append configuration to package file"""
```

## UI/UX Enhancements

### Dashboard Integration

Add new section to main UI:
```
┌─────────────────────────────────────────────────────┐
│ 🌡️ SmartIR Device Profiles                          │
├─────────────────────────────────────────────────────┤
│ [+ Create New SmartIR Device]                       │
│                                                      │
│ Saved Profiles:                                     │
│ • Living Room AC (Climate) - Code: 10001 [Edit]    │
│ • Bedroom TV (Media Player) - Code: 10002 [Edit]   │
│ • Ceiling Fan (Fan) - Code: 10003 [Edit]           │
│                                                      │
│ Drafts:                                             │
│ • Kitchen AC (Climate) - 25/45 commands [Continue] │
└─────────────────────────────────────────────────────┘
```

### Learning Mode Improvements

- **Visual feedback**: Highlight current command being learned
- **Progress bar**: Show completion percentage
- **Bulk learning**: Learn multiple similar commands in sequence
- **Test mode**: Send learned command to verify it works
- **Command preview**: Show Base64 code for verification

## Technical Considerations

### File System Access

✅ **Already Available:**
- Broadlink Manager has `/config` directory access
- Can read/write files in custom_components
- Has necessary permissions

### SmartIR Detection

```python
def check_smartir_installed():
    smartir_path = Path("/config/custom_components/smartir")
    if not smartir_path.exists():
        return {
            "installed": False,
            "message": "SmartIR not found. Please install via HACS first.",
            "install_url": "https://github.com/smartHomeHub/SmartIR"
        }
    return {"installed": True}
```

### Device Code Management

```python
def find_available_device_code(device_type: str) -> int:
    """Find next available device code starting from 10000"""
    codes_dir = Path(f"/config/custom_components/smartir/codes/{device_type}")
    if not codes_dir.exists():
        return 10000
    
    existing_codes = []
    for file in codes_dir.glob("*.json"):
        try:
            code = int(file.stem)
            if code >= 10000:  # Only consider custom codes
                existing_codes.append(code)
        except ValueError:
            continue
    
    if not existing_codes:
        return 10000
    
    return max(existing_codes) + 1
```

### Validation

```python
REQUIRED_COMMANDS = {
    "climate": {
        "mandatory": ["off"],
        "recommended": ["cool", "heat"],
        "optional": ["auto", "dry", "fan_only"]
    },
    "media_player": {
        "mandatory": ["power"],
        "recommended": ["volumeUp", "volumeDown"],
        "optional": ["mute", "source", "channelUp", "channelDown"]
    },
    "fan": {
        "mandatory": ["off"],
        "recommended": ["speed1", "speed2", "speed3"],
        "optional": ["oscillate"]
    }
}
```

## Benefits

### For Users
- ✅ **No manual JSON editing** - All done through UI
- ✅ **No YAML guesswork** - Pre-generated configuration
- ✅ **Guided workflow** - Step-by-step process
- ✅ **Error prevention** - Validation at every step
- ✅ **Save progress** - Draft system prevents lost work
- ✅ **One tool** - Everything in Broadlink Manager

### For Community
- ✅ **Lower barrier to entry** - More users can use IR devices
- ✅ **Better device coverage** - Easier to create custom profiles
- ✅ **Standardization** - All profiles follow SmartIR format
- ✅ **Sharing** - Users can export/import profiles

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Add SmartIR detection
- [ ] Create basic UI for device profile creation
- [ ] Implement draft saving system
- [ ] Build structured learning form for climate devices

### Phase 2: Core Functionality (Week 3-4)
- [ ] Implement JSON builder for all device types
- [ ] Add device code management
- [ ] Create file writer with safety checks
- [ ] Add validation system

### Phase 3: Polish (Week 5-6)
- [ ] Build configuration helper
- [ ] Add YAML generation
- [ ] Create success dialogs
- [ ] Implement package file integration

### Phase 4: Enhancement (Week 7-8)
- [ ] Add profile import/export
- [ ] Create profile sharing system
- [ ] Add test mode for learned commands
- [ ] Build profile library/database

## Future Enhancements

### Profile Sharing
- Export profile as JSON
- Import profiles from other users
- Community profile repository
- Rating/review system

### Advanced Features
- Bulk command learning (e.g., "learn all temperatures 16-30")
- Command cloning (copy similar commands)
- Profile templates (pre-fill common patterns)
- Integration with SmartIR's official database
- Automatic profile submission to SmartIR repo

### AI/ML Possibilities
- Pattern recognition for similar commands
- Suggest missing commands based on learned ones
- Auto-detect device type from command patterns

## Resources

- **SmartIR GitHub**: https://github.com/smartHomeHub/SmartIR
- **SmartIR Format Docs**: https://github.com/smartHomeHub/SmartIR#creating-your-own-codes
- **Climate Codes**: https://github.com/smartHomeHub/SmartIR/tree/master/codes/climate
- **Media Player Codes**: https://github.com/smartHomeHub/SmartIR/tree/master/codes/media_player
- **Fan Codes**: https://github.com/smartHomeHub/SmartIR/tree/master/codes/fan

## Notes

This is a **long-term roadmap**. The current priority is fixing the immediate issues (media_player, climate removal). This integration can be tackled when ready, as it's a major feature addition that will require significant development time.

The good news: All the infrastructure is already in place (file access, learning capability, UI framework). This is primarily about creating the right workflow and user experience.
