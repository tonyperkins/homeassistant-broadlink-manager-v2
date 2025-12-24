# Testing Guide: Entity Generation Fixes

## Prerequisites

1. **Broadlink Manager v2** running in Home Assistant
2. At least one Broadlink device configured
3. Some learned IR/RF commands on a device

## Test Setup

### Create a Test Light Device

1. **Create the Device:**
   - Click "Add Device" in Broadlink Manager
   - **Device Name:** "Test Light"
   - **Entity Type:** Select "💡 Light"
   - **Device Type:** Select "📡 Broadlink Device (Learn IR Codes)"
   - **Broadlink Remote:** Select your Broadlink remote entity from dropdown
   - **Icon:** (optional) e.g., mdi:lightbulb
   - Click "Save"

2. **Learn Commands:**
   - Find "Test Light" in your device list
   - Click the device card to expand it
   - Click "Learn Command" button
   - Learn the following commands (use any IR remote):
     - `turn_on` - Basic on command
     - `turn_off` - Basic off command
     - `brightness_up` - Increase brightness
     - `brightness_down` - Decrease brightness
     - `warm_tone` - Custom command (any IR code)
     - `cool_tone` - Custom command (any IR code)
     - `reading_mode` - Custom command (any IR code)

---

## Test 1: Brightness Range Conversion

### Objective
Verify that brightness values are correctly converted between HA's 0-255 scale and the helper's 0-100 percentage.

### Steps

1. **Generate Entities:**
   ```
   - Go to Broadlink Manager
   - Click "Generate Entities" button
   - Wait for success message
   ```

2. **Restart Home Assistant:**
   ```
   Settings → System → Restart Home Assistant
   ```

3. **Verify Helper Creation:**
   ```
   - Go to Settings → Devices & Services → Helpers
   - Search for "Test Light Brightness"
   - Should show: min=0, max=100, step=1, unit=%
   ```

4. **Test Brightness Control:**

   **Test Case 1.1: Set 50% Brightness**
   ```
   - Open the light entity in HA
   - Set brightness slider to 50%
   - Expected: No errors
   - Check helper value: Should be ~50 (not 127)
   ```

   **Test Case 1.2: Set 100% Brightness**
   ```
   - Set brightness slider to 100%
   - Expected: No errors
   - Check helper value: Should be 100 (not 255)
   ```

   **Test Case 1.3: Set 25% Brightness**
   ```
   - Set brightness slider to 25%
   - Expected: No errors
   - Check helper value: Should be ~25 (not 63)
   ```

   **Test Case 1.4: Set 0% Brightness**
   ```
   - Set brightness slider to 0%
   - Expected: No errors
   - Check helper value: Should be 0
   ```

5. **Verify Helper → Entity Sync:**
   ```
   - Go to Developer Tools → States
   - Find input_number.test_light_brightness
   - Set value to 75
   - Check light entity brightness
   - Expected: Should show ~75% (not 75/255)
   ```

### Expected Results

✅ **PASS Criteria:**
- No "can't go above 100" errors at any brightness level
- Helper always shows 0-100 range
- Light brightness slider matches helper percentage
- All brightness levels work smoothly

❌ **FAIL Indicators:**
- Errors when setting brightness above 50%
- Helper shows values > 100
- Brightness slider shows incorrect percentage
- Mismatch between slider and helper values

---

## Test 2: Custom Commands as Buttons

### Objective
Verify that custom commands (warm_tone, cool_tone, reading_mode) are generated as button entities.

### Steps

1. **Check Generated YAML:**
   ```
   - Open /config/broadlink_manager/package.yaml
   - Look for template: section
   - Should contain button: section
   ```

   **Expected YAML Structure:**
   ```yaml
   template:
     - button:
         - unique_id: test_light_warm_tone_button
           name: "Test Light Warm Tone"
           press:
             - service: remote.send_command
               target:
                 entity_id: remote.your_broadlink
               data:
                 command: "b64:..."
         - unique_id: test_light_cool_tone_button
           name: "Test Light Cool Tone"
           press: ...
         - unique_id: test_light_reading_mode_button
           name: "Test Light Reading Mode"
           press: ...
   ```

2. **Verify Buttons in Home Assistant:**
   ```
   - Go to Settings → Devices & Services → Entities
   - Search for "Test Light"
   - Should see:
     * light.test_light (main entity)
     * button.test_light_warm_tone
     * button.test_light_cool_tone
     * button.test_light_reading_mode
   ```

3. **Test Button Functionality:**

   **Test Case 2.1: Warm Tone Button**
   ```
   - Find button.test_light_warm_tone
   - Press the button
   - Expected: IR/RF command sent to device
   - Check logs for "remote.send_command" call
   ```

   **Test Case 2.2: Cool Tone Button**
   ```
   - Find button.test_light_cool_tone
   - Press the button
   - Expected: IR/RF command sent to device
   ```

   **Test Case 2.3: Reading Mode Button**
   ```
   - Find button.test_light_reading_mode
   - Press the button
   - Expected: IR/RF command sent to device
   ```

