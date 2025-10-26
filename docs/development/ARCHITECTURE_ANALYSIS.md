# Architecture Analysis: Decoupling from Broadlink Integration Storage

**Date:** October 25, 2025  
**Status:** Proposal / Prototype Phase  
**Branch:** `feature/independent-command-storage`

## Executive Summary

This document analyzes the proposal to decouple Broadlink Manager from the Broadlink integration's `.storage` files and manage IR/RF codes independently. The goal is to eliminate storage lag issues, gain full control over command lifecycle, and simplify the codebase.

**Key Finding:** This architectural change is viable and recommended, with the main challenge being entity generation. The approach depends on whether Home Assistant's Broadlink integration accepts raw base64 data in `remote.send_command`.

---

## Current Architecture

### Dependencies on Broadlink Integration

1. **Device Discovery** - Finding Broadlink devices on the network
2. **Command Learning** - Capturing IR/RF codes (saves to `.storage/broadlink_remote_*_codes`)
3. **Command Sending** - Transmitting IR/RF codes
4. **Storage File Reading** - Syncing commands from `.storage` files
5. **Entity Generation** - Creating HA entities that reference Broadlink storage

### Current Pain Points

| Issue | Impact | Workaround |
|-------|--------|------------|
| 10+ second lag in `.storage` file updates | Poor UX, delayed feedback | Optimistic UI updates |
| Sync complexity | Code complexity, race conditions | Polling with retries |
| Dual storage systems | Data inconsistency risk | Backup/recovery system |
| Limited control | Can't add metadata, features | Store separately in metadata.json |
| External changes | Commands learned outside app | Sync system to detect changes |

### Current Data Flow

```
User Action (Learn Command)
    ↓
Broadlink Integration API
    ↓
.storage/broadlink_remote_*_codes (10+ second lag)
    ↓
Our Sync System (polling)
    ↓
metadata.json (our tracking)
    ↓
UI Update (optimistic + eventual consistency)
```

---

## Proposed Architecture

### What We'd Control

- ✅ **Command Storage** - Our own format in `devices.json`
- ✅ **Command Metadata** - Names, types, categories, tags, favorites
- ✅ **Command Lifecycle** - Full CRUD operations
- ✅ **Immediate Updates** - Zero lag, no optimistic updates needed
- ✅ **Advanced Features** - Macros, sequences, delays, versioning

### What We'd Still Need Broadlink For

- 🔌 **Device Discovery** - Finding devices on network
- 📡 **Learning Commands** - Capturing IR/RF data from remotes
- 📤 **Sending Commands** - Transmitting IR/RF codes to devices

### Proposed Data Flow

```
User Action (Learn Command)
    ↓
Broadlink Integration API (learn)
    ↓
Capture command data immediately
    ↓
Save to devices.json (our storage)
    ↓
Delete from Broadlink .storage (cleanup)
    ↓
UI Update (immediate, no lag)
```

---

## Deep Analysis

### 1. Command Learning Workflow

#### Option A: Clean Learn (Recommended)
```
1. User clicks "Learn Command"
2. Call Broadlink integration learn service
3. Wait for command to appear in .storage (poll with timeout)
4. Read command data from .storage
5. Save to our devices.json
6. Delete from Broadlink .storage
7. Update UI immediately
```

**Pros:**
- ✅ Clean separation of concerns
- ✅ No orphaned commands in Broadlink storage
- ✅ Users won't see duplicate commands

**Cons:**
- ⚠️ Extra API call to delete
- ⚠️ Slightly more complex

#### Option B: Let it Save
```
1. User clicks "Learn Command"
2. Call Broadlink integration learn service
3. Wait for command to appear in .storage
4. Read command data
5. Save to our devices.json
6. Update UI immediately
(Leave command in Broadlink storage)
```

**Pros:**
- ✅ Simpler implementation
- ✅ Fewer API calls

**Cons:**
- ❌ Orphaned commands pile up in Broadlink storage
- ❌ Confusing if users look at Broadlink integration directly
- ❌ Storage bloat over time

**Recommendation:** **Option A** - Clean separation is worth the extra API call.

#### Option C: Direct python-broadlink (Future)
```
1. User clicks "Learn Command"
2. Use python-broadlink library directly
3. Enter learning mode on device
4. Capture IR/RF data directly
5. Save to our devices.json
6. Update UI immediately
(Never touch Broadlink storage)
```

