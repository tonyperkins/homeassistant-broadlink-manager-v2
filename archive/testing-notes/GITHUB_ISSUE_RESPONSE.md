# Response to mansf-1 - Custom Fan/Swing Modes Request

Hi @mansf-1,

Thank you for the excellent feedback and feature request! 🎉

I'm happy to report that **custom fan and swing mode support has been implemented** and is now available in the climate profile builder UI!

## What's New

The interface is no longer limited to the predefined modes. You can now:

### Fan Modes
- **Predefined options** (quick select): Auto, Low, Medium, High, Silent, Turbo
- **Custom input field**: Add any mode your device supports (e.g., `mid`, `mid_low`, `mid_high`, `quiet`, `powerful`)

### Swing Modes
- **Predefined options** (quick select): Off, Vertical, Horizontal, Both, Swing, Stop
- **Custom input field**: Add any position (e.g., `position_1`, `position_2`, `auto`, `fixedtop`)

## How to Use

1. **Quick Selection**: Check boxes for common modes
2. **Add Custom Modes**: 
   - Type the mode name in the input field (e.g., `mid_low`)
   - Press **Enter** or click the **Add** button
3. **Visual Management**: 
   - All selected modes appear as chips with a count
   - Click the × button on any chip to remove it
4. **Proceed with Learning**: Custom modes are automatically included in the command generation

## Example

For a device with fan modes: `silent`, `low`, `mid`, `high`, `turbo`

1. Check: Low, High, Silent, Turbo
2. Type `mid` → Press Enter
3. Result: All 5 modes selected and ready for learning

## Features

✅ No more manual YAML editing required  
✅ Support for any device-specific mode names  
✅ Visual chips with easy removal  
✅ Automatic validation (lowercase, duplicate prevention)  
✅ Fully compatible with SmartIR JSON/YAML format  
✅ Dark mode support and mobile responsive  

## Documentation

Complete documentation with examples and best practices: [`docs/CUSTOM_FAN_SWING_MODES.md`](docs/CUSTOM_FAN_SWING_MODES.md)

## Availability

This feature will be available in the next release. You can also test it now by:
- Installing from the `develop` branch, or
- Waiting for the upcoming release (will be tagged shortly)

Your workaround of generating profiles via UI and then manually editing YAML should no longer be necessary! 👍

Let me know if you have any questions or if there's anything else that could be improved.

Thanks again for the great suggestion!
