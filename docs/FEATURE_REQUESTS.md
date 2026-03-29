# Feature Requests

This document tracks user-requested features for future implementation.

## SmartIR Extra Modes as Selectable Buttons

**Status:** Proposed  
**Priority:** Medium  
**Requested By:** mansf-1 (GitHub Issue/Discussion)  
**Date:** 2026-03-29

### Description
Currently, extra modes defined in SmartIR JSON files (beyond the standard modes like cool, heat, fan_only, etc.) can be learned during the command learning phase. However, they are only accessible during learning and not exposed in the device control interface.

### Proposed Enhancement
Expose extra modes as selectable buttons in the device configuration/control step, making them easily accessible for regular use without needing to re-enter the learning workflow.

### User Benefit
- More intuitive workflow
- More convenient access to custom modes
- Better discoverability of available device modes
- Consistent with how other commands are presented

### Implementation Notes
- Parse `modes` array from SmartIR JSON
- Identify modes beyond standard set (cool, heat, fan_only, dry, auto, off)
- Generate buttons in UI for extra modes
- Wire buttons to send appropriate IR commands
- Consider grouping with other mode controls or in a separate "Custom Modes" section

### Related Code
- `frontend/src/components/smartir/CommandLearningWizard.vue` - Current learning interface
- `frontend/src/components/devices/DeviceCard.vue` - Device control interface
- `app/smartir_code_service.py` - SmartIR code parsing

### Example Use Case
A climate device JSON with modes: `["cool", "heat", "fan_only", "dry", "auto", "eco", "turbo", "sleep"]`

Currently:
- Standard modes (cool, heat, etc.) are accessible in control interface
- Extra modes (eco, turbo, sleep) only accessible during learning

Proposed:
- All modes accessible as buttons in control interface
- Extra modes clearly labeled or grouped separately

---

## Optional Stateless Entity Generation for RM4 Pro Devices

**Status:** ✅ Implemented (v0.4.0-beta.10)  
**Priority:** Medium  
**Requested By:** jakubsuchybio (GitHub Issue)  
**Date Requested:** 2026-03-29  
**Date Implemented:** 2026-03-29

### Description
When learning commands through RM4 Pro, devices like blinds cannot track state (since RM4 Pro is IR/RF transmit-only). Currently, the entity generator creates stateful entities (e.g., `cover` with state tracking via `input_boolean`), which causes issues:

- User sends "close" command → blinds start closing
- User sends "stop" command → blinds stop (half-open)
- Home Assistant shows state as "closed" (incorrect)
- User cannot send "close" again because HA thinks it's already closed

### Proposed Enhancement
Add an option during entity generation to create **stateless entities** (buttons/scripts) instead of stateful entities for devices that cannot track state.

### User Benefit
- Accurate representation of device capabilities
- No misleading state information
- Buttons always available (not disabled based on incorrect state)
- User can send any command at any time
- Better UX for one-way control devices

### Implementation Notes

**Backend Changes:**
- Add `stateless` flag to device configuration in `devices.json`
- Modify `entity_generator.py` to check for stateless flag
- When `stateless=true`, generate buttons/scripts instead of stateful entities
- Skip `input_boolean` helper generation for stateless devices

**Frontend Changes:**
- Add checkbox/toggle in device creation/edit form: "Stateless Device (no state tracking)"
- Show appropriate help text explaining when to use this option
- Update device card to show buttons instead of state controls for stateless devices

**Entity Generation Logic:**
```python
# Instead of:
cover:
  - platform: template
    covers:
      my_blinds:
        open_cover: ...
        close_cover: ...
        stop_cover: ...
        value_template: "{{ is_state('input_boolean.my_blinds_state', 'on') }}"

# Generate:
button:
  - platform: template
    buttons:
      my_blinds_open:
        press: ...
      my_blinds_close:
        press: ...
      my_blinds_stop:
        press: ...
```

### Related Code
- `app/entity_generator.py` - Entity generation logic (lines 247-462 for covers)
- `app/api/devices.py` - Device CRUD operations
- `frontend/src/components/devices/DeviceForm.vue` - Device creation/edit form
- `frontend/src/components/devices/DeviceCard.vue` - Device display

### Example Use Case
**Blinds controlled via RM4 Pro:**
- Commands: open, close, stop
- Cannot track actual position
- User wants buttons that are always available

**Current behavior:**
- Creates cover entity with state tracking
- State gets out of sync with reality
- Buttons disabled based on incorrect state

**Proposed behavior:**
- Creates three buttons: Open, Close, Stop
- No state tracking
- All buttons always available
- User manually controls based on visual observation

### LOE Estimate
**Small-Medium (4-8 hours)**

**Breakdown:**
- Backend (2-3 hours):
  - Add `stateless` field to device schema
  - Modify entity generator to support stateless mode
  - Update button generation logic
  - Skip helper generation for stateless devices
  
- Frontend (2-3 hours):
  - Add stateless toggle to device form
  - Update device card to handle stateless devices
  - Add help text and tooltips
  
- Testing (1-2 hours):
  - Test stateless entity generation
  - Verify YAML output
  - Test UI changes
  - Test migration of existing devices

**Complexity:** Low-Medium
- Mostly additive changes (new code path)
- Minimal changes to existing logic
- Clear separation between stateful and stateless modes

---

## Other Feature Requests

(Add additional feature requests below as they come in)
