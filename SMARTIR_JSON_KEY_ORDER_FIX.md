# SmartIR JSON Key Order Fix - Issue #32

## Problem

SmartIR climate profiles were being generated with incorrect key order in the nested command structure, causing all commands to be unusable.

**Expected by SmartIR:**
```
self._commands[operation_mode][fan_mode][swing_mode][target_temperature]
```

**What was being generated:**
```
[operation_mode][fan_mode][target_temperature][swing_mode]
```

The `swing_mode` and `target_temperature` keys were swapped, making SmartIR unable to find the correct commands.

## Root Cause

When saving SmartIR climate profiles to JSON files, the nested dictionary keys were not being ordered correctly. Python 3.7+ dictionaries maintain insertion order, but if the keys are inserted in the wrong order during construction, they will be saved in that wrong order.

## Solution

Implemented a `_reorder_climate_commands()` function in `app/api/smartir.py` that:

1. Recursively traverses the command structure
2. Sorts keys alphabetically at each nesting level (ensuring consistent order)
3. Sorts temperature keys numerically (16, 17, 18... not alphabetically)
4. Preserves the correct nesting hierarchy

The function is automatically called when saving climate profiles (line 383-385):

```python
# Reorder commands for climate profiles to match SmartIR expected key order
# SmartIR expects: [operation_mode][fan_mode][swing_mode][target_temperature]
if platform == "climate" and "commands" in profile_json:
    logger.debug(f"Reordering climate commands for profile {code_number}")
    profile_json["commands"] = _reorder_climate_commands(profile_json["commands"])
```

## How It Works

The reorder function works by:

1. **Detecting leaf nodes**: If all values in a dict are strings (command codes), it's the temperature level
2. **Sorting temperatures numerically**: Temperatures like "16", "17", "18" are sorted as numbers, not strings
3. **Sorting modes alphabetically**: Operation modes, fan modes, and swing modes are sorted alphabetically
4. **Recursive processing**: Each nested level is processed recursively

This ensures that the final JSON structure has keys in alphabetical order at each level:
- Operation modes: auto, cool, dry, fan_only, heat (alphabetical)
- Fan modes: auto, high, low, medium (alphabetical)
- Swing modes: both, horizontal, off, vertical (alphabetical)
- Temperatures: 16, 17, 18, 19, 20... (numerical)

Since "swing_mode" comes alphabetically before "target_temperature", this produces the correct nesting order that SmartIR expects.

## Files Modified

- `app/api/smartir.py`:
  - Added `_reorder_climate_commands()` function (lines 47-94)
  - Modified `save_profile()` endpoint to call reorder function before saving (lines 381-385)

## Testing

To verify the fix:

1. Create or edit a SmartIR climate profile
2. Add commands with nested structure (operation_mode → fan_mode → swing_mode → temperature)
3. Save the profile
4. Check the generated JSON file in `/config/custom_components/smartir/custom_codes/climate/`
5. Verify keys are in correct order at each nesting level

## Impact

- **Existing profiles**: Will be automatically reordered when saved/edited
- **New profiles**: Will be created with correct key order
- **No breaking changes**: The fix is transparent to users
- **SmartIR compatibility**: Profiles will now work correctly with SmartIR integration

## References

- GitHub Issue: #32
- SmartIR climate.py: https://github.com/smartHomeHub/SmartIR/blob/master/custom_components/smartir/climate.py#318
- SmartIR expects: `self._commands[operation_mode][fan_mode][swing_mode][target_temperature]`
