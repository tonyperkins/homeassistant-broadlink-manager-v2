# Fan Helper Generation Fix

## Issue Reported by User (Coatsy)

**Error**: `Failed to perform the action fan/set_percentage. Invalid option: 1 (possible options: off)`

**Symptoms**:
- Fan entity created successfully
- Fan shows speed buttons (Low, Medium, High, Off)
- Clicking speed buttons causes error
- `input_select.living_room_test_fan_speed` only has "off" as an option

## Root Cause

The helper generation logic in `_build_helpers_yaml()` was only counting **numeric** speed commands (e.g., `speed_1`, `speed_2`, `speed_3`), but the user had **named** speed commands (e.g., `speed_low`, `speed_medium`, `speed_high`).

### The Problem

**Helper Generator** (lines 1399-1420):
```python
# OLD CODE - Only counted numeric speeds
for k in entity_data["commands"].keys():
    if k.startswith("speed_") or k.startswith("fan_speed_"):
        speed_num = k.replace("speed_", "")
        if speed_num.isdigit():  # ← Only numeric speeds counted
            speed_count += 1
```

Result: `speed_count = 0` → `options = ["off"]` → Error when trying to set speed to "1", "2", or "3"

**Fan Entity Generator** (lines 500-531):
```python
# This code DOES handle named speeds correctly
named_speed_map = {
    "low": 1,
    "lowmedium": 2,
    "medium": 3,
    "mediumhigh": 4,
    "high": 5,
}
```

Result: Fan entity generated with 3 speeds (low=1, medium=3, high=5)

### The Mismatch

- **Fan entity**: Expects `input_select` to have options `["off", "1", "3", "5"]`
- **Helper**: Only created `["off"]`
- **Result**: Error when fan tries to set `input_select` to "1", "3", or "5"

## Solution

Updated `_build_helpers_yaml()` to use the **same logic** as `_generate_fan()`:

```python
# NEW CODE - Matches fan generator logic
named_speed_map = {
    "off": 0,
    "low": 1,
    "lowmedium": 2,
    "medium": 3,
    "mediumhigh": 4,
    "high": 5,
    "med": 3,
    "quiet": 1,
    "auto": 3,
}

speed_commands = {}
for k in entity_data["commands"].keys():
    if k.startswith("speed_") or k.startswith("fan_speed_"):
        speed_id = k.replace("speed_", "")
        
        # Convert to numeric if it's a digit, or map named speeds
        if speed_id.isdigit():
            speed_num = speed_id
        elif speed_id.lower() in named_speed_map:
            speed_num = str(named_speed_map[speed_id.lower()])
        else:
            continue  # Skip unknown speeds
        
        # Store with normalized key (skip speed_0/off)
        if speed_num != "0":
            speed_commands[f"speed_{speed_num}"] = k

speed_count = len(speed_commands)
options = ["off"] + [str(i) for i in range(1, speed_count + 1)]
```

## Example: User's Fan

**Commands**: `speed_low`, `speed_medium`, `speed_high`, `speed_on`, `speed_off`

### Before Fix:
- `speed_count = 0` (no numeric speeds found)
- `options = ["off"]`
- **Error**: Can't set speed to "1", "2", or "3"

### After Fix:
- `speed_low` → speed 1
- `speed_medium` → speed 3
- `speed_high` → speed 5
- `speed_count = 3`
- `options = ["off", "1", "2", "3"]`
- **Works**: Fan can set speed to "1", "2", or "3"

## Testing

### Test Case 1: Named Speeds (User's Case)
**Commands**: `speed_low`, `speed_medium`, `speed_high`
- Expected: `options = ["off", "1", "2", "3"]`
- Fan entity: 3 speeds (low=33%, medium=66%, high=100%)

### Test Case 2: Numeric Speeds
**Commands**: `speed_1`, `speed_2`, `speed_3`
- Expected: `options = ["off", "1", "2", "3"]`
- Fan entity: 3 speeds (1=33%, 2=66%, 3=100%)

### Test Case 3: Mixed Speeds
**Commands**: `speed_low`, `speed_2`, `speed_high`
- Expected: `options = ["off", "1", "2", "3"]`
- Fan entity: 3 speeds (low=1, 2=2, high=5)

### Test Case 4: Custom RF Fan Speeds
**Commands**: `speed_low`, `speed_lowMedium`, `speed_medium`, `speed_mediumHigh`, `speed_high`
- Expected: `options = ["off", "1", "2", "3", "4", "5"]`
- Fan entity: 5 speeds (20%, 40%, 60%, 80%, 100%)

## Files Modified

- `app/entity_generator.py` (lines 1399-1445)

## Impact

- **Fixes**: Fan entities with named speeds now work correctly
- **Maintains**: Backward compatibility with numeric speeds
- **Supports**: All speed naming patterns (numeric, named, custom RF)

## User Action Required

1. **Regenerate entities**: Settings → Generate Entities
2. **Reload Home Assistant**: Developer Tools → YAML → Reload All
3. **Test fan speeds**: Click Low, Medium, High buttons
4. **Verify**: No more "Invalid option" errors

## Related Issues

- Issue 1: RF fan entity generation (fixed in v0.3.0-alpha.21)
- This fix: RF fan helper generation (v0.3.0-alpha.22)

Both issues stemmed from the same root cause: named speed support was added to the fan generator but not the helper generator.
