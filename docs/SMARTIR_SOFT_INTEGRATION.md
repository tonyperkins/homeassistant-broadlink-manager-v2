# SmartIR Soft Integration Design

## Overview

Broadlink Manager will gracefully integrate with SmartIR when available, but function fully without it. This is a **soft dependency** - SmartIR enhances functionality but is not required.

## Design Principles

1. **Auto-detection** - Detect SmartIR on startup and page load
2. **Graceful degradation** - Full functionality without SmartIR
3. **Contextual guidance** - Show SmartIR benefits at relevant points
4. **No hard dependency** - Never block features if SmartIR is missing
5. **Clear messaging** - Users understand what they gain with SmartIR

## Detection Strategy

### On Application Startup

```python
# app/main.py
from smartir_detector import SmartIRDetector

smartir = SmartIRDetector()
status = smartir.get_status()

if status["installed"]:
    logger.info(f"SmartIR detected (v{status['version']})")
    logger.info(f"Available platforms: {', '.join(status['platforms'])}")
else:
    logger.info("SmartIR not detected - climate features limited")
```

### On Page Load (Frontend)

```javascript
// Check SmartIR status when app loads
async function checkSmartIR() {
  const response = await fetch('/api/smartir/status');
  const status = await response.json();
  
  // Store in app state
  store.commit('setSmartIRStatus', status);
  
  // Show notification if not installed
  if (!status.installed) {
    showSmartIRPromotion();
  }
}
```

## UI Integration Points

### 1. Dashboard Banner (When SmartIR Not Installed)

**Location**: Top of main interface

```
┌─────────────────────────────────────────────────────────────┐
│ ℹ️ Want climate device support? Install SmartIR!           │
│                                                              │
│ SmartIR enables full AC/heater control with:                │
│ • Temperature control • HVAC modes • 120+ device profiles   │
│                                                              │
│ [Learn More] [Install Guide] [Dismiss]                      │
└─────────────────────────────────────────────────────────────┘
```

**Behavior**:
- Shows once per session
- Dismissible (stored in localStorage)
- "Don't show again" option

### 2. Entity Type Selection (Contextual Messaging)

**Location**: When user selects entity type

```
Entity Type: [Dropdown ▼]
  • Light
  • Fan
  • Switch
  • Media Player
  • Climate ⓘ Requires SmartIR
```

**When "Climate" is selected without SmartIR**:

```
┌─────────────────────────────────────────────────────────────┐
│ ⚠️ Climate Entity Type Not Available                        │
│                                                              │
│ Climate entities (AC, heaters) require SmartIR integration. │
│                                                              │
│ What you can do:                                            │
│ 1. Install SmartIR via HACS (recommended)                   │
│ 2. Use switches for basic AC control (workaround)           │
│                                                              │
│ [View SmartIR Install Guide] [Use Switches Instead]         │
└─────────────────────────────────────────────────────────────┘
```

### 3. SmartIR Profile Builder (When Installed)

**Location**: New section in main interface

**When SmartIR is installed**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🌡️ SmartIR Device Profiles                                 │
│                                                              │
│ ✅ SmartIR v1.17.9 detected                                 │
│                                                              │
│ [+ Create Climate Profile]                                  │
│ [+ Create Media Player Profile]                             │
│ [+ Create Fan Profile]                                      │
│                                                              │
│ Your Profiles:                                              │
│ • Living Room AC (Climate) - Code: 10001 [Edit]            │
│ • Bedroom TV (Media Player) - Code: 10002 [Edit]           │
└─────────────────────────────────────────────────────────────┘
```

**When SmartIR is NOT installed**:
```
┌─────────────────────────────────────────────────────────────┐
│ 🌡️ SmartIR Device Profiles                                 │
│                                                              │
│ ⚠️ SmartIR not detected                                     │
│                                                              │
│ Install SmartIR to unlock:                                  │
│ • Climate device profiles (AC, heaters)                     │
│ • Advanced media player controls                            │
│ • Pre-configured device database                            │
│                                                              │
│ [View Installation Guide]                                   │
└─────────────────────────────────────────────────────────────┘
```

### 4. Command Learning Interface

**Location**: When learning commands for climate devices

**Without SmartIR**:
```
Device: bedroom_ac
Commands: ac_on, ac_off, cool_18, cool_19, heat_22...

💡 Tip: These climate commands work best with SmartIR!
   [Learn about SmartIR integration →]
