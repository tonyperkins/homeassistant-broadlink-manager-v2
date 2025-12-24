# Entity Generation Fixes

## Issues Fixed

### Issue 1: Brightness Range Conversion Bug

**Problem:**
- Light entities showed incorrect brightness values
- Setting 50% brightness triggered "can't go above 100" error
- Setting 100% brightness displayed as "255%" instead of "100%"

**Root Cause:**
Home Assistant's template light `brightness` attribute uses a 0-255 scale, but the helper `input_number` was configured with 0-100 range. The template was passing values directly without conversion, causing:
- HA sends `brightness=127` (50% of 255) → compared against helper's 0-100 range → error
- HA sends `brightness=255` (100%) → stored in helper as "255" → displayed as "255%"

**Solution:**
Added bidirectional conversion between HA's 0-255 scale and helper's 0-100 percentage scale:

1. **Reading brightness (level):** Convert helper's 0-100 to HA's 0-255
   ```jinja
   level: "{{ (states('input_number.{id}_brightness') | int * 255 / 100) | int }}"
   ```

2. **Setting brightness (set_level):** Convert HA's 0-255 to helper's 0-100
   ```jinja
   value: "{{ (brightness * 100 / 255) | int }}"
   ```

**Files Modified:**
- `app/entity_generator.py` lines 283-285, 410-416

---

### Issue 2: Custom Commands Not Added to YAML

**Problem:**
- Custom commands with non-standard names (e.g., `warm_tone`, `cool_tone`, `reading_mode`) were completely ignored
- Only predefined command names were recognized (turn_on, turn_off, brightness_up, etc.)
- Users couldn't access their custom learned commands through Home Assistant entities

**Root Cause:**
The entity generator only checked for specific predefined command names. Any command that didn't match these patterns was silently ignored and not included in the generated YAML.

**Solution:**
Implemented automatic button entity generation for custom commands:

1. **Detection:** Identify commands that don't match standard patterns
2. **Generation:** Create template button entities for each custom command
3. **Naming:** Auto-generate friendly names (e.g., `warm_tone` → "Living Room Light Warm Tone")
4. **Integration:** Buttons appear alongside main entity in Home Assistant

**Standard Commands Excluded:**
- Light: turn_on, turn_off, toggle, brightness_up/down, bright, dim, cooler, warmer
- Fan: fan_on, fan_off, fan_toggle, fan_reverse, speed_*, fan_speed_*
- Switch: on, off
- Cover: open, close, stop, open_tilt, close_tilt, position_*
- Media Player: power, volume_up/down, mute, play, pause, stop, next, previous, source_*

**Example:**
For a light with commands: `turn_on`, `turn_off`, `warm_tone`, `cool_tone`
- Main light entity handles: turn_on, turn_off
- Button entities created: `light.living_room_light_warm_tone_button`, `light.living_room_light_cool_tone_button`

**Files Modified:**
- `app/entity_generator.py`:
  - Added `button` to template_entities dict (line 163)
  - Added button generation call (lines 224-229)
  - New method `_generate_custom_command_buttons()` (lines 1331-1450)

---

## Testing

### Brightness Fix Testing
1. Create a light entity with brightness commands
2. Generate entities
3. In Home Assistant:
   - Set brightness to 50% → should work without errors
   - Set brightness to 100% → should show "100%" not "255%"
   - Verify helper shows correct percentage (0-100)

### Custom Commands Testing
1. Learn custom commands on a device (e.g., `warm_tone`, `reading_mode`)
2. Generate entities
3. Check generated YAML:
   - Main entity should have standard controls
   - Button entities should exist for custom commands
4. In Home Assistant:
   - Main entity should work normally
   - Custom command buttons should appear
   - Pressing buttons should send correct IR/RF codes

---

## Migration Notes

**Existing Users:**
- Regenerate entities to apply fixes
- Old entities will continue to work but won't have fixes
- Brightness values in existing helpers will be preserved
- Custom commands will appear as new button entities after regeneration

**No Breaking Changes:**
- Helper configurations remain the same (0-100 range)
- Entity IDs unchanged
- Existing automations continue to work
- Button entities are additive (don't replace anything)

---

## Technical Details

### Brightness Conversion Math
- **HA → Helper:** `(brightness * 100 / 255) | int`
  - Example: 127 → (127 * 100 / 255) = 49.8 → 50%
- **Helper → HA:** `(helper_value * 255 / 100) | int`
  - Example: 50 → (50 * 255 / 100) = 127.5 → 127

### Button Entity Format
```yaml
template:
  - button:
      - unique_id: living_room_light_warm_tone_button
        name: "Living Room Light Warm Tone"
        press:
          - service: remote.send_command
            target:
              entity_id: remote.broadlink_rm4
            data:
              command: "b64:JgBQAAABK..."
```

---

## Related Files
- `app/entity_generator.py` - Main entity generator with fixes
- `app/entity_generator_v2.py` - Wrapper that uses v1 generator
- `app/web_server.py` - Entity generation endpoint
