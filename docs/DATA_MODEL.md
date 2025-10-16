# Broadlink Manager Data Model

**Version:** 2.0  
**Last Updated:** October 15, 2025

---

## Overview

Broadlink Manager uses three primary data storage systems:

1. **Device Manager** - Manages device metadata and commands (new in v2)
2. **Storage Manager** - Legacy entity metadata (backward compatibility)
3. **Home Assistant Storage** - Broadlink IR/RF codes (managed by HA)

---

## 1. Device Manager Storage

**Location:** `/config/broadlink_manager/devices.json`

**Purpose:** Track managed devices (both Broadlink and SmartIR)

### Device Schema

```json
{
  "devices": {
    "<device_id>": {
      "device_id": "string",           // Unique identifier
      "device_type": "string",         // "broadlink" or "smartir"
      "device_name": "string",         // Display name (optional)
      "name": "string",                // Alias for device_name (compatibility)
      "broadlink_entity": "string",    // HA entity ID (e.g., "remote.master_bedroom_rm4_pro")
      "area": "string",                // Area name (e.g., "Master Bedroom")
      "commands": {                    // Command mappings
        "<command_name>": "string"     // Command name in Broadlink storage
      },
      "created_at": "string",          // ISO 8601 timestamp
      "updated_at": "string"           // ISO 8601 timestamp (optional)
    }
  }
}
```

### Device Types

#### Broadlink Device

Represents a device controlled via learned IR/RF commands.

```json
{
  "samsung_model1": {
    "device_id": "samsung_model1",
    "device_type": "broadlink",
    "device_name": "Samsung Model1",
    "broadlink_entity": "remote.master_bedroom_rm4_pro",
    "area": "Master Bedroom",
    "commands": {
      "turn_on": "turn_on",
      "turn_off": "turn_off",
      "volume_up": "volume_up"
    },
    "created_at": "2025-10-15T19:30:00Z"
  }
}
```

**Field Notes:**
- `device_id`: Used as storage key in Broadlink codes (e.g., `broadlink_remote_<id>_codes`)
- `commands`: Maps logical command names to Broadlink storage command names
- `broadlink_entity`: Which Broadlink remote sends the commands

#### SmartIR Device

Represents a device controlled via SmartIR integration.

```json
{
  "climate.living_room_ac": {
    "device_id": "climate.living_room_ac",
    "device_type": "smartir",
    "device_name": "Living Room AC",
    "area": "Living Room",
    "smartir_config": {
      "platform": "climate",
      "code_id": 1080,
      "manufacturer": "Samsung",
      "model": "AR09FSSEDWUNEU"
    },
    "created_at": "2025-10-15T19:30:00Z"
  }
}
```

**Field Notes:**
- `device_id`: Usually matches HA entity ID
- `smartir_config`: Configuration for SmartIR integration
- No `commands` field (uses SmartIR code library)

---

## 2. Storage Manager (Legacy)

**Location:** `/config/broadlink_manager/metadata.json`

**Purpose:** Backward compatibility with v1 entity metadata

### Entity Schema

```json
{
  "entities": {
    "<entity_id>": {
      "entity_type": "string",         // "light", "fan", "switch", "media_player"
      "device": "string",              // Device name in Broadlink storage
      "broadlink_entity": "string",    // HA entity ID of Broadlink remote
      "area": "string",                // Area name
      "commands": {                    // Command role mappings
        "<role>": "string"             // e.g., "turn_on": "light_on"
      },
      "friendly_name": "string",       // Display name
      "name": "string",                // Custom name (overrides friendly_name)
      "icon": "string",                // MDI icon (optional)
      "enabled": boolean,              // Whether to generate entity
      "speed_count": number,           // For fans: number of speeds
      "auto_detected": boolean         // Whether auto-detected
    }
  },
  "stats": {
    "total_entities": number,
    "entities_by_type": {
      "<type>": number
    },
    "last_generated": "string"         // ISO 8601 timestamp
  }
}
```

### Example Entity

```json
{
  "tony_s_office_ceiling_fan_light": {
    "entity_type": "light",
    "device": "tony_s_office_ceiling_fan",
    "broadlink_entity": "remote.tony_s_office_rm4_pro",
    "area": "Tony's Office",
    "commands": {
      "turn_on": "light_on",
      "turn_off": "light_off"
    },
    "friendly_name": "Tony's Office Ceiling Fan Light",
    "icon": "mdi:ceiling-fan-light",
    "enabled": true,
    "auto_detected": true
  }
}
```

### Command Roles by Entity Type

#### Light
- `turn_on` - Turn light on
- `turn_off` - Turn light off
- `toggle` - Toggle light (optional)

#### Fan
- `turn_on` - Turn fan on (optional)
- `turn_off` - Turn fan off
- `speed_1` through `speed_6` - Speed levels
- `reverse` - Reverse direction (optional)

#### Switch
- `turn_on` - Turn switch on
- `turn_off` - Turn switch off
- `toggle` - Toggle switch (optional)

