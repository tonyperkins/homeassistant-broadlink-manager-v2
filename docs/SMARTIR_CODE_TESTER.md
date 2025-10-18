# SmartIR Code Tester

## Overview

A simple, focused modal dialog for testing SmartIR codes from the device index before creating custom profiles. Solves the use case: **"I want to test if a code works with my device."**

## Features

### Step 1: Code Selection
- **Platform dropdown**: Climate, Media Player, Fan, Light
- **Manufacturer dropdown**: Searchable list from device index
- **Model dropdown**: Filtered by selected manufacturer
- **Code display**: Shows the selected code number
- **Load button**: Fetches the full code with commands

### Step 2: Command Testing
- **Code info**: Shows manufacturer, model, and code number
- **Broadlink device selector**: Choose which device to test with
- **Commands list**: All commands from the selected code
- **Test buttons**: Send individual commands to test
- **Visual feedback**: 
  - Tested commands marked with checkmark
  - Testing state shows spinner
  - Success/error toasts
- **Clone button**: Create custom profile from working code

## User Flow

```
1. Click "Test Codes" button in SmartIR section
   ↓
2. Select platform (e.g., Climate)
   ↓
3. Select manufacturer (e.g., Daikin)
   ↓
4. Select model (e.g., FTXS25CVMA - Code 1000)
   ↓
5. Click "Load Commands"
   ↓
6. Select Broadlink device
   ↓
7. Test individual commands (off, cool, heat, etc.)
   ↓
8. If it works → Click "Clone to Custom Profile"
   ↓
9. Edit the cloned profile as needed
```

## Technical Details

### Component
**File**: `frontend/src/components/smartir/SmartIRCodeTester.vue`

### API Endpoints Used
- `/api/smartir/codes/manufacturers?entity_type={platform}` - Get manufacturers
- `/api/smartir/codes/models?entity_type={platform}&manufacturer={name}` - Get models
- `/api/smartir/codes/code?entity_type={platform}&code_id={code}` - Get full code
- `/api/remote/devices` - Get Broadlink devices
- `/api/commands/test` - Test command
- `/api/smartir/platforms/{platform}/next-code` - Get next available code
- `/api/smartir/profiles` - Save cloned profile

### Props
- `isOpen` (Boolean) - Controls modal visibility

### Events
- `@close` - Emitted when modal is closed
- `@clone` - Emitted when profile is cloned (payload: `{ platform, code }`)

### State Management
- Platform selection
- Manufacturer/model cascading dropdowns
- Loaded code data
- Command list
- Tested commands tracking
- Selected Broadlink device

## Integration

### SmartIRStatusCard.vue
Added "Test Codes" button next to "Create SmartIR Profile":
```vue
<button @click="openCodeTester" class="btn btn-secondary">
  <i class="mdi mdi-test-tube"></i>
  Test Codes
</button>
```

Modal component included at bottom of template:
```vue
<SmartIRCodeTester
  :isOpen="showCodeTester"
  @close="showCodeTester = false"
  @clone="handleCodeClone"
/>
```

## Styling

- **Modal overlay**: Full-screen dark backdrop
- **Modal container**: Centered, max-width 600px, max-height 90vh
- **Scrollable content**: Commands list scrolls independently
- **Responsive**: Works on desktop, tablet, mobile
- **Consistent design**: Matches existing Broadlink Manager UI

## Command Icons

Commands are automatically assigned icons based on their name:
- `power/off` → Power icon
- `cool` → Snowflake icon
- `heat` → Fire icon
- `fan` → Fan icon
- `auto` → Auto-fix icon
- `dry` → Water-percent icon
- `temp` → Thermometer icon
- `swing` → Swap-vertical icon
- Default → Remote icon

## Benefits

✅ **Simple & Focused**: One clear purpose  
✅ **No Complex State**: Easy to maintain  
✅ **Reuses Backend API**: Leverages existing endpoints  
✅ **Visual Feedback**: Clear indication of tested commands  
✅ **Practical Use Case**: Solves real user need  
✅ **Quick Testing**: Test before committing to custom profile  
✅ **Easy Cloning**: One-click clone if it works  

## Future Enhancements

Potential improvements for future versions:
- [ ] Save test results/notes
- [ ] Batch test all commands
- [ ] Compare multiple codes side-by-side
- [ ] Export test results
- [ ] Command parameter testing (temp, fan speed, etc.)
- [ ] Test history/favorites

## Usage Example

### Scenario
User has a Daikin AC and wants to find the right code:

1. Click "Test Codes"
2. Select "Climate" platform
3. Select "Daikin" manufacturer
4. Browse models, select "FTXS25CVMA (Code: 1000)"
5. Click "Load Commands"
6. Select their Broadlink RM4 Pro
7. Test "off" command → Works! ✓
8. Test "cool" command → Works! ✓
9. Test "heat" command → Works! ✓
10. Click "Clone to Custom Profile"
11. Profile created as code 10005
12. Edit in Profile Builder to customize

## Files Modified

### Created
- `frontend/src/components/smartir/SmartIRCodeTester.vue` - Main modal component

### Modified
- `frontend/src/components/smartir/SmartIRStatusCard.vue` - Added button and integration

### Backend (Already Exists)
- All necessary API endpoints already implemented
- No backend changes required

## Testing Checklist

- [ ] Modal opens/closes correctly
- [ ] Platform selection works
- [ ] Manufacturer dropdown populates
- [ ] Model dropdown filters by manufacturer
- [ ] Code loads successfully
- [ ] Broadlink devices populate
- [ ] Commands display correctly
- [ ] Test button sends command
- [ ] Tested commands marked
- [ ] Clone creates custom profile
- [ ] Profile list refreshes after clone
- [ ] Error handling works
- [ ] Responsive on mobile
- [ ] Toast notifications appear

## Comparison: Complex Browser vs Simple Tester

| Feature | Profile Browser | Code Tester |
|---------|----------------|-------------|
| Purpose | Browse all profiles | Test specific codes |
| Complexity | High | Low |
| State Management | Complex | Simple |
| Bug Risk | High | Low |
| Maintenance | Difficult | Easy |
| User Value | Medium | High |
| Development Time | Days | Hours |
| Lines of Code | 800+ | 400 |
| Dependencies | Many | Few |

**Result**: Code Tester provides better value with less complexity! ✅
