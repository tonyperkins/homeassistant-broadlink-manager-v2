# Phase 1: Backend Foundation - COMPLETE ✅

**Date:** October 25, 2025  
**Branch:** `feature/independent-command-storage`  
**Status:** ✅ Backend Complete, Ready for Frontend

---

## What We Built

### 1. BroadlinkLearner (`app/broadlink_learner.py`)
Direct learning from Broadlink devices using python-broadlink.

**Features:**
- ✅ IR learning (1-step process)
- ✅ RF learning (2-step process with frequency sweep)
- ✅ Direct command testing
- ✅ StorageError/ReadError handling (like HA)
- ✅ 30-second timeout with 1-second polling
- ✅ Returns base64 encoded data
- ✅ RF frequency detection

**Methods:**
```python
learner = BroadlinkLearner(host, mac_bytes, device_type)
learner.authenticate()
base64_data = learner.learn_ir_command(timeout=30)
(base64_data, frequency) = learner.learn_rf_command(timeout=30)
success = learner.test_command(base64_data)
```

### 2. BroadlinkDeviceManager (`app/broadlink_device_manager.py`)
Device discovery and connection management.

**Features:**
- ✅ Network device discovery
- ✅ HA entity info retrieval
- ✅ Connection info extraction (host, MAC, type)
- ✅ Device matching (discovered ↔ HA entity)

**Methods:**
```python
manager = BroadlinkDeviceManager(ha_url, ha_token)
devices = manager.discover_devices(timeout=5)
connection_info = manager.get_device_connection_info(entity_id)
entity_info = manager.get_ha_entity_info(entity_id)
```

### 3. Enhanced DeviceManager (`app/device_manager.py`)
Extended with new command schema support.

**New Methods:**
```python
# Add learned command with base64 data
add_learned_command(device_id, command_name, command_data, command_type, frequency=None)

# Update test status
update_command_test_status(device_id, command_name, test_method)

# Get command data
get_command_data(device_id, command_name) -> base64_string

# Update connection info
update_device_connection_info(device_id, connection_info)
```

**New Schema:**
```json
{
  "device_123": {
    "name": "Living Room TV",
    "entity_id": "remote.living_room_rm4_pro",
    "connection": {
      "host": "192.168.1.100",
      "mac": "e8:70:72:3f:13:a5",
      "type": 10119,
      "type_hex": "0x2787",
      "model": "RM4 pro"
    },
    "commands": {
      "power": {
        "name": "power",
        "type": "ir",
        "data": "scBIAdieBgALFgsXFwsXDAoXFwsXCwoXGAoL...",
        "learned_at": "2025-10-25T12:00:00Z",
        "tested": true,
        "test_method": "direct",
        "tested_at": "2025-10-25T12:05:00Z"
      }
    }
  }
}
```

### 4. API Endpoints (`app/api/commands.py`)

#### POST `/api/commands/learn`
Learn a command directly from device.

**Request:**
```json
{
  "device_id": "living_room_tv",
  "entity_id": "remote.living_room_rm4_pro",
  "command_name": "power",
  "command_type": "ir"
}
```

**Response:**
```json
{
  "success": true,
  "command_name": "power",
  "command_type": "ir",
  "data": "scBIAdieBgALFgsXFwsXDAoXFwsXCwoXGAoL...",
  "data_length": 444,
  "frequency": 433.92
}
```

#### POST `/api/commands/test/direct`
Test command via direct connection.

**Request:**
```json
{
  "device_id": "living_room_tv",
  "entity_id": "remote.living_room_rm4_pro",
  "command_name": "power"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command sent successfully via direct connection"
}
```

#### POST `/api/commands/test/ha`
Test command via HA `remote.send_command`.

**Request:**
```json
{
  "device_id": "living_room_tv",
  "entity_id": "remote.living_room_rm4_pro",
  "command_name": "power"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Command sent successfully via Home Assistant"
}
```

---

## How It Works

### IR Learning Flow
```
1. Frontend calls POST /api/commands/learn (type=ir)
2. Backend gets device connection info from HA entity
3. Backend creates BroadlinkLearner, authenticates
4. Backend calls device.enter_learning()
5. Backend polls device.check_data() (catches StorageError)
6. User presses remote button
7. Device captures signal, returns packet
8. Backend converts to base64
9. Backend saves to devices.json with metadata
10. Backend returns base64 to frontend
```

