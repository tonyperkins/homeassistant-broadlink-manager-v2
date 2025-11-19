# Fan Direction Controls - Optional Based on Commands

## Issue

**Reported by**: Coatsy  
**Date**: 2025-11-19

Fans that only have one direction (no reverse function) were still showing direction controls (forward/reverse) in Home Assistant. This cluttered the UI with unnecessary controls.

## Root Cause

The entity generator was **forcing** direction support for all fans, regardless of whether direction commands were learned:

```python
# For now, always enable direction support for fans (even if no command exists yet)
# This allows the UI to show direction controls
has_direction = True  # ← Always True!
```

This meant:
- ✅ Direction helper (`input_select.{fan}_direction`) was always created
- ✅ Direction template (`direction_template`) was always added to fan entity
- ✅ Direction controls appeared in HA UI even when fan had no reverse function

## The Fix

Changed the logic to **only enable direction support when direction commands exist**:

### 1. Fan Entity Generation (Line 545-552)

**Before**:
```python
# Check if reverse/direction command exists (support fan_reverse too)
has_direction = (
    "reverse" in commands
    or "direction" in commands
    or "fan_reverse" in commands
)

# For now, always enable direction support for fans (even if no command exists yet)
# This allows the UI to show direction controls
has_direction = True  # ← FORCED!
```

**After**:
```python
# Check if reverse/direction command exists (support fan_reverse too)
has_direction = (
    "reverse" in commands
    or "direction" in commands
    or "fan_reverse" in commands
    or "fan_direction_forward" in commands
    or "fan_direction_reverse" in commands
)
# ← No more forcing! Only True if commands exist
```

### 2. Helper Generation (Line 1477-1490)

**Before**:
```python
# Always add direction selector for fans (matches fan generator behavior)
# Even if no reverse command exists, the UI can still show direction controls
helpers["input_select"][f"{sanitized_id}_direction"] = {
    "name": f"{display_name} Direction",
    "options": ["forward", "reverse"],
    "initial": "forward",
}
```

**After**:
```python
# Only add direction selector if direction commands exist
has_direction_commands = (
    "reverse" in commands
    or "direction" in commands
    or "fan_reverse" in commands
    or "fan_direction_forward" in commands
    or "fan_direction_reverse" in commands
)
if has_direction_commands:
    helpers["input_select"][f"{sanitized_id}_direction"] = {
        "name": f"{display_name} Direction",
        "options": ["forward", "reverse"],
        "initial": "forward",
    }
```

## Supported Direction Command Names

The fix checks for any of these command names:
- `reverse` - Simple reverse command
- `direction` - Generic direction toggle
- `fan_reverse` - Explicit fan reverse
- `fan_direction_forward` - Explicit forward direction
- `fan_direction_reverse` - Explicit reverse direction

## Impact

### Fans WITH Direction Commands ✅
**Commands**: `speed_low`, `speed_medium`, `speed_high`, `reverse`

**Generated**:
- ✅ `input_boolean.{fan}_state` - State tracking
- ✅ `input_select.{fan}_speed` - Speed control
- ✅ `input_select.{fan}_direction` - Direction control ← **Created**
- ✅ `fan.{fan}` with `direction_template` and `set_direction` ← **Included**

**HA UI Shows**:
- Power on/off
- Speed slider (33%, 66%, 100%)
- Direction toggle (forward/reverse) ← **Visible**

### Fans WITHOUT Direction Commands ✅
**Commands**: `speed_low`, `speed_medium`, `speed_high`

**Generated**:
- ✅ `input_boolean.{fan}_state` - State tracking
- ✅ `input_select.{fan}_speed` - Speed control
- ❌ `input_select.{fan}_direction` - **NOT created**
- ✅ `fan.{fan}` **without** `direction_template` and `set_direction` ← **Omitted**

**HA UI Shows**:
- Power on/off
- Speed slider (33%, 66%, 100%)
- ❌ Direction toggle **HIDDEN** ← **Clean UI!**

## Testing

### Test Case 1: Fan with Direction Commands

**Device**: "Office Ceiling Fan"  
**Commands**: `speed_1`, `speed_2`, `speed_3`, `reverse`

**Expected**:
```yaml
# helpers.yaml
input_select:
  office_ceiling_fan_direction:  # ← Created
    name: Office Ceiling Fan Direction
    options:
      - forward
      - reverse
    initial: forward

# package.yaml
fan:
  - platform: template
    fans:
      office_ceiling_fan:
        direction_template: "{{ states('input_select.office_ceiling_fan_direction') }}"  # ← Included
        set_direction:  # ← Included
          - service: remote.send_command
            ...
```

### Test Case 2: Fan without Direction Commands

**Device**: "Bedroom Fan"  
**Commands**: `speed_1`, `speed_2`, `speed_3`

**Expected**:
```yaml
# helpers.yaml
input_select:
  # NO direction helper created ← Clean!

# package.yaml
fan:
  - platform: template
    fans:
      bedroom_fan:
        # NO direction_template ← Omitted
        # NO set_direction ← Omitted
```

## User Experience

### Before Fix ❌
**All fans** showed direction controls, even single-direction fans:
- Confusing for users (why is there a direction toggle if it doesn't work?)
- Cluttered UI with unnecessary controls
- Toggling direction did nothing for single-direction fans

### After Fix ✅
**Only fans with direction commands** show direction controls:
- Clean, intuitive UI
- Controls match actual fan capabilities
- No confusion about non-functional controls

## Backward Compatibility

**Existing fans with direction commands**: ✅ No change, still works  
**Existing fans without direction commands**: ✅ Direction controls will be removed on next entity generation (improvement!)

Users should regenerate entities to get the cleaner UI.

## Files Modified

- `app/entity_generator.py`:
  - Line 545-552: Removed forced `has_direction = True`
  - Line 1477-1490: Added conditional direction helper generation

## Commit

✅ `[commit hash]` - Fix: Only show fan direction controls when direction commands exist

## User Feedback

> "Amazing work and thanks for all the fixes, got my fans working and it's flawless. Only one more request... If no direction commands for fans are learnt, probably the fan only has one direction. Is it visible to hide forward and reverse"  
> — Coatsy

**Status**: ✅ Implemented!

## Notes

- This is a UX improvement that makes the generated entities match the actual device capabilities
- The fix is automatic - users just need to regenerate entities
- Direction controls only appear when the fan actually supports direction changes
- Cleaner, more intuitive Home Assistant UI
