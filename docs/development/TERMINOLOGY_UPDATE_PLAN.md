# Terminology Update Plan: Generic Remote References

## Goal

Update UI terminology to be generic ("Controller Device", "Remote Device") instead of "Broadlink Device" except where specifically referring to Broadlink-only functionality.

## Terminology Changes

### General References (Change These)

| Current | New | Context |
|---------|-----|---------|
| "Broadlink Device" | "Controller Device" | When selecting remote for SmartIR |
| "Broadlink Device" | "Remote Device" | When selecting remote for any device |
| "Select Broadlink Device" | "Select Controller Device" | Dropdown placeholders |
| "All Broadlink Devices" | "All Controller Devices" | Filter labels |
| `broadlinkDevice` (variable) | `controllerDevice` | SmartIR context |
| `broadlinkDevices` (array) | `controllerDevices` or `remoteDevices` | General lists |

### Broadlink-Specific References (Keep These)

| Current | Keep As-Is | Context |
|---------|-----------|---------|
| "Broadlink Device (Learn IR Codes)" | ✅ Keep | Device type selection - learning is Broadlink-specific |
| "Broadlink Entity" | ✅ Keep | When specifically referring to Broadlink integration |
| "Point remote at Broadlink device" | ✅ Keep | Learning instructions - requires physical Broadlink |
| `/api/broadlink/devices` | ✅ Keep | API endpoint name |

## Files to Update

### High Priority (User-Facing UI)

#### 1. `frontend/src/components/devices/DeviceForm.vue`

**Lines to change:**

```vue
<!-- BEFORE -->
<label for="broadlink-entity">Broadlink Device *</label>
<option value="">-- Select Broadlink Device --</option>

<!-- AFTER -->
<label for="broadlink-entity">Remote Device *</label>
<option value="">-- Select Remote Device --</option>
```

**But keep this (Broadlink-specific):**
```vue
<option value="broadlink">📡 Broadlink Device (Learn IR Codes)</option>
```

#### 2. `frontend/src/components/devices/DeviceList.vue`

**Lines to change:**

```vue
<!-- BEFORE -->
<option value="">All Broadlink Devices</option>

<!-- AFTER -->
<option value="">All Controller Devices</option>
```

**Variable renames:**
```javascript
// BEFORE
const filters = ref({
  broadlinkDevice: ''
})

// AFTER
const filters = ref({
  controllerDevice: ''
})
```

#### 3. `frontend/src/components/devices/SmartIRDeviceSelector.vue`

**Lines to change:**

```vue
<!-- BEFORE -->
<option value="">-- Select Broadlink Device --</option>
<small>Which Broadlink device will send the IR codes</small>

<!-- AFTER -->
<option value="">-- Select Controller Device --</option>
<small>Which remote device will send the IR codes</small>
```

**Props rename:**
```javascript
// BEFORE
props: {
  broadlinkDevices: {
    type: Array,
    default: () => []
  }
}

// AFTER
props: {
  controllerDevices: {
    type: Array,
    default: () => []
  }
}
```

#### 4. `frontend/src/components/smartir/SmartIRProfileBuilder.vue`

**Lines to change:**

```vue
<!-- BEFORE -->
<label>Broadlink Device *</label>
<option value="">Select Broadlink device...</option>
<small>This device will be used to learn commands</small>

<!-- AFTER -->
<label>Controller Device *</label>
<option value="">Select controller device...</option>
<small>This device will be used to send commands</small>
```

**Variable renames:**
```javascript
// BEFORE
const broadlinkDevices = ref([])
const profile = {
  broadlinkDevice: ''
}

// AFTER
const controllerDevices = ref([])
const profile = {
  controllerDevice: ''
}
```

**Keep Broadlink-specific references in learning instructions:**
```vue
<!-- KEEP AS-IS (Broadlink-specific) -->
<p><strong>Point your IR remote directly at the Broadlink device</strong></p>
```

#### 5. `frontend/src/components/smartir/CommandLearningWizard.vue`

**Props rename:**
```javascript
// BEFORE
props: {
  broadlinkDevice: {
    type: String,
    required: true
  }
}

// AFTER
props: {
  controllerDevice: {
    type: String,
    required: true
  }
}
```

**Keep learning instructions as-is (Broadlink-specific):**
```vue
<!-- KEEP AS-IS -->
<p><strong>Point your remote directly at the Broadlink device and press the button.</strong></p>
```