```

### 5. Entity Generation Results

**Location**: After generating entities

**Without SmartIR**:
```
✅ Generated 15 entities
   • 5 lights
   • 3 fans
   • 7 switches

ℹ️ Climate commands detected but not generated
   Install SmartIR to create climate entities
   [View SmartIR Guide]
```

**With SmartIR**:
```
✅ Generated 18 entities
   • 5 lights
   • 3 fans
   • 7 switches
   • 3 climate (via SmartIR profiles)
```

## API Endpoints

### GET /api/smartir/status

**Response when installed**:
```json
{
  "installed": true,
  "version": "1.17.9",
  "path": "/config/custom_components/smartir",
  "platforms": ["climate", "media_player", "fan"],
  "device_counts": {
    "climate": 125,
    "media_player": 45,
    "fan": 12
  },
  "recommendation": {
    "message": "SmartIR detected! You can now create climate device profiles.",
    "action": "create_profile",
    "next_steps": [
      "Use 'Create SmartIR Profile' to build device profiles",
      "Learn IR codes for your climate devices",
      "Generate SmartIR-compatible JSON files"
    ]
  }
}
```

**Response when not installed**:
```json
{
  "installed": false,
  "version": null,
  "path": "/config/custom_components/smartir",
  "platforms": [],
  "device_counts": {},
  "recommendation": {
    "message": "SmartIR not detected. Install it to unlock climate device support!",
    "action": "install_smartir",
    "url": "https://github.com/smartHomeHub/SmartIR",
    "benefits": [
      "Full climate entity support (AC, heaters)",
      "120+ pre-configured device profiles",
      "Temperature and humidity sensor integration",
      "HVAC mode control (heat, cool, auto, dry, fan)"
    ]
  }
}
```

### GET /api/smartir/install-instructions

**Response**:
```json
{
  "title": "Install SmartIR",
  "description": "SmartIR enables full climate device support...",
  "methods": [
    {
      "name": "HACS (Recommended)",
      "steps": [
        "Open HACS in Home Assistant",
        "Go to Integrations",
        "Click the 3 dots menu → Custom repositories",
        "Add: https://github.com/smartHomeHub/SmartIR",
        "Category: Integration",
        "Click 'Install'",
        "Restart Home Assistant"
      ]
    },
    {
      "name": "Manual Installation",
      "steps": [...]
    }
  ],
  "verification": "After installation, refresh this page to enable SmartIR features.",
  "links": {
    "github": "https://github.com/smartHomeHub/SmartIR",
    "documentation": "https://github.com/smartHomeHub/SmartIR#readme"
  }
}
```

## Feature Matrix

| Feature | Without SmartIR | With SmartIR |
|---------|----------------|--------------|
| **Light entities** | ✅ Full support | ✅ Full support |
| **Fan entities** | ✅ Full support | ✅ Full support |
| **Switch entities** | ✅ Full support | ✅ Full support |
| **Media Player entities** | ✅ Full support | ✅ Enhanced with SmartIR profiles |
| **Climate entities** | ⚠️ Switches only | ✅ Full native climate entities |
| **IR code learning** | ✅ Full support | ✅ Full support |
| **Command management** | ✅ Full support | ✅ Full support |
| **Entity generation** | ✅ Template YAML | ✅ Template YAML + SmartIR profiles |
| **Device profiles** | ❌ Not available | ✅ Create SmartIR profiles |
| **Profile library** | ❌ Not available | ✅ Access 120+ devices |

## User Workflows

### Workflow 1: User Without SmartIR (Basic Usage)

1. **Install Broadlink Manager** add-on
2. **Learn IR codes** for devices
3. **Create entities** (lights, fans, switches)
4. **See promotion** for SmartIR (dismissible)
5. **Continue using** basic entities
6. **Optional**: Install SmartIR later

### Workflow 2: User Installs SmartIR Later

1. **Using Broadlink Manager** with basic entities
2. **Sees SmartIR promotion** in UI
3. **Clicks "Install Guide"**
4. **Installs SmartIR** via HACS
5. **Refreshes Broadlink Manager**
6. **New features appear**: "Create SmartIR Profile" button
7. **Creates climate profiles** for existing devices

### Workflow 3: User With SmartIR (Advanced Usage)

1. **Install SmartIR** first (via HACS)
2. **Install Broadlink Manager** add-on
3. **Auto-detected**: "SmartIR detected!" message
4. **Full feature set** available immediately
5. **Create SmartIR profiles** for climate devices
6. **Generate native climate entities**

## Implementation Phases

### Phase 1: Detection & Messaging (Week 1)
- ✅ Create `smartir_detector.py`
- ✅ Create `/api/smartir/status` endpoint
- [ ] Add SmartIR status check to frontend
- [ ] Show banner when not installed
- [ ] Add contextual messages in entity type selection

### Phase 2: UI Integration (Week 2)
- [ ] Create SmartIR status component (Vue)
- [ ] Add install guide modal
- [ ] Update entity type dropdown with icons/warnings
- [ ] Add "Learn More" links throughout UI

### Phase 3: Profile Builder (Week 3-4)
- [ ] Create SmartIR profile builder UI (climate only)
- [ ] Guided workflow for learning climate codes
- [ ] JSON file generation
- [ ] YAML config generation

### Phase 4: Polish (Week 5)
- [ ] Add profile management (edit, delete)
- [ ] Profile import/export
- [ ] Better error messages
- [ ] Documentation updates

## Configuration

No configuration needed! Detection is automatic.

**Optional**: User can dismiss SmartIR promotions:
```javascript
// Stored in localStorage
{
  "smartir_promotion_dismissed": true,
  "smartir_last_check": "2025-10-14T12:00:00Z"
}
```

## Error Handling

### SmartIR Installed But Broken

```json
{
  "installed": true,
  "version": null,
  "error": "Could not read manifest.json",
  "recommendation": {
    "message": "SmartIR installation appears corrupted",
    "action": "reinstall",
    "steps": [
      "Uninstall SmartIR via HACS",
      "Restart Home Assistant",
      "Reinstall SmartIR via HACS"
    ]
  }
}
```

### SmartIR Removed After Profiles Created

```
⚠️ Warning: SmartIR profiles detected but SmartIR is not installed
   
   You have 3 SmartIR profiles that won't work without SmartIR:
   • Living Room AC (Climate)
   • Bedroom TV (Media Player)
   
   [Reinstall SmartIR] [Delete Profiles]