4. **Verify Button Names:**
   ```
   - Check that button names are friendly:
     * "Test Light Warm Tone" (not "test_light_warm_tone")
     * "Test Light Cool Tone"
     * "Test Light Reading Mode"
   ```

5. **Test in Lovelace Dashboard:**
   ```
   - Add buttons to a dashboard card
   - Verify they appear and are clickable
   - Test pressing each button
   ```

### Expected Results

✅ **PASS Criteria:**
- All custom commands appear as button entities
- Button names are properly formatted (Title Case with spaces)
- Pressing buttons sends correct IR/RF commands
- Buttons work in dashboards and automations
- Standard commands (turn_on, brightness_up) NOT duplicated as buttons

❌ **FAIL Indicators:**
- Custom commands missing from entity list
- Buttons don't appear in HA
- Pressing buttons does nothing
- Button names are malformed (e.g., "test_light_warm_tone")
- Standard commands appear as duplicate buttons

---

## Test 3: Standard Commands Not Duplicated

### Objective
Verify that standard commands (turn_on, turn_off, brightness_up, brightness_down) are NOT created as button entities.

### Steps

1. **Check Entity List:**
   ```
   - Search for "Test Light" in entity list
   - Should NOT see:
     * button.test_light_turn_on
     * button.test_light_turn_off
     * button.test_light_brightness_up
     * button.test_light_brightness_down
   ```

2. **Verify Main Entity Functionality:**
   ```
   - Main light entity should handle:
     * Turn on/off via toggle
     * Brightness control via slider
   - These should NOT require separate buttons
   ```

### Expected Results

✅ **PASS Criteria:**
- Only custom commands appear as buttons
- Standard commands integrated into main entity
- No duplicate functionality

❌ **FAIL Indicators:**
- Standard commands appear as buttons
- Duplicate controls for same functionality

---

## Test 4: Multiple Entity Types

### Objective
Verify custom commands work for different entity types (fan, switch, etc.).

### Steps

1. **Create Test Fan:**
   ```
   - Learn commands: fan_on, fan_off, speed_1, speed_2, speed_3, turbo_mode
   - Create fan entity
   - Generate entities
   ```

2. **Verify Fan Buttons:**
   ```
   - Should see button.test_fan_turbo_mode
   - Should NOT see buttons for speed_1, speed_2, speed_3 (handled by main entity)
   ```

3. **Create Test Switch:**
   ```
   - Learn commands: on, off, night_mode, eco_mode
   - Create switch entity
   - Generate entities
   ```

4. **Verify Switch Buttons:**
   ```
   - Should see:
     * button.test_switch_night_mode
     * button.test_switch_eco_mode
   - Should NOT see buttons for on/off
   ```

### Expected Results

✅ **PASS Criteria:**
- Custom commands work for all entity types
- Each entity type correctly identifies standard vs custom commands

---

## Test 5: Backward Compatibility

### Objective
Verify that existing entities continue to work after regeneration.

### Steps

1. **Before Regeneration:**
   ```
   - Note current entity states
   - Note current helper values
   - Test existing automations
   ```

2. **Regenerate Entities:**
   ```
   - Click "Generate Entities"
   - Restart Home Assistant
   ```

3. **After Regeneration:**
   ```
   - Verify entity IDs unchanged
   - Verify helper values preserved
   - Test existing automations still work
   - New button entities added (not replacing anything)
   ```

### Expected Results

✅ **PASS Criteria:**
- No breaking changes
- Existing automations work
- Helper values preserved
- New buttons are additive

---

## Troubleshooting

### Issue: Brightness still shows 255%

**Solution:**
1. Delete the entity from HA
2. Delete the helper (input_number.xxx_brightness)
3. Regenerate entities
4. Restart HA

### Issue: Custom command buttons not appearing

**Check:**
1. Verify commands are learned (check devices.json)
2. Check package.yaml for button: section
3. Restart HA after generation
4. Check HA logs for YAML errors

### Issue: Buttons don't send commands

**Check:**
1. Verify broadlink_entity is set correctly
2. Check command codes exist in .storage/broadlink_remote_*_codes
3. Check HA logs for remote.send_command errors
4. Test command directly via Developer Tools → Services

---

## Verification Checklist

- [ ] Brightness helper shows 0-100 range
- [ ] Setting 50% brightness works without errors
- [ ] Setting 100% brightness shows "100%" not "255%"
- [ ] All brightness levels (0%, 25%, 50%, 75%, 100%) work correctly
- [ ] Custom commands appear as button entities
- [ ] Button names are properly formatted
- [ ] Pressing buttons sends IR/RF commands
- [ ] Standard commands NOT duplicated as buttons
- [ ] Main entity controls work normally
- [ ] Existing automations still work
- [ ] Helper values preserved after regeneration

---

## Reporting Issues

If tests fail, collect:
1. Generated YAML file (/config/broadlink_manager/package.yaml)
2. Helper configuration (Settings → Helpers)
3. Entity states (Developer Tools → States)
4. Home Assistant logs (Settings → System → Logs)
5. Broadlink Manager logs

Submit to: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues
