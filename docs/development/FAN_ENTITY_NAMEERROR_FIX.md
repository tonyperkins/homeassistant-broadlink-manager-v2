# Fan Entity Generation NameError Fix

## Issue

Entity generation was failing with a `NameError` when generating fan entities:

```python
NameError: name 'default_speed' is not defined. Did you mean: 'default_speed_idx'?
```

## Root Cause

**File**: `app/entity_generator.py`, line 615

Variable name typo in the fan turn_on action:

```python
# Line 593: Variable is defined as default_speed_idx
default_speed_idx = (len(speed_numbers) + 1) // 2

# Line 615: But referenced as default_speed (WRONG!)
"data": {"option": str(default_speed)},
```

## The Fix

Changed line 615 to use the correct variable name:

```python
# Before (WRONG)
"data": {"option": str(default_speed)},

# After (CORRECT)
"data": {"option": str(default_speed_idx)},
```

## Impact

This bug prevented **all** fan entity generation from working. The error occurred when:
1. User had a device with fan-type commands
2. User tried to generate entities
3. Entity generator attempted to create the fan turn_on action
4. Python raised NameError because `default_speed` didn't exist

## How It Was Discovered

User was testing entity generation locally and got the error in the terminal output:

```
2025-11-18 18:44:28,654 - entity_generator - ERROR - Failed to generate entities: name 'default_speed' is not defined
Traceback (most recent call last):
  File "...\app\entity_generator.py", line 95, in generate_all
    entities_yaml = self._build_entities_yaml(entities, broadlink_commands)
  File "...\app\entity_generator.py", line 160, in _build_entities_yaml
    config = self._generate_fan(entity_id, entity_data, broadlink_commands)
  File "...\app\entity_generator.py", line 615, in _generate_fan
    "data": {"option": str(default_speed)},
                           ^^^^^^^^^^^^^
NameError: name 'default_speed' is not defined. Did you mean: 'default_speed_idx'?
```

## Testing

### Before Fix
```powershell
# Entity generation fails
python app/main.py
# Try to generate entities
# ERROR: NameError: name 'default_speed' is not defined
```

### After Fix
```powershell
# Entity generation succeeds
python app/main.py
# Try to generate entities
# ✅ Generated 4 Broadlink native entity configuration(s)
```

## Related Code

The `default_speed_idx` variable is used to set the default speed when the fan is turned on via the power button:

```python
# Get sorted list of actual speed numbers and pick the middle one
speed_numbers = sorted([int(k.split("_")[1]) for k in speed_commands.keys()])
default_speed_idx = (len(speed_numbers) + 1) // 2  # Middle speed (1-indexed)
default_speed_num = speed_numbers[default_speed_idx - 1]  # Convert to 0-indexed
```

For example:
- 3 speeds (1, 2, 3) → default_speed_idx = 2 (medium)
- 5 speeds (1, 3, 5, 7, 9) → default_speed_idx = 3 (middle)

## Files Modified

- `app/entity_generator.py` - Line 615: Changed `default_speed` to `default_speed_idx`

## Commit

✅ `7139e9f` - Fix: NameError in fan entity generation - use default_speed_idx instead of default_speed

## Notes

- This was a simple typo that slipped through
- Python's helpful error message ("Did you mean: 'default_speed_idx'?") made it easy to identify
- The fix is a single character change (adding `_idx`)
- All fan entity generation now works correctly
