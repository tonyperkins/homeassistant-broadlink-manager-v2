# SmartIR Command Learning Issues - Bug Report

## Date: 2025-01-19
## Version: 0.3.0-alpha.1-dev.10

---

## Issues Identified

### 1. ✅ FIXED: Grid/List Toggle Doesn't Persist
**Status**: Fixed  
**Files**: 
- `frontend/src/components/smartir/SmartIRStatusCard.vue` (SmartIR profiles)
- `frontend/src/components/devices/DeviceList.vue` (Device list)

**Fix**: Added watcher to persist viewMode changes to localStorage in both components

```javascript
// Watch for viewMode changes and persist to localStorage
watch(viewMode, (newMode) => {
  localStorage.setItem('profile_view_mode', newMode)  // For SmartIR profiles
  // OR
  localStorage.setItem('device_view_mode', newMode)   // For device list
})
```

---

### 2. ❌ No Broadlink Devices in Dropdown (Image 1)
**Status**: Needs Investigation  
**File**: `frontend/src/components/smartir/CommandLearningWizard.vue`  
**Current Code**: Line 583
```javascript
const response = await fetch('/api/remote/devices')
```

**Backend Endpoint**: `app/api/config.py` - Line 43
```python
@api_bp.route("/remote/devices", methods=["GET"])
def get_all_remote_devices():
```

**Possible Causes**:
1. API endpoint not returning devices in add-on mode
2. Filtering logic too aggressive (skipping Broadlink devices)
3. Entity ID format different in add-on vs dev mode

**Investigation Needed**:
- Check if `/api/remote/devices` returns data in add-on mode
- Verify entity IDs match expected format
- Check if filtering logic is excluding Broadlink devices

---

### 3. ❌ Commands View Shows 404 Errors (Image 2)
**Status**: API Endpoint Missing  
**Error**: `GET http://192.168.50.84:8123/api/commands/all 404 (Not Found)`

**Issue**: The commands view is trying to fetch from `/api/commands/all` which doesn't exist

**Files to Check**:
- Where is this endpoint being called?
- Should it be `/api/commands` instead?
- Or does the endpoint need to be created?

---

### 4. ❌ IR/RF Selector Disappears When Clicking Command (Image 3)
**Status**: UI State Issue  
**File**: `frontend/src/components/smartir/CommandLearningWizard.vue`

**Current Behavior**:
- When learning a command, the IR/RF radio buttons disappear
- Only "Learning..." message shows

**Expected Behavior**:
- IR/RF selector should remain visible but disabled during learning
- Or should be shown above the learning message

**Fix Needed**:
- Update template to keep command type selector visible
- Add `:disabled="learningCommand !== null"` to radio buttons

---

### 5. ❌ Wrong Instructions for RF Learning (Image 3)
**Status**: Content Issue  
**File**: `frontend/src/components/smartir/CommandLearningWizard.vue`  
**Lines**: 58-64

**Current Instructions** (RF):
```
1. Click "Learn Command" for each combination
2. Step 1: Hold button on remote - Broadlink scans for RF frequency
3. Step 2: Watch for Home Assistant notification, then press and release button
4. Keep remote within 5cm of Broadlink (RF doesn't need line-of-sight)
5. Wait for confirmation (may take up to 30 seconds)
```

**Correct Instructions** (from profile card learn):
```
1. Click "Learn Command"
2. Point your remote at the Broadlink device and press the button
3. Wait for confirmation (up to 30 seconds)
```

**Note**: RF learning in SmartIR context is simpler - just press the button, no two-step process

---

### 6. ❌ Learned Command Not Showing in Tracked List (Image 4)
**Status**: Data Sync Issue  
**File**: `frontend/src/components/smartir/CommandLearningWizard.vue`

**Current Behavior**:
- Command learns successfully (backend confirms)
- Command doesn't appear in "Tracked Commands" list at bottom
- Command card doesn't update to show "Learned" state

