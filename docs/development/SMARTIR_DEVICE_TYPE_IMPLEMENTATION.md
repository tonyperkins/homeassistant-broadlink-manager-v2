# SmartIR Device Type Implementation Plan

## Overview
Expand the device management system to support multiple IR/RF device types (Broadlink, SmartIR) with a unified interface. This will allow users to either learn IR codes manually via Broadlink devices or use pre-configured SmartIR device codes from the community repository.

## Goals
1. Add device type selection (dropdown for future extensibility)
2. Integrate SmartIR code repository for manufacturer/model selection
3. Create consistent UI flow for both Broadlink and SmartIR device paths
4. Fix YAML generation to create proper device instances (not just profiles)
5. Support searchable manufacturer/model dropdowns

## Architecture Changes

### Backend Components

#### 1. SmartIR Code Service (`app/smartir_code_service.py`)
**Purpose**: Fetch and cache SmartIR device codes from GitHub repository

**Key Features**:
- Fetch code directory structure from GitHub API
- Cache manufacturer/model data locally (24hr TTL)
- Parse JSON files to extract device information
- Filter codes by entity type (climate, fan, media_player)

**API Endpoints**:
```python
GET /api/smartir/manufacturers?entity_type=climate
GET /api/smartir/models?entity_type=climate&manufacturer=samsung
GET /api/smartir/code/{code_id}  # Fetch specific device code details
```

#### 2. Device Manager Updates (`app/device_manager.py`)
**Changes**:
- Add `device_type` field to device model (enum: 'broadlink', 'smartir')
- Add SmartIR-specific fields:
  - `manufacturer`
  - `model`
  - `device_code` (SmartIR code ID)
  - `controller_device` (which Broadlink device sends the codes)
  - `temperature_sensor` (for climate entities)
  - `humidity_sensor` (for climate entities)

#### 3. YAML Generator Updates (`app/yaml_generator.py`)
**Current Issue**: Generates profile files instead of device instances

**Fix Required**:
```yaml
# BEFORE (incorrect - profile file)
# config/smartir/climate_samsung.yaml
- platform: smartir
  name: Samsung AC
  device_code: 1000

# AFTER (correct - device instance file)
# config/smartir/living_room_ac.yaml
climate:
  - platform: smartir
    name: Living Room AC
    unique_id: living_room_ac
    device_code: 1000
    controller_data:
      host: 192.168.1.50  # Broadlink device IP
    temperature_sensor: sensor.living_room_temperature
    humidity_sensor: sensor.living_room_humidity
```

### Frontend Components

#### 1. Device Type Selection
**Component**: `AddDeviceModal.vue` (update existing)

**Changes**:
- Add device type dropdown at top of form (before device name)
- Options: "Broadlink Device", "SmartIR Device"
- Show/hide relevant fields based on selection
- Default to "Broadlink Device" for backward compatibility

#### 2. SmartIR Manufacturer/Model Selection
**New Components**:
- `SmartIRDeviceSelector.vue` - Container for SmartIR-specific fields
- `SearchableDropdown.vue` - Reusable searchable dropdown component

**Fields**:
1. **Manufacturer** (searchable dropdown)
   - Fetches from `/api/smartir/manufacturers?entity_type={type}`
   - Filters models when selected
   
2. **Model/Code** (searchable dropdown)
   - Fetches from `/api/smartir/models?entity_type={type}&manufacturer={mfr}`
   - Shows model name and code ID
   
3. **Broadlink Controller** (dropdown)
   - Select which Broadlink device will send the IR codes
   - Required for SmartIR devices
   
4. **Additional Sensors** (conditional)
   - For climate entities: temperature_sensor, humidity_sensor
   - Optional fields with HA entity selector

#### 3. Consistent UI Flow
**Shared Fields** (both device types):
- Device Name
- Entity Type (climate, fan, media_player, etc.)
- Area
- Icon

**Broadlink-Specific Fields**:
- Broadlink Device (which device to use)
- Learn Commands button (existing flow)

**SmartIR-Specific Fields**:
- Manufacturer (searchable dropdown)
- Model (searchable dropdown)
- Broadlink Controller (which device sends codes)
- Temperature Sensor (climate only)
- Humidity Sensor (climate only)

## Implementation Phases

### Phase 1: Backend Infrastructure
**Tasks**:
1. ✅ Create docs/development folder structure
2. ✅ Move development docs to new location
3. Create `SmartIRCodeService` class
4. Implement GitHub API integration with caching
5. Add API endpoints for manufacturers/models
6. Update device model with new fields

**Deliverables**:
- Working API endpoints for SmartIR code fetching
- Cached manufacturer/model data
- Updated device data model

### Phase 2: YAML Generation Fix
**Tasks**:
1. Audit current YAML generation logic
2. Implement proper device instance generation
3. Add controller_data with Broadlink device IP
4. Support optional sensor fields
5. Create migration script for existing SmartIR configs

