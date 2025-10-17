# Testing Framework Setup Summary

## What Was Created

A comprehensive testing framework for Broadlink Manager v2 that mocks Home Assistant services, allowing unit and integration tests to run without a real HA instance.

## Files Created

### 1. Mock Service Implementations (`tests/mocks/`)

- **`ha_api_mock.py`** - Mock Home Assistant REST API
  - Simulates service calls (learn_command, delete_command, send_command)
  - Tracks service calls for verification
  - Creates notifications
  - Manages areas and states

- **`broadlink_storage_mock.py`** - Mock Broadlink storage files
  - Simulates `~/.homeassistant/.storage/broadlink_remote_*_codes` files
  - Manages command storage and retrieval
  - Handles command deletion

- **`websocket_mock.py`** - Mock WebSocket API
  - Simulates area management
  - Entity registry operations
  - Service calls via WebSocket

### 2. Test Fixtures (`tests/conftest.py`)

Enhanced with new fixtures:
- `mock_ha_api` - Mocked HA REST API
- `mock_broadlink_storage` - Mocked storage files
- `mock_websocket_api` - Mocked WebSocket API
- `web_server_with_mocks` - Full web server with mocked dependencies
- `entity_generator` - Entity generator instance
- `area_manager_with_mock` - Area manager with mocked WebSocket
- `sample_entity_config` - Sample entity configuration
- `sample_ir_code` - Sample IR code

### 3. Example Test Files

- **`tests/unit/test_command_learning.py`** - Command learning tests
  - Test successful learning
  - Test RF vs IR commands
  - Test legacy format support
  - Test multiple commands
  - Test notification creation

- **`tests/unit/test_command_deletion.py`** - Command deletion tests
  - Test successful deletion
  - Test nonexistent command deletion
  - Test storage cleanup
  - Test multiple deletions

- **`tests/unit/test_area_assignment.py`** - Area management tests
  - Test getting/creating areas
  - Test entity assignment
  - Test bulk operations
  - Test missing area handling

- **`tests/integration/test_full_workflow.py`** - Integration tests
  - Test complete device creation workflow
  - Test fan with multiple speeds
  - Test multiple devices in same area

### 4. Documentation

- **`docs/development/TESTING_FRAMEWORK_DESIGN.md`** - Comprehensive design document
  - Architecture overview
  - Mock implementation details
  - Testing patterns
  - Best practices

- **`docs/development/TESTING_QUICK_START.md`** - Quick reference guide
  - Common test patterns
  - Available fixtures
  - Running tests
  - Debugging tips

## Key Features

### ✅ No Real HA Required
Tests run completely isolated without needing a running Home Assistant instance.

### ✅ Fast Execution
Mock services respond instantly, making tests run quickly.

### ✅ Deterministic
Tests produce consistent, repeatable results.

### ✅ Safe
No risk of corrupting real HA configuration or storage.

### ✅ Comprehensive Coverage
Can test:
- Command learning (IR and RF)
- Command deletion
- Command sending
- Entity generation
- Area management
- Full workflows
- Error conditions

### ✅ Easy to Use
Simple fixtures and clear examples make writing tests straightforward.

## How to Use

### Install Dependencies
```bash
pip install -r requirements-test.txt
```

### Run Tests
```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Write a Test
```python
import pytest

@pytest.mark.unit
@pytest.mark.asyncio
async def test_my_feature(web_server_with_mocks, mock_ha_api):
    server = web_server_with_mocks
    
    # Test your feature
    result = await server._learn_command({
        "entity_id": "remote.test",
        "device": "tv",
        "command": "power"
    })
    
    # Verify results
    assert result["success"] is True
    assert len(mock_ha_api.services_called) == 1
```

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual components in isolation
- Mock all external dependencies
- Fast execution
- High coverage of edge cases

### Integration Tests (`tests/integration/`)
- Test complete workflows
- Multiple components working together
- Verify end-to-end functionality
- Ensure components integrate correctly

### E2E Tests (`tests/e2e/`)
- Browser-based tests with Playwright
- Test actual UI interactions
- Verify accessibility
- Slower but comprehensive

## What Can Be Tested

### ✅ Broadlink Integration API
- Learning commands (IR/RF)
- Deleting commands
- Sending commands
- Reading storage files
- Notifications

### ✅ Entity Generation
- YAML file creation
- Multiple entity types (light, fan, switch, media_player, cover)
- Helper entities (input_boolean, input_select)
- Entity ID format validation
- Command mapping

### ✅ Area Management
- Getting/creating areas
- Assigning entities to areas
- Bulk operations
- WebSocket communication

### ✅ Device Management
- Creating devices
- Updating devices
- Deleting devices
- Command storage
- Metadata management

### ✅ Full Workflows
- Device creation → command learning → entity generation
- Multiple devices in same area
- Different entity types
- Error handling

## Important Notes

### Entity ID Format
**CRITICAL**: Always verify entity IDs don't have type prefix:
```python
# ✅ Correct
entity_id = "bedroom_light"

# ❌ Wrong
entity_id = "light.bedroom_light"
```

This was a production bug that caused "invalid slug" errors in Home Assistant.

### Mock Cleanup
Fixtures automatically clean up after tests using `yield`:
```python
@pytest.fixture
def mock_ha_api():
    api = MockHAAPI()
    yield api
    api.reset()  # Cleanup happens here
```

### Async Tests
Use `@pytest.mark.asyncio` for async test functions:
```python
@pytest.mark.asyncio
async def test_async_feature():
    result = await some_async_function()
    assert result is not None
```

## Next Steps

1. **Run existing tests** to verify setup:
   ```bash
   pytest tests/unit/test_device_manager.py -v
   pytest tests/unit/test_command_learning.py -v
   ```

2. **Write tests for new features** using the provided patterns

3. **Add tests for bug fixes** to prevent regressions

4. **Maintain test coverage** - aim for >80% coverage

5. **Update tests** when changing functionality

## Benefits

- **Faster development** - Catch bugs early
- **Confidence in changes** - Tests verify nothing breaks
- **Documentation** - Tests show how code should be used
- **Refactoring safety** - Tests ensure behavior stays consistent
- **Regression prevention** - Tests catch when bugs reappear

## Resources

- **Design Document**: `docs/development/TESTING_FRAMEWORK_DESIGN.md`
- **Quick Start**: `docs/development/TESTING_QUICK_START.md`
- **Testing Guide**: `tests/TESTING_GUIDE.md`
- **Example Tests**: `tests/unit/` and `tests/integration/`
- **Pytest Docs**: https://docs.pytest.org/

## Support

For questions or issues:
1. Check the documentation in `docs/development/`
2. Look at existing tests for examples
3. Run `pytest --fixtures` to see available fixtures
4. Check pytest documentation for advanced features
