# Analysis: Three SmartIR & RF Fan Issues

## Issue 1: RF Fan Commands Not Generating `entities.yaml`

### Problem
User has RF fan with custom speeds (`low`, `lowMedium`, `medium`, `mediumHigh`, `high`) saved correctly in `devices.json`, but no entities are being generated in `entities.yaml`.

### Root Cause
The `_generate_fan()` function in `app/entity_generator.py` (lines 500-531) only recognizes specific speed command patterns:

**Recognized patterns:**
- `speed_N` (where N is a digit: `speed_1`, `speed_2`, `speed_3`)
- `fan_speed_N` (same as above)
- Named speeds with mapping: `low=1`, `medium=2`, `med=2`, `high=3`, `off=0`

**NOT recognized:**
- `lowMedium` - No mapping exists
- `mediumHigh` - No mapping exists

```python
# Current code (lines 503-509):
named_speed_map = {
    "low": 1,
    "medium": 2,
    "med": 2,
    "high": 3,
    "off": 0,  # Some fans have speed_off
}
```

When the generator encounters `speed_lowMedium` or `speed_mediumHigh`, it logs:
```
Skipping unknown speed command: speed_lowMedium
```

If **all** speed commands are skipped, `speed_count` becomes 0, and the function returns `None` (line 539), preventing entity generation.

### Solution
**Option 1: Expand named_speed_map (Recommended)**
```python
named_speed_map = {
    "off": 0,
    "low": 1,
    "lowmedium": 2,  # Add this
    "medium": 3,
    "mediumhigh": 4,  # Add this
    "high": 5,
    "med": 3,  # Keep for compatibility
}
```

**Option 2: Auto-assign sequential numbers**
```python
# If speed name is unknown, assign next available number
if speed_id.lower() not in named_speed_map:
    # Auto-assign next number
    existing_nums = [int(k.split('_')[1]) for k in speed_commands.keys()]
    next_num = max(existing_nums, default=0) + 1
    speed_num = str(next_num)
```

**Option 3: Use original command names as-is**
Store speeds with their original names (`lowMedium`, `mediumHigh`) and generate percentage ranges dynamically.

---

## Issue 2: SmartIR Search Only Shows First `supportedModel`

### Problem
User's SmartIR JSON has 8 models in `supportedModels`:
```json
"supportedModels": [
  "CTXM20RVMA",
  "CTXM25RVMA",  ← Searching for this returns no results
  "CTXM35RVMA",
  ...
]
```

Searching for "CTXM25RVMA" returns no results, but "CTXM20RVMA" (first model) works.

### Root Cause
The `generate_device_index.py` script (line 118) only indexes the **first** model:

```python
print(f"  ✓ {code}: {manufacturer} - {supported_models[0] if supported_models else 'Unknown'}")
```

While the script stores **all** models in the index (line 111):
```python
device_entry = {
    "code": code,
    "models": supported_models,  # ← All models stored
    "url": f"{GITHUB_RAW_BASE}/codes/{platform}/{code}.json"
}
```

The problem is likely in the **search logic** (frontend or backend), not the index generation.

### Investigation Needed
Need to check:
1. **Frontend search** (`SmartIRProfileBrowser.vue`) - How does it filter by model?
2. **Backend search** (`app/api/smartir.py` - `/profiles/search` endpoint) - Does it search all models in the array?

### Likely Issue
The search is probably doing:
```python
# WRONG - only checks first model
if query.lower() in profile['models'][0].lower():
    results.append(profile)
```

Instead of:
```python
# CORRECT - checks all models
if any(query.lower() in model.lower() for model in profile['models']):
    results.append(profile)
```

---

## Issue 3: Using Existing SmartIR Profile as Basis for Editing

### Problem
User wants to:
1. Load an existing SmartIR JSON file (e.g., their custom `5656.json`)
2. Add/modify a few commands
3. Save back without re-learning everything from scratch

### Current Behavior
The `CommandLearningWizard.vue` component has an intentionally empty `loadExistingCommands()` function (lines 576-581):

```javascript
async function loadExistingCommands() {
  // Note: This function is intentionally left empty for SmartIR devices
  // SmartIR commands are managed through the SmartIR JSON files, not Broadlink storage
  // The wizard will start with empty commands and users learn them one by one
  
  console.log('SmartIR device - commands will be loaded from SmartIR JSON file, not Broadlink storage')
}
```

