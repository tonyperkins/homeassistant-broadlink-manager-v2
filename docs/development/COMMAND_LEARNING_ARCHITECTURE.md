# Command Learning Architecture

## Overview

This document explains how command learning works in Broadlink Manager v2, including the API flow, storage file polling, and the differences between Broadlink native and SmartIR device handling.

## The Challenge

Home Assistant's `remote.learn_command` service **does not return the learned IR/RF code**. It only returns `[]` (empty array) on success. The actual code must be read from `.storage` files, which are written **asynchronously** with unpredictable lag (3-60 seconds).

## Architecture Components

### 1. Learning API Call (`app/api/commands.py`)

**Endpoint:** `POST /api/commands/learn`

**Flow:**
```
Frontend → Backend API → Home Assistant remote.learn_command → Storage Files
```

**What Happens:**
1. User clicks "Learn Command" in UI
2. Frontend calls `/api/commands/learn` with:
   - `entity_id`: Broadlink remote entity (e.g., `remote.bedroom_rm4`)
   - `device`: Device name for storage lookup
   - `command`: Command name (e.g., "power", "off")
   - `command_type`: "ir" or "rf"
   - `device_id`: Optional device ID in devices.json
   - `save_destination`: "manager_only", "integration_only", or "both"

3. Backend calls HA's `remote.learn_command` service
4. HA returns `[]` (success) or error
5. Backend saves command as "pending" in devices.json
6. Backend schedules background polling for the actual code

**Key Code:**
```python
# Call HA to learn command
result = self._learn_command(entity_id, device, command, command_type)

# Save as pending
learned_code = "pending"

# Schedule background polling
web_server.schedule_command_poll(
    device_id,
    device,
    command,
    entity_id if save_destination == "manager_only" else None,
    smartir_metadata  # For SmartIR devices
)
```

### 2. Background Polling Thread (`app/web_server.py`)

**Purpose:** Poll `.storage` files until the learned code appears, then update the appropriate destination.

**Polling Mechanism:**
- Runs in background thread (`_poll_pending_commands`)
- Polls every 3 seconds
- 60-second timeout before marking as error
- Automatic fallback search if code not found under expected device name

**Storage File Location:**
```
/config/.storage/broadlink_remote_<MAC>_codes
```

**Polling Flow:**
```
1. Check pending_command_polls list
2. For each pending command:
   - Read all .storage files
   - Look for device_name/command_name
   - If found:
     - Update destination (devices.json or SmartIR profile)
     - Delete from integration storage (if manager_only)
     - Remove from poll list
   - If timeout (60s):
     - Try fallback search across all device names
     - Mark as error if still not found
3. Sleep 3 seconds
4. Repeat until no pending commands
```

**Key Code:**
```python
def _poll_pending_commands(self):
    while True:
        time.sleep(3)
        
        for poll_item in self.pending_command_polls:
            # Unpack tuple (handles both 5 and 6 element formats)
            if len(poll_item) == 6:
                device_id, device_name, command_name, start_time, entity_id_for_deletion, metadata = poll_item
            else:
                device_id, device_name, command_name, start_time, entity_id_for_deletion = poll_item
                metadata = None
            
            # Try to fetch code from storage
            all_commands = await self._get_all_broadlink_commands()
            learned_code = all_commands.get(device_name, {}).get(command_name)
            
            if learned_code:
                # Update destination based on metadata
                if metadata and "smartir_profile" in metadata:
                    # Update SmartIR profile JSON
                    self._update_smartir_profile(metadata, command_name, learned_code)
                else:
                    # Update devices.json
                    self._update_devices_json(device_id, command_name, learned_code)
```

### 3. SmartIR Detection (`app/api/commands.py`)

**Challenge:** SmartIR devices created via UI don't exist in `devices.json`, so we need to detect them by scanning profile files.

**Detection Strategy:**
1. **First:** Check if device_id exists in devices.json with `device_type: "smartir"`
2. **Fallback:** Scan SmartIR profile files and match device name against manufacturer/model