#### Media Player
- `power` - Power toggle
- `volume_up` - Increase volume
- `volume_down` - Decrease volume
- `mute` - Mute toggle
- `play` - Play
- `pause` - Pause
- `stop` - Stop
- `play_pause` - Play/pause toggle
- `next` - Next track/channel
- `previous` - Previous track/channel
- `channel_up` - Next channel
- `channel_down` - Previous channel

---

## 3. Home Assistant Broadlink Storage

**Location:** `/config/.storage/broadlink_remote_<unique_id>_codes`

**Purpose:** Store learned IR/RF codes (managed by Broadlink integration)

### Storage Schema

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "broadlink_remote_<unique_id>_codes",
  "data": {
    "<device_name>": {
      "<command_name>": "base64_encoded_ir_code"
    }
  }
}
```

### Example

```json
{
  "version": 1,
  "minor_version": 1,
  "key": "broadlink_remote_34ea34f5b5d8_codes",
  "data": {
    "samsung_model1": {
      "turn_on": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFBIU...",
      "turn_off": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFBIU...",
      "volume_up": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFBIU..."
    },
    "living_room_ceiling_fan": {
      "light_on": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFBIU...",
      "light_off": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFBIU...",
      "fan_speed_1": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFBIU..."
    }
  }
}
```

**Notes:**
- Each Broadlink device has its own storage file
- `<device_name>` is the key used in Device Manager `device_id`
- Commands are stored as base64-encoded IR/RF signals
- **Write Latency:** Updates may take 10-30 seconds to persist

---

## 4. SmartIR Code Library

**Location:** `/config/custom_components/smartir/codes/`

**Purpose:** Pre-configured IR codes for common devices

### Directory Structure

```
codes/
├── climate/
│   ├── 1000.json  # Manufacturer codes
│   ├── 1080.json
│   └── ...
├── media_player/
│   ├── 1000.json
│   ├── 1500.json
│   └── ...
├── fan/
│   └── ...
└── light/
    └── ...
