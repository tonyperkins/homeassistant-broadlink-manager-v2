# Device Type Detection and Controller Type Detection

## Overview

The system currently tracks **device types** (Broadlink vs. SmartIR), but does **NOT** detect **controller types** (Broadlink remote vs. Xiaomi vs. Harmony Hub). This is a gap that should be addressed in Phase 2/3.

## Current State: Device Type Detection

### Device Types

The system recognizes two device types:

1. **`broadlink`** - Native Broadlink devices that learn and send IR/RF commands
2. **`smartir`** - SmartIR devices that use pre-configured profiles

### How Device Type is Stored

**Field**: `device_type` in device metadata

**Location**: `devices.json` (device manager) or entity metadata (storage manager)

**Values**:
- `"broadlink"` (default if not specified)
- `"smartir"`

### How Device Type is Set

#### When Creating a Device

**File**: `app/api/devices.py` (line 463)

```python
device_type = data.get('device_type', 'broadlink')  # Default to 'broadlink'
```

**Source**: Comes from frontend when user creates a device

#### When Validating

**File**: `app/device_manager.py` (lines 95-98)

```python
device_type = device_data.get("device_type", "broadlink")
if device_type not in ["broadlink", "smartir"]:
    logger.error(f"Invalid device_type: {device_type}")
    return False
```

### How Device Type is Used

#### 1. Entity Generation

**File**: `app/web_server.py` (lines 594-601)

```python
# Separate Broadlink and SmartIR devices
broadlink_devices = {
    k: v for k, v in all_devices.items() 
    if v.get("device_type", "broadlink") == "broadlink"
}
smartir_devices = {
    k: v for k, v in all_devices.items() 
    if v.get("device_type") == "smartir"
}
```

**Purpose**: Generate different YAML for Broadlink (template entities) vs. SmartIR (SmartIR platform)

#### 2. Command Testing

**File**: `app/api/commands.py` (lines 176-177)

```python
is_smartir = entity_data.get('device_type') == 'smartir'
logger.info(f"Device type detected: {'SmartIR' if is_smartir else 'Broadlink'}")
```

**Purpose**: Use different command format for SmartIR (no `device` parameter)

#### 3. Command Deletion

**File**: `app/api/devices.py` (line 689)

```python
if delete_commands and device.get('device_type') == 'broadlink' and web_server:
    # Only delete from Broadlink storage for Broadlink devices
```

**Purpose**: Only Broadlink devices have commands in storage files

---

## Missing: Controller Type Detection

### The Problem

**Current**: We know if a device is "Broadlink" or "SmartIR"

**Missing**: We don't know what **controller** is being used:
- Is it a Broadlink RM4 Pro?
- Is it a Xiaomi IR remote?
- Is it a Harmony Hub?
- Is it an ESPHome IR blaster?

### Why This Matters

Different controllers have different capabilities:

| Controller Type | Learn Commands | Delete Commands | Send Commands |
|----------------|----------------|-----------------|---------------|
| **Broadlink** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Xiaomi** | ❌ No | ❌ No | ✅ Yes |
| **Harmony Hub** | ❌ No | ❌ No | ✅ Yes |
| **ESPHome** | ❌ No* | ❌ No | ✅ Yes |

*ESPHome has its own learning mechanism, not via HA

### What We Need to Detect

For SmartIR devices, we need to know:
- What is the `controller_device` entity?
- What **type** of remote is it?

---

## Solution: Controller Type Detection

### Approach 1: Parse Entity ID (Simple)

**Method**: Look at the entity ID pattern

```python
def detect_controller_type(controller_entity: str) -> str:
    """
    Detect controller type from entity ID
    
    Returns: 'broadlink', 'xiaomi', 'harmony', 'esphome', 'unknown'
    """
    entity_lower = controller_entity.lower()
    
    if 'broadlink' in entity_lower or 'rm4' in entity_lower or 'rm_' in entity_lower:
        return 'broadlink'
    elif 'xiaomi' in entity_lower or 'aqara' in entity_lower:
        return 'xiaomi'
    elif 'harmony' in entity_lower:
        return 'harmony'
    elif 'esphome' in entity_lower:
        return 'esphome'
    else:
        return 'unknown'
```

**Pros**: Simple, fast, no API calls
**Cons**: Not 100% reliable, depends on naming

### Approach 2: Query Home Assistant (Accurate)