**Pros:**
- ✅ Complete independence from Broadlink integration
- ✅ No storage interaction at all
- ✅ Full control over learning process

**Cons:**
- ❌ Need to manage device connections
- ❌ Need to handle authentication
- ❌ More code to maintain
- ❌ Duplicate functionality

**Recommendation:** Consider for v3.0 after proving the concept.

---

### 2. Command Storage Format

#### Proposed Schema: Expand `devices.json`

```json
{
  "device_id_123": {
    "name": "Living Room TV",
    "friendly_name": "Living Room TV",
    "entity_id": "remote.living_room_tv",
    "device_type": "broadlink",
    "host": "192.168.1.100",
    "mac": "AA:BB:CC:DD:EE:FF",
    "model": "RM4 Pro",
    "area": "living_room",
    "commands": {
      "power": {
        "type": "ir",
        "data": "JgBQAAABKZIVEBUQFRAVEBU...",
        "learned_at": "2025-10-25T16:00:00Z",
        "learned_from": "broadlink_manager",
        "notes": "Power toggle for Samsung TV"
      },
      "volume_up": {
        "type": "ir",
        "data": "JgBQAAABKZIVEBUQFRAVEBU...",
        "learned_at": "2025-10-25T16:05:00Z",
        "learned_from": "broadlink_manager"
      }
    }
  }
}
```

#### Benefits

- ✅ **Single Source of Truth** - All device data in one place
- ✅ **Atomic Updates** - Device and commands updated together
- ✅ **Backup System** - Already in place for devices.json
- ✅ **Easy Export/Import** - Single file contains everything
- ✅ **Extensible** - Can add metadata fields easily

#### Alternative: Separate `commands.json`

```json
{
  "device_id_123": {
    "power": {
      "type": "ir",
      "data": "JgBQAAABKZIVEBUQFRAVEBU..."
    }
  }
}
```

**Pros:**
- Separation of concerns
- Smaller device file

**Cons:**
- Two files to keep in sync
- More complex backup/restore
- Harder to export/import

**Recommendation:** **Expand devices.json** - simpler and more maintainable.

---

### 3. Entity Generation Challenge

This is the **critical decision point** that determines the entire approach.

#### Current Approach (Broadlink Storage)

```yaml
button:
  - platform: template
    buttons:
      living_room_tv_power:
        friendly_name: "Living Room TV Power"
        press:
          service: remote.send_command
          target:
            entity_id: remote.living_room_rm4
          data:
            command: power  # Must exist in .storage
```

**Problem:** If commands aren't in Broadlink storage, `remote.send_command` with command name won't work.

---

#### Solution Option 1: Raw Base64 Data (NEEDS TESTING)

```yaml
button:
  - platform: template
    buttons:
      living_room_tv_power:
        friendly_name: "Living Room TV Power"
        press:
          service: remote.send_command
          target:
            entity_id: remote.living_room_rm4
          data:
            command: "b64:JgBQAAABKZIVEBUQFRAVEBU..."
```

**Analysis:**
- ✅ Simple and clean
- ✅ Still uses Broadlink integration for sending
- ✅ No custom integration needed
- ❓ **UNKNOWN:** Does Broadlink integration support this format?

**Action Required:** Test if Broadlink integration accepts raw base64 in `send_command`.

**If YES:** This is the ideal solution - simple, clean, no custom code.

**If NO:** Need to use Option 2 or 3.

---

#### Solution Option 2: REST API Entities

```yaml
button:
  - platform: rest
    name: "Living Room TV Power"
    resource: "http://localhost:8099/api/commands/send"
    method: POST
    payload: '{"device_id": "device_id_123", "command": "power"}'
    headers:
      Content-Type: "application/json"
    scan_interval: 86400  # Don't poll
```

**Backend API:**
```python
@app.route('/api/commands/send', methods=['POST'])
def send_command():
    data = request.json
    device_id = data['device_id']
    command = data['command']
    
    # Get command data from devices.json
    device = device_manager.get_device(device_id)
    command_data = device['commands'][command]['data']
    
    # Send via python-broadlink
    device = broadlink.hello(host, port)
    device.auth()
    device.send_data(base64.b64decode(command_data))
    
    return jsonify({"success": True})
```

