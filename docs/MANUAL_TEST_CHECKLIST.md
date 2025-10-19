# Manual Test Checklist - User Perspective
## Broadlink Manager v2 - Quick Testing Guide

**Version**: 0.3.0-alpha.1  
**Purpose**: Simple checklist for manual testing before release  
**Time Required**: 45-60 minutes for full test

---

## 🎯 Quick Start

### Test Priority
- ✅ **CRITICAL (P0)**: Must pass - blocks release
- 🔶 **HIGH (P1)**: Should pass - important features  
- 🔵 **MEDIUM (P2)**: Nice to have - UI/UX polish

### Prerequisites
- Home Assistant running
- Broadlink device configured (e.g., RM4, RM Mini)
- Physical remote for learning
- Test device (TV, fan, light, etc.)

---

## 📋 Test Checklist

### Section 1: Initial Setup (5 min)

#### ✅ P0: First Launch
- [ ] Open Broadlink Manager from HA sidebar
- [ ] Dashboard loads without errors
- [ ] No console errors (F12 → Console tab)
- [ ] Navigation menu visible

#### 🔶 P1: SmartIR Detection
- [ ] SmartIR status card shows correct state
- [ ] Version displayed if installed
- [ ] Installation instructions if not installed

#### 🔵 P2: Settings Menu
- [ ] Settings gear icon opens menu
- [ ] Toggle SmartIR on/off toggles SmartIR section visibility
- [ ] Update Device List button works
- [ ] "Copy Diagnostics" works
- [ ] "Download Diagnostics" creates ZIP file
- [ ] GitHub link opens

**Notes**: _______________________________________________

---

### Section 2: Device Management (15 min)

#### ✅ P0: Create Broadlink Light
- [ ] Click "Create Device"
- [ ] Select "Broadlink" type
- [ ] Fill form: Name="Test Light", Type="Light", Broadlink Entity=(your device)
- [ ] Device created successfully
- [ ] Device appears in list with correct icon

**Device ID Created**: _______________

#### ✅ P0: Create Broadlink Fan
- [ ] Create fan device: Name="Test Fan", Type="Fan"
- [ ] Fan icon displayed
- [ ] Device ready for commands

#### ✅ P0: Create Broadlink Switch
- [ ] Create switch device: Name="Test Switch"
- [ ] Switch appears in list

#### 🔶 P1: Edit Device
- [ ] Click edit icon on device
- [ ] Change name and area
- [ ] Changes save and display immediately

#### 🔶 P1: Delete Device
- [ ] Create temporary device
- [ ] Click delete icon
- [ ] Confirmation modal appears
- [ ] Device deleted after confirmation

#### 🔵 P2: View Modes
- [ ] Toggle between Grid and List view
- [ ] Both views display correctly
- [ ] View preference persists

#### 🔵 P2: Search & Filter
- [ ] Search by device name
- [ ] Filter by entity type
- [ ] Filter by area
- [ ] Multiple filters work together

**Notes**: _______________________________________________

---

### Section 3: Command Learning (15 min)

#### ✅ P0: Learn IR Command - Power
- [ ] Open device card
- [ ] Click "Learn Command"
- [ ] Enter name: "power", Type: "IR"
- [ ] Point remote at Broadlink and press button
- [ ] Command learned within 5 seconds
- [ ] Command appears in list with base64 code

**Command Code Length**: _______ chars

#### ✅ P0: Learn Multiple Commands
- [ ] Learn "turn_on" command
- [ ] Learn "turn_off" command
- [ ] Learn "brightness_up" command
- [ ] Learn "brightness_down" command
- [ ] All 4 commands saved successfully

**Commands Learned**: _____/4

#### ✅ P0: Test Learned Command
- [ ] Click "Test" button on power command
- [ ] Physical device responds correctly
- [ ] Success notification shown
- [ ] No errors in console

**Device Response**: ☐ Correct ☐ Incorrect

#### 🔶 P1: Learn RF Command (if available)
- [ ] Create RF device
- [ ] Learn RF command
- [ ] RF code format different from IR
- [ ] Test RF command works

**Result**: ☐ Pass ☐ Fail ☐ Skipped

#### 🔵 P2: Delete Command
- [ ] Click delete on a command
- [ ] Confirmation shown
- [ ] Command removed from list

#### 🔵 P2: Learning Timeout
- [ ] Start learning without pressing remote
- [ ] Timeout message after ~30 seconds
- [ ] Can retry learning

**Notes**: _______________________________________________

---

### Section 4: Entity Generation (10 min)

#### ✅ P0: Generate Light Entities
- [ ] Select device with learned commands
- [ ] Click "Generate Entities"
- [ ] Review YAML preview
- [ ] Confirm generation
- [ ] entities.yaml created
- [ ] **CRITICAL**: Entity ID format is `bedroom_light` (NO `light.` prefix)