**Why it's empty:**
- SmartIR commands are stored in JSON files, not Broadlink `.storage` files
- The wizard was designed for learning new profiles from scratch
- No mechanism exists to load commands from an existing SmartIR JSON

### Solution Architecture

**Backend API Endpoint** (new):
```python
# app/api/smartir.py
@smartir_bp.route('/profiles/<platform>/<code>/commands', methods=['GET'])
def get_profile_commands(platform: str, code: str):
    """
    Load commands from an existing SmartIR JSON file
    Returns: {
        "success": true,
        "commands": {
            "auto_18_auto_Off": "JgBQAg4ODg4NDw...",
            "cool_24_auto_Off": "JgBQAg0ODQ8NDg...",
            ...
        },
        "profile_data": { ... }  # Full JSON for reference
    }
    """
```

**Frontend Integration**:
1. **SmartIRProfileBuilder.vue** - Add "Edit Existing" button/flow
2. **CommandLearningWizard.vue** - Implement `loadExistingCommands()`:
   ```javascript
   async function loadExistingCommands() {
     if (props.editMode && props.existingCode) {
       const response = await axios.get(
         `/api/smartir/profiles/${props.platform}/${props.existingCode}/commands`
       )
       commands.value = response.data.commands
       hasLearnedAny.value = true
     }
   }
   ```

**User Workflow**:
1. User clicks "Edit" on existing profile (5656.json)
2. Profile Builder loads with existing commands pre-populated
3. User can:
   - Keep existing commands (shown as learned)
   - Re-learn specific commands (replace existing)
   - Add new commands (e.g., new preset modes)
4. Save back to same code or new code

**UI Indicators**:
- Existing commands shown with ✅ checkmark
- "Re-learn" button to replace
- "Keep" button to preserve
- Clear visual distinction between learned and loaded commands

---

## Priority & Impact

### Issue 1: RF Fan Commands (HIGH PRIORITY)
- **Impact**: Complete feature failure - no entities generated
- **Users Affected**: Anyone using RF fans with custom speed names
- **Fix Complexity**: Low (add mappings or auto-assignment)
- **Estimated Time**: 30 minutes

### Issue 2: SmartIR Search (MEDIUM PRIORITY)
- **Impact**: Usability issue - can't find profiles by non-first model
- **Users Affected**: Anyone with multi-model profiles
- **Fix Complexity**: Low (fix search logic)
- **Estimated Time**: 1 hour (need to find search code first)

### Issue 3: Edit Existing Profiles (LOW PRIORITY - FEATURE REQUEST)
- **Impact**: Usability/convenience - not a blocker
- **Users Affected**: Power users wanting to modify existing profiles
- **Fix Complexity**: Medium (new API endpoint + frontend integration)
- **Estimated Time**: 3-4 hours

---

## Recommended Fix Order

1. **Issue 1** - Critical bug, quick fix
2. **Issue 2** - Important usability, quick fix
3. **Issue 3** - Nice-to-have feature, more complex

---

## Testing Requirements

### Issue 1 Testing:
1. Create RF fan device with commands: `low`, `lowMedium`, `medium`, `mediumHigh`, `high`
2. Generate entities
3. Verify `entities.yaml` created with 5-speed fan
4. Test in Home Assistant UI

### Issue 2 Testing:
1. Create SmartIR profile with multiple `supportedModels`
2. Search for non-first model
3. Verify profile appears in results
4. Test with all models in array

### Issue 3 Testing:
1. Load existing SmartIR profile (e.g., 5656.json)
2. Verify all commands loaded
3. Re-learn one command
4. Add new command
5. Save and verify JSON updated correctly
6. Test in Home Assistant

---

## Files to Modify

### Issue 1:
- `app/entity_generator.py` (lines 503-531)

### Issue 2:
- Find search logic (likely `app/api/smartir.py` or `frontend/src/components/smartir/SmartIRProfileBrowser.vue`)

### Issue 3:
- `app/api/smartir.py` (new endpoint)
- `frontend/src/components/smartir/CommandLearningWizard.vue` (implement loadExistingCommands)
- `frontend/src/components/smartir/SmartIRProfileBuilder.vue` (add edit mode)
