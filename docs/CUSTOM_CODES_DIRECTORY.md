# SmartIR Custom Codes Directory

## Overview

Broadlink Manager now saves all SmartIR profiles to a `custom_codes` directory instead of the main `codes` directory. This ensures your custom profiles persist through HACS updates.

## Why This Matters

### The Problem
Previously, when you edited a SmartIR profile and saved it, the file was written to:
```
/config/custom_components/smartir/codes/<platform>/<code>.json
```

**Issue:** HACS manages the `codes` directory. When SmartIR updates via HACS, all files in `codes` are overwritten, causing you to lose your customizations.

### The Solution
Now all profiles are saved to:
```
/config/custom_components/smartir/custom_codes/<platform>/<code>.json
```

**Benefit:** The `custom_codes` directory is **not managed by HACS**, so your customizations persist through updates.

## How It Works

### Directory Structure
```
/config/custom_components/smartir/
├── codes/                    # Managed by HACS (builtin profiles)
│   ├── climate/
│   │   ├── 1000.json
│   │   ├── 1001.json
│   │   └── ...
│   └── media_player/
│       └── ...
└── custom_codes/             # Your custom profiles (persists)
    ├── climate/
    │   ├── 10000.json        # Your custom profiles
    │   ├── 10001.json
    │   └── 1000.json         # Edited builtin profile
    └── media_player/
        └── ...
```

### Precedence Rules

1. **Custom codes take precedence**: If a profile exists in both `codes` and `custom_codes`, the `custom_codes` version is used
2. **Builtin profiles are read-only**: You cannot delete builtin profiles from the UI
3. **All saves go to custom_codes**: Whether creating new or editing existing profiles

### Code Number Ranges

- **1-9999**: Reserved for builtin profiles (from SmartIR/HACS)
- **10000+**: Custom profiles created by users

**Note:** You can edit builtin profiles (e.g., 1000.json), and the edited version will be saved to `custom_codes/1000.json`, taking precedence over the builtin version.

## User Workflow

### Creating a New Profile
1. Click "Create SmartIR Profile" in the UI
2. Follow the wizard to configure and learn commands
3. Click "Save to SmartIR"
4. Profile is saved to `custom_codes/<platform>/<code>.json`
5. ✅ Profile persists through HACS updates

### Editing an Existing Profile
1. Browse profiles in the SmartIR Status Card
2. Click "Edit" on any profile (builtin or custom)
3. Make your changes
4. Click "Save to SmartIR"
5. If editing a builtin profile (e.g., 1000), the edited version is saved to `custom_codes/1000.json`
6. ✅ Your edits persist through HACS updates

### Deleting a Profile
- **Custom profiles**: Can be deleted via the UI
- **Builtin profiles**: Cannot be deleted (protected)
- If you edited a builtin profile, you can delete your custom version to revert to the builtin

## Technical Details

### Backend Changes

#### SmartIRDetector (`app/smartir_detector.py`)
- Added `custom_codes_path` property
- `get_device_codes()` checks `custom_codes` first, then `codes`
- `find_next_custom_code()` checks both directories
- `get_code_save_path()` always returns `custom_codes` path
- `write_code_file()` always writes to `custom_codes`

#### API Endpoints (`app/api/smartir.py`)

**POST /api/smartir/profiles**
- Saves profiles to `custom_codes/<platform>/<code>.json`
- Creates directory if it doesn't exist
- Logs whether creating new or updating existing

**GET /api/smartir/platforms/<platform>/profiles/<code>**
- Checks `custom_codes` first, then `codes`
- Returns `source` field: "custom" or "builtin"
- Returns file path for debugging

**DELETE /api/smartir/profiles/<code>**
- Only allows deleting custom profiles
- Returns error if attempting to delete builtin profile
- Checks if profile is in use before deletion

### Migration

No migration is needed. Existing profiles in `codes` will continue to work:
- Builtin profiles remain in `codes` (managed by HACS)
- Any future edits will create a copy in `custom_codes`
- The `custom_codes` version takes precedence

### Logging

Look for these log messages:
```
✅ Saved SmartIR profile to custom_codes: /config/custom_components/smartir/custom_codes/climate/10000.json
Creating new profile 10000 in custom_codes (persists through HACS updates)
Profile file 1000 already exists in custom_codes, updating
```

## FAQ

### Q: What happens to my existing custom profiles in `codes`?
**A:** They will continue to work. When you edit them next, the updated version will be saved to `custom_codes` and take precedence.

### Q: Can I manually move profiles from `codes` to `custom_codes`?
**A:** Yes! Simply copy the JSON file from `codes/<platform>/` to `custom_codes/<platform>/`. The `custom_codes` version will take precedence.

### Q: What if I want to revert to the builtin version of a profile?
**A:** Delete the custom version from `custom_codes/<platform>/<code>.json`. The builtin version from `codes` will then be used.

### Q: Will HACS delete my `custom_codes` directory?
**A:** No. HACS only manages the `codes` directory. Your `custom_codes` directory is safe.

### Q: Can I share my custom profiles?
**A:** Yes! Custom profiles are standard SmartIR JSON files. You can:
1. Download the JSON via "Download JSON" button
2. Share the file with others
3. Submit to the SmartIR repository for inclusion

## References

- [SmartIR Documentation](https://github.com/smartHomeHub/SmartIR)
- [SmartIR HACS Integration](https://github.com/litinoveweedle/SmartIR)
- SmartIR recommends using `custom_codes` for user customizations

## Version History

- **v2.1.0**: Implemented `custom_codes` directory support
- Addresses user feedback about profiles being overwritten by HACS updates
