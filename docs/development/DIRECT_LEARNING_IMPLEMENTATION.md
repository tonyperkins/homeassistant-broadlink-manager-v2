# Direct Learning Implementation Guide

**Date:** October 25, 2025  
**Status:** ✅ Tested and Confirmed Working  
**Branch:** `feature/independent-command-storage`

## Executive Summary

We have successfully tested and confirmed that **direct python-broadlink learning works** without Home Assistant's Broadlink integration. This allows us to implement the hybrid approach:

- **Learning:** Direct python-broadlink (instant, full control)
- **Sending:** HA Broadlink integration (reliable, maintained)
- **Storage:** Our `devices.json` (no `.storage` lag)

---

## Key Findings

### 1. Raw Base64 Works ✅

**Test:** `test_raw_base64_send.py`  
**Result:** All three formats work:
- `b64:` prefix ✅
- No prefix (raw base64) ✅
- `base64:` prefix ✅

**Conclusion:** We can store commands in `devices.json` and send them via HA's `remote.send_command` service with embedded base64 data.

### 2. Direct Learning Works ✅

**Test:** `test_direct_learning.py`  
**Result:** Both IR and RF learning work when properly implemented.

**Critical Fix:** Must catch `StorageError` and `ReadError` exceptions and continue looping (just like HA does).

### 3. Device Buffer Management

**Issue:** Device internal buffer can fill up with unread commands from previous learning sessions.

**Solution:** Catch `StorageError`/`ReadError` and continue - don't try to clear buffer, just ignore errors from old commands.

**Why It Works:** New commands are captured successfully even when old commands cause errors. The errors are from trying to read OLD commands, not from learning NEW ones.

---

## Implementation Details

### IR Learning (1-Step Process)

```python
import broadlink
import base64
import time

def learn_ir_command(device, timeout=30):
    """Learn an IR command using direct python-broadlink"""
    
    # Step 1: Enter learning mode
    device.enter_learning()
    
    # Step 2: Poll for data (30 second timeout)
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)  # Sleep 1 second between checks
        
        try:
            packet = device.check_data()
        except (broadlink.exceptions.ReadError, broadlink.exceptions.StorageError):
            # Ignore errors from old commands in buffer
            continue
        
        if packet:
            # Got the command!
            return base64.b64encode(packet).decode('utf-8')
    
    # Timeout
    raise TimeoutError("No IR signal detected within 30 seconds")
```

### RF Learning (2-Step Process)

```python
def learn_rf_command(device, timeout=30):
    """Learn an RF command using direct python-broadlink"""
    
    # Step 1: Sweep frequency
    device.sweep_frequency()
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)
        
        is_found, frequency = device.check_frequency()
        if is_found:
            break
    else:
        device.cancel_sweep_frequency()
        raise TimeoutError("No RF frequency found within 30 seconds")
    
    # Sleep 1 second (let user release button)
    time.sleep(1)
    
    # Step 2: Capture RF packet
    device.find_rf_packet()
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(1)
        
        try:
            packet = device.check_data()
        except (broadlink.exceptions.ReadError, broadlink.exceptions.StorageError):
            # Ignore errors from old commands in buffer
            continue
        
        if packet:
            # Got the command!
            return base64.b64encode(packet).decode('utf-8')
    
    # Timeout
    raise TimeoutError("No RF signal detected within 30 seconds")
```

---

## User Experience Flow

### IR Learning
```
1. User clicks "Learn IR Command"
2. Dialog shows: "Point remote at device and press button"
3. Backend: enter_learning() → poll check_data()
4. Dialog shows: "Learning... (3/30s)"
5. User presses button
6. Backend: Got packet! → return base64
7. Dialog shows: "✅ Command learned!"
8. Save to devices.json immediately
```

### RF Learning
```
1. User clicks "Learn RF Command"
2. Dialog shows: "Press and HOLD button for 2-3 seconds"
3. Backend: sweep_frequency() → poll check_frequency()
4. Dialog shows: "Scanning frequency... (5/30s)"
5. Backend: Frequency locked! → sleep(1)
6. Dialog shows: "Press button again (short press)"
7. Backend: find_rf_packet() → poll check_data()
8. Dialog shows: "Capturing... (2/30s)"
9. User presses button
10. Backend: Got packet! → return base64
11. Dialog shows: "✅ Command learned!"
12. Save to devices.json immediately
```

---

## API Endpoint Design

### POST /api/commands/learn

**Request:**
```json
{
  "device_id": "device_123",
  "entity_id": "remote.tony_s_office_rm4_pro",
  "command_name": "power",
  "command_type": "ir"  // or "rf"
}
```

**Response (Success):**
```json
{
  "success": true,
  "command_name": "power",
  "command_type": "ir",
  "data": "scBIAdieBgALFgsXFwsXDAoXFwsXCwoXGAoL...",
  "data_length": 444
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Timeout - no signal detected within 30 seconds"
}
```

### Implementation

