# Fan Auto-On Behavior Fix

## Issue Reported by User (Coatsy)

**Expected Behavior** (SmartIR fans):
- Click "Low" → Fan turns on at low speed
- Click "Medium" → Fan turns on at medium speed
- Click "Off" → Fan turns off

**Actual Behavior** (Broadlink Manager fans):
- Click "Low" → Fan sends speed command but shows as "off"
- Must manually click power button to turn "on"
- Click "Off" → Shows "on", must click power button again to turn off

## Root Cause

The `set_percentage` action was only:
1. Updating the speed helper (`input_select`)
2. Sending the IR/RF command

But it was **NOT** updating the state helper (`input_boolean`), which tracks whether the fan is "on" or "off".

### The Code

**Before** (lines 665-690):
```python
fan_config["set_percentage"] = [
    {
        "service": "input_select.select_option",
        "target": {"entity_id": f"input_select.{sanitized_id}_speed"},
        "data": {"option": "..."},  # Update speed
    },
    {
        "service": "remote.send_command",
        "target": {"entity_id": broadlink_entity},
        "data": {"command": "..."},  # Send IR/RF command
    },
    # ❌ Missing: Update input_boolean state
]
```

**Result**:
- User clicks "Low" (33%)
- Speed helper updates to "1"
- IR command sent to fan
- **But** state helper stays "off"
- Fan UI shows "off" even though fan is running

## Solution

Added a `choose` action to automatically update the state helper based on percentage:

```python
fan_config["set_percentage"] = [
    # ... existing actions ...
    {
        "choose": [
            {
                "conditions": "{{ percentage == 0 }}",
                "sequence": [
                    {
                        "service": "input_boolean.turn_off",
                        "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                    }
                ],
            },
            {
                "conditions": "{{ percentage > 0 }}",
                "sequence": [
                    {
                        "service": "input_boolean.turn_on",
                        "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                    }
                ],
            },
        ]
    },
]
```

### How It Works

1. **User clicks "Low" (33%)**:
   - Speed helper → "1"
   - IR command → `speed_low`
   - State helper → **"on"** (because percentage > 0)
   - Fan UI shows "on" ✅

2. **User clicks "Off" (0%)**:
   - Speed helper → "off"
   - IR command → `turn_off` or `speed_off`
   - State helper → **"off"** (because percentage == 0)
   - Fan UI shows "off" ✅

3. **User clicks "Medium" while already on**:
   - Speed helper → "3"
   - IR command → `speed_medium`
   - State helper → stays "on" (because percentage > 0)
   - Fan UI shows "on" ✅

## Comparison with SmartIR

### SmartIR Behavior
SmartIR fans have built-in logic that automatically turns on when you set a speed:
- Setting speed → Sends combined command (power on + speed)
- Fan integration knows to update state

### Broadlink Manager Behavior (After Fix)
Now matches SmartIR:
- Setting speed > 0 → Sends speed command + updates state to "on"
- Setting speed = 0 → Sends off command + updates state to "off"
- User experience is identical to SmartIR

## Why Use `choose` Instead of Simple Actions?

We could have used two separate actions:
```python
# Alternative approach (NOT used):
{
    "service": "input_boolean.turn_on",
    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
}
```

But this would **always** turn on, even when percentage is 0. The `choose` action allows conditional logic:
- If percentage == 0 → Turn off
- If percentage > 0 → Turn on

This is more robust and handles edge cases correctly.

## Testing

### Test Case 1: Turn On from Off
1. Fan is off
2. Click "Low" (33%)
3. **Expected**: Fan turns on, shows "on", runs at low speed
4. **Result**: ✅ Works

### Test Case 2: Change Speed While On
1. Fan is on at low speed
2. Click "High" (100%)
3. **Expected**: Fan changes to high speed, stays "on"
4. **Result**: ✅ Works

### Test Case 3: Turn Off from On
1. Fan is on at medium speed
2. Click "Off" (0%)
3. **Expected**: Fan turns off, shows "off"
4. **Result**: ✅ Works

### Test Case 4: Set Speed to 0% (Edge Case)
1. Fan is on
2. Use slider to set 0%
3. **Expected**: Fan turns off, shows "off"
4. **Result**: ✅ Works

## Impact

- **Fixes**: Fan auto-on behavior to match SmartIR
- **Improves**: User experience - no need to manually toggle power
- **Maintains**: Backward compatibility - existing fans will work better
- **No Breaking Changes**: Only adds functionality, doesn't remove anything

## User Action Required

1. **Regenerate entities**: Settings → Generate Entities
2. **Reload Home Assistant**: Developer Tools → YAML → Reload All
3. **Test**: Click speed buttons without manually turning on first

## Related Issues

- **v0.3.0-alpha.21**: Added named speed support to fan entity generator
- **v0.3.0-alpha.22**: Added named speed support to helper generator
- **v0.3.0-alpha.23**: Added auto-on behavior to match SmartIR (this fix)

All three fixes work together to provide a complete, SmartIR-compatible fan experience.

## Technical Notes

### Home Assistant Template Fan Platform

The template fan platform supports these actions:
- `turn_on`: Turn on the fan (with optional speed)
- `turn_off`: Turn off the fan
- `set_percentage`: Set fan speed (0-100%)
- `set_direction`: Set fan direction (forward/reverse)

Our implementation now correctly handles all of these, with `set_percentage` being the most complex because it needs to:
1. Map percentage to speed number
2. Send the correct IR/RF command
3. Update the speed helper
4. Update the state helper (on/off)

### Why Not Use `turn_on` with Speed?

Home Assistant's fan platform allows `turn_on` to accept a `percentage` parameter:
```yaml
turn_on:
  - service: fan.turn_on
    data:
      percentage: 50
```

However, this doesn't work well with IR/RF fans because:
1. We need to send a specific speed command (e.g., `speed_medium`)
2. We can't send a generic "turn on" command with a percentage
3. Each speed is a discrete IR/RF code, not a continuous value

So we use `set_percentage` as the primary way to control the fan, and it handles both turning on and setting the speed in one action.

## Files Modified

- `app/entity_generator.py` (lines 665-712)

## Version

- **Fixed in**: v0.3.0-alpha.23
- **Release Date**: 2025-11-17
