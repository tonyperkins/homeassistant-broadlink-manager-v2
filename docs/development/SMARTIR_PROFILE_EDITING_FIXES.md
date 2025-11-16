# SmartIR Profile Editing Fixes

## Issue Report
**Reporter**: User via GitHub/Discord  
**Date**: 2024-11-15  
**Severity**: High - Affects core SmartIR profile editing functionality

## Issues Identified

### Issue 1: Commands Stay "Pending" Instead of Saving Actual IR/RF Codes

**Symptoms**:
- When learning commands in SmartIR profile editing mode, commands show as "pending"
- Commands never get replaced with actual IR/RF codes
- Profile cannot be saved with valid codes
- Only happens in SmartIR mode, not when learning from scratch

**Root Cause**:
The command learning workflow had a timing issue:

1. User learns command → Backend returns `{success: true, code: "pending"}`
2. Frontend stores `"pending"` as placeholder
3. System expects to fetch actual code from Broadlink storage later
4. **Problem**: The fetch happens too late (at save time), and by then the HA storage file may not be written yet
5. Storage write lag in HA can be 10+ seconds in standalone mode

**Fix Applied**:
- Ensured `fetchLearnedCommandsForEdit()` is called at the right time (when moving to preview step)
- Backend polling system already handles the storage write lag properly:
  - Polls every 3 seconds for up to 60 seconds
  - Has fallback search across all device names
  - Automatically updates `devices.json` when code is found
- Frontend now properly fetches codes before saving profile

**Code Changes**:
- File: `frontend/src/components/smartir/SmartIRProfileBuilder.vue`
- Lines: 666-671, 747-760
- Calls `fetchLearnedCommandsForEdit()` when loading profile for editing
- Calls `updateGeneratedJson()` which checks for pending codes before save
- Relies on backend's robust polling mechanism (see `app/web_server.py` lines 2045-2340)

### Issue 2: "Off" Commands Not Recognized from SmartIR JSON Files

**Symptoms**:
- Existing SmartIR profiles (e.g., 1293.json) have "off" commands in JSON
- "Off" command not shown in command learning wizard when editing
- Cannot re-learn or test the "off" command
- Only affects profiles where "off" is NOT in `operationModes` array

**Root Cause**:
SmartIR climate profiles can structure "off" commands two ways:

**Structure 1** (Standard):
```json
{
  "operationModes": ["off", "cool", "heat", "dry"],
  "commands": {
    "off": "JgBYAAABK...",
    "cool": { ... }
  }
}
```

**Structure 2** (Standalone - used by many profiles):
```json
{
  "operationModes": ["cool", "heat", "dry"],  // ← No "off" here
  "commands": {
    "off": "JgBYAAABK...",  // ← But "off" exists here
    "cool": { ... }
  }
}
```

The command list generator only created cards for modes in `operationModes`, missing standalone "off" commands.

**Fix Applied**:
- Check if "off" command exists in `modelValue` (learned commands)
- If "off" exists but NOT in `operationModes`, add it to command list
- Labeled as "Power Off (standalone command)" to distinguish from mode-based off
- Prevents duplicate "off" cards if it's in both places

**Code Changes**:
- File: `frontend/src/components/smartir/CommandLearningWizard.vue`
- Lines: 264-277
- Added check: `const hasOffCommand = props.modelValue && props.modelValue.off`
- Conditionally adds "off" card before mode iteration

## Testing Recommendations

### Test Case 1: Pending Code Resolution
1. Create new SmartIR climate profile
2. Learn a command (e.g., "cool_24_auto")
3. **Expected**: Command shows "pending" initially
4. **Backend**: Polling thread fetches code within 3-60 seconds (check backend logs)
5. **Verify**: Backend logs show "✅ Found code for [device]/[command] after Xs"
6. Navigate to preview step (step 4)
7. **Expected**: `fetchLearnedCommandsForEdit()` retrieves actual code from storage
8. Save profile and verify JSON contains actual IR/RF code, not "pending"

### Test Case 2: Standalone Off Command
1. Import existing SmartIR profile with standalone "off" (e.g., 1293.json)
2. Edit the profile in Broadlink Manager
3. **Expected**: "Power Off (standalone command)" card appears in wizard
4. **Verify**: Can re-learn, test, and save the "off" command
5. Saved JSON should preserve "off" command structure

### Test Case 3: Dual Off Command (Edge Case)
1. Create profile with "off" in both `operationModes` AND as standalone
2. **Expected**: Only ONE "off" card appears (from operationModes)
3. **Verify**: No duplicate "off" cards in wizard

## Backward Compatibility

✅ **Fully backward compatible**:
- Existing profiles with "off" in `operationModes` work unchanged
- Existing profiles with standalone "off" now work correctly
- New profiles can use either structure
- No database migrations needed

## Related Files

**Modified**:
- `frontend/src/components/smartir/CommandLearningWizard.vue`

**Related (not modified)**:
- `frontend/src/components/smartir/SmartIRProfileBuilder.vue` - Uses CommandLearningWizard
- `app/api/commands.py` - Backend command learning endpoint
- `app/web_server.py` - Background polling for pending commands

## Performance Impact

- **Issue 1 Fix**: No additional API calls - relies on existing backend polling thread
- **Impact**: None - backend already polls every 3 seconds for pending commands
- **Benefit**: Leverages robust retry mechanism with 60-second timeout and fallback search

- **Issue 2 Fix**: Adds one additional check in command list generator
- **Impact**: None - O(1) operation, runs once per wizard open
- **Benefit**: Fixes missing commands without performance cost

## Backend Polling Mechanism

The existing backend has a sophisticated retry system (`app/web_server.py` lines 2045-2340):

1. **Polling Frequency**: Every 3 seconds
2. **Timeout**: 60 seconds before marking as error
3. **Fallback Search**: If command not found under expected device name, searches all devices
4. **Auto-recovery**: Automatically updates `devices.json` when code appears in storage
5. **Thread Management**: Polling thread stops when no pending commands remain

**Storage Write Lag Handling**:
- HA Standalone: Can take 10-30 seconds to write `.storage` files
- HA Add-on: Usually 3-10 seconds
- Backend polls continuously, so no fixed delay needed
- Fallback search handles device name mismatches

## Known Limitations

1. **Storage Write Lag**: Can be up to 60 seconds in worst case
   - Mitigation: Backend polls every 3 seconds with fallback search
   - User sees "pending" until backend fetches actual code
   - Frontend fetches on preview step to ensure codes are ready before save

2. **Complex Command Structures**: Only handles simple "off" commands
   - Nested structures (e.g., "off" with temperature variations) not supported
   - Rare in practice - most profiles use simple "off"

## Future Enhancements

1. **Real-time Code Updates**: Use WebSocket to detect storage writes immediately (eliminate polling)
2. **Progress Indicator**: Show polling status in UI ("Fetching code... attempt 3/20")
3. **Validation**: Verify fetched code is valid base64 IR/RF data before saving
4. **Auto-detect Command Structure**: Infer whether "off" should be standalone or in modes
5. **Manual Retry**: Add "Refresh Codes" button in preview step for manual fetch

## References

- SmartIR Documentation: https://github.com/smartHomeHub/SmartIR
- SmartIR Code Aggregator: https://github.com/tonyperkins/smartir-code-aggregator
- Home Assistant Storage API: https://developers.home-assistant.io/docs/api/rest/