**Possible Causes**:
1. `commands.value[cmd.key]` not being set correctly
2. Vue reactivity issue - need to use `Object.assign()` or spread operator
3. Command key mismatch between what's learned and what's displayed

**Investigation**:
- Check if `commands.value` is being updated
- Verify command key matches between learn and display
- Check if emit is working: `emit('update:modelValue', commands.value)`

---

### 7. ❌ Shows "IR" Instead of "RF" (Image 4)
**Status**: Display Bug  
**File**: `frontend/src/components/smartir/CommandLearningWizard.vue`  
**Line**: 134-136

**Current Code**:
```vue
<span class="command-type-badge" :class="localCommandType">
  {{ localCommandType.toUpperCase() }}
</span>
```

**Issue**: 
- Badge shows command type from `localCommandType`
- But the actual learned command might be different type
- Need to store command type with each learned command

**Fix Needed**:
- Store command type in commands object: `commands.value[cmd.key] = { code: result.code, type: localCommandType.value }`
- Display the stored type, not the current selection

---

### 8. ❌ Test Button Doesn't Work (Image 4)
**Status**: API Error  
**File**: `frontend/src/components/smartir/CommandLearningWizard.vue`  
**Lines**: 460-502

**Current Code**:
```javascript
const response = await fetch('/api/commands/send-raw', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    entity_id: localBroadlinkDevice.value,
    command: rawCode,  // Send the base64 IR/RF code directly
    command_type: localCommandType.value  // 'ir' or 'rf'
  })
})
```

**Error**: 400 (BAD REQUEST) - "Missing required fields: command"

**Possible Causes**:
1. API expects different field name (maybe `code` instead of `command`)
2. Command value is "pending" instead of actual code
3. API endpoint signature mismatch

**Backend Endpoint to Check**: `app/api/commands.py` - `/commands/send-raw`

---

## Priority Fixes

### P0 (Critical - Blocks Usage)
1. ✅ Grid/List toggle persistence - **FIXED**
2. ❌ No Broadlink devices in dropdown - **BLOCKS LEARNING**
3. ❌ Test button doesn't work - **CAN'T VERIFY COMMANDS**

### P1 (High - Poor UX)
4. ❌ Learned command not showing in list - **CONFUSING**
5. ❌ Shows wrong command type (IR vs RF) - **MISLEADING**
6. ❌ Commands view 404 errors - **BROKEN FEATURE**

### P2 (Medium - Polish)
7. ❌ IR/RF selector disappears - **MINOR ANNOYANCE**
8. ❌ Wrong RF instructions - **DOCUMENTATION**

---

## Next Steps

1. **Investigate `/api/remote/devices` in add-on mode**
   - Add logging to see what's returned
   - Check entity ID format
   - Verify filtering logic

2. **Fix command storage structure**
   - Store command type with each command
   - Ensure proper Vue reactivity
   - Fix display to show correct type

3. **Fix test command API call**
   - Check backend endpoint signature
   - Verify field names match
   - Handle "pending" codes properly

4. **Update RF learning instructions**
   - Simplify to match actual behavior
   - Remove confusing two-step process

5. **Fix commands view 404**
   - Find where `/api/commands/all` is called
   - Create endpoint or fix the call

---

## Testing Checklist

After fixes:
- [ ] Broadlink devices appear in dropdown (add-on mode)
- [ ] Can learn IR command
- [ ] Can learn RF command  
- [ ] Learned command shows in tracked list
- [ ] Command type badge shows correct type (IR/RF)
- [ ] Test button works for IR commands
- [ ] Test button works for RF commands
- [ ] IR/RF selector visible during learning (disabled)
- [ ] RF instructions are correct
- [ ] Grid/List toggle persists across reloads
- [ ] Commands view doesn't show 404 errors

---

**Status**: Document created, fixes in progress  
**Next**: Implement P0 fixes first
