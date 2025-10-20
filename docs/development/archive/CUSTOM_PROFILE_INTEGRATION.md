# Custom SmartIR Profile Integration

## Problem
When users created custom SmartIR profiles (e.g., "LG COOLER" with code 10003), these profiles were saved successfully to the SmartIR codes directory. However, when trying to add a device using that custom profile, the manufacturer and model would not appear in the device creation form dropdowns.

## Root Cause
The SmartIR device form was only loading manufacturers and models from the pre-built device index (`smartir_device_index.json`), which contains profiles from the SmartIR Code Aggregator repository. Custom profiles created locally (codes 10000+) were not being included in the API responses.

## Solution
Updated the `SmartIRCodeService` to merge custom profiles with the device index when returning manufacturer and model lists.

### Changes Made

#### 1. **SmartIRCodeService** (`app/smartir_code_service.py`)

**Added `smartir_detector` parameter to constructor:**
```python
def __init__(self, cache_path: str = "/config/broadlink_manager/cache", smartir_detector=None):
    # ...
    self.smartir_detector = smartir_detector
```

**Added `_get_custom_profiles()` method:**
- Scans local SmartIR installation for custom profiles (code >= 10000)
- Returns list of custom profile info (code, manufacturer, models, controller)
- Handles errors gracefully if SmartIR is not installed

**Updated `get_manufacturers()` method:**
- Starts with manufacturers from device index
- Adds manufacturers from custom profiles
- Returns merged, sorted list

**Updated `get_models()` method:**
- Starts with models from device index
- Adds models from custom profiles for the selected manufacturer
- Marks custom profiles with `"custom": True` flag
- Returns merged, sorted list by code number

#### 2. **WebServer** (`app/web_server.py`)

**Updated SmartIRCodeService initialization:**
```python
self.smartir_code_service = SmartIRCodeService(
    str(self.config_loader.get_broadlink_manager_path() / "cache"),
    smartir_detector=self.smartir_detector  # Pass detector instance
)
```

### How It Works

1. **User creates custom profile:**
   - Uses "Create SmartIR Profile" feature
   - Profile saved to `/config/custom_components/smartir/codes/{platform}/{code}.json`
   - Code number is 10000 or higher (custom range)

2. **User adds device:**
   - Opens "Add New Device" modal
   - Selects "SmartIR Device (Pre-configured Codes)"
   - Selects platform (e.g., Climate)

3. **Manufacturer dropdown loads:**
   - API calls `/api/smartir/codes/manufacturers?entity_type=climate`
   - `SmartIRCodeService.get_manufacturers()` is called
   - Returns manufacturers from index + custom profiles
   - **Custom manufacturer (e.g., "LG") now appears in list**

4. **Model dropdown loads:**
   - User selects manufacturer (e.g., "LG")
   - API calls `/api/smartir/codes/models?entity_type=climate&manufacturer=LG`
   - `SmartIRCodeService.get_models()` is called
   - Returns models from index + custom profiles for that manufacturer
   - **Custom model (e.g., "COOLER" with code 10003) now appears in list**

5. **Device creation:**
   - User selects custom model
   - Device is created with `device_code: "10003"`
   - SmartIR integration uses the custom profile

### Custom Profile Detection

Custom profiles are identified by:
- **Code range:** >= 10000 (SmartIR convention for custom codes)
- **Location:** `/config/custom_components/smartir/codes/{platform}/`
- **Format:** Standard SmartIR JSON format

### Benefits

✅ **Seamless integration:** Custom profiles appear alongside repository profiles  
✅ **No manual editing:** Users don't need to manually enter code numbers  
✅ **Consistent UX:** Same workflow for both repository and custom profiles  
✅ **Automatic discovery:** Custom profiles are detected on-the-fly  
✅ **Marked as custom:** Custom profiles have `"custom": true` flag for future features

### Testing

To verify the fix:

1. Create a custom SmartIR profile (code 10000+)
2. Open "Add New Device" modal
3. Select "SmartIR Device (Pre-configured Codes)"
4. Select the platform matching your custom profile
5. Verify manufacturer appears in dropdown
6. Select manufacturer
7. Verify custom model appears in dropdown with correct code number

### Additional Fix: Command Counting for Custom Profiles

**Problem:** Device cards using custom profiles showed "0 commands" even though the profile had learned commands.

**Root Cause:** The `/api/smartir/codes/code` endpoint only fetched from GitHub, which doesn't have custom codes (10000+).

**Solution:**
1. **Backend (`app/api/smartir.py`):** Updated endpoint to check for local custom profiles first
   - If code >= 10000 and SmartIR is installed, load from local file
   - Falls back to GitHub for repository codes (< 10000)

2. **Frontend (`DeviceCard.vue`):** Fixed command counting for nested structures
   - Added recursive `countCommands()` function
   - Properly counts climate device commands (nested: mode → temp → fan)
   - Works for all SmartIR device types (climate, fan, media_player, light)

**Example Climate Command Structure:**
```json
{
  "commands": {
    "cool": {
      "16": {"auto": "JgBQAAA...", "low": "JgBQAAA..."},
      "17": {"auto": "JgBQAAA...", "low": "JgBQAAA..."}
    }
  }
}
```
- Old counting: 1 (just "cool" key)
- New counting: 4 (all IR codes recursively)

### Additional Fix: Command Sending for Custom Profiles

**Problem:** When testing commands on devices using custom profiles, the system tried to fetch the profile from GitHub and failed with 404 error.

**Root Cause:** The `fetch_full_code()` method in `SmartIRCodeService` only fetched from GitHub, which doesn't have custom codes (10000+).

**Solution:**

1. **Backend (`app/smartir_code_service.py`):** Updated `fetch_full_code()` method
   - Checks if code >= 10000 and SmartIR is installed
   - Loads custom profile from local file: `/config/custom_components/smartir/codes/{platform}/{code}.json`
   - Falls back to GitHub for repository codes (< 10000)
   - Used by command sending API (`/api/commands/test`)

2. **Backend (`app/api/commands.py`):** Fixed service payload for SmartIR commands
   - Send raw IR codes **without** `device` parameter (device is only for learned commands)
   - Raw base64 IR codes are sent directly in the `command` array

**Errors Before:**
```
WARNING - Network error fetching code 10003: 404 Client Error: Not Found 
for url: https://raw.githubusercontent.com/.../codes/climate/10003.json

KeyError: 'smartir_raw'
ValueError: Command not found: 'pending'
```

**Service Payload (Correct):**
```python
# For SmartIR raw codes
{
    "entity_id": "remote.master_bedroom_rm4_pro",
    "command": ["JgBQAAA..."]  # Raw IR code only, no device parameter
}

# For Broadlink learned commands
{
    "entity_id": "remote.master_bedroom_rm4_pro", 
    "device": "device_name",
    "command": ["power"]  # Command name from storage
}
```

**Success After:**
```
INFO - Loaded custom profile 10003 from local file: /config/custom_components/smartir/codes/climate/10003.json
INFO - Sending SmartIR raw code to HA (code length: 348 chars)
INFO - ✅ Command sent successfully
```

### Future Enhancements

Potential improvements:
- Visual indicator in dropdown for custom profiles (e.g., badge or icon)
- Filter/toggle to show only custom profiles
- Export/import custom profiles
- Sync custom profiles across devices