**Pros:**
- ✅ Full control over command execution
- ✅ No dependency on Broadlink storage
- ✅ Can add features (macros, delays, sequences)
- ✅ Can add retry logic, error handling
- ✅ Can log command usage

**Cons:**
- ❌ Requires our app to be running (add-on must be started)
- ❌ More complex entity definitions
- ❌ Verbose YAML (but we generate it automatically)
- ❌ Not "native" HA entities

**Recommendation:** **Good fallback** if Option 1 doesn't work.

---

#### Solution Option 3: Custom Integration (Auto-installed)

Create a minimal custom integration that:
- Reads from our `devices.json`
- Creates button/switch entities automatically
- Calls our API to send commands

**Installation via Add-on:**
```python
# In add-on startup script
import shutil

integration_src = "/app/custom_components/broadlink_manager"
integration_dst = "/config/custom_components/broadlink_manager"

# Auto-install integration
shutil.copytree(integration_src, integration_dst, dirs_exist_ok=True)

# Notify user to restart HA
logger.info("Custom integration installed. Please restart Home Assistant.")
```

**Integration Structure:**
```
custom_components/broadlink_manager/
├── __init__.py
├── manifest.json
├── button.py
├── switch.py
└── config_flow.py (optional)
```

**Pros:**
- ✅ Best UX - entities appear automatically
- ✅ Native HA integration feel
- ✅ Can leverage HA's entity registry
- ✅ Proper state management
- ✅ Works in HA UI, automations, scripts

**Cons:**
- ⚠️ Auto-installing custom integrations is unconventional
- ⚠️ Requires HA restart after first install
- ⚠️ Integration must be maintained separately
- ⚠️ More complex to develop and test

**Recommendation:** **Best long-term solution** for v3.0, but more work upfront.

---

### 4. Command Sending

#### Current Approach
```python
# We rely on Broadlink integration to send
# Command must exist in .storage file
```

#### Proposed Approach
```python
import broadlink
import base64

def send_command(device_id, command_name):
    # Get device info
    device = device_manager.get_device(device_id)
    host = device['host']
    port = device.get('port', 80)
    
    # Get command data
    command_data = device['commands'][command_name]['data']
    
    # Connect and send
    broadlink_device = broadlink.hello(host, port)
    broadlink_device.auth()
    broadlink_device.send_data(base64.b64decode(command_data))
```

**Pros:**
- ✅ Direct control, no lag
- ✅ Can add retry logic
- ✅ Better error handling
- ✅ Can log command usage
- ✅ Can add features (macros, delays)

**Cons:**
- ⚠️ Need to maintain device connections
- ⚠️ Need to handle authentication
- ⚠️ Need to handle device offline scenarios

**Recommendation:** Implement with proper error handling and connection pooling.

---

### 5. Impact on SmartIR Integration

**Current SmartIR Approach:**
- Stores commands in JSON files (`/config/smartir/codes/`)
- Generates YAML entities using SmartIR platforms
- SmartIR integration handles sending via Broadlink

**With Proposed Changes:**
- SmartIR would continue working as-is (uses its own storage)
- Our Broadlink devices would work differently
- No conflict or interference

**Analysis:** ✅ SmartIR integration is separate and wouldn't be affected. This is good.

---

## Comprehensive Evaluation

### Pros of Decoupling

#### Performance
- ✅ **Zero lag** - Immediate UI updates
- ✅ **No optimistic updates needed** - Actual state is immediate
- ✅ **No sync complexity** - No polling, no retries

#### Control
- ✅ **Full command lifecycle management** - Create, read, update, delete
- ✅ **Custom metadata** - Tags, categories, favorites, notes
- ✅ **Advanced features** - Macros, sequences, delays, conditions
- ✅ **Better backup/restore** - Single source of truth

#### Reliability
- ✅ **No dependency on Broadlink storage timing** - We control when data is saved
- ✅ **Atomic operations** - Device and commands updated together
- ✅ **Better error handling** - We control the entire flow

#### Features
- ✅ **Command versioning** - Track changes over time
- ✅ **Command testing/validation** - Test before saving
- ✅ **Import/export** - Easy data portability
- ✅ **Bulk operations** - Update multiple commands at once
- ✅ **Command analytics** - Track usage, popular commands

### Cons of Decoupling

#### Entity Generation Complexity
- ❌ Can't use simple `remote.send_command` with names (unless raw base64 works)
- ❌ Need REST API or custom integration
- ❌ More complex YAML generation