**Method**: Get entity details from HA API

```python
async def detect_controller_type_from_ha(controller_entity: str) -> str:
    """
    Detect controller type by querying HA entity details
    
    Returns: 'broadlink', 'xiaomi', 'harmony', 'esphome', 'unknown'
    """
    # Get entity state from HA
    entity_state = await ha_api.get_state(controller_entity)
    
    if not entity_state:
        return 'unknown'
    
    # Check integration/platform
    integration = entity_state.get('attributes', {}).get('integration')
    platform = entity_state.get('attributes', {}).get('platform')
    device_class = entity_state.get('attributes', {}).get('device_class')
    
    # Map integration to controller type
    integration_map = {
        'broadlink': 'broadlink',
        'xiaomi_miio': 'xiaomi',
        'xiaomi_aqara': 'xiaomi',
        'harmony': 'harmony',
        'esphome': 'esphome'
    }
    
    return integration_map.get(integration, 'unknown')
```

**Pros**: Accurate, reliable
**Cons**: Requires API call, slower

### Approach 3: Hybrid (Recommended)

**Method**: Try entity ID pattern first, fall back to HA API if needed

```python
async def detect_controller_type(controller_entity: str, ha_api=None) -> dict:
    """
    Detect controller type with confidence level
    
    Returns: {
        'type': 'broadlink' | 'xiaomi' | 'harmony' | 'esphome' | 'unknown',
        'confidence': 'high' | 'medium' | 'low',
        'supports_learning': bool,
        'supports_deletion': bool
    }
    """
    # Quick check from entity ID
    entity_lower = controller_entity.lower()
    
    if 'broadlink' in entity_lower or 'rm4' in entity_lower:
        return {
            'type': 'broadlink',
            'confidence': 'high',
            'supports_learning': True,
            'supports_deletion': True
        }
    elif 'xiaomi' in entity_lower or 'aqara' in entity_lower:
        return {
            'type': 'xiaomi',
            'confidence': 'high',
            'supports_learning': False,
            'supports_deletion': False
        }
    elif 'harmony' in entity_lower:
        return {
            'type': 'harmony',
            'confidence': 'high',
            'supports_learning': False,
            'supports_deletion': False
        }
    elif 'esphome' in entity_lower:
        return {
            'type': 'esphome',
            'confidence': 'medium',
            'supports_learning': False,  # Has own mechanism
            'supports_deletion': False
        }
    
    # If uncertain, query HA API
    if ha_api:
        ha_type = await detect_controller_type_from_ha(controller_entity, ha_api)
        if ha_type != 'unknown':
            return {
                'type': ha_type,
                'confidence': 'high',
                'supports_learning': ha_type == 'broadlink',
                'supports_deletion': ha_type == 'broadlink'
            }
    
    # Unknown controller
    return {
        'type': 'unknown',
        'confidence': 'low',
        'supports_learning': False,  # Assume no learning for safety
        'supports_deletion': False
    }
```

---

## Implementation Plan (Phase 2/3)

### Phase 2: Add Controller Type Detection

#### 1. Create Detection Module

**File**: `app/controller_detector.py`

```python
class ControllerDetector:
    """Detect controller type and capabilities"""
    
    def __init__(self, ha_api):
        self.ha_api = ha_api
    
    async def detect_controller_type(self, controller_entity: str) -> dict:
        """Detect controller type with capabilities"""
        # Implementation from Approach 3 above
        pass
    
    def get_controller_capabilities(self, controller_type: str) -> dict:
        """Get capabilities for a controller type"""
        capabilities = {
            'broadlink': {
                'supports_learning': True,
                'supports_deletion': True,
                'supports_sending': True,
                'icon': 'mdi:remote',
                'color': '#03a9f4'
            },
            'xiaomi': {
                'supports_learning': False,
                'supports_deletion': False,
                'supports_sending': True,
                'icon': 'mdi:cellphone-wireless',
                'color': '#ff6f00'
            },
            'harmony': {
                'supports_learning': False,
                'supports_deletion': False,
                'supports_sending': True,
                'icon': 'mdi:television-guide',
                'color': '#00bcd4'
            },
            'esphome': {
                'supports_learning': False,
                'supports_deletion': False,
                'supports_sending': True,
                'icon': 'mdi:chip',
                'color': '#4caf50'
            },
            'unknown': {
                'supports_learning': False,
                'supports_deletion': False,
                'supports_sending': True,
                'icon': 'mdi:remote',
                'color': '#9e9e9e'
            }
        }
        return capabilities.get(controller_type, capabilities['unknown'])
```