**Profile Scanning:**
```python
# Scan custom_codes directories
smartir_path = Path(config_path) / "custom_components" / "smartir"
custom_codes_path = smartir_path / "custom_codes"

for platform_dir in custom_codes_path.iterdir():  # climate, fan, etc.
    for profile_file in platform_dir.glob("*.json"):
        profile_data = json.load(profile_file)
        
        # Generate device name from profile
        manufacturer = profile_data.get("manufacturer", "")
        model = profile_data.get("supportedModels", [""])[0]
        profile_device_name = f"{manufacturer.lower()}_{model.lower()}"
        profile_device_name = re.sub(r"[^a-z0-9]+", "_", profile_device_name)
        
        # Match against learning device name
        if profile_device_name == device.lower():
            # Found matching profile - add metadata
            smartir_metadata = {
                "smartir_profile": str(profile_file),
                "device_code": profile_file.stem,
                "platform": platform_dir.name
            }
```

### 4. Update Destinations

#### Broadlink Native Devices (devices.json)

**File:** `test-config/devices.json` or `h:/broadlink_manager/devices.json`

**Structure:**
```json
{
  "device_id": {
    "name": "Living Room TV",
    "entity_type": "media_player",
    "device_type": "broadlink",
    "commands": {
      "power": {
        "data": "JgBYAAABH5ASEhI2EhESEhE3ERISNhI2ERISExA4ETYRExE2EjYSEhI1EjYRExI1EhISEhI1EjcQExISEjYRExE2ETcREhISEgAFAgABH0kSAAwAAAEfSREADQU=",
        "type": "ir",
        "name": "power"
      }
    }
  }
}
```

**Update Process:**
1. Read device from devices.json
2. Update command data from "pending" to actual code
3. Write back to devices.json

#### SmartIR Profiles (custom_codes/*.json)

**File:** `h:/custom_components/smartir/custom_codes/climate/10000.json`

**Structure:**
```json
{
  "manufacturer": "FooBar",
  "supportedModels": ["Dog1"],
  "supportedController": "Broadlink",
  "commandsEncoding": "Base64",
  "commandType": "ir",
  "commands": {
    "off": "JgBYAAABH5ASEhI2EhESEhE3ERISNhI2ERISExA4ETYRExE2EjYSEhI1EjYRExI1EhISEhI1EjcQExISEjYRExE2ETcREhISEgAFAgABH0kSAAwAAAEfSREADQU="
  }
}
```

**Update Process:**
1. Read profile JSON file
2. Update command from "pending" to actual code
3. Write back to profile JSON file
4. SmartIR integration reads updated profile

### 5. Storage File Cleanup

**For manager_only commands:**
- After fetching code, delete from integration storage
- Prevents duplicate entries in HA's Broadlink integration
- Uses `remote.delete_command` service

**Code:**
```python
if entity_id_for_deletion:
    # Delete from integration storage
    await self._delete_command_from_storage(
        entity_id_for_deletion,
        device_name,
        command_name
    )
```

## Device Type Handling

### Broadlink Native Devices

**Characteristics:**
- Created via "Broadlink Device (Learn IR Codes)" option
- Stored in `devices.json`
- Commands stored in `devices.json`
- Entities generated by Broadlink Manager

**Learning Flow:**
```
Learn → Poll Storage → Update devices.json → Done
```

### SmartIR Devices

**Characteristics:**
- Created via "SmartIR Profile" option
- Profile stored in `custom_codes/*.json`
- Commands stored in profile JSON
- Entities managed by SmartIR integration

**Learning Flow:**
```
Learn → Detect SmartIR → Poll Storage → Update Profile JSON → Done
```

**Key Difference:** SmartIR devices may not be in `devices.json`, so detection happens via profile scanning.

## Storage File Format

**Location:** `/config/.storage/broadlink_remote_<MAC>_codes`

**Structure:**
```json
{
  "version": 1,
  "minor_version": 1,
  "key": "broadlink_remote_e870723f13a5_codes",
  "data": {
    "device_name": {
      "command_name": "JgBYAAABH5ASEhI2EhESEhE3ERISNhI2ERISExA4ETYRExE2EjYSEhI1EjYRExI1EhISEhI1EjcQExISEjYRExE2ETcREhISEgAFAgABH0kSAAwAAAEfSREADQU="
    }
  }
}
```