#### Broadlink Integration Dependency
- ⚠️ Still need it for learning/sending (unless we go full python-broadlink)
- ⚠️ Commands pile up in .storage (if we don't delete)
- ⚠️ Users might be confused by orphaned commands

#### Migration
- ❌ Need to migrate existing users
- ❌ Breaking change for existing setups
- ❌ Documentation updates required

#### Maintenance
- ⚠️ Direct device communication code
- ⚠️ Connection management
- ⚠️ Authentication handling
- ⚠️ Error scenarios (device offline, network issues)

---

## Recommended Implementation Path

### Phase 1: Proof of Concept (CRITICAL)

**Test if Broadlink integration accepts raw base64 data in `send_command`**

Create test script: `tests/manual/test_raw_base64_send.py`

```python
# Test if we can send raw base64 data via Broadlink integration
# If YES: Simple path forward
# If NO: Need REST API entities or custom integration
```

**Outcomes:**
- ✅ **If raw base64 works:** Use Option 1 (template entities with embedded data)
- ❌ **If raw base64 doesn't work:** Use Option 2 (REST API entities)

---

### Phase 2: Implementation Strategy

#### If Raw Base64 Works (Option 1)

```yaml
# Generated entity - simple and clean
button:
  - platform: template
    buttons:
      living_room_tv_power:
        friendly_name: "Living Room TV Power"
        press:
          service: remote.send_command
          target:
            entity_id: remote.living_room_rm4
          data:
            command: "b64:JgBQAAABKZIVEBUQFRAVEBU..."
```

**Implementation Steps:**
1. Expand `devices.json` schema to store command data
2. Update learning workflow to save to our storage
3. Delete commands from Broadlink storage after learning
4. Update entity generator to embed base64 data
5. Test and validate

**Timeline:** 2-3 days

---

#### If Raw Base64 Doesn't Work (Option 2)

```yaml
# Generated entity - REST API
button:
  - platform: rest
    name: "Living Room TV Power"
    resource: "http://localhost:8099/api/commands/send"
    method: POST
    payload: '{"device_id": "abc123", "command": "power"}'
    scan_interval: 86400
```

**Implementation Steps:**
1. Expand `devices.json` schema to store command data
2. Update learning workflow to save to our storage
3. Implement `/api/commands/send` endpoint with python-broadlink
4. Update entity generator to create REST entities
5. Add connection management and error handling
6. Test and validate

**Timeline:** 4-5 days

---

### Phase 3: Learning Workflow

**Recommended Flow (Clean Learn):**

```python
def learn_command(device_id, command_name):
    # 1. Call Broadlink integration learn service
    hass.services.call('remote', 'learn_command', {
        'entity_id': f'remote.{device_entity_id}',
        'command': command_name
    })
    
    # 2. Poll .storage file for new command (with timeout)
    command_data = wait_for_command_in_storage(device_id, command_name, timeout=30)
    
    # 3. Save to our devices.json
    device = device_manager.get_device(device_id)
    device['commands'][command_name] = {
        'type': detect_command_type(command_data),
        'data': command_data,
        'learned_at': datetime.now().isoformat(),
        'learned_from': 'broadlink_manager'
    }
    device_manager.update_device(device_id, device)
    
    # 4. Delete from Broadlink .storage
    delete_command_from_broadlink_storage(device_id, command_name)
    
    # 5. Return success immediately
    return {'success': True, 'command': command_name}
```

**Benefits:**
- ✅ Clean separation
- ✅ No orphaned commands
- ✅ Immediate UI update
- ✅ Full control

---

### Phase 4: Testing & Validation

**Test Cases:**
1. ✅ Learn IR command
2. ✅ Learn RF command
3. ✅ Send command via entity
4. ✅ Delete command
5. ✅ Rename command
6. ✅ Export/import device
7. ✅ Backup/restore
8. ✅ Migration from old format
9. ✅ Device offline scenarios
10. ✅ Network error handling

---

### Phase 5: Migration Path

**Backward Compatibility:**
1. Detect old vs new storage format
2. Auto-migrate on first load
3. Keep backup of old format
4. Deprecation warnings in UI

**Migration Script:**
```python
def migrate_to_independent_storage():
    # Read commands from .storage files
    # Save to devices.json with new schema
    # Create backup of old data
    # Log migration results
```

---

## Entity Generation Comparison

### Current (Broadlink Storage)
```yaml
# Simple but laggy
button:
  - platform: template
    buttons:
      living_room_tv_power:
        friendly_name: "Living Room TV Power"
        press:
          service: remote.send_command
          target:
            entity_id: remote.living_room_rm4
          data:
            command: power  # Must exist in .storage
```

**Pros:** Simple, native HA
**Cons:** Requires Broadlink storage, 10+ second lag

---

### Proposed Option 1 (Raw Base64)
```yaml
# Simple and immediate
button:
  - platform: template
    buttons:
      living_room_tv_power:
        friendly_name: "Living Room TV Power"
        press:
          service: remote.send_command
          target:
            entity_id: remote.living_room_rm4
          data:
            command: "b64:JgBQAAABKZIVEBUQFRAVEBU..."
```

**Pros:** Simple, immediate, no lag, native HA
**Cons:** Unknown if Broadlink integration supports this

---

### Proposed Option 2 (REST API)
```yaml
# More complex but full control
button:
  - platform: rest
    name: "Living Room TV Power"
    resource: "http://localhost:8099/api/commands/send"
    method: POST
    payload: '{"device_id": "abc123", "command": "power"}'
    headers:
      Content-Type: "application/json"
    scan_interval: 86400
```

**Pros:** Full control, immediate, advanced features
**Cons:** Verbose, requires app running, not native HA

---

### Proposed Option 3 (Custom Integration)
```yaml
# No YAML needed - entities appear automatically
# Integration reads devices.json and creates entities
```

**Pros:** Best UX, native HA, automatic
**Cons:** More complex, requires HA restart, maintenance

---

## Decision Matrix

| Criteria | Option 1 (Raw) | Option 2 (REST) | Option 3 (Integration) |
|----------|----------------|-----------------|------------------------|
| **Simplicity** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **UX** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Control** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Maintenance** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Native HA Feel** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Advanced Features** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Feasibility** | ❓ Unknown | ✅ Proven | ⚠️ Unconventional |

---

## Final Recommendation

### Short Term (v2.1 - Current Branch)

1. **✅ Test raw base64 in Broadlink `send_command`** (CRITICAL FIRST STEP)
2. **If raw works:** Implement Option 1 (simple, clean, fast)
3. **If raw doesn't work:** Implement Option 2 (REST API entities)

**Timeline:** 1 week for prototype

---

### Long Term (v3.0)

1. **Create lightweight custom integration** (Option 3)
   - Auto-installed by add-on
   - Reads `devices.json`
   - Creates native HA entities
   - Calls our API for command sending
2. **Full decoupling from Broadlink storage**
3. **Optional: Direct python-broadlink usage** (complete independence)

**Timeline:** 2-3 weeks for full implementation

---

### Migration Path

1. **v2.1:** Prototype with new storage (backward compatible)
2. **v2.2:** Stable release with migration tool
3. **v2.3:** Deprecation warnings for old format
4. **v3.0:** Remove old format support, custom integration

---

## Conclusion

**Your instinct is correct** - decoupling from Broadlink storage would:
- ✅ **Eliminate lag issues completely**
- ✅ **Give us full control over command lifecycle**
- ✅ **Enable advanced features** (macros, sequences, analytics)
- ✅ **Simplify the codebase** (no optimistic updates, no sync complexity)

**The main challenge** is entity generation, which depends on testing raw base64 support.

**Next Steps:**
1. ✅ Test raw base64 in Broadlink integration (`tests/manual/test_raw_base64_send.py`)
2. Based on results, implement Option 1 or Option 2
3. Expand `devices.json` schema
4. Update learning workflow
5. Update entity generator
6. Test thoroughly
7. Document migration path

**Remove all the optimistic update code** - This is a major benefit. Clean, predictable, immediate feedback.

---

## References

- [Broadlink Integration Documentation](https://www.home-assistant.io/integrations/broadlink/)
- [python-broadlink Library](https://github.com/mjg59/python-broadlink)
- [Home Assistant Template Button](https://www.home-assistant.io/integrations/button.template/)
- [Home Assistant RESTful Button](https://www.home-assistant.io/integrations/button.rest/)
- [Custom Integration Development](https://developers.home-assistant.io/docs/creating_integration_manifest)

---

**Document Version:** 1.0  
**Last Updated:** October 25, 2025  
**Author:** Broadlink Manager Development Team
