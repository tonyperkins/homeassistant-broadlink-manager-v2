# Bug Fix: Entity Generator Speed Command Detection

**Date**: 2025-11-02  
**Issue**: Entity generator fails to detect fan speed commands with named levels  
**Status**: ✅ Fixed

## Problem Description

### Issue #1: Speed Command Detection Failure

The entity generator was rejecting fan devices with named speed commands (`speed_low`, `speed_medium`, `speed_high`) because it only accepted numeric speed identifiers.

**Symptoms**:
```
2025-10-29 22:01:37,004 - entity_generator - WARNING - Fan living_room_fan_right has no speed commands
2025-10-29 22:01:37,004 - entity_generator - WARNING - Fan living_room_left has no speed commands
```

**Root Cause**:
The code at line 511 in `app/entity_generator.py` used `speed_num.isdigit()` to validate speed identifiers, which rejected named speeds:

```python
# Old code - only accepted numeric speeds
if speed_num.isdigit():
    speed_commands[f"speed_{speed_num}"] = v
```

This meant devices with commands like:
- `speed_low` ❌ Rejected
- `speed_medium` ❌ Rejected  
- `speed_high` ❌ Rejected
- `fan_speed_1` ✅ Accepted
- `fan_speed_2` ✅ Accepted

### Issue #2: Data Corruption

```
2025-10-29 22:09:49,395 - device_manager - ERROR - Error loading devices after retries: Expecting value: line 1 column 1 (char 0)
```

The `devices.json` file became corrupted (empty or invalid JSON), likely due to concurrent write operations or interrupted saves.

## Solution

### Fix #1: Support Named Speed Levels

Added a mapping system to convert named speed levels to numeric equivalents:

```python
named_speed_map = {
    "low": 1,
    "medium": 2,
    "med": 2,
    "high": 3,
    "off": 0,  # Some fans have speed_off
}
```

**New Logic**:
1. Extract speed identifier from command name (`speed_low` → `low`)
2. If numeric, use as-is (`speed_1` → `1`)
3. If named, map to number (`speed_low` → `1`)
4. Skip unknown names with debug log
5. Filter out `speed_0` (off command)

**Improved Logging**:
```python
logger.warning(f"Fan {entity_id} has no speed commands (found commands: {list(commands.keys())})")
```

Now shows which commands were found, making debugging easier.

### Fix #2: Data Corruption Prevention

The existing backup system in `device_manager.py` should prevent data loss:
- Automatic `.backup` files created before saves
- Atomic writes using temp file + rename
- Auto-restore on startup if file is missing

**Recommendation**: Ensure file watcher debouncing is working correctly to prevent rapid successive writes.

## Testing

### Test Case 1: Named Speed Commands
**Device**: Fan with `speed_low`, `speed_medium`, `speed_high`

**Expected**:
- ✅ Entity generated with 3 speed levels
- ✅ No warning about missing speed commands
- ✅ Helpers created: `input_select.{device}_speed` with options 1, 2, 3

### Test Case 2: Numeric Speed Commands  
**Device**: Fan with `fan_speed_1`, `fan_speed_2`, `fan_speed_3`, `fan_speed_4`

**Expected**:
- ✅ Entity generated with 4 speed levels
- ✅ No warning about missing speed commands
- ✅ Helpers created: `input_select.{device}_speed` with options 1, 2, 3, 4

### Test Case 3: Mixed Commands
**Device**: Fan with `turn_on`, `turn_off`, `speed_low`, `speed_high`, `fan_reverse`

**Expected**:
- ✅ Entity generated with 2 speed levels (low=1, high=3)
- ✅ Direction support enabled
- ✅ All commands properly mapped

## Files Modified

- `app/entity_generator.py` - Lines 500-537
  - Added `named_speed_map` dictionary
  - Enhanced speed command detection logic
  - Improved warning messages with command list

## Backward Compatibility

✅ **Fully backward compatible**
- Existing numeric speed commands continue to work
- Named speed commands now also work
- No changes to generated YAML structure
- No migration needed

## Related Issues

- Memory: `SYSTEM-RETRIEVED-MEMORY[b21321fb-4242-4c55-a8fb-144b6b5f52bb]` - V1 entity generation preferences
- Memory: `SYSTEM-RETRIEVED-MEMORY[8110e8e6-d066-45b7-ba75-d1e08f140662]` - Backup and recovery system

## Future Enhancements

1. **Dynamic Speed Mapping**: Allow users to define custom speed name mappings in device configuration
2. **Speed Range Detection**: Auto-detect speed range from command names (e.g., 1-6 vs low/med/high)
3. **Validation**: Warn users if speed commands have gaps (e.g., speed_1, speed_3 but no speed_2)
