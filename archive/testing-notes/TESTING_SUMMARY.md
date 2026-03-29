# Quick Start: Testing Coatsy's Issue Locally

## TL;DR - 30 Second Setup

```powershell
# 1. Run the test script
.\test_coatsy_issue.ps1

# 2. Set environment variables
$env:CONFIG_PATH = "C:\temp\broadlink_test"
$env:HA_URL = "http://localhost:8123"
$env:HA_TOKEN = "any_value_works_for_this_test"

# 3. Start the app
python app/main.py

# 4. Open browser
# http://localhost:8099

# 5. Try to generate entities
# Settings (⚙️) → Generate Entities

# Expected: Error message about missing Broadlink remote entity
```

## What the Test Script Does

Creates a test device at `C:\temp\broadlink_test\broadlink_manager\devices.json`:

```json
{
  "living_room_test_fan": {
    "name": "Living Room Test Fan",
    "broadlink_entity": "",  // ← EMPTY! This is the bug
    "commands": { ... 4 commands ... }
  }
}
```

## What You Should See

### In the UI
1. Device appears in device list
2. Click Settings → Generate Entities
3. **Error toast**: "The following device(s) are missing a Broadlink remote entity: Living Room Test Fan. Please edit each device and select a Broadlink remote from the dropdown."

### In the Logs
```
📝 Generating 1 Broadlink native entities...
Device 'living_room_test_fan': broadlink_entity='', has_commands=True
ERROR - The following device(s) are missing a Broadlink remote entity: Living Room Test Fan
```

## Testing the Fix

1. Click Edit on the device
2. Select any value from "Remote Device" dropdown (or manually edit JSON to add `"broadlink_entity": "remote.test"`)
3. Save
4. Try generating entities again
5. **Should succeed** (or fail with different error about HA connection)

## Files Created

- `docs/development/REPRODUCE_COATSY_ISSUE.md` - Detailed reproduction guide with multiple scenarios
- `test_coatsy_issue.ps1` - Quick setup script

## Clean Up

```powershell
Remove-Item -Recurse -Force C:\temp\broadlink_test
```

## Full Documentation

See `docs/development/REPRODUCE_COATSY_ISSUE.md` for:
- Multiple reproduction scenarios
- Debugging tips
- Expected results
- Testing checklist
