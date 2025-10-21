# Bug Fix: Commands Not Showing in List View

## Issue Summary

Commands were not visible in the list view, but were working correctly in grid view and the command learner dialog.

## Root Cause

**Missing `device_type` field in older devices.**

Your devices were created before the `device_type` field was added to the device schema. When this field is missing (undefined), the list view's conditional rendering failed:

```vue
<!-- This evaluated to false when device_type was undefined -->
<div v-if="device.device_type === 'broadlink'" class="command-list">
```

The grid view worked because `DeviceCard.vue` had a fallback:
```javascript
const deviceType = props.device.device_type || 'broadlink'
```

But `DeviceListView.vue` was missing this fallback.

## Fix Applied

Updated `frontend/src/components/devices/DeviceListView.vue` to add the same fallback logic:

### Change 1: Type Badge (Line 28)
```vue
<!-- Before -->
<span class="type-badge" :class="device.device_type">

<!-- After -->
<span class="type-badge" :class="device.device_type || 'broadlink'">
```

### Change 2: Commands Section (Line 35)
```vue
<!-- Before -->
<div v-if="device.device_type === 'broadlink'" class="command-list">

<!-- After -->
<div v-if="(device.device_type || 'broadlink') === 'broadlink'" class="command-list">
```

## How to Apply the Fix

### Option 1: Rebuild from Source
```bash
cd frontend
npm run build
cd ..
# Restart your Home Assistant add-on
```

### Option 2: Wait for Next Release
This fix will be included in the next release.

## Verification

After applying the fix:
1. Open Broadlink Manager
2. Navigate to "Managed Devices"
3. Click the **List** view button
4. Commands should now be visible in the "Commands" column

## Long-Term Solution (Optional)

To permanently add the `device_type` field to your existing devices:

### Manual Method
1. Open each device in the edit dialog
2. Click "Save" (no changes needed)
3. This will update the device with the `device_type` field

### Automatic Migration (Future Enhancement)
We could add a migration script that automatically adds `device_type: 'broadlink'` to all devices in `devices.json` that don't have it.

## Files Modified

- `frontend/src/components/devices/DeviceListView.vue` (lines 28, 35)
- `docs/development/ISSUE_LIST_VIEW_COMMANDS.md` (documentation)

## Related Issue

GitHub Issue: [Link to issue]

## Testing Checklist

- [x] Commands visible in list view for Broadlink devices
- [x] Type badge displays correctly
- [x] Command buttons are clickable
- [x] No console errors
- [x] Grid view still works correctly
- [x] SmartIR devices display profile code (not commands)

## Notes

This is a backward compatibility fix. All new devices created after the `device_type` field was introduced will have this field and won't be affected by this issue.
