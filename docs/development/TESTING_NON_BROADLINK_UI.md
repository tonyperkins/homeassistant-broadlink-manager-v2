# Testing Non-Broadlink Devices in the UI

## Quick Test Setup

### Option 1: Mock Remote Entities (Recommended for Testing)

Create a mock remote entity in Home Assistant to test the UI without needing actual hardware.

#### Step 1: Add Mock Remote to Home Assistant

Add this to your `configuration.yaml`:

```yaml
# Mock remote entities for testing
remote:
  - platform: template
    remotes:
      xiaomi_ir_remote:
        friendly_name: "Xiaomi IR Remote (Test)"
        turn_on:
          service: script.mock_remote_on
        turn_off:
          service: script.mock_remote_off
        send_command:
          service: script.mock_send_command
          data:
            command: "{{ command }}"
      
      harmony_hub:
        friendly_name: "Harmony Hub (Test)"
        turn_on:
          service: script.mock_remote_on
        turn_off:
          service: script.mock_remote_off
        send_command:
          service: script.mock_send_command
          data:
            command: "{{ command }}"

# Mock scripts (just log the commands)
script:
  mock_remote_on:
    sequence:
      - service: system_log.write
        data:
          message: "Mock remote turned on"
          level: info
  
  mock_remote_off:
    sequence:
      - service: system_log.write
        data:
          message: "Mock remote turned off"
          level: info
  
  mock_send_command:
    sequence:
      - service: system_log.write
        data:
          message: "Mock remote sent command: {{ command }}"
          level: info
```

#### Step 2: Restart Home Assistant

```bash
# Restart HA to load the mock remotes
ha core restart
```

#### Step 3: Verify Mock Remotes Exist

Check Developer Tools → States:
- `remote.xiaomi_ir_remote`
- `remote.harmony_hub`

#### Step 4: Create SmartIR Device in Broadlink Manager

1. Open Broadlink Manager UI
2. Click "Add Device"
3. Select **Device Type**: SmartIR
4. **Entity Type**: Climate
5. **Name**: "Test AC with Xiaomi"
6. **Controller Device**: Select `remote.xiaomi_ir_remote` from dropdown
7. **Device Code**: 1000 (any valid SmartIR code)
8. **Temperature Sensor**: (optional) Select any sensor
9. Click "Save"

#### Step 5: Test Commands

1. Click "Test" on any command
2. Check HA logs - you should see: "Mock remote sent command: ..."
3. Generate entities
4. Verify YAML has `controller_data: remote.xiaomi_ir_remote`

---

### Option 2: Use Existing Non-Broadlink Remote

If you have an actual Xiaomi, Harmony Hub, or ESPHome remote:

1. Ensure it's configured in Home Assistant
2. Verify it appears in Developer Tools → States
3. Use it directly in Broadlink Manager

---

### Option 3: Browser DevTools Override (Quick & Dirty)

For UI testing only, you can inject mock data via browser console:

#### Step 1: Open Broadlink Manager UI

#### Step 2: Open Browser DevTools (F12)

#### Step 3: Inject Mock Remote Data

```javascript
// Override the Broadlink devices API to include mock remotes
const originalFetch = window.fetch;
window.fetch = function(...args) {
  const url = args[0];
  
  // Intercept Broadlink devices API call
  if (url.includes('/api/broadlink/devices')) {
    return Promise.resolve({
      ok: true,
      json: () => Promise.resolve({
        devices: [
          // Real Broadlink device (if any)
          {
            entity_id: "remote.broadlink_rm4_pro",
            name: "Broadlink RM4 Pro",
            host: "192.168.1.100",
            type: "RM4 Pro"
          },
          // Mock Xiaomi remote
          {
            entity_id: "remote.xiaomi_ir_remote",
            name: "Xiaomi IR Remote (Mock)",
            host: "192.168.1.101",
            type: "Xiaomi"
          },
          // Mock Harmony Hub
          {
            entity_id: "remote.harmony_hub",
            name: "Harmony Hub (Mock)",
            host: "192.168.1.102",
            type: "Harmony"
          }
        ]
      })
    });
  }
  
  // Pass through all other requests
  return originalFetch.apply(this, args);
};

console.log('✅ Mock remotes injected! Refresh the page to see them in dropdowns.');
```

#### Step 4: Refresh Page

The mock remotes will now appear in the controller device dropdown.

---

## Testing Scenarios

### Scenario 1: Create SmartIR Device with Xiaomi Remote