**Device Name Matching:**
- Device name is derived from manufacturer/model for SmartIR
- Must match exactly (case-insensitive)
- Fallback search tries all device names if not found

## Timing Considerations

### Storage Write Lag

**Typical Delays:**
- Add-on mode: 3-10 seconds
- Standalone mode: 10-30 seconds
- Worst case: Up to 60 seconds

**Why Polling is Necessary:**
- HA writes storage files asynchronously
- No event notification when file is written
- No way to know when code is available
- Must poll until found or timeout

### Timeout Handling

**60-Second Timeout:**
1. Poll every 3 seconds for 60 seconds
2. If not found, try fallback search across all device names
3. If still not found, mark as error
4. User can retry learning

## Error Scenarios

### 1. Code Never Appears
**Cause:** HA didn't save the code (learning failed)
**Solution:** User retries learning

### 2. Wrong Device Name
**Cause:** Device name mismatch between manager and storage
**Solution:** Fallback search tries all device names

### 3. Timeout
**Cause:** Storage write lag exceeded 60 seconds
**Solution:** User retries, code may appear on next attempt

### 4. SmartIR Profile Not Found
**Cause:** Profile file doesn't exist or name mismatch
**Solution:** Check profile exists and device name matches manufacturer/model

## Debugging

### Backend Logs

**Successful Learning:**
```
📋 SmartIR device detected by profile scan - will update profile 10000.json
📋 Scheduled poll for foobar_dog1/off
🔍 Looking for foobar_dog1/off in storage
✅ Found code for foobar_dog1/off after 5.2s (length: 348 chars)
✅ Updated SmartIR profile 10000.json with code for off
🗑️ Deleted foobar_dog1/off from integration storage
```

**Timeout:**
```
📋 Scheduled poll for foobar_dog1/off
🔍 Looking for foobar_dog1/off in storage
⚠️ Timeout approaching for foobar_dog1/off, trying fallback search...
❌ Timeout polling for foobar_dog1/off after 61.0s - marking as error
```

### Frontend Indicators

**During Learning:**
- Command shows as "pending" in UI
- Spinner/loading indicator
- "Learning in progress..." message

**After Success:**
- Command shows actual code (truncated)
- "Test" button becomes available
- Success toast notification

**After Timeout:**
- Command remains "pending"
- Error toast notification
- User can retry learning

## Best Practices

### For Users

1. **Wait for confirmation** - Don't retry immediately if learning seems slow
2. **Check HA notifications** - HA shows learning progress
3. **Ensure line of sight** - Remote must point at Broadlink device
4. **One command at a time** - Don't learn multiple commands simultaneously

### For Developers

1. **Never wait synchronously** - Always use background polling
2. **Handle both tuple formats** - Support 5 and 6 element tuples
3. **Provide clear feedback** - Show pending status and progress
4. **Log everything** - Debugging requires detailed logs
5. **Test timeout scenarios** - Ensure graceful failure

## Future Improvements

### Potential Enhancements

1. **WebSocket Monitoring** - Listen for storage file changes (if possible)
2. **Faster Polling** - Reduce 3-second interval to 1 second
3. **Better Timeout Handling** - Exponential backoff instead of fixed timeout
4. **Retry Queue** - Automatically retry failed commands
5. **Progress Indicators** - Show polling progress in UI

### Known Limitations

1. **No Real-Time Feedback** - Must poll, can't get instant notification
2. **Storage Lag Unpredictable** - Can't guarantee timing
3. **Device Name Matching** - Fragile, depends on exact name match
4. **No Parallel Learning** - One command at a time per device

## Summary

**Command learning is a multi-step asynchronous process:**

1. **API Call** - Frontend → Backend → Home Assistant
2. **Pending State** - Command marked as "pending" in destination
3. **Background Polling** - Thread polls storage files every 3 seconds
4. **Code Detection** - Found in `.storage` files after 3-60 seconds
5. **Update Destination** - devices.json or SmartIR profile updated
6. **Cleanup** - Optional deletion from integration storage
7. **Complete** - Command available for testing

**Key Insight:** The polling mechanism bridges the gap between HA's synchronous API (which doesn't return codes) and the asynchronous storage file writes (which contain the actual codes).
