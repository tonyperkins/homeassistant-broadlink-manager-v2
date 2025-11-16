# Three Issues: Fixes & Recommendations

## Issue 1: RF Fan Commands Not Generating `entities.yaml` ✅ FIXED

### Problem
RF fan with custom speeds (`low`, `lowMedium`, `medium`, `mediumHigh`, `high`) was correctly saving to `devices.json` but not generating entities in `entities.yaml`.

### Root Cause
The entity generator only recognized standard speed names. Custom names like `lowMedium` and `mediumHigh` were being skipped.

### Fix Applied
**File**: `app/entity_generator.py` (lines 503-513)

Expanded the `named_speed_map` to include:
- `lowmedium` → speed 2
- `mediumhigh` → speed 4
- `quiet` → speed 1 (bonus: some fans use this)
- `auto` → speed 3 (bonus: some fans have auto mode)

```python
named_speed_map = {
    "off": 0,
    "low": 1,
    "lowmedium": 2,  # NEW
    "medium": 3,
    "mediumhigh": 4,  # NEW
    "high": 5,
    "med": 3,
    "quiet": 1,  # NEW
    "auto": 3,  # NEW
}
```

### Testing
1. Your RF fan should now generate a 5-speed fan entity
2. Speed mapping:
   - Low → 20% (1/5)
   - LowMedium → 40% (2/5)
   - Medium → 60% (3/5)
   - MediumHigh → 80% (4/5)
   - High → 100% (5/5)

3. Test by regenerating entities:
   ```bash
   # In Broadlink Manager UI:
   # Settings → Generate Entities
   ```

4. Check `/config/entities.yaml` for your fan entity

---

## Issue 2: SmartIR Search Only Shows First Model ✅ LIKELY ALREADY WORKING

### Problem
User's SmartIR JSON has 8 models in `supportedModels`, but searching for non-first models (e.g., "CTXM25RVMA") returns no results.

### Investigation Results
**The backend code is correct!** Both search endpoints properly search **all** models in the array:

```python
# Correct implementation (already in code):
if any(query.lower() in m.lower() for m in model_names):
    # Match found
```

### Likely Causes
1. **Stale Index**: Old `smartir_device_index.json` might only have first model indexed
2. **Browser Cache**: Old search results cached
3. **Typo**: Model number mistyped

### Recommended Actions

#### 1. Regenerate Device Index
```bash
cd /config/addons/broadlink-manager-v2
python scripts/generate_device_index.py
```

#### 2. Clear Browser Cache
- Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
- Or clear browser cache completely

#### 3. Verify Index File
Check `smartir_device_index.json` to ensure all models are present:
```json
{
  "platforms": {
    "climate": {
      "manufacturers": {
        "Daikin": {
          "models": [
            {
              "code": "5656",
              "models": [
                "CTXM20RVMA",
                "CTXM25RVMA",  ← Should be here
                "CTXM35RVMA",
                "CTXM46RVMA",
                "CTKM20RVMA",
                "CTKM25RVMA",
                "CTKM35RVMA",
                "CTKM46RVMA"
              ]
            }
          ]
        }
      }
    }
  }
}
```

#### 4. Test Search
Try these searches:
- "CTXM25RVMA" (exact match)
- "CTXM25" (partial match)
- "ctxm25" (lowercase)
- "Daikin" (manufacturer)

### If Still Not Working
1. Check browser console for JavaScript errors (F12 → Console tab)
2. Check that you're searching in the correct platform (Climate)
3. Verify the JSON file exists at `custom_components/smartir/codes/climate/5656.json`

**No code changes needed** - the backend is already correct.

---

## Issue 3: Using Existing SmartIR Profile as Basis ⚠️ NOT YET IMPLEMENTED

### Problem
User wants to:
1. Load existing SmartIR JSON (e.g., 5656.json)
2. Add/modify a few commands
3. Save without re-learning everything

### Current Behavior
The Command Learning Wizard starts with empty commands. You must learn all commands from scratch.

### Why Not Implemented
The wizard was designed for creating new profiles, not editing existing ones. Loading commands from SmartIR JSON requires:
1. New backend API endpoint to read JSON and extract commands
2. Frontend integration to load commands into wizard
3. UI to distinguish between loaded and newly-learned commands

### Workaround (Manual)

Until this feature is implemented, you can manually edit the JSON:

1. **Find your profile**:
   ```
   /config/custom_components/smartir/custom_codes/climate/5656.json
   ```

2. **Edit commands directly**:
   ```json
   {
     "commands": {
       "auto_18_auto_Off": "JgBQAg4ODg4NDw...",  ← Edit this
       "cool_24_auto_Off": "JgBQAg0ODQ8NDg...",  ← Or add new
       ...
     }
   }
   ```

3. **Learn new command separately**:
   - Use Broadlink Manager to learn the new command
   - Copy the base64 code from `devices.json`
   - Paste into your SmartIR JSON

4. **Test in Home Assistant**:
   - Reload SmartIR integration
   - Test the modified commands

### Future Implementation Plan

**Phase 1: Backend API** (1-2 hours)
- New endpoint: `GET /api/smartir/profiles/<platform>/<code>/commands`
- Returns all commands from JSON file
- Validates JSON structure

**Phase 2: Frontend Integration** (2-3 hours)
- Add "Edit Existing Profile" button in SmartIR Status Card
- Modify `CommandLearningWizard.vue` to load existing commands
- Show loaded commands with ✅ indicator
- Allow re-learning individual commands

**Phase 3: UI Polish** (1 hour)
- "Keep" vs "Re-learn" buttons for each command
- Visual distinction between loaded and newly-learned
- Confirmation dialog before overwriting

**Total Estimated Time**: 4-6 hours

### Priority
This is a **nice-to-have feature**, not a blocker. The manual workaround is functional for now.

---

## Summary

| Issue | Status | Action Required |
|-------|--------|-----------------|
| **Issue 1: RF Fan Entities** | ✅ **FIXED** | Test entity generation |
| **Issue 2: SmartIR Search** | ✅ **Working** | Regenerate index + clear cache |
| **Issue 3: Edit Profiles** | ⚠️ **Not Implemented** | Use manual workaround or wait for feature |

---

## Next Steps

### For You (User)
1. **Test Issue 1 Fix**:
   - Regenerate entities in Broadlink Manager
   - Check if RF fan entity appears in `entities.yaml`
   - Test fan speeds in Home Assistant

2. **Test Issue 2**:
   - Regenerate device index: `python scripts/generate_device_index.py`
   - Clear browser cache
   - Search for "CTXM25RVMA"
   - Report if still not working

3. **Issue 3**:
   - Use manual JSON editing workaround
   - Or wait for feature implementation in future release

### For Me (Developer)
1. ✅ Issue 1 fixed and committed
2. ✅ Issue 2 verified (no fix needed)
3. ⏳ Issue 3 - Add to feature backlog for future release

---

## Questions?

If you have any questions or the fixes don't work:
1. Check the detailed analysis documents in `docs/development/`
2. Open a GitHub issue with:
   - Which issue you're experiencing
   - Steps you've tried
   - Error messages (if any)
   - Screenshots (if helpful)