**Entity ID**: _______________  
**Format Correct**: ☐ Yes ☐ No

#### ✅ P0: Generate Fan Entities
- [ ] Create fan with speed commands
- [ ] Generate entities
- [ ] Check helpers.yaml created
- [ ] **CRITICAL**: Direction helper exists: `{entity_id}_direction`
- [ ] Speed selector helper: `{entity_id}_speed`
- [ ] State tracker helper: `{entity_id}_state`

**Helpers Created**: ☐ Direction ☐ Speed ☐ State

#### ✅ P0: Generate Switch Entities
- [ ] Create switch with on/off
- [ ] Generate entities
- [ ] Switch template created correctly

#### 🔵 P2: Download Generated Files
- [ ] Download entities.yaml
- [ ] Download helpers.yaml
- [ ] Files contain valid YAML

**Notes**: _______________________________________________

---

### Section 5: SmartIR Integration (10 min)
**Skip if SmartIR not installed**

#### 🔶 P1: Create SmartIR Device
- [ ] Click "Create Device"
- [ ] Select "SmartIR" type
- [ ] Select Entity Type: "Climate"
- [ ] Browse device codes
- [ ] Select code (e.g., 1000 - Daikin)
- [ ] Select controller (Broadlink device)
- [ ] Device created with SmartIR badge
- [ ] YAML file generated in `/config/smartir/climate.yaml`

**Device Code Used**: _______

#### 🔶 P1: Browse Device Codes
- [ ] Open code browser
- [ ] Switch between platforms (Climate, Media Player, Fan)
- [ ] Search for manufacturer
- [ ] Pagination works (50 per page)
- [ ] Can view profile details

#### 🔶 P1: Edit SmartIR Device
- [ ] Edit SmartIR device
- [ ] Change device code
- [ ] Save changes
- [ ] Refresh page
- [ ] **CRITICAL**: Changes persisted in devices.json

#### 🔶 P1: Verify Controller Format
- [ ] Check generated YAML file
- [ ] **CRITICAL**: `controller_data: "remote.bedroom_rm4"` (entity ID)
- [ ] **NOT**: `controller_data: "192.168.1.100"` (IP address)

**Controller Data**: _______________  
**Format Correct**: ☐ Yes ☐ No

**Notes**: _______________________________________________

---

### Section 6: UI/UX (10 min)

#### 🔵 P2: Dark Mode
- [ ] Switch HA to dark mode
- [ ] All text readable
- [ ] Proper contrast
- [ ] Icons visible
- [ ] No white backgrounds bleeding

#### 🔵 P2: Mobile Responsive
- [ ] Resize browser to mobile width (390px) or use phone
- [ ] Layout adapts correctly
- [ ] All buttons accessible
- [ ] Modals fit on screen
- [ ] No horizontal scrolling

**Device/Size Tested**: _______________

#### 🔵 P2: Toast Notifications
- [ ] Success toasts appear (green)
- [ ] Error toasts appear (red)
- [ ] Auto-dismiss after 3 seconds
- [ ] Messages clear and helpful

**Notes**: _______________________________________________

---

### Section 7: Error Handling (10 min)

#### 🔶 P1: Network Error
- [ ] Start learning command
- [ ] Disconnect WiFi briefly
- [ ] Error message shown
- [ ] Can retry
- [ ] UI recovers gracefully

#### 🔶 P1: Device Offline
- [ ] Unplug Broadlink device
- [ ] Try to learn/test command
- [ ] Clear error about device unavailable
- [ ] No crash or hang

#### 🔶 P1: Invalid Input
- [ ] Try to create device with empty name
- [ ] Validation prevents submission
- [ ] Error message clear

**Notes**: _______________________________________________

---

### Section 8: Data Persistence (5 min)

#### ✅ P0: Page Refresh
- [ ] Create devices and commands
- [ ] Refresh browser (F5)
- [ ] All data still present
- [ ] No data loss

#### ✅ P0: HA Restart
- [ ] Create test data
- [ ] Restart Home Assistant
- [ ] Wait for restart
- [ ] All data persists
- [ ] Files intact: devices.json, metadata.json

#### 🔶 P1: Backup Files
- [ ] Check `/config/broadlink_manager/`
- [ ] devices.json.backup exists
- [ ] metadata.json.backup exists
- [ ] Backups contain valid data

**Notes**: _______________________________________________

---

### Section 9: Regression Tests (10 min)
**Critical bug fixes - must not regress**

#### ✅ P0: Entity ID Format (Bug Fix)
**Issue**: Entity IDs had domain prefix causing HA errors