**Deliverables**:
- Correct YAML file generation for SmartIR devices
- Migration path for existing configurations

### Phase 3: Frontend Components
**Tasks**:
1. Create `SearchableDropdown.vue` component
2. Update `AddDeviceModal.vue` with device type dropdown
3. Create `SmartIRDeviceSelector.vue` component
4. Implement manufacturer/model selection flow
5. Add Broadlink controller selection
6. Add conditional sensor fields for climate entities

**Deliverables**:
- Unified device creation UI
- Working SmartIR device selection flow
- Searchable manufacturer/model dropdowns

### Phase 4: Integration & Testing
**Tasks**:
1. End-to-end testing of device creation flow
2. Verify YAML file generation
3. Test with actual Home Assistant integration
4. Update documentation
5. Add unit tests for new services
6. Add E2E tests for new UI flows

**Deliverables**:
- Fully tested feature
- Updated user documentation
- Test coverage for new code

## Technical Specifications

### SmartIR Code Repository Structure
```
https://github.com/smartHomeHub/SmartIR/tree/master/codes/
├── climate/
│   ├── 1000.json (Samsung)
│   ├── 1001.json (LG)
│   └── ...
├── fan/
│   ├── 1000.json
│   └── ...
└── media_player/
    ├── 1000.json
    └── ...
```

### GitHub API Endpoints
```
# List files in a directory
GET https://api.github.com/repos/smartHomeHub/SmartIR/contents/codes/{entity_type}

# Get file content
GET https://api.github.com/repos/smartHomeHub/SmartIR/contents/codes/{entity_type}/{code_id}.json
```

### Device Code JSON Structure
```json
{
  "manufacturer": "Samsung",
  "supportedModels": ["AR09FSSEDWUN", "AR12FSSEDWUN"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "minTemperature": 16,
  "maxTemperature": 30,
  "precision": 1,
  "operationModes": ["off", "cool", "heat", "dry", "fan_only"],
  "fanModes": ["auto", "low", "medium", "high"],
  "commands": {
    "off": "...",
    "cool": {
      "16": {
        "auto": "...",
        "low": "..."
      }
    }
  }
}
```

### Cache Strategy
- **Storage**: In-memory cache with file system backup
- **TTL**: 24 hours for manufacturer/model lists
- **Invalidation**: Manual refresh button in UI
- **Fallback**: Serve from cache if GitHub API unavailable

## UI/UX Considerations

### Device Type Selection
- Prominent placement at top of form
- Clear labels: "Broadlink Device" vs "SmartIR Device"
- Help text explaining the difference
- Default to Broadlink for backward compatibility

### Searchable Dropdowns
- Type-ahead filtering
- Show both manufacturer and model name
- Display code ID for reference
- Keyboard navigation support
- Loading states while fetching data

### Form Validation
- Require manufacturer/model for SmartIR devices
- Require Broadlink controller for SmartIR devices
- Validate sensor entity IDs (if provided)
- Show clear error messages

### Progressive Disclosure
- Only show relevant fields based on device type
- Collapse/expand sections as needed
- Maintain form state when switching device types

## Migration Strategy

### Existing SmartIR Configurations
1. Detect old-style profile files
2. Prompt user to migrate
3. Convert to new device instance format
4. Preserve all existing settings
5. Backup old files before migration

### Backward Compatibility
- Existing Broadlink devices continue to work unchanged
- Old SmartIR profile files still readable (deprecated)
- Gradual migration path for users

## Success Criteria

1. ✅ Users can select device type from dropdown
2. ✅ SmartIR manufacturer/model selection works smoothly
3. ✅ Generated YAML files create proper HA entities
4. ✅ UI is consistent between Broadlink and SmartIR flows
5. ✅ Code fetching and caching works reliably
6. ✅ Existing devices continue to work without changes
7. ✅ Documentation is clear and comprehensive

## Future Enhancements

### Additional Device Types
- Tuya IR devices
- ESPHome IR transmitters
- Other IR/RF controllers

### Enhanced SmartIR Features
- Custom code editing
- Code contribution workflow
- Community ratings for device codes
- Code testing interface

### Advanced Features
- Bulk device import
- Device templates
- Automated device discovery
- IR code learning improvements

## Notes

- Keep UI consistent with existing design patterns
- Maintain backward compatibility with existing devices
- Use existing Vue components where possible
- Follow Home Assistant naming conventions
- Ensure proper error handling and user feedback
- Add comprehensive logging for debugging

## References

- SmartIR Repository: https://github.com/smartHomeHub/SmartIR
- SmartIR Codes: https://github.com/smartHomeHub/SmartIR/tree/master/codes
- GitHub API Docs: https://docs.github.com/en/rest
- Home Assistant SmartIR Integration: https://github.com/smartHomeHub/SmartIR

---

**Document Status**: Active Development
**Last Updated**: 2025-10-14
**Next Review**: After Phase 1 completion
