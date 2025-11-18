# Fan Entity Type Detection Fix

## Issue Reported by User (Coatsy)

**Problem**: After reinstalling the add-on and recreating the fan, entity generation fails with "No entities configured".

**Symptoms**:
- `devices.json` shows fan with all commands (`speed_low`, `speed_medium`, `speed_high`, `turn_off`) ✅
- Entity generation fails with "Entity Generation Failed - No entities configured" ❌
- No `entities.yaml` or `helpers.yaml` files generated ❌

## Root Cause

The `EntityGeneratorV2` adapter has a function `_infer_entity_type()` that determines whether a device should be a fan, light, or switch based on its commands.

### The Bug

The fan detection logic was only looking for specific patterns:

```python
fan_patterns = {
    "fan_speed_1",
    "fan_speed_2",
    "fan_speed_3",
    # ...
}
if command_names & fan_patterns:
    return "fan"
```

**User's commands**: `speed_low`, `speed_medium`, `speed_high`, `turn_off`

These don't match the `fan_speed_*` pattern, so the function returned **"switch"** instead of **"fan"**.

### Why This Caused "No entities configured"

1. Device detected as "switch" (wrong)
2. Switch entity generator runs
3. Switch generator sees `speed_low`, `speed_medium`, `speed_high` commands
4. Switch generator doesn't know what to do with speed commands
5. Switch generator returns `None` (no entity created)
6. No entities generated → "No entities configured" error

## Solution

Added detection for `speed_*` command patterns:

```python
# Also check for speed_* patterns (speed_low, speed_1, etc.)
has_speed_commands = any(cmd.startswith("speed_") for cmd in command_names)

if command_names & fan_patterns or has_speed_commands:
    return "fan"
```

Now the function correctly identifies devices with `speed_*` commands as fans.

## How It Works Now

**User's commands**: `speed_low`, `speed_medium`, `speed_high`, `turn_off`

1. Check for `fan_speed_*` patterns → Not found
2. Check for `speed_*` patterns → **Found!** ✅
3. Return "fan" entity type
4. Fan entity generator runs
5. Fan entity created successfully
6. Helpers created successfully
7. Entity generation succeeds

## Examples

### Example 1: Named Speeds (Coatsy's case)
**Commands**: `speed_low`, `speed_medium`, `speed_high`, `turn_off`
- **Old**: Detected as "switch" → No entity generated ❌
- **New**: Detected as "fan" → Fan entity generated ✅

### Example 2: Numeric Speeds
**Commands**: `speed_1`, `speed_2`, `speed_3`, `turn_off`
- **Old**: Detected as "switch" → No entity generated ❌
- **New**: Detected as "fan" → Fan entity generated ✅

### Example 3: Standard Fan Patterns
**Commands**: `fan_speed_1`, `fan_speed_2`, `fan_off`
- **Old**: Detected as "fan" ✅
- **New**: Detected as "fan" ✅ (no change)

### Example 4: Custom RF Fan Speeds
**Commands**: `speed_lowMedium`, `speed_mediumHigh`, etc.
- **Old**: Detected as "switch" → No entity generated ❌
- **New**: Detected as "fan" → Fan entity generated ✅

## Why This Regression Happened

This bug was always present in `entity_generator_v2.py`, but it wasn't noticed because:

1. Most users were upgrading from v1, which had `metadata.json` with explicit `entity_type`
2. The adapter checks for explicit `entity_type` first (line 83)
3. If `entity_type` exists in device data, it uses that and skips inference

When Coatsy **reinstalled** the add-on:
- No existing `metadata.json` or `entity_type` in device data
- Inference logic ran for the first time
- Bug was exposed

## Testing

### Test Case 1: Fresh Install with Named Speeds
1. Fresh install (no existing data)
2. Create fan with `speed_low`, `speed_medium`, `speed_high`
3. Generate entities
4. **Expected**: Fan entity created ✅
5. **Result**: Fixed!

### Test Case 2: Fresh Install with Numeric Speeds
1. Fresh install
2. Create fan with `speed_1`, `speed_2`, `speed_3`
3. Generate entities
4. **Expected**: Fan entity created ✅
5. **Result**: Fixed!

### Test Case 3: Upgrade from Existing
1. Existing installation with `entity_type` in device data
2. Generate entities
3. **Expected**: Still works (uses explicit type) ✅
4. **Result**: No regression

## Impact

- **Fixes**: Fresh installations with `speed_*` commands now work
- **Fixes**: Entity generation no longer fails with "No entities configured"
- **Maintains**: Backward compatibility with existing installations
- **Maintains**: Compatibility with `fan_speed_*` patterns
- **No Breaking Changes**: Only adds detection, doesn't remove anything

## User Action Required

1. **Update to v0.3.0-alpha.25**
2. **Try generating entities again**: Settings → Generate Entities
3. **Should now succeed** and create fan entity
4. **Reload Home Assistant**: Developer Tools → YAML → Reload All
5. **Test fan**: All speeds should work

## Files Modified

- `app/entity_generator_v2.py` (lines 86-101)

## Version

- **Fixed in**: v0.3.0-alpha.25
- **Release Date**: 2025-11-18

## Related Issues

- **v0.3.0-alpha.21**: Added named speed support to fan entity generator
- **v0.3.0-alpha.22**: Added named speed support to helper generator
- **v0.3.0-alpha.23**: Added auto-on behavior to match SmartIR
- **v0.3.0-alpha.24**: Fixed medium speed not working (non-sequential numbering)
- **v0.3.0-alpha.25**: Fixed entity type detection for speed_* commands (this fix!)

All five fixes work together to provide a complete, fully-functional RF fan experience for both upgrades and fresh installations.