#### 2. Add API Endpoint

**File**: `app/api/devices.py`

```python
@api_bp.route('/devices/controller-info/<controller_entity>', methods=['GET'])
async def get_controller_info(controller_entity):
    """Get controller type and capabilities"""
    try:
        detector = ControllerDetector(web_server.ha_api)
        info = await detector.detect_controller_type(controller_entity)
        capabilities = detector.get_controller_capabilities(info['type'])
        
        return jsonify({
            'success': True,
            'controller_entity': controller_entity,
            'type': info['type'],
            'confidence': info['confidence'],
            'capabilities': capabilities
        })
    except Exception as e:
        logger.error(f"Error detecting controller type: {e}")
        return jsonify({'error': str(e)}), 500
```

#### 3. Update Frontend

**File**: `frontend/src/components/devices/DeviceForm.vue`

```vue
<script setup>
// Detect controller type when selected
const onControllerChange = async (controllerEntity) => {
  const response = await api.get(`/api/devices/controller-info/${controllerEntity}`);
  controllerInfo.value = response.data;
  
  // Show/hide learn button based on capabilities
  showLearnButton.value = controllerInfo.value.capabilities.supports_learning;
};
</script>

<template>
  <div class="controller-info" v-if="controllerInfo">
    <span class="controller-badge" :style="{ color: controllerInfo.capabilities.color }">
      <i :class="controllerInfo.capabilities.icon"></i>
      {{ controllerInfo.type }}
    </span>
    
    <div class="capabilities">
      <span v-if="!controllerInfo.capabilities.supports_learning" class="warning">
        ⚠️ This controller doesn't support learning commands
      </span>
    </div>
  </div>
  
  <!-- Hide learn button if controller doesn't support it -->
  <button 
    v-if="showLearnButton"
    @click="learnCommand"
    class="btn btn-primary"
  >
    Learn Command
  </button>
</template>
```

---

## Current Workaround (Phase 1)

Since we don't have controller type detection yet:

### For Users

**Assumption**: If `device_type == 'smartir'`, assume controller might not support learning

**UI Behavior**: Show learn/delete buttons for all devices (not ideal)

**Documentation**: Explain in docs that non-Broadlink controllers don't support learning

### For Testing

**Use the browser DevTools method** from `TESTING_NON_BROADLINK_UI.md`:

```javascript
// Check what controller is being used
const device = /* your device object */;
const controller = device.controller_device;

if (controller.includes('broadlink')) {
  console.log('✅ Broadlink - supports learning');
} else {
  console.log('⚠️ Non-Broadlink - no learning support');
}
```

---

## Summary

### Current State ✅
- **Device type** detection works (`broadlink` vs. `smartir`)
- Used for entity generation and command handling
- Stored in device metadata

### Missing ❌
- **Controller type** detection (Broadlink vs. Xiaomi vs. Harmony Hub)
- Capability detection (supports learning/deletion?)
- UI indicators for controller type
- Automatic show/hide of learn/delete buttons

### Phase 1 (Complete) ✅
- Fixed SmartIR to work with any controller
- Backend supports non-Broadlink remotes
- YAML generation uses entity IDs

### Phase 2 (Needed) 🔨
- Add controller type detection
- Update UI to show all remote entities
- Add controller type indicators

### Phase 3 (Needed) 🔨
- Hide learn/delete buttons for non-Broadlink controllers
- Show appropriate help text
- Graceful degradation based on capabilities

---

## Testing Controller Type Detection

Once implemented, test with:

```python
# Test detection
from app.controller_detector import ControllerDetector

detector = ControllerDetector(ha_api)

# Test Broadlink
info = await detector.detect_controller_type('remote.broadlink_rm4_pro')
assert info['type'] == 'broadlink'
assert info['supports_learning'] == True

# Test Xiaomi
info = await detector.detect_controller_type('remote.xiaomi_ir_remote')
assert info['type'] == 'xiaomi'
assert info['supports_learning'] == False

# Test Harmony
info = await detector.detect_controller_type('remote.harmony_hub')
assert info['type'] == 'harmony'
assert info['supports_learning'] == False
```
