# Custom Fan and Swing Modes in Climate Profile Builder

## Overview

The SmartIR Climate Profile Builder now supports custom fan modes and swing modes beyond the predefined options. This allows you to create profiles for devices with unique fan speeds (e.g., `silent`, `turbo`, `mid_low`, `mid_high`) and custom swing positions.

## Feature Details

### Fan Modes

**Predefined Options (Quick Select):**
- Auto
- Low
- Medium
- High
- Silent
- Turbo

**Custom Mode Support:**
You can add any custom fan mode your device supports, such as:
- `mid` - Mid-range speed
- `mid_low` - Between low and medium
- `mid_high` - Between medium and high
- `quiet` - Ultra-quiet operation
- `powerful` - Maximum power mode
- Any other mode your device uses

### Swing Modes

**Predefined Options (Quick Select):**
- Off
- Vertical
- Horizontal
- Both
- Swing
- Stop

**Custom Mode Support:**
You can add any custom swing position your device supports, such as:
- `position_1`, `position_2`, etc. - Specific vane positions
- `auto` - Automatic swing
- `fixedtop`, `fixedmiddle`, `fixedbottom` - Fixed positions
- Any other mode your device uses

## How to Use

### Adding Custom Modes

1. **Using Predefined Checkboxes:**
   - Simply check the boxes for common modes your device supports
   - These are the most frequently used modes across different manufacturers

2. **Adding Custom Modes:**
   - Locate the "Add Custom Fan Mode" or "Add Custom Swing Mode" input field
   - Type the custom mode name (e.g., `mid_low`)
   - Press **Enter** or click the **Add** button
   - The mode will be added to your selected modes list

3. **Managing Selected Modes:**
   - All selected modes (both predefined and custom) appear as chips below the input
   - Each chip shows the mode name and a remove button (×)
   - Click the × button to remove any mode you don't need
   - The count of selected modes is displayed in the label

### Best Practices

**Mode Naming Conventions:**
- Use lowercase letters only
- Use underscores (`_`) for multi-word modes (e.g., `mid_low`)
- Avoid spaces and special characters
- Match the exact mode names from your device's manual or SmartIR JSON files

**Finding Your Device's Modes:**
1. Check your device's remote control for available fan/swing settings
2. Consult the device manual for mode names
3. Look at existing SmartIR profiles for similar devices:
   - Browse the [SmartIR Code Aggregator](https://github.com/tonyperkins/smartir-code-aggregator)
   - Search for your manufacturer and model
   - Review the `fanModes` and `swingModes` arrays in the JSON

## Examples

### Example 1: Samsung AC with Custom Fan Modes

**Device Modes:**
- Auto, Low, Mid, High, Turbo

**Setup:**
1. Check: Auto, Low, High
2. Add custom: `mid`
3. Check: Turbo
4. Result: `['auto', 'low', 'high', 'mid', 'turbo']`

### Example 2: Daikin AC with Granular Swing Positions

**Device Modes:**
- Off, Position 1, Position 2, Position 3, Position 4, Position 5, Swing

**Setup:**
1. Check: Off, Swing
2. Add custom: `position_1`, `position_2`, `position_3`, `position_4`, `position_5`
3. Result: `['off', 'swing', 'position_1', 'position_2', 'position_3', 'position_4', 'position_5']`

### Example 3: LG AC with Silent and Powerful Modes

**Device Modes:**
- Auto, Silent, Low, Medium, High, Powerful

**Setup:**
1. Check: Auto, Low, Medium, High, Silent
2. Add custom: `powerful`
3. Result: `['auto', 'low', 'medium', 'high', 'silent', 'powerful']`

## Technical Details

### Data Format

Custom modes are stored in the same array as predefined modes in the profile configuration:

```json
{
  "fanModes": ["auto", "low", "mid", "high", "turbo"],
  "swingModes": ["off", "vertical", "position_1", "position_2", "swing"]
}
```

### Validation

- Mode names are automatically converted to lowercase
- Duplicate modes are prevented
- Empty mode names are rejected
- Modes can be removed at any time before learning

### Learning Process

When you proceed to the learning phase:
1. The system generates all combinations based on your selected modes
2. Each custom mode is treated identically to predefined modes
3. You'll be prompted to learn IR codes for each mode combination
4. The final JSON profile includes all your custom modes

## Workflow Integration

### Quick Mode
- Select/add all fan and swing modes your device supports
- Learn one temperature for each mode combination
- Custom modes are included in the command count calculation

### Complete Mode
- Select/add all fan and swing modes
- Learn all temperature combinations for each mode
- Custom modes multiply the total command count

## Troubleshooting

**Issue: Custom mode not working in Home Assistant**
- **Solution:** Ensure the mode name exactly matches what SmartIR expects
- Check the SmartIR integration logs for errors
- Verify the mode is present in the generated JSON file

**Issue: Too many modes to learn**
- **Solution:** Use Quick Mode instead of Complete Mode
- Only add modes you actually use frequently
- Consider creating separate profiles for different use cases

**Issue: Mode name contains spaces**
- **Solution:** Use underscores instead (e.g., `mid_low` not `mid low`)
- The system automatically converts to lowercase, but spaces may cause issues

## Migration from Manual Editing

If you previously edited YAML files manually to add custom modes:

1. **Create a new profile** using the UI
2. **Add your custom modes** using the custom input fields
3. **Learn the commands** through the guided process
4. **Replace the old profile** with the new one

This ensures proper validation and consistency.

## Related Documentation

- [SmartIR Climate Documentation](https://github.com/smartHomeHub/SmartIR/blob/master/docs/CLIMATE.md)
- [SmartIR Code Aggregator](https://github.com/tonyperkins/smartir-code-aggregator)
- [Climate Profile Builder Guide](./SMARTIR_CLIMATE_BUILDER.md)

## Feedback

This feature was implemented based on user feedback. If you encounter any issues or have suggestions for improvement, please [open an issue on GitHub](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues).