**Expected Behavior:**
- ✅ Xiaomi remote appears in controller dropdown
- ✅ Can select it as controller
- ✅ Can save device successfully
- ✅ Generated YAML uses `controller_data: remote.xiaomi_ir_remote`
- ✅ Test command works (sends to Xiaomi remote)
- ❌ Learn command button should be hidden/disabled (Phase 3)

### Scenario 2: Create SmartIR Device with Harmony Hub

**Expected Behavior:**
- ✅ Harmony Hub appears in controller dropdown
- ✅ Can select it as controller
- ✅ Can save device successfully
- ✅ Generated YAML uses `controller_data: remote.harmony_hub`
- ✅ Test command works (sends to Harmony Hub)

### Scenario 3: Mixed Controllers

**Expected Behavior:**
- ✅ Can have Device 1 with Broadlink controller
- ✅ Can have Device 2 with Xiaomi controller
- ✅ Can have Device 3 with Harmony Hub controller
- ✅ All work independently
- ✅ Entity generation creates correct YAML for each

---

## What to Verify in UI

### ✅ Device Creation Form
- [ ] Controller dropdown shows all remote entities
- [ ] Can select non-Broadlink remotes
- [ ] Form saves successfully
- [ ] No errors in console

### ✅ Device List
- [ ] Devices with non-Broadlink controllers display correctly
- [ ] Controller entity shown in device card
- [ ] Can edit device and change controller

### ✅ Command Testing
- [ ] Test button works with non-Broadlink controllers
- [ ] Commands sent to correct remote entity
- [ ] Success/error messages display correctly

### ✅ Entity Generation
- [ ] Generate Entities button works
- [ ] YAML files created correctly
- [ ] `controller_data` uses entity ID (not IP)
- [ ] Can verify in `/config/smartir/` directory

### ❌ Known Limitations (Phase 1)
- [ ] Learn command button still shows (should hide in Phase 3)
- [ ] Delete command still shows (should hide in Phase 3)
- [ ] No visual indicator of remote type (add in Phase 2)

---

## Troubleshooting

### Mock Remotes Don't Appear in Dropdown

**Check:**
1. Are they in HA? Developer Tools → States
2. Does the API return them? Check Network tab for `/api/broadlink/devices`
3. Is the frontend filtering them out? Check console for errors

**Current Issue:** The frontend likely only fetches Broadlink devices. This needs fixing in Phase 2.

**Workaround:** Use browser DevTools override (Option 3 above)

### Commands Don't Send

**Check:**
1. Is the remote entity valid in HA?
2. Check HA logs for errors
3. Verify `remote.send_command` service works manually in Developer Tools

### Generated YAML Still Has IP Address

**This means the fix didn't work!** Check:
1. Is the code change in `app/smartir_yaml_generator.py` applied?
2. Restart the Broadlink Manager service
3. Check logs for errors

---

## Quick Verification Script

Run this to verify the backend works:

```bash
# Test the YAML generator directly
python test_phase1.py

# Expected output:
# ✅ SUCCESS - controller_data: remote.xiaomi_ir_remote
# ✅ SUCCESS - controller_data: remote.harmony_hub
```

---

## Current Limitations (To Fix in Phase 2)

### Frontend Needs Updates

The frontend currently only fetches Broadlink devices:

**File:** `frontend/src/services/api.js` or similar

**Current (likely):**
```javascript
async getBroadlinkDevices() {
  const response = await fetch('/api/broadlink/devices');
  return response.json();
}
```

**Needed:**
```javascript
async getAllRemoteDevices() {
  // Should fetch ALL remote entities from HA, not just Broadlink
  const response = await fetch('/api/homeassistant/remotes');
  return response.json();
}
```

**This is Phase 2 work** - for now, use the browser DevTools override.

---

## Summary

### For Quick UI Testing (Right Now):

1. **Use Browser DevTools Override** (Option 3)
   - Paste the JavaScript in console
   - Refresh page
   - Mock remotes appear in dropdowns
   - Test the full workflow

2. **Verify Backend Works**
   - Run `python test_phase1.py`
   - Confirms YAML generation is correct

3. **Check Generated YAML**
   - After creating device, check `/config/smartir/climate.yaml`
   - Verify `controller_data` is entity ID, not IP

### For Proper Testing (Recommended):

1. **Add Mock Remotes to HA** (Option 1)
   - More realistic
   - Tests actual HA integration
   - Can test command sending

2. **Update Frontend** (Phase 2)
   - Fetch all remote entities, not just Broadlink
   - Add remote type indicators
   - Hide learn/delete for non-Broadlink (Phase 3)
