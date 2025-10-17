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
- ✅ Storage manager operations (CRUD, backup/recovery)
- ✅ Regression tests for known bugs

### API Endpoints (Should Have)
- ✅ Device creation
- ✅ Device update
- ✅ Device deletion
- ✅ SmartIR config update
- ✅ Entity generation endpoint
- ✅ Config API endpoints
- ✅ Diagnostics endpoints
- ✅ Input validation

### Integration (Nice to Have)
- ✅ Full workflow: create device → learn commands → generate entities
- ✅ SmartIR workflow: create device → generate SmartIR YAML
- ✅ Device validation workflows
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

All regression tests are in `tests/unit/test_regressions.py` and marked with `@pytest.mark.regression`.

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

**Test**: `TestEntityIDPrefixRegression` class prevents regression

### Bug: Fan Direction Helper Missing (Fixed)
**Symptom**: Fan entities failed validation with "show_direction_control - Expected a value of type 'never'"

**Root Cause**: Direction helper only created if fan had reverse command, but direction_template always referenced it

**Fix**: Always create direction helper for all fans

**Test**: `TestFanDirectionHelperRegression` class prevents regression

### Bug: SmartIR Config Not Saving (Fixed)
**Symptom**: Editing SmartIR device config didn't persist changes

**Root Cause**: `update_managed_device` wasn't extracting fields from nested `smartir_config` object

**Fix**: Extract fields to top level in `api/devices.py`

**Test**: `TestSmartIRConfigPersistenceRegression` class prevents regression

### Bug: SmartIR Controller Data Format (Fixed)
**Symptom**: SmartIR devices failed with "entity not found" errors

**Root Cause**: controller_data used IP addresses instead of entity IDs

**Fix**: Use entity IDs (e.g., "remote.bedroom_rm4") not IPs

**Test**: `TestSmartIRControllerDataRegression` class prevents regression

### Bug: Data Loss on Interrupted Writes (Fixed)
**Symptom**: Corrupted devices.json/metadata.json files causing permanent data loss

**Root Cause**: Non-atomic writes could be interrupted

**Fix**: Atomic writes with backup before save

**Test**: `TestBackupRecoveryRegression` class prevents regression

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

## New Test Files Added

### Unit Tests
- **`test_storage_manager.py`** - Comprehensive tests for StorageManager
  - Initialization and setup
  - Entity CRUD operations
  - Backup and recovery functionality
  - Metadata management
  - Edge cases and error handling
  - Unicode and special character handling
  - Coverage: Targets 15% → 80%+

- **`test_regressions.py`** - Regression tests for known bugs
  - Entity ID prefix bug
  - Fan direction helper bug
  - SmartIR config persistence bug
  - SmartIR controller_data format bug
  - Device name normalization issues
  - Data loss on interrupted writes
  - Multiple entity grouping issues

### Integration Tests
- **`test_smartir_api.py`** - SmartIR API endpoint tests
  - SmartIR device creation (climate, media_player, fan)
  - Code retrieval from aggregator
  - Device index functionality
  - Validation (codes, controllers, platforms)
  - YAML generation
  - Device lifecycle (CRUD)
  - Different controller types (Broadlink, Xiaomi, Harmony)
  - Error handling
  - Coverage: Targets 0% → 60%+

- **`test_config_api.py`** - Configuration API tests
  - Config retrieval
  - System information
  - HA connection status
  - Broadlink device discovery
  - Area configuration
  - Storage paths
  - Deployment mode
  - Version information
  - Config validation
  - Diagnostics endpoints
  - Health checks
  - Error handling
  - Coverage: Targets 18% → 70%+

- **`test_device_validation.py`** - Device validation tests
  - Device name validation (special chars, Unicode, length)
  - Entity type validation
  - Broadlink entity validation
  - Area validation
  - Duplicate device handling
  - Command validation
  - Update validation
  - Readonly field protection
  - Coverage: Improves overall API validation

## Test Organization Best Practices

### Test File Naming
- Unit tests: `test_<module_name>.py`
- Integration tests: `test_<feature>_api.py` or `test_<workflow>.py`
- E2E tests: `test_<user_flow>.py`
- Regression tests: `test_regressions.py`

