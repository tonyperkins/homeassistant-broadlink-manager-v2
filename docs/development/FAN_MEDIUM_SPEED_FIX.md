# Fan Medium Speed Fix

## Issue Reported by User (Coatsy)

**Problem**: "Only seem to be getting low, high and off working within the home assistant dashboard. Medium, at 66% doesn't seem to send the commands. Have confirmed that All the commands work when I click play within the Broadlink manager."

**Symptoms**:
- Low speed (33%) works ✅
- High speed (100%) works ✅
- Off (0%) works ✅
- Medium speed (66%) does nothing ❌
- All commands work when tested in Broadlink Manager ✅

## Root Cause

The user has 3 speeds with **non-sequential** numbering:
- `speed_low` → maps to speed number **1**
- `speed_medium` → maps to speed number **3**
- `speed_high` → maps to speed number **5**

So `speed_commands` contains: `{"speed_1": "speed_low", "speed_3": "speed_medium", "speed_5": "speed_high"}`

### The Bug

The `set_percentage` action was iterating from 1 to `speed_count` (1 to 3):

```python
for i in range(1, speed_count + 1):  # i = 1, 2, 3
    speed_cmd_name = speed_commands.get(f"speed_{i}", "")
```

This looked for:
- `speed_1` ✅ Found → Low works
- `speed_2` ❌ **Not found** → Medium fails (empty command sent)
- `speed_3` ✅ Found → But this is mapped to 100%, not 66%!

### Why It Happened

The named speed mapping assigns specific numbers:
```python
named_speed_map = {
    "low": 1,
    "medium": 3,  # ← Not 2!
    "high": 5,    # ← Not 3!
}
```

These numbers were chosen to allow for intermediate speeds (like `lowmedium` = 2, `mediumhigh` = 4), but the percentage calculation assumed sequential numbering (1, 2, 3).

## Solution

Changed the iteration to use the **actual speed numbers** from `speed_commands`:

```python
# Get sorted list of actual speed numbers (e.g., [1, 3, 5] not [1, 2, 3])
speed_numbers = sorted([int(k.split('_')[1]) for k in speed_commands.keys()])

for idx, speed_num in enumerate(speed_numbers, start=1):
    percentage = int((idx / speed_count) * 100)
    
    # Use sequential index for helper (1, 2, 3)
    set_percentage_option_conditions.append(
        f"{{%- elif percentage <= {percentage} -%}}\n" f"  {idx}"
    )
    
    # Use actual speed number for command lookup (1, 3, 5)
    speed_cmd_name = speed_commands.get(f"speed_{speed_num}", "")
```

### How It Works Now

**User's speeds**: `[1, 3, 5]`

**Iteration**:
1. `idx=1`, `speed_num=1`, `percentage=33%` → Low
2. `idx=2`, `speed_num=3`, `percentage=66%` → Medium ✅ Fixed!
3. `idx=3`, `speed_num=5`, `percentage=100%` → High

**Percentage mapping**:
- 0-33% → Speed 1 (Low)
- 34-66% → Speed 3 (Medium)
- 67-100% → Speed 5 (High)

**Helper options**: `["off", "1", "2", "3"]` (sequential)
**Command lookup**: Uses actual speed numbers (1, 3, 5)

## Example Scenarios

### Scenario 1: User with Low/Medium/High (Coatsy's case)
**Commands**: `speed_low`, `speed_medium`, `speed_high`
**Mapped to**: 1, 3, 5
**Result**:
- 33% → `speed_1` → `speed_low` ✅
- 66% → `speed_3` → `speed_medium` ✅ Fixed!
- 100% → `speed_5` → `speed_high` ✅

### Scenario 2: User with 5 Custom Speeds
**Commands**: `speed_low`, `speed_lowMedium`, `speed_medium`, `speed_mediumHigh`, `speed_high`
**Mapped to**: 1, 2, 3, 4, 5
**Result**:
- 20% → `speed_1` → `speed_low` ✅
- 40% → `speed_2` → `speed_lowMedium` ✅
- 60% → `speed_3` → `speed_medium` ✅
- 80% → `speed_4` → `speed_mediumHigh` ✅
- 100% → `speed_5` → `speed_high` ✅

### Scenario 3: User with Numeric Speeds
**Commands**: `speed_1`, `speed_2`, `speed_3`
**Mapped to**: 1, 2, 3
**Result**:
- 33% → `speed_1` ✅
- 66% → `speed_2` ✅
- 100% → `speed_3` ✅

All scenarios now work correctly!

## Additional Fix: Turn On Default Speed

Also fixed the `turn_on` action to use the actual middle speed:

```python
# OLD: Assumed sequential numbering
default_speed = (speed_count + 1) // 2  # Would be 2
default_speed_cmd_name = speed_commands.get(f"speed_{default_speed}", ...)  # ❌ speed_2 not found

# NEW: Uses actual speed numbers
speed_numbers = sorted([int(k.split('_')[1]) for k in speed_commands.keys()])
default_speed_idx = (len(speed_numbers) + 1) // 2  # Index 2 (middle)
default_speed_num = speed_numbers[default_speed_idx - 1]  # Number 3
default_speed_cmd_name = speed_commands.get(f"speed_{default_speed_num}", ...)  # ✅ speed_3 found
```

**Result**: Clicking the power button now correctly turns on at medium speed (speed 3), not a missing speed (speed 2).

## Testing

### Test Case 1: Low Speed
1. Set fan to 33%
2. **Expected**: Sends `speed_low` command
3. **Result**: ✅ Works

### Test Case 2: Medium Speed (The Bug)
1. Set fan to 66%
2. **Expected**: Sends `speed_medium` command
3. **Result**: ✅ Fixed!

### Test Case 3: High Speed
1. Set fan to 100%
2. **Expected**: Sends `speed_high` command
3. **Result**: ✅ Works

### Test Case 4: Power Button
1. Click power button (turn on)
2. **Expected**: Turns on at medium speed (speed 3)
3. **Result**: ✅ Fixed!

## Impact

- **Fixes**: Medium speed (and any other non-sequential speeds) now work
- **Maintains**: Backward compatibility with sequential speeds (1, 2, 3)
- **Supports**: All speed naming patterns (numeric, named, custom)
- **No Breaking Changes**: Only fixes broken functionality

## User Action Required

1. **Update to v0.3.0-alpha.24**
2. **Regenerate entities**: Settings → Generate Entities
3. **Reload Home Assistant**: Developer Tools → YAML → Reload All
4. **Test all speeds**: Low, Medium, High should all work now

## Files Modified

- `app/entity_generator.py` (lines 590-600, 640-660)

## Version

- **Fixed in**: v0.3.0-alpha.24
- **Release Date**: 2025-11-17

## Related Issues

- **v0.3.0-alpha.21**: Added named speed support to fan entity generator
- **v0.3.0-alpha.22**: Added named speed support to helper generator
- **v0.3.0-alpha.23**: Added auto-on behavior to match SmartIR
- **v0.3.0-alpha.24**: Fixed medium speed not working (this fix!)

All four fixes work together to provide a complete, fully-functional RF fan experience.
