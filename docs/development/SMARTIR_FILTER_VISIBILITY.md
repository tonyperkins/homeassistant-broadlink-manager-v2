# SmartIR Filter Visibility Fix

## Issue

The "SmartIR Only" filter toggle was visible in the device list even when:
- SmartIR integration was disabled via the settings toggle
- SmartIR integration was not installed

This caused confusion as the filter had no purpose when SmartIR was disabled/not installed.

## Solution

Updated the `smartirInstalled` computed property in `DeviceList.vue` to check both:
1. Whether SmartIR is actually installed (`smartirStatus?.value?.installed`)
2. Whether SmartIR is enabled via the user toggle (`smartirEnabled?.value`)

## Changes Made

### File: `frontend/src/components/devices/DeviceList.vue`

**Before:**
```javascript
const smartirInstalled = computed(() => {
  // Check if simulating not-installed
  const isSimulating = localStorage.getItem('smartir_simulate_not_installed') === 'true'
  if (isSimulating) return false
  return smartirStatus?.value?.installed || false
})
```

**After:**
```javascript
const smartirInstalled = computed(() => {
  // Check if simulating not-installed
  const isSimulating = localStorage.getItem('smartir_simulate_not_installed') === 'true'
  if (isSimulating) return false
  // Hide filter if SmartIR is disabled or not installed
  if (!smartirEnabled?.value) return false
  return smartirStatus?.value?.installed || false
})
```

## Behavior

The "SmartIR Only" filter toggle now:
- ✅ Shows when SmartIR is installed AND enabled
- ❌ Hides when SmartIR is disabled (via settings toggle)
- ❌ Hides when SmartIR is not installed
- ❌ Hides when simulating not-installed (dev mode)

## User Experience

**Before:**
- User disables SmartIR in settings
- "SmartIR Only" filter still visible in device list
- Filter has no effect (confusing)

**After:**
- User disables SmartIR in settings
- "SmartIR Only" filter automatically hides
- Clean UI without unnecessary controls

## Testing

1. **With SmartIR Enabled:**
   - Go to Settings → Enable SmartIR toggle
   - Open device list
   - ✅ "SmartIR Only" filter should be visible

2. **With SmartIR Disabled:**
   - Go to Settings → Disable SmartIR toggle
   - Open device list
   - ✅ "SmartIR Only" filter should be hidden

3. **SmartIR Not Installed:**
   - Fresh installation without SmartIR
   - Open device list
   - ✅ "SmartIR Only" filter should be hidden

## Related Files

- `frontend/src/components/devices/DeviceList.vue` - Filter visibility logic
- `frontend/src/App.vue` - SmartIR enabled toggle and injection

## Related Issues

This fix aligns with the existing behavior where:
- SmartIR device cards are hidden when disabled
- SmartIR banner is hidden when disabled
- SmartIR status card is hidden when disabled

Now the filter follows the same pattern for consistency.