- [ ] Generate entities for any device
- [ ] Open entities.yaml
- [ ] **VERIFY**: Entity IDs like `bedroom_light` ✓
- [ ] **NOT**: `light.bedroom_light` ✗
- [ ] Load YAML in HA - no "invalid slug" errors

**Entity ID Format**: _______________  
**Result**: ☐ PASS ☐ FAIL

---

#### ✅ P0: Fan Direction Helper (Bug Fix)
**Issue**: Missing direction helper caused validation errors

- [ ] Create fan device
- [ ] Generate entities
- [ ] Open helpers.yaml
- [ ] **VERIFY**: Direction helper exists: `input_select.{entity_id}_direction`
- [ ] Helper created even without reverse command

**Direction Helper**: ☐ Present ☐ Missing  
**Result**: ☐ PASS ☐ FAIL

---

#### ✅ P0: SmartIR Config Persistence (Bug Fix)
**Issue**: SmartIR device edits didn't save

- [ ] Create SmartIR device
- [ ] Edit device (change device code)
- [ ] Save changes
- [ ] Refresh page
- [ ] **VERIFY**: Changes persisted in devices.json

**Result**: ☐ PASS ☐ FAIL

---

#### ✅ P0: SmartIR Controller Format (Bug Fix)
**Issue**: Used IP address instead of entity ID

- [ ] Create SmartIR device
- [ ] Check generated YAML
- [ ] **VERIFY**: `controller_data: "remote.bedroom_rm4"` ✓
- [ ] **NOT**: `controller_data: "192.168.1.100"` ✗

**Controller Data**: _______________  
**Result**: ☐ PASS ☐ FAIL

---

## 📊 Test Summary

### Session Info
```
Date: _______________
Tester: _______________
Environment: _______________
HA Version: _______________
Broadlink Manager: 0.3.0-alpha.1
SmartIR Version: _______________
Browser: _______________
```

### Results
```
Total Tests: _______
✅ P0 Passed: _______
🔶 P1 Passed: _______
🔵 P2 Passed: _______
❌ Failed: _______
⏭️ Skipped: _______
```

### Critical Issues (Blockers)
```
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________
```

### High Priority Issues
```
1. _______________________________________________
2. _______________________________________________
```

### Medium Priority Issues
```
1. _______________________________________________
2. _______________________________________________
```

### Release Decision
```
☐ ✅ READY FOR RELEASE - All P0 tests passed
☐ 🔶 READY WITH NOTES - Minor issues documented
☐ ❌ NOT READY - Critical issues found
☐ 🚫 BLOCKED - Major bugs prevent release
```

### Additional Notes
```
_______________________________________________
_______________________________________________
_______________________________________________
_______________________________________________
```

---

## 🔧 Quick Reference

### File Locations
- **Devices**: `/config/broadlink_manager/devices.json`
- **Metadata**: `/config/broadlink_manager/metadata.json`
- **Entities**: `/config/broadlink_manager/entities.yaml`
- **Helpers**: `/config/broadlink_manager/helpers.yaml`
- **SmartIR Climate**: `/config/smartir/climate.yaml`
- **SmartIR Media Player**: `/config/smartir/media_player.yaml`
- **SmartIR Fan**: `/config/smartir/fan.yaml`

### Common Issues
- **Entity ID has domain prefix**: Check entity generation code
- **Fan missing direction helper**: Check helper generation logic
- **SmartIR changes don't save**: Check devices.json write operation
- **Controller uses IP not entity**: Check YAML generation

### Browser Console
- Open: Press `F12` or `Ctrl+Shift+I`
- Check for errors in Console tab
- Network tab shows API calls
- Look for red errors or warnings

---

## 📝 Testing Tips

1. **Test in Order**: Follow sections sequentially for best results
2. **Take Screenshots**: Capture any errors or unexpected behavior
3. **Check Console**: Always have DevTools open during testing
4. **Document Everything**: Note even minor issues
5. **Test Real Devices**: Use actual IR/RF devices for realistic testing
6. **Verify Files**: Check generated YAML files manually
7. **Test Edge Cases**: Try invalid inputs, network issues, etc.
8. **Regression First**: Always run regression tests before release

---

## 🎯 Smoke Test (15 min)
**Quick test for rapid verification**

1. [ ] Launch app - no errors
2. [ ] Create one device
3. [ ] Learn one command
4. [ ] Test command works
5. [ ] Generate entities
6. [ ] Check entity ID format (no domain prefix)
7. [ ] Refresh page - data persists
8. [ ] All 4 regression tests pass

**Smoke Test Result**: ☐ PASS ☐ FAIL

---

**End of Manual Test Checklist**
