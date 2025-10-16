# Quick Reference: Testing Non-Broadlink Devices

## TL;DR - Test the UI Right Now

### Option 1: Browser DevTools (Fastest - 2 minutes)

1. Open Broadlink Manager UI
2. Press F12 (DevTools)
3. Paste this in Console:

```javascript
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const url = args[0];
  if (url.includes('/api/broadlink/devices')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        devices: [
          {
            entity_id: "remote.broadlink_rm4_pro",
            name: "Broadlink RM4 Pro",
            host: "192.168.1.100",
            type: "RM4 Pro"
          },
          {
            entity_id: "remote.xiaomi_ir_remote",
            name: "Xiaomi IR Remote (Test)",
            host: "192.168.1.101",
            type: "Xiaomi"
          },
          {
            entity_id: "remote.harmony_hub",
            name: "Harmony Hub (Test)",
            host: "192.168.1.102",
            type: "Harmony"
          }
        ]
      })
    });
  }
  return originalFetch.apply(this, args);
};
console.log('✅ Mock remotes injected! Refresh page.');
```

4. Refresh the page
5. Create a SmartIR device and select `remote.xiaomi_ir_remote` as controller
6. Generate entities and verify YAML has entity ID (not IP)

---

## Device Type Detection - Current State

### What We Track ✅

**Device Type** (`device_type` field):
- `"broadlink"` - Native Broadlink devices (learn/send commands)
- `"smartir"` - SmartIR devices (use pre-configured profiles)

**Where it's stored**: `devices.json` or entity metadata

**How it's used**:
```python
# Separate for entity generation
if device.get('device_type') == 'smartir':
    # Generate SmartIR YAML
else:
    # Generate Broadlink template entities
```

### What We DON'T Track ❌

**Controller Type** (Broadlink vs. Xiaomi vs. Harmony Hub):
- ❌ Not detected automatically
- ❌ No capability detection (supports learning?)
- ❌ No UI indicators

**Impact**:
- Learn/Delete buttons show for all devices (even non-Broadlink)
- No visual indication of controller type
- Users need to know their controller's capabilities

---

## Quick Answers

### Q: How do I test with a non-Broadlink remote?

**A**: Use the browser DevTools method above (2 minutes)

### Q: How does the system know if a device is Broadlink or SmartIR?

**A**: The `device_type` field in device metadata:
- Set when creating device (from frontend)
- Defaults to `"broadlink"` if not specified
- Used to generate different YAML formats

### Q: How does it know if a controller supports learning?

**A**: It doesn't! This is missing and needs to be added in Phase 2/3.

**Current workaround**: Assume SmartIR devices might use non-Broadlink controllers

### Q: Can I use a Xiaomi remote right now?

**A**: ✅ Yes! Phase 1 is complete:
- Backend works with any remote entity
- YAML generation uses entity IDs
- Commands send correctly

**But**: UI still shows learn/delete buttons (will fix in Phase 3)

### Q: Where is controller type stored?

**A**: It's not! We only store:
- `device_type`: "broadlink" or "smartir"
- `controller_device`: Entity ID (e.g., "remote.xiaomi_ir_remote")

We need to **detect** controller type from the entity ID or HA API.

---

## What Needs to Be Built (Phase 2/3)

### Phase 2: Controller Type Detection

**Add**:
1. `app/controller_detector.py` - Detect controller type from entity ID
2. API endpoint: `/api/devices/controller-info/<entity_id>`
3. Frontend: Fetch all remote entities (not just Broadlink)
4. UI: Show controller type badge

**Result**: Know what type of controller is being used

### Phase 3: Graceful Degradation

**Add**:
1. Hide learn button if controller doesn't support learning
2. Hide delete button if controller doesn't support deletion
3. Show help text: "This controller uses pre-programmed codes"

**Result**: UI adapts to controller capabilities

---

## File References

### Testing Documentation
- **`docs/development/TESTING_NON_BROADLINK_UI.md`** - Complete testing guide
- **`docs/development/DEVICE_TYPE_DETECTION.md`** - How detection works

### Phase 1 Documentation
- **`PHASE1_COMPLETE.md`** - Phase 1 summary
- **`docs/NON_BROADLINK_REMOTES.md`** - User guide
- **`docs/development/PHASE1_NON_BROADLINK_SUPPORT.md`** - Technical details

### Test Files
- **`test_phase1.py`** - Quick backend verification
- **`tests/unit/test_smartir_yaml_generator.py`** - 9 unit tests
- **`tests/integration/test_smartir_non_broadlink.py`** - 5 integration tests

---

## Quick Verification Commands

```bash
# Verify backend works
python test_phase1.py

# Run all tests
python -m pytest tests/ -v

# Check generated YAML
cat /config/smartir/climate.yaml
# Should see: controller_data: remote.xiaomi_ir_remote (entity ID, not IP)
```

---

## Summary

### ✅ What Works Now (Phase 1)
- SmartIR with any HA remote entity
- YAML generation uses entity IDs
- Commands send correctly
- Comprehensive tests

### ❌ What's Missing (Phase 2/3)
- Controller type detection
- Capability detection
- UI shows all remotes (not just Broadlink)
- Hide learn/delete for non-Broadlink

### 🧪 How to Test Now
- Use browser DevTools to inject mock remotes
- Create SmartIR device with non-Broadlink controller
- Verify YAML has entity ID (not IP)
- Test command sending

---

**For full details, see:**
- Testing: `docs/development/TESTING_NON_BROADLINK_UI.md`
- Detection: `docs/development/DEVICE_TYPE_DETECTION.md`
