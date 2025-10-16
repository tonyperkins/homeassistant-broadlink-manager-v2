# Testing Guide for Broadlink Manager v2

## Running Tests

### Setup
First, install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test Files
```bash
# Unit tests
pytest tests/unit/test_entity_generator.py -v
pytest tests/unit/test_device_api.py -v
pytest tests/unit/test_device_manager.py -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (requires Playwright)
pytest tests/e2e/ -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## Critical Tests Added

### 1. Entity ID Format Test (`test_entity_generator.py`)
**Purpose**: Ensures entity IDs are generated WITHOUT entity type prefix

**What it tests**:
- Entity IDs like `bedroom_light` (✅ correct)
- NOT `light.bedroom_light` (❌ causes "invalid slug" errors)

**Why it's critical**: 
This was a production bug where Home Assistant rejected the generated YAML because entity IDs had the domain prefix, which is invalid for template platform configurations.

**Test case**:
```python
def test_entity_id_without_type_prefix(self, generator, mock_storage):
    """Test that entity IDs are used without entity type prefix in YAML"""
    entities = {
        "bedroom_light": {  # Correct: no "light." prefix
            "device": "bedroom_light",
            "entity_type": "light",
            ...
        }
    }
    # Verify YAML doesn't contain "light.bedroom_light"
    assert "light.bedroom_light" not in entities_content
```

### 2. Device API Tests (`test_device_api.py`)
**Purpose**: Validates device creation and entity ID generation

**What it tests**:
- `normalize_device_name()` function
- Entity ID creation without type prefix
- Helper ID format (state trackers, speed selectors)
- Entity ID uniqueness checks

**Key test cases**:
```python
# Test normalization
assert normalize_device_name("Tony's Office Light") == "tony_s_office_light"

# Test entity ID format
entity_id = normalize_device_name("Bedroom Light")
assert entity_id == "bedroom_light"  # ✅
assert entity_id != "light.bedroom_light"  # ❌

# Test helper format
state_tracker = f"{entity_id}_state"
assert state_tracker == "bedroom_light_state"  # ✅
assert state_tracker != "light.bedroom_light_state"  # ❌
```

## Test Coverage Goals

### Core Functionality (Must Have)
- ✅ Entity ID format validation
- ✅ Device name normalization
- ✅ Entity generation (lights, fans, switches)
- ✅ Helper generation (input_boolean, input_select)
- ✅ Multiple entity grouping
- ✅ SmartIR device handling

### API Endpoints (Should Have)
- ✅ Device creation
- ✅ Device update
- ✅ Device deletion
- ⏳ SmartIR config update
- ⏳ Entity generation endpoint

### Integration (Nice to Have)
- ⏳ Full workflow: create device → learn commands → generate entities
- ⏳ SmartIR workflow: create device → generate SmartIR YAML
- ⏳ Migration from v1 to v2

## Common Test Patterns

### Testing Entity Generation
```python
def test_my_entity_type(self, generator, mock_storage):
    entities = {
        "my_device": {
            "device": "my_device",  # No prefix!
            "entity_type": "light",
            "name": "My Device",
            "enabled": True,
            "commands": {...},
            "broadlink_entity": "remote.test",
        }
    }
    
    mock_storage.get_all_entities = Mock(return_value=entities)
    result = generator.generate_all({})
    
    assert result["success"] is True
    
    # Read generated YAML
    with open(mock_storage.entities_file, "r") as f:
        content = f.read()
    
    # Verify correct format
    assert "my_device:" in content
    assert "light.my_device" not in content  # Critical!
```

### Testing Device API
```python
def test_device_creation():
    device_name = "Living Room TV"
    entity_type = "media_player"
    
    # Normalize name
    normalized = normalize_device_name(device_name)
    
    # Entity ID should be just the normalized name
    entity_id = normalized
    
    # Assertions
    assert entity_id == "living_room_tv"
    assert "." not in entity_id
    assert entity_id != f"{entity_type}.{normalized}"
```

## Regression Tests

### Bug: Invalid Slug Errors (Fixed)
**Symptom**: Home Assistant logs showed:
```
Invalid config for 'light' from integration 'template': 
invalid slug light.bedroom_light (try bedroom_light)
```

**Root Cause**: Entity IDs were created with type prefix (`light.bedroom_light`)

**Fix**: Remove prefix in `api/devices.py`:
```python
# Before (wrong):
entity_id = f"{entity_type}.{device_name}"

# After (correct):
entity_id = device_name
```

**Test**: `test_entity_id_without_type_prefix()` prevents regression

### Bug: SmartIR Config Not Saving (Fixed)
**Symptom**: Editing SmartIR device config didn't persist changes

**Root Cause**: `update_managed_device` wasn't extracting fields from nested `smartir_config` object

**Fix**: Extract fields to top level in `api/devices.py`

**Test**: TODO - Add test for SmartIR config persistence

## Running Tests in CI/CD

The GitHub Actions workflow (`.github/workflows/tests.yml`) runs:
1. Unit tests
2. Integration tests  
3. Code coverage report
4. Linting (flake8, black, mypy)

## Writing New Tests

1. **Identify the core functionality** you're testing
2. **Create test fixtures** for mock data
3. **Write clear test names** that describe what's being tested
4. **Add assertions** for both positive and negative cases
5. **Document why** the test is important (especially for bug fixes)

Example:
```python
def test_entity_id_format_prevents_invalid_slug_error(self):
    """
    Test that entity IDs don't include type prefix.
    
    This prevents the "invalid slug" error that occurred in production
    when Home Assistant rejected YAML with entity IDs like "light.bedroom_light"
    instead of just "bedroom_light".
    
    See: GitHub Issue #123
    """
    # Test implementation...
```

## Debugging Failed Tests

### View detailed output:
```bash
pytest tests/unit/test_device_api.py -vv
```

### Run specific test:
```bash
pytest tests/unit/test_device_api.py::TestDeviceAPI::test_entity_id_format_without_prefix -v
```

### Drop into debugger on failure:
```bash
pytest tests/unit/test_device_api.py --pdb
```

### Show print statements:
```bash
pytest tests/unit/test_device_api.py -s
```