```

### Code File Schema

```json
{
  "manufacturer": "Samsung",
  "supportedModels": ["AR09FSSEDWUNEU", "AR12FSSEDWUNEU"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "minTemperature": 16,
  "maxTemperature": 30,
  "precision": 1,
  "operationModes": ["auto", "cool", "dry", "fan_only", "heat"],
  "fanModes": ["auto", "low", "medium", "high"],
  "commands": {
    "auto": {
      "16": {
        "auto": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIU..."
      }
    }
  }
}
```

---

## 5. Area Management

**Source:** Home Assistant Core (via WebSocket API)

**Purpose:** Organize entities by physical location

### Area Schema (from HA)

```json
{
  "area_id": "living_room",
  "name": "Living Room",
  "picture": null,
  "aliases": []
}
```

**Notes:**
- Areas are managed by Home Assistant
- Broadlink Manager assigns devices to areas
- Area names are stored in device/entity metadata

---

## 6. Data Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                     Home Assistant                          │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                │
│  │   Broadlink  │         │    Areas     │                │
│  │   Storage    │         │   (Core)     │                │
│  │              │         │              │                │
│  │ IR/RF Codes  │         │ Area Names   │                │
│  └──────────────┘         └──────────────┘                │
│         │                        │                         │
└─────────┼────────────────────────┼─────────────────────────┘
          │                        │
          ▼                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Broadlink Manager                              │
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐           │
│  │ Device Manager   │      │ Storage Manager  │           │
│  │                  │      │                  │           │
│  │ devices.json     │      │ metadata.json    │           │
│  │                  │      │                  │           │
│  │ • Broadlink      │      │ • Entities       │           │
│  │ • SmartIR        │      │ • Legacy format  │           │
│  └──────────────────┘      └──────────────────┘           │
│         │                           │                      │
│         └───────────┬───────────────┘                      │
│                     ▼                                      │
│         ┌──────────────────────┐                          │
│         │  Generated Entities  │                          │
│         │                      │                          │
│         │  entities.yaml       │                          │
│         │  helpers.yaml        │                          │
│         └──────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Data Flow

### Device Adoption Flow

```
1. User discovers untracked device
   ↓
2. Frontend sends adoption request
   {
     "device_name": "Samsung Model1",
     "device": "samsung_model1",
     "broadlink_entity": "remote.master_bedroom_rm4_pro",
     "commands": { "turn_on": "turn_on", ... }
   }
   ↓
3. Device Manager creates device entry
   ↓
4. Device saved to devices.json
   ↓
5. Device removed from untracked list
```

### Command Learning Flow

```
1. User initiates learn command
   ↓
2. Backend calls HA learn_command service
   ↓
3. HA prompts user to press remote button
   ↓
4. HA captures IR/RF signal
   ↓
5. HA saves to Broadlink storage (10-30s delay)
   ↓
6. Backend returns success immediately
   ↓
7. Command appears in storage after delay
```

### Entity Generation Flow

```
1. User triggers entity generation
   ↓
2. Generator reads metadata.json
   ↓
3. For each enabled entity:
   - Generate template YAML
   - Generate helper entities
   ↓
4. Write to entities.yaml and helpers.yaml
   ↓
5. Reload HA configuration
   ↓
6. Entities appear in Home Assistant
```

---

## 8. Migration Between Formats

### V1 to V2 Migration

**Scenario:** Existing metadata.json → devices.json

```python
# Old format (metadata.json)
{
  "tony_s_office_ceiling_fan_light": {
    "entity_type": "light",
    "device": "tony_s_office_ceiling_fan",
    "commands": {"turn_on": "light_on", "turn_off": "light_off"}
  }
}

# New format (devices.json)
{
  "tony_s_office_ceiling_fan": {
    "device_id": "tony_s_office_ceiling_fan",
    "device_type": "broadlink",
    "commands": {"light_on": "light_on", "light_off": "light_off"},
    "created_at": "2025-10-15T19:30:00Z"
  }
}
```

**Migration Logic:**
1. Extract unique device names from entities
2. Aggregate commands from all entities for same device
3. Create device entries in devices.json
4. Preserve original metadata.json for backward compatibility

---

## 9. API Data Contracts

### Device Adoption Request

```typescript
{
  device_name: string;           // Display name
  device: string;                // Storage key (device_id)
  broadlink_entity: string;      // HA entity ID
  commands: {                    // Command mappings
    [key: string]: string;
  };
  area?: string;                 // Optional area assignment
}
```

### Device Response

```typescript
{
  id: string;                    // device_id
  name: string;                  // Display name
  device_type: 'broadlink' | 'smartir';
  broadlink_entity?: string;     // For Broadlink devices
  area?: string;
  commands: {
    [key: string]: string;
  };
  command_count: number;         // Number of commands
  created_at: string;            // ISO 8601
}
```

### Untracked Device Response

```typescript
{
  device_name: string;           // Storage key
  command_count: number;
  commands: string[];            // List of command names
}
```

---

## 10. Storage Considerations

### Write Latency

**Home Assistant Broadlink Storage:**
- **Latency:** 10-30 seconds after API call
- **Reason:** Async storage writes in HA
- **Mitigation:** 
  - Return success immediately
  - Use deletion cache to filter recently deleted items
  - Add small delays (0.5s) after write operations

### Deletion Cache

**Purpose:** Track recently deleted commands to filter from discovery

```python
{
  "device_name": {
    "command_name": timestamp
  }
}
```

**TTL:** 60 seconds (configurable)

**Cleanup:** Automatic on discovery requests

---

## 11. Best Practices

### Device Naming
- Use snake_case: `living_room_ceiling_fan`
- Include location: `bedroom_fan`, not just `fan`
- Be descriptive: `samsung_tv_model1`, not `tv1`

### Command Naming
- Use consistent patterns: `turn_on`, `turn_off`, `volume_up`
- Avoid special characters
- Use underscores, not spaces

### Area Assignment
- Assign to controlled device location, not Broadlink location
- Use consistent area names across HA
- Update when devices are moved

### Data Integrity
- Always validate device_type field
- Check for required fields before saving
- Handle missing fields gracefully
- Maintain backward compatibility

---

## 12. Future Considerations

### Planned Enhancements

1. **Device Groups**
   - Group related devices (e.g., all bedroom devices)
   - Bulk operations on groups

2. **Command Macros**
   - Sequence multiple commands
   - Conditional logic

3. **Backup/Restore**
   - Export/import device configurations
   - Cloud backup integration

4. **Version Control**
   - Track changes to device configurations
   - Rollback capability

---

## Appendix A: File Locations

| File | Purpose | Format |
|------|---------|--------|
| `/config/broadlink_manager/devices.json` | Device metadata | JSON |
| `/config/broadlink_manager/metadata.json` | Legacy entity metadata | JSON |
| `/config/broadlink_manager/entities.yaml` | Generated HA entities | YAML |
| `/config/broadlink_manager/helpers.yaml` | Generated HA helpers | YAML |
| `/config/.storage/broadlink_remote_*_codes` | IR/RF codes | JSON |
| `/config/custom_components/smartir/codes/` | SmartIR library | JSON |

---

## Appendix B: Data Validation Rules

### Device ID
- **Pattern:** `^[a-z0-9_]+$`
- **Max Length:** 64 characters
- **Required:** Yes

### Device Type
- **Values:** `"broadlink"` or `"smartir"`
- **Required:** Yes

### Broadlink Entity
- **Pattern:** `^(remote|climate|media_player|fan)\.[a-z0-9_]+$`
- **Required:** For Broadlink devices

### Command Name
- **Pattern:** `^[a-z0-9_]+$`
- **Max Length:** 32 characters
- **Required:** Yes

### Area Name
- **Max Length:** 64 characters
- **Required:** No
- **Must exist:** In Home Assistant areas

---

## Appendix C: Error Handling

### Common Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `Device not found` | Invalid device_id | Check device exists in devices.json |
| `Command not found` | Command not in storage | Wait for HA storage sync (10-30s) |
| `Invalid device type` | Wrong device_type value | Use "broadlink" or "smartir" |
| `Broadlink entity required` | Missing for Broadlink device | Provide valid remote entity ID |
| `Area not found` | Area doesn't exist in HA | Create area in HA first |

---

**End of Data Model Documentation**
