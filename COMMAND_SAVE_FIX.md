# Command Save Fix

## Problem

When learning a new command through the UI, the command was successfully learned and stored in Broadlink storage (`.storage/broadlink_remote_*_codes`), but it was **not saved to `devices.json`**. This caused:

1. ✅ Command learned successfully in Broadlink storage
2. ✅ No errors reported in the UI
3. ❌ Command not visible in the device card
4. ❌ Command not tracked in device manager
5. ⚠️ Command would appear as "untracked" if you clicked the "Sync Commands" button

## Root Cause

In `app/api/commands.py`, the `/api/commands/learn` endpoint:

1. Called Home Assistant's `learn_command` service ✅
2. Fetched the learned code from Broadlink storage ✅
3. Returned success to the frontend ✅
4. **Never saved the command to `devices.json`** ❌

The command existed in Broadlink storage but wasn't tracked in the device manager, so it didn't appear in the UI.

## Solution

Added code to save the learned command to `devices.json` immediately after successfully fetching it from Broadlink storage.

### Changes Made

**File**: `app/api/commands.py`

**Location**: Lines 164-188 (after successfully fetching the learned code)

**Added Logic**:
```python
# Save the command to devices.json if device_id is provided
if device_id:
    device_manager = current_app.config.get("device_manager")
    if device_manager:
        # Detect command type from the learned code
        detected_type = detect_command_type(learned_code)
        command_data = {
            "command_type": detected_type,
            "type": detected_type,
            "learned_at": result.get("learned_at"),
        }
        
        # Save to device manager
        if device_manager.add_command(device_id, command, command_data):
            logger.info(
                f"✅ Saved command '{command}' to device '{device_id}' with type '{detected_type}'"
            )
        else:
            logger.warning(
                f"⚠️ Failed to save command '{command}' to device manager"
            )
    else:
        logger.warning("⚠️ Device manager not available to save command")
else:
    logger.info("ℹ️ No device_id provided, command not saved to device manager")
```

### Key Features

1. **Automatic Command Type Detection**: Uses `detect_command_type()` to determine if the command is IR or RF based on the learned code
2. **Proper Metadata**: Saves command with type and timestamp
3. **Error Handling**: Logs warnings if device manager is unavailable or save fails
4. **Backward Compatible**: Only saves if `device_id` is provided (managed devices)

## Testing

To verify the fix:

1. Create a new device or use an existing one
2. Click "Learn Commands" button
3. Learn a new command (IR or RF)
4. ✅ Command should immediately appear in the device card
5. ✅ Command should be visible in the command list
6. ✅ Command should be saved to `devices.json`
7. ✅ No need to click "Sync Commands" button

## Impact

- **Before**: Commands learned but not tracked → required manual sync
- **After**: Commands automatically tracked → immediately visible in UI
- **User Experience**: Seamless - commands appear instantly after learning
- **Data Integrity**: Commands properly saved to `devices.json` with correct type detection

## Related Systems

This fix works in conjunction with:
- **Command Sync System**: Still useful for commands learned outside the app (v1, HA Broadlink integration)
- **Device Manager**: Uses `add_command()` method to save to `devices.json`
- **Command Type Detection**: Automatically detects IR vs RF from the learned code

## Code Quality

- ✅ Black formatted
- ✅ Flake8 compliant (0 errors)
- ✅ Proper logging
- ✅ Error handling
- ✅ Backward compatible
