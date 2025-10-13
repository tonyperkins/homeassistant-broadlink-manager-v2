# Testing Guide for Broadlink Manager

This document provides comprehensive testing guidance for the Broadlink Manager add-on, including automated tests and manual test procedures.

## Table of Contents

- [Automated Testing](#automated-testing)
- [Manual Testing](#manual-testing)
- [Test Coverage](#test-coverage)
- [Continuous Integration](#continuous-integration)

---

## Automated Testing

### Test Framework

The project uses **pytest** as the primary testing framework with the following plugins:

- **pytest** - Core testing framework
- **pytest-flask** - Flask application testing
- **pytest-cov** - Code coverage reporting
- **pytest-mock** - Mocking and fixtures
- **pytest-asyncio** - Async code testing
- **responses** - HTTP request mocking

### Installation

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Or install individually:

```bash
pip install pytest pytest-flask pytest-cov pytest-mock pytest-asyncio responses
```

### Running Tests

#### Run All Tests

```bash
pytest
```

#### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Exclude slow tests
pytest -m "not slow"

# Exclude tests requiring actual devices
pytest -m "not requires_device"
```

#### Run Specific Test Files

```bash
# Test device manager
pytest tests/unit/test_device_manager.py

# Test API endpoints
pytest tests/integration/test_api_endpoints.py
```

#### Run with Coverage Report

```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

#### Verbose Output

```bash
pytest -v
pytest -vv  # Extra verbose
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures and configuration
├── unit/                          # Unit tests
│   ├── __init__.py
│   ├── test_device_manager.py    # DeviceManager tests
│   ├── test_area_manager.py      # AreaManager tests
│   └── test_storage_manager.py   # StorageManager tests
└── integration/                   # Integration tests
    ├── __init__.py
    └── test_api_endpoints.py     # API endpoint tests
```

### Test Markers

Tests are categorized using pytest markers:

- `@pytest.mark.unit` - Unit tests for individual components
- `@pytest.mark.integration` - Integration tests for API endpoints
- `@pytest.mark.slow` - Tests that take longer to run
- `@pytest.mark.requires_ha` - Tests requiring Home Assistant connection
- `@pytest.mark.requires_device` - Tests requiring actual Broadlink device

### Writing New Tests

#### Example Unit Test

```python
import pytest

@pytest.mark.unit
def test_device_creation(device_manager, sample_device_data):
    """Test creating a new device"""
    result = device_manager.create_device('test_device', sample_device_data)
    assert result is True
    
    device = device_manager.get_device('test_device')
    assert device is not None
    assert device['name'] == sample_device_data['name']
```

#### Example Integration Test

```python
import pytest
import json

@pytest.mark.integration
def test_api_create_device(client, sample_device_data):
    """Test device creation via API"""
    response = client.post(
        '/api/devices',
        data=json.dumps({
            'device_id': 'test_device',
            'device_data': sample_device_data
        }),
        content_type='application/json'
    )
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['success'] is True
```

---

## Manual Testing

### Manual Test Plan

This section provides step-by-step manual test procedures for features that require human verification or actual hardware.

---

## 1. Installation and Startup Tests

### 1.1 Fresh Installation (First-Time User)

**Objective**: Verify clean installation experience

**Prerequisites**:
- Home Assistant OS/Supervised installation
- No existing Broadlink Manager installation
- At least one Broadlink device configured

**Steps**:
1. Add repository to Home Assistant
2. Install Broadlink Manager add-on
3. Start the add-on
4. Access web interface at `http://homeassistant.local:8099`

**Expected Results**:
- ✅ Add-on installs without errors
- ✅ Add-on starts successfully
- ✅ Web interface loads and shows welcome screen
- ✅ Broadlink devices are detected and listed
- ✅ No errors in add-on logs

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 1.2 Upgrade from Previous Version

**Objective**: Verify smooth upgrade process

**Prerequisites**:
- Existing Broadlink Manager installation
- Existing devices and commands

**Steps**:
1. Note current version number
2. Update to new version via Add-on Store
3. Restart add-on
4. Access web interface
5. Verify all existing devices and commands are present

**Expected Results**:
- ✅ Upgrade completes without errors
- ✅ All existing data preserved
- ✅ New features available
- ✅ No data loss

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 1.3 Automatic Migration (Existing Broadlink Users)

**Objective**: Verify automatic command discovery and migration

**Prerequisites**:
- Home Assistant with existing Broadlink commands
- Commands stored in `.storage/broadlink_remote_*_codes` files
- No existing Broadlink Manager installation

**Steps**:
1. Install and start Broadlink Manager
2. Check add-on logs for migration messages
3. Access web interface
4. Verify all existing commands are discovered

**Expected Results**:
- ✅ Migration runs automatically on first start
- ✅ All existing commands discovered
- ✅ Commands properly organized by device
- ✅ Migration summary shown in logs
- ✅ Original storage files unchanged

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 2. Device Management Tests

### 2.1 Create New Device

**Objective**: Verify device creation workflow

**Steps**:
1. Click "Add Device" button
2. Select area (e.g., "Master Bedroom")
3. Enter device name (e.g., "Samsung TV")
4. Select device type (e.g., "TV")
5. Select Broadlink entity
6. Enter manufacturer and model (optional)
7. Click "Save"

**Expected Results**:
- ✅ Device appears in device list
- ✅ Device ID generated correctly (e.g., `master_bedroom_samsung_tv`)
- ✅ All metadata saved correctly
- ✅ Success message displayed

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 2.2 Edit Device

**Objective**: Verify device editing functionality

**Steps**:
1. Select existing device
2. Click "Edit" button
3. Modify device name
4. Change device type
5. Update manufacturer/model
6. Click "Save"

**Expected Results**:
- ✅ Changes saved successfully
- ✅ Device list updates immediately
- ✅ Commands preserved
- ✅ Timestamp updated

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 2.3 Delete Device

**Objective**: Verify device deletion with confirmation

**Steps**:
1. Select device with commands
2. Click "Delete" button
3. Confirm deletion in dialog
4. Verify device removed from list

**Expected Results**:
- ✅ Confirmation dialog appears
- ✅ Device and all commands deleted
- ✅ Device removed from UI
- ✅ Success message displayed

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 3. Command Learning Tests

### 3.1 Learn IR Command

**Objective**: Verify IR command learning process

**Prerequisites**:
- Broadlink device in learning mode range
- IR remote control

**Steps**:
1. Select device
2. Click "Add Command"
3. Enter command name (e.g., "power")
4. Click "Learn" button
5. Point remote at Broadlink device
6. Press button on remote within 30 seconds
7. Wait for confirmation

**Expected Results**:
- ✅ Learning mode activated
- ✅ Countdown timer displayed
- ✅ Command captured successfully
- ✅ Success message with code preview
- ✅ Command appears in command list
- ✅ Command code stored correctly

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 3.2 Learn RF Command

**Objective**: Verify RF command learning (if supported)

**Prerequisites**:
- Broadlink device with RF support (e.g., RM4 Pro)
- RF remote control

**Steps**:
1. Select device
2. Add command with RF type
3. Click "Learn"
4. Press button on RF remote
5. Verify capture

**Expected Results**:
- ✅ RF learning mode activated
- ✅ Command captured
- ✅ RF code stored correctly

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 3.3 Learning Timeout

**Objective**: Verify timeout handling

**Steps**:
1. Click "Learn" button
2. Do NOT press any remote button
3. Wait for 30-second timeout

**Expected Results**:
- ✅ Timeout message displayed
- ✅ Learning mode exits gracefully
- ✅ No command created
- ✅ Can retry immediately

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 4. Command Testing Tests

### 4.1 Test Learned Command

**Objective**: Verify command testing functionality

**Prerequisites**:
- Device with learned command
- Target device in range

**Steps**:
1. Select device with commands
2. Click "Test" button next to command
3. Observe target device response

**Expected Results**:
- ✅ Command sent successfully
- ✅ Target device responds correctly
- ✅ Success message displayed
- ✅ No errors in logs

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 4.2 Test Multiple Commands

**Objective**: Verify rapid command testing

**Steps**:
1. Test command 1
2. Immediately test command 2
3. Test command 3
4. Verify all commands work

**Expected Results**:
- ✅ All commands sent successfully
- ✅ No rate limiting issues
- ✅ Target device responds to all commands

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 5. Entity Generation Tests

### 5.1 Auto-Detect Entity Types

**Objective**: Verify automatic entity type detection

**Prerequisites**:
- Device with commands using naming conventions

**Steps**:
1. Create device with commands:
   - `light_on`
   - `light_off`
   - `fan_speed_1`
   - `fan_speed_2`
   - `fan_off`
2. Click "Generate Entities"
3. Review detected entity types

**Expected Results**:
- ✅ Light entity detected (on/off commands)
- ✅ Fan entity detected (speed commands)
- ✅ Correct command roles assigned
- ✅ Entity preview shown

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 5.2 Generate Entity Files

**Objective**: Verify entity file generation

**Steps**:
1. Configure entities for devices
2. Click "Generate Entities" button
3. Check `/config/broadlink_manager/` directory
4. Verify files created:
   - `entities.yaml`
   - `helpers.yaml`
   - `package.yaml`

**Expected Results**:
- ✅ All files created successfully
- ✅ Valid YAML syntax
- ✅ Correct entity definitions
- ✅ Helper entities included
- ✅ Success message displayed

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 5.3 Test Generated Entities in Home Assistant

**Objective**: Verify generated entities work in HA

**Prerequisites**:
- Entity files generated
- Files included in `configuration.yaml`

**Steps**:
1. Add includes to `configuration.yaml`:
   ```yaml
   light: !include broadlink_manager/entities.yaml
   fan: !include broadlink_manager/entities.yaml
   switch: !include broadlink_manager/entities.yaml
   input_boolean: !include broadlink_manager/helpers.yaml
   input_select: !include broadlink_manager/helpers.yaml
   ```
2. Restart Home Assistant
3. Check Developer Tools > States
4. Test entity controls

**Expected Results**:
- ✅ Home Assistant restarts without errors
- ✅ All entities appear in States
- ✅ Light entities toggle correctly
- ✅ Fan entities change speed correctly
- ✅ Switch entities work correctly
- ✅ Helper entities created

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 6. Area Management Tests

### 6.1 Create Area

**Objective**: Verify area creation

**Steps**:
1. Click "Manage Areas"
2. Click "Add Area"
3. Enter area name (e.g., "Guest Bedroom")
4. Select icon
5. Select floor
6. Click "Save"

**Expected Results**:
- ✅ Area created successfully
- ✅ Area appears in area list
- ✅ Area available in device creation dropdown

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 7. Error Handling Tests

### 7.1 Network Disconnection

**Objective**: Verify behavior when Home Assistant is unreachable

**Steps**:
1. Disconnect network or stop Home Assistant
2. Try to learn a command
3. Try to send a command
4. Reconnect network

**Expected Results**:
- ✅ Appropriate error messages displayed
- ✅ No crashes or hangs
- ✅ Graceful recovery after reconnection

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 7.2 Invalid Input Handling

**Objective**: Verify input validation

**Steps**:
1. Try to create device with empty name
2. Try to create device with invalid characters
3. Try to learn command with empty name
4. Try to delete non-existent device

**Expected Results**:
- ✅ Validation errors displayed
- ✅ No data corruption
- ✅ Clear error messages

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 8. Performance Tests

### 8.1 Large Command Set

**Objective**: Verify performance with many commands

**Prerequisites**:
- Device with 50+ commands

**Steps**:
1. Create device
2. Learn 50+ commands
3. Navigate command list
4. Search/filter commands
5. Generate entities

**Expected Results**:
- ✅ UI remains responsive
- ✅ Command list loads quickly
- ✅ Search/filter works smoothly
- ✅ Entity generation completes in reasonable time

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 8.2 Multiple Devices

**Objective**: Verify performance with many devices

**Steps**:
1. Create 10+ devices
2. Add commands to each
3. Navigate between devices
4. Generate entities for all

**Expected Results**:
- ✅ UI remains responsive
- ✅ Device switching is smooth
- ✅ No memory leaks
- ✅ Entity generation handles all devices

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 9. Browser Compatibility Tests

### 9.1 Chrome/Edge

**Objective**: Verify full functionality in Chrome/Edge

**Steps**:
1. Access web interface in Chrome/Edge
2. Test all major features
3. Check console for errors

**Expected Results**:
- ✅ All features work correctly
- ✅ UI renders properly
- ✅ No console errors

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 9.2 Firefox

**Objective**: Verify full functionality in Firefox

**Steps**:
1. Access web interface in Firefox
2. Test all major features
3. Check console for errors

**Expected Results**:
- ✅ All features work correctly
- ✅ UI renders properly
- ✅ No console errors

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 9.3 Safari (if applicable)

**Objective**: Verify full functionality in Safari

**Steps**:
1. Access web interface in Safari
2. Test all major features
3. Check console for errors

**Expected Results**:
- ✅ All features work correctly
- ✅ UI renders properly
- ✅ No console errors

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## 10. Mobile Responsiveness Tests

### 10.1 Mobile Browser (Phone)

**Objective**: Verify mobile responsiveness

**Steps**:
1. Access interface on mobile phone
2. Test device creation
3. Test command learning
4. Test command testing
5. Verify touch interactions

**Expected Results**:
- ✅ UI adapts to mobile screen
- ✅ All buttons accessible
- ✅ Touch interactions work
- ✅ No horizontal scrolling
- ✅ Readable text size

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

### 10.2 Tablet

**Objective**: Verify tablet responsiveness

**Steps**:
1. Access interface on tablet
2. Test in portrait and landscape
3. Verify all features work

**Expected Results**:
- ✅ UI adapts to tablet screen
- ✅ Both orientations work well
- ✅ All features accessible

**Status**: [ ] Pass [ ] Fail [ ] N/A

**Notes**: _______________________________________________

---

## Test Coverage

### Current Coverage Goals

- **Unit Tests**: > 80% code coverage
- **Integration Tests**: All API endpoints
- **Manual Tests**: All user-facing features

### Generating Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

### Coverage by Module

Target coverage by module:

| Module | Target | Current |
|--------|--------|---------|
| device_manager.py | 90% | TBD |
| area_manager.py | 90% | TBD |
| storage_manager.py | 85% | TBD |
| entity_generator.py | 80% | TBD |
| web_server.py | 75% | TBD |
| migration_manager.py | 80% | TBD |

---

## Continuous Integration

### GitHub Actions (Recommended)

Create `.github/workflows/tests.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Troubleshooting Tests

### Common Issues

#### Import Errors

```bash
# Ensure app directory is in Python path
export PYTHONPATH="${PYTHONPATH}:./app"
```

#### Fixture Not Found

Check that `conftest.py` is in the correct location and fixtures are defined properly.

#### Tests Fail with Real Devices

Use markers to skip device-dependent tests:

```bash
pytest -m "not requires_device"
```

#### Coverage Not Working

Ensure pytest-cov is installed:

```bash
pip install pytest-cov
```

---

## Contributing Tests

When contributing new features:

1. **Write tests first** (TDD approach recommended)
2. **Ensure tests pass** before submitting PR
3. **Maintain coverage** - don't decrease overall coverage
4. **Add manual test cases** for UI features
5. **Document test scenarios** in this file

---

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-flask Documentation](https://pytest-flask.readthedocs.io/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

---

## Test Execution Checklist

Before each release, complete this checklist:

- [ ] All automated tests pass
- [ ] Code coverage > 80%
- [ ] Manual test plan completed
- [ ] No critical bugs identified
- [ ] Performance tests acceptable
- [ ] Browser compatibility verified
- [ ] Mobile responsiveness verified
- [ ] Documentation updated
- [ ] Changelog updated

---

**Last Updated**: 2025-01-12
**Version**: 1.0.0