```python
# app/api/commands.py
from app.broadlink_learner import BroadlinkLearner

@router.post("/commands/learn")
async def learn_command(request: LearnCommandRequest):
    """Learn a command directly from Broadlink device"""
    
    # Get device connection info
    device_info = get_device_connection_info(request.entity_id)
    
    # Create learner
    learner = BroadlinkLearner(
        host=device_info['host'],
        mac=device_info['mac'],
        device_type=device_info['type']
    )
    
    # Authenticate
    learner.authenticate()
    
    # Learn command
    try:
        if request.command_type == 'ir':
            base64_data = learner.learn_ir_command(timeout=30)
        else:
            base64_data = learner.learn_rf_command(timeout=30)
        
        # Save to devices.json
        device_manager.add_command(
            device_id=request.device_id,
            command_name=request.command_name,
            command_data=base64_data,
            command_type=request.command_type
        )
        
        return {
            "success": True,
            "command_name": request.command_name,
            "command_type": request.command_type,
            "data": base64_data,
            "data_length": len(base64_data)
        }
        
    except TimeoutError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Learning failed: {str(e)}"}
```

---

## Device Connection Info

We need to map HA entity IDs to device connection info:

```python
# app/broadlink_device_manager.py
class BroadlinkDeviceManager:
    def get_device_connection_info(self, entity_id: str) -> dict:
        """Get device connection info from HA entity"""
        
        # Get entity state from HA
        entity = ha_api.get_state(entity_id)
        
        # Extract connection info
        return {
            'host': entity['attributes'].get('host'),
            'mac': bytes.fromhex(entity['attributes']['mac'].replace(':', '')),
            'type': entity['attributes'].get('type'),
            'model': entity['attributes'].get('model')
        }
```

---

## Frontend Implementation

### CommandLearner.vue Updates

```vue
<template>
  <div class="learn-dialog">
    <h3>Learn Command: {{ commandName }}</h3>
    
    <!-- IR Learning -->
    <div v-if="commandType === 'ir' && learningState === 'learning'">
      <p>📡 Point your remote at the Broadlink device and press the button</p>
      <p>⏳ Learning... ({{ elapsed }}/30s)</p>
      <button @click="cancel">Cancel</button>
    </div>
    
    <!-- RF Learning - Step 1 -->
    <div v-if="commandType === 'rf' && learningState === 'sweep'">
      <p>📡 Press and HOLD the button for 2-3 seconds</p>
      <p>⏳ Scanning frequency... ({{ elapsed }}/30s)</p>
      <button @click="cancel">Cancel</button>
    </div>
    
    <!-- RF Learning - Step 2 -->
    <div v-if="commandType === 'rf' && learningState === 'capture'">
      <p>✅ Frequency locked!</p>
      <p>📡 Press the button again (short press)</p>
      <p>⏳ Capturing... ({{ elapsed }}/30s)</p>
      <button @click="cancel">Cancel</button>
    </div>
    
    <!-- Success -->
    <div v-if="learningState === 'success'">
      <p>✅ Command learned successfully!</p>
      <button @click="close">Done</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      learningState: 'ready',  // ready, learning, sweep, capture, success, error
      elapsed: 0,
      interval: null
    }
  },
  methods: {
    async startLearning() {
      this.learningState = this.commandType === 'ir' ? 'learning' : 'sweep'
      this.elapsed = 0
      
      // Start countdown
      this.interval = setInterval(() => {
        this.elapsed++
      }, 1000)
      
      try {
        const response = await fetch('/api/commands/learn', {
          method: 'POST',
          body: JSON.stringify({
            device_id: this.deviceId,
            entity_id: this.entityId,
            command_name: this.commandName,
            command_type: this.commandType
          })
        })
        
        const result = await response.json()
        clearInterval(this.interval)
        
        if (result.success) {
          this.learningState = 'success'
          this.$emit('learned', result)
        } else {
          this.learningState = 'error'
          this.errorMessage = result.error
        }
      } catch (error) {
        clearInterval(this.interval)
        this.learningState = 'error'
        this.errorMessage = error.message
      }
    }
  }
}
</script>
```

---

## Benefits of This Approach

1. ✅ **Instant learning** - No waiting for `.storage` files
2. ✅ **Full control** - We manage the entire learning flow
3. ✅ **Better UX** - Real-time feedback in our dialog
4. ✅ **No storage lag** - Commands saved to `devices.json` immediately
5. ✅ **No sync needed** - We control the data lifecycle
6. ✅ **Cleaner code** - No optimistic updates, no polling
7. ✅ **Works with full buffers** - Ignores old command errors

---

## Next Steps

1. Create `app/broadlink_learner.py` - Learning logic
2. Create `app/broadlink_device_manager.py` - Device connection management
3. Update `app/api/commands.py` - Add `/commands/learn` endpoint
4. Update `CommandLearner.vue` - New learning UI
5. Update `devices.json` schema - Store command data
6. Update entity generator - Embed base64 in entities
7. Test end-to-end flow
8. Document for users

---

## Testing Checklist

- [ ] IR learning on device with empty buffer
- [ ] IR learning on device with full buffer
- [ ] RF learning on device with empty buffer
- [ ] RF learning on device with full buffer
- [ ] Timeout handling (no button press)
- [ ] Cancel during learning
- [ ] Multiple commands in sequence
- [ ] Command sending after learning
- [ ] Entity generation with embedded base64
- [ ] Migration from old format

---

**Status:** Ready for implementation! 🚀