### Test Class Naming
- Descriptive class names: `TestStorageManagerInitialization`, `TestSmartIRDeviceEndpoints`
- Group related tests together
- Use inheritance for shared fixtures

### Test Function Naming
- Start with `test_`
- Be descriptive: `test_create_device_with_special_characters`
- Include expected outcome: `test_empty_name_is_rejected`

### Markers
Use pytest markers to categorize tests:
```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # API/workflow tests
@pytest.mark.e2e           # Browser tests
@pytest.mark.regression    # Bug regression tests
@pytest.mark.slow          # Long-running tests
@pytest.mark.requires_ha   # Needs HA connection
@pytest.mark.requires_device  # Needs physical device
```

### Fixtures
- Keep fixtures in `conftest.py` for reusability
- Use scope appropriately: `function`, `class`, `module`, `session`
- Name fixtures clearly: `mock_storage`, `temp_storage_dir`, `client`

## Running Specific Test Categories

### Run only unit tests:
```bash
pytest tests/unit/ -v
```

### Run only integration tests:
```bash
pytest tests/integration/ -v
```

### Run only regression tests:
```bash
pytest tests/ -v -m regression
```

### Run tests for specific module:
```bash
pytest tests/unit/test_storage_manager.py -v
```

### Run with coverage for specific module:
```bash
pytest tests/unit/test_storage_manager.py --cov=app.storage_manager --cov-report=term-missing
```

## Coverage Improvement Strategy

### Before Enhancement (Baseline)
- Overall: 3% (4,554 of 4,759 statements missed)
- storage_manager.py: 15%
- api/smartir.py: 0%
- api/devices.py: 7%
- api/config.py: 18%
- api/commands.py: 6%

### After Enhancement (Target)
- Overall: 40%+ (significant improvement)
- storage_manager.py: 80%+
- api/smartir.py: 60%+
- api/devices.py: 50%+
- api/config.py: 70%+
- Regression coverage: 100% (all known bugs tested)

### Next Steps for Full Coverage
1. Add tests for `api/commands.py` (command learning/sending)
2. Add tests for `entity_detector.py` (entity discovery)
3. Add tests for `smartir_code_service.py` (code aggregator integration)
4. Add tests for `web_server.py` (Flask app initialization)
5. Add tests for `migration_manager.py` (v1 to v2 migration)

## Continuous Integration

### GitHub Actions Workflow
The `.github/workflows/tests.yml` should run:
1. All unit tests (fast feedback)
2. Integration tests (API validation)
3. Regression tests (prevent regressions)
4. Coverage report (track progress)
5. E2E tests (optional, slower)

### Pre-commit Hooks
Consider adding:
```bash
# Run fast tests before commit
pytest tests/unit/ -v --tb=short

# Run linting
flake8 app/
black --check app/
```

## Troubleshooting Common Test Failures

### Import Errors
- Ensure `app/` is in Python path
- Check `sys.path.insert(0, ...)` in test files

### Fixture Not Found
- Check `conftest.py` for fixture definition
- Verify fixture scope matches usage

### Temp Directory Issues
- Use `tempfile.TemporaryDirectory()` context manager
- Ensure cleanup in fixture teardown

### Mock Issues
- Use `unittest.mock.Mock` for simple mocks
- Use `@patch` decorator for patching modules
- Verify mock return values match expected types

### Async Test Failures
- Use `pytest-asyncio` for async tests
- Mark async tests with `@pytest.mark.asyncio`

## Test Maintenance

### When Adding New Features
1. Write tests BEFORE implementing (TDD)
2. Test happy path AND error cases
3. Add regression test if fixing a bug
4. Update TESTING_GUIDE.md with new patterns

### When Modifying Existing Code
1. Run affected tests first
2. Update tests to match new behavior
3. Don't delete tests without good reason
4. Maintain backward compatibility when possible

### Code Review Checklist
- [ ] New code has tests
- [ ] Tests cover edge cases
- [ ] Regression tests for bug fixes
- [ ] Tests are documented
- [ ] Coverage increased (or maintained)
- [ ] All tests pass locally