### RF Learning Flow
```
1. Frontend calls POST /api/commands/learn (type=rf)
2. Backend gets device connection info from HA entity
3. Backend creates BroadlinkLearner, authenticates
4. Backend calls device.sweep_frequency()
5. Backend polls device.check_frequency()
6. User holds remote button for 2-3 seconds
7. Device locks frequency
8. Backend sleeps 1 second (let user release)
9. Backend calls device.find_rf_packet()
10. Backend polls device.check_data() (catches StorageError)
11. User presses remote button again
12. Device captures signal, returns packet
13. Backend converts to base64
14. Backend saves to devices.json with metadata
15. Backend returns base64 + frequency to frontend
```

### Testing Flow (Direct)
```
1. Frontend calls POST /api/commands/test/direct
2. Backend gets command data from devices.json
3. Backend gets device connection info
4. Backend creates BroadlinkLearner, authenticates
5. Backend calls device.send_data(packet)
6. Backend updates test status in devices.json
7. Backend returns success
```

### Testing Flow (HA)
```
1. Frontend calls POST /api/commands/test/ha
2. Backend gets command data from devices.json
3. Backend calls HA API: remote.send_command
4. Backend updates test status in devices.json
5. Backend returns success
```

---

## Key Implementation Details

### StorageError Handling
Just like Home Assistant, we catch and ignore `StorageError` and `ReadError`:

```python
try:
    packet = device.check_data()
except (broadlink.exceptions.ReadError, broadlink.exceptions.StorageError):
    # Ignore errors from old commands in buffer
    continue
```

This allows learning to work even when device buffer is full.

### RF Frequency Detection
RF learning returns a tuple:

```python
is_found, frequency = device.check_frequency()
if is_found:
    print(f"Locked at {frequency} MHz")
```

### Connection Info Storage
We store connection info in `devices.json` for future direct operations:

```json
"connection": {
  "host": "192.168.1.100",
  "mac": "e8:70:72:3f:13:a5",
  "type": 10119,
  "type_hex": "0x2787",
  "model": "RM4 pro"
}
```

### Test Status Tracking
Commands track whether they've been tested and how:

```json
"tested": true,
"test_method": "direct",  // or "ha"
"tested_at": "2025-10-25T12:05:00Z"
```

---

## What's Next: Phase 2 (Frontend)

### Components to Create/Update

1. **CommandLearner.vue** - Learning dialog with:
   - IR/RF type selection
   - Real-time status updates
   - Countdown timer
   - Test options after learning
   - Error handling

2. **CommandTester.vue** - Testing dialog with:
   - Direct test button
   - HA test button
   - Skip test option
   - Success/failure feedback

3. **DeviceCard.vue** - Update to show:
   - Command test status badges
   - Test buttons per command
   - Connection info

4. **DeviceForm.vue** - Auto-populate connection info

### User Flow

```
1. User clicks "Learn Command" on device card
2. Dialog opens: "Command Name?" → "power"
3. Dialog: "Type?" → IR or RF
4. Dialog: "Point remote and press button" (IR)
   OR "Press and hold for 2-3 seconds" (RF step 1)
   OR "Press button again" (RF step 2)
5. Progress: "Learning... (5/30s)"
6. Success: "✅ Command learned!"
7. Dialog: "Test command?"
   - 🔧 Test Direct
   - 🏠 Test via HA
   - ⏭️ Skip Testing
8. User clicks test method
9. Command sent, device responds
10. Dialog: "Did it work?" → Yes/No
11. If yes: Mark as tested, close
12. If no: Try again or skip
```

---

## Testing Checklist

- [ ] IR learning with empty buffer
- [ ] IR learning with full buffer
- [ ] RF learning with empty buffer
- [ ] RF learning with full buffer
- [ ] Direct testing
- [ ] HA testing
- [ ] Connection info storage
- [ ] Test status updates
- [ ] Timeout handling
- [ ] Error handling

---

## Files Created

- ✅ `app/broadlink_learner.py` - Direct learning logic
- ✅ `app/broadlink_device_manager.py` - Connection management
- ✅ `docs/DIRECT_LEARNING_IMPLEMENTATION.md` - Implementation guide
- ✅ `docs/PHASE1_COMPLETE.md` - This document

## Files Modified

- ✅ `app/device_manager.py` - Enhanced command methods
- ✅ `app/api/commands.py` - New learning/testing endpoints

---

**Status:** Phase 1 Complete! Ready for Phase 2 (Frontend) 🚀
