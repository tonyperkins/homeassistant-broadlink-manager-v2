# Entity Generation Fix - Media Player Commands

## Issue Report

User reported that generated entities for a Denon RCD-CX1 receiver were not working correctly:
- 9 learned commands generated 6 entities
- Only 2 entities worked (Mute button and Switch L1/L2 button)
- Other entities failed with error: `Failed to perform the action media_player/turn_on. Command not found: 'turn_on'`

## Root Cause

The entity generator was using command **names** instead of actual base64-encoded IR/RF **data** when generating YAML configurations.

**Incorrect format (what was generated):**
```yaml
data:
  device: denon_rcd_cx1
  command: turn_on  # ❌ This is just a name, not the actual IR code
```

**Correct format (what Home Assistant expects):**
```yaml
data:
  command: b64:JgBkAmw2DQ4NDg0pDQ0OKQsPDigNDg0ODCkNDwwODSkNKQsQDA4ODQ0ODQ4MDwwpDSkNKQ0ODSgODQ0ODQ4MKg0oDQ8LKg0NDg4MDwwODg0NDg0ODA8NKA0PCw8NDg0ODQ0OKQsqDQAJV2w2Dg0NDg0pDA4OKA0ODSkNDQ4ODCkODQ0NDikNKA0PDA4NDgwPDQ0NDwsqDSkNKQ0NDikMDg0ODQ0OKQwpDQ4NKQwPDA4ODgwPDA4NDgwODg4MKQ4NDQ8MDg0ODA8NKQwpDQAJVmw3DQ4NDg0pDA8MKQwPDSkNDQ4NDSkMDw0ODSkMKQ0ODQ4NDgwPDQ0NDg0pDCoNKQsPDSkMDw0ODA8NKQwpDQ4NKQwPDA4ODQ0PCw8MDw0ODA4NKQ0ODQ4NDg0ODA8NKA0pDAAJV201DQ8MDw0oDQ8MKQ0ODSkMDg0ODSkNDgwPDSgNKQwPDA4ODgwPDA4NDg0pDCoNKQwODSkNDQ4ODA8MKQ0pDA8NKA0PDA4NDg0ODQ4NDgsQDA4NKQwPDA8MDg0ODBAMKQwqDAAJV201Dg0NDwsqDQ4NKQwPDSgNDg0ODCkODgwPDCkNKQwPDA4NDg0PDA4NDg0oDikMKQ0ODCoNDQ4NDQ8MKQ0pDA8MKQ0ODQ4NDgwPDQ0ODQ0PDA4NKA4ODA8LDw4NDQ4NKQ0oDQAJV2w3DQ0NDgwqDA8NKQwPDCkNDg0ODCkODQ0ODSkNKA4ODA8LDw0ODA4ODgwpDikMKQ0ODSkMDg0ODQ4MKgwpDQ4NKQwPDQ0ODgwPCw8ODQ0ODQ4NKQ0NDQ8MDg0ODQ4NKQwpDQANBQ==
```

## Files Fixed

### `app/entity_generator.py`

Fixed the following entity generator methods to use base64 command data:

1. **`_generate_media_player_switch()`** (lines 1092-1154)
   - Power switch for media player entities
   - Now looks up actual base64 data from `broadlink_commands`
   - Uses `b64:` prefix for Home Assistant

2. **`_generate_media_player()`** (lines 949-1071)
   - Volume up/down commands
   - Mute command
   - Play/pause/stop commands
   - Next/previous track commands
   - Source selection (with choose/conditions)

3. **`_generate_climate()`** (lines 1246-1293)
   - Turn on/off commands
   - Set temperature command

4. **`_generate_cover()`** (lines 1338-1438)
   - Open/close commands
   - Stop command
   - Tilt commands

## How It Works Now

1. Generator receives `broadlink_commands` dict with structure:
   ```python
   {
     "device_name": {
       "command_name": "base64_encoded_data..."
     }
   }
   ```

2. For each command, it:
   - Gets the command name from entity metadata
   - Looks up the actual base64 data: `broadlink_commands.get(device, {}).get(command_name, "")`
   - Generates YAML with `b64:` prefix: `{"command": f"b64:{command_data}"}`

3. Home Assistant receives the actual IR/RF code and can send it via the Broadlink device

## Why Buttons Worked

The custom command buttons (like "Volume Mute" and "Switch L1 L2") were already using the correct format:

```python
button_config = {
    "press": [{
        "service": "remote.send_command",
        "target": {"entity_id": broadlink_entity},
        "data": {"command": f"b64:{cmd_code}"},  # ✅ Already correct
    }]
}
```

This is why those two entities worked while the media player entity and its companion switch failed.

## Testing

After this fix, users should:
1. Delete the old generated entities from Home Assistant
2. Regenerate entities using the "Generate Entities" button
3. Restart Home Assistant
4. Test all entity functions (power, volume, source selection, etc.)

All commands should now work correctly because they're sending actual IR/RF codes instead of command names.

## Code Quality

- ✅ Formatted with Black
- ✅ Passes flake8 linting (0 errors)
- ✅ Consistent with existing switch/light/fan generators
- ✅ Proper error handling (checks if command data exists)
