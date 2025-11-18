# Fix Summary for Coatsy's Fan Issue

## Problem

Your fan entity was created successfully, but clicking speed buttons caused this error:

**Error**: `Failed to perform the action fan/set_percentage. Invalid option: 1 (possible options: off)`

## Root Cause

You have **two separate but related issues**:

### Issue 1: Fan Entity Generation ✅ Fixed in v0.3.0-alpha.21
The fan entity generator wasn't recognizing custom speed names like `lowMedium` and `mediumHigh`.

### Issue 2: Fan Helper Generation ✅ Fixed in v0.3.0-alpha.22 (NEW)
The helper generator (which creates `input_select` entities) was only counting **numeric** speeds (like `speed_1`, `speed_2`), not **named** speeds (like `speed_low`, `speed_medium`, `speed_high`).

**Result**: 
- Your fan entity expected speeds: `["off", "1", "3", "5"]` (for low, medium, high)
- But the helper only had: `["off"]`
- When you clicked "Low" (speed 1), it tried to set the helper to "1", which didn't exist → Error!

## The Fix

Updated the helper generator to use the **same logic** as the fan entity generator, so both now recognize:
- Numeric speeds: `speed_1`, `speed_2`, `speed_3`
- Named speeds: `speed_low`, `speed_medium`, `speed_high`
- Custom speeds: `speed_lowMedium`, `speed_mediumHigh`
- Special speeds: `speed_quiet`, `speed_auto`

## What Changed

**File**: `app/entity_generator.py`

The helper generator now maps named speeds to numbers:
```python
named_speed_map = {
    "low": 1,
    "lowmedium": 2,
    "medium": 3,
    "mediumhigh": 4,
    "high": 5,
    "quiet": 1,
    "auto": 3,
}
```

So your commands:
- `speed_low` → Creates option "1" in helper
- `speed_medium` → Creates option "3" in helper  
- `speed_high` → Creates option "5" in helper

Result: `input_select` options = `["off", "1", "2", "3"]` (3 speeds total)

## How to Fix Your Fan

### Step 1: Update to v0.3.0-alpha.22

Wait for the Docker build to complete (5-10 minutes), then update the add-on in Home Assistant.

### Step 2: Regenerate Entities

1. Open Broadlink Manager
2. Go to **Settings** (gear icon)
3. Click **Generate Entities**
4. Wait for success message

This will recreate your `entities.yaml` and `helpers.yaml` with the correct options.

### Step 3: Reload Home Assistant

1. Go to **Developer Tools** → **YAML**
2. Click **Reload All** (or restart Home Assistant)

### Step 4: Test Your Fan

1. Open your fan entity: `fan.living_room_test_fan`
2. Click **Low** → Should work without error
3. Click **Medium** → Should work without error
4. Click **High** → Should work without error
5. Click **Off** → Should work without error

### Step 5: Verify Helper

Check that `input_select.living_room_test_fan_speed` now has the correct options:

1. Go to **Developer Tools** → **States**
2. Search for `input_select.living_room_test_fan_speed`
3. Check attributes → Should show: `options: ["off", "1", "2", "3"]` (or similar)

## Expected Behavior

With 3 named speeds (low, medium, high):
- **Low** = 33% (speed 1 of 3)
- **Medium** = 66% (speed 2 of 3)
- **High** = 100% (speed 3 of 3)
- **Off** = 0%

The fan UI will show a slider with 3 positions plus off.

## If It Still Doesn't Work

### Check 1: Verify Commands in devices.json

Look at `/config/broadlink_manager/devices.json` and find your fan device. Check that commands are saved correctly:

```json
{
  "commands": {
    "speed_low": "JgBQAg4ODg4NDw...",
    "speed_medium": "JgBQAg0ODQ8NDg...",
    "speed_high": "JgBQAg0ODQ8NDg...",
    "speed_on": "JgBQAg0ODQ8NDg...",
    "speed_off": "JgBQAg0ODQ8NDg..."
  }
}
```

### Check 2: Verify Helper Options

Check `/config/helpers.yaml` (or wherever your helpers are defined):

```yaml
input_select:
  living_room_test_fan_speed:
    name: Living Room Test Fan Speed
    options:
      - "off"
      - "1"
      - "2"
      - "3"
    initial: "off"
```

If it still only shows `["off"]`, the regeneration didn't work. Try:
1. Delete the old helper manually
2. Regenerate entities again
3. Restart Home Assistant

### Check 3: Verify Entity YAML

Check `/config/entities.yaml` (or wherever your entities are defined):

Look for your fan entity and verify it has `speed_count: 3` (or the correct number).

## Why This Happened

The original code was written to handle numeric speeds (`speed_1`, `speed_2`, `speed_3`) because that's the standard pattern. When we added support for named speeds in the fan entity generator (v0.3.0-alpha.21), we forgot to update the helper generator to match.

Your fan was the first real-world test of named speeds, so you found the bug! Thank you for reporting it.

## Related Fixes

- **v0.3.0-alpha.21**: Added named speed support to fan entity generator
- **v0.3.0-alpha.22**: Added named speed support to helper generator (this fix)

Both fixes are now included, so your fan should work perfectly.

## Questions?

If you still have issues after following these steps:
1. Check the detailed documentation in `docs/development/FAN_HELPER_FIX.md`
2. Share your `devices.json` (just the fan section)
3. Share your `helpers.yaml` (just the fan helper)
4. Share any error messages from Home Assistant logs

We'll get it working! 🎉