#### 6. `frontend/src/components/commands/CommandLearner.vue`

**Lines to change:**

```vue
<!-- BEFORE -->
<label for="broadlink-entity">Broadlink Device</label>

<!-- AFTER -->
<label for="broadlink-entity">Remote Device</label>
```

**But keep comments that reference Broadlink-specific functionality:**
```javascript
// KEEP AS-IS
// Pre-select broadlink device if set on device (this is Broadlink-specific learning)
```

### Medium Priority (Internal Variables)

#### Variable Naming Conventions

**SmartIR Context** (use `controller`):
```javascript
// BEFORE
broadlinkDevice: ''
broadlinkDevices: []

// AFTER
controllerDevice: ''
controllerDevices: []
```

**General Context** (use `remote`):
```javascript
// BEFORE
broadlinkDevice: ''
broadlinkDevices: []

// AFTER
remoteDevice: ''
remoteDevices: []
```

**Broadlink-Specific Context** (keep `broadlink`):
```javascript
// KEEP AS-IS
broadlink_entity: ''  // Refers to actual Broadlink integration
```

### Low Priority (Backend - Future)

Backend terminology is mostly correct already:
- `controller_device` ✅ (SmartIR field)
- `broadlink_entity` ✅ (Broadlink-specific field)

## Implementation Strategy

### Phase 1: User-Facing Labels (Quick Win)

Update all user-visible text in UI components:
- Form labels
- Dropdown placeholders
- Help text
- Filter labels

**Time**: 30 minutes
**Impact**: High - users immediately see generic terminology

### Phase 2: Variable Names (Refactor)

Rename JavaScript variables and props:
- `broadlinkDevice` → `controllerDevice`
- `broadlinkDevices` → `controllerDevices`

**Time**: 1-2 hours
**Impact**: Medium - cleaner code, easier to understand

### Phase 3: Comments and Documentation (Polish)

Update code comments and inline documentation:
- Clarify when something is Broadlink-specific
- Update variable descriptions

**Time**: 30 minutes
**Impact**: Low - but improves maintainability

## Testing Checklist

After changes, verify:

- [ ] SmartIR device creation shows "Controller Device"
- [ ] Broadlink device creation shows "Remote Device"
- [ ] Device type selection still shows "Broadlink Device (Learn IR Codes)"
- [ ] Filter dropdown shows "All Controller Devices"
- [ ] Learning instructions still reference "Broadlink device" (correct)
- [ ] No console errors from renamed props
- [ ] All dropdowns populate correctly
- [ ] Device creation/editing works

## Example: Before and After

### Before (Confusing)
```vue
<template>
  <div class="form-group">
    <label>Broadlink Device *</label>
    <select v-model="device.broadlinkDevice">
      <option value="">Select Broadlink device...</option>
    </select>
    <small>This device will be used to learn commands</small>
  </div>
</template>
```

**Problem**: User has Xiaomi remote, sees "Broadlink Device", thinks it won't work

### After (Clear)
```vue
<template>
  <div class="form-group">
    <label>Controller Device *</label>
    <select v-model="device.controllerDevice">
      <option value="">Select controller device...</option>
    </select>
    <small>This device will send IR/RF commands</small>
  </div>
</template>
```

**Better**: Generic terminology, works with any remote type

### Exception: Learning (Keep Broadlink-Specific)
```vue
<template>
  <div v-if="device.device_type === 'broadlink'">
    <h3>Learn Commands</h3>
    <p><strong>Point your IR remote at the Broadlink device</strong></p>
    <small>Learning requires a physical Broadlink RM device</small>
  </div>
</template>
```

**Correct**: Learning IS Broadlink-specific, so terminology is accurate

## Summary

### Change These:
- ❌ "Broadlink Device" (when selecting controller)
- ❌ "Select Broadlink Device" (dropdown placeholders)
- ❌ "All Broadlink Devices" (filters)
- ❌ `broadlinkDevice` variables (in SmartIR context)

### Keep These:
- ✅ "Broadlink Device (Learn IR Codes)" (device type)
- ✅ "Point remote at Broadlink device" (learning instructions)
- ✅ `broadlink_entity` (actual Broadlink integration field)
- ✅ `/api/broadlink/devices` (API endpoint)

### Result:
- Users understand any remote works
- Broadlink-specific features clearly labeled
- Code is clearer and more maintainable