```

## Testing Strategy

### Manual Testing Checklist

**Without SmartIR:**
- [ ] Banner shows on first load
- [ ] Banner dismissible
- [ ] Climate type shows warning
- [ ] Install guide accessible
- [ ] All other features work normally

**With SmartIR:**
- [ ] Auto-detected on load
- [ ] Version shown correctly
- [ ] Platform list accurate
- [ ] Profile builder accessible
- [ ] No warning messages

**Transition (Install SmartIR mid-session):**
- [ ] Refresh detects SmartIR
- [ ] UI updates to show new features
- [ ] No errors or broken states

## Documentation Updates

### README.md

Add section:
```markdown
## SmartIR Integration (Optional)

Broadlink Manager works great on its own, but integrates seamlessly with 
SmartIR for advanced climate device support.

**Without SmartIR:**
- ✅ Learn IR codes
- ✅ Create lights, fans, switches, media players
- ⚠️ Climate devices as switches only

**With SmartIR:**
- ✅ Everything above, plus:
- ✅ Full climate entities (AC, heaters)
- ✅ Temperature control
- ✅ HVAC modes (heat, cool, auto, dry)
- ✅ 120+ pre-configured device profiles

[Install SmartIR →](docs/SMARTIR_INTEGRATION.md)
```

### New Doc: SMARTIR_INTEGRATION.md

Comprehensive guide covering:
- What is SmartIR
- Why integrate with it
- Installation steps
- Creating profiles
- Troubleshooting

## Benefits of This Approach

### For Users
- ✅ **No forced dependency** - Works without SmartIR
- ✅ **Clear upgrade path** - Easy to add SmartIR later
- ✅ **Contextual guidance** - Learn about SmartIR when relevant
- ✅ **No confusion** - Clear what features require SmartIR

### For Development
- ✅ **Modular design** - SmartIR code isolated
- ✅ **Easy testing** - Test with/without SmartIR
- ✅ **Maintainable** - No tight coupling
- ✅ **Future-proof** - Can add more integrations

### For Community
- ✅ **Lower barrier** - Don't need SmartIR to start
- ✅ **Promotes SmartIR** - More users discover it
- ✅ **Better ecosystem** - Tools work together
- ✅ **No fragmentation** - One tool, multiple modes
