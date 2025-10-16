# Mock Services for Testing

This directory contains mock implementations of Home Assistant services used for testing.

## Overview

These mocks simulate the behavior of Home Assistant's Broadlink integration and related services, allowing tests to run without a real HA instance.

## Mock Modules

### `ha_api_mock.py` - Home Assistant REST API Mock

Simulates Home Assistant's REST API for service calls and state queries.

**Key Features:**
- Service call simulation (learn_command, delete_command, send_command)
- State management
- Notification creation
- Area management
- Service call tracking for verification

**Usage:**
```python
from tests.mocks import MockHAAPI

api = MockHAAPI()

# Add Broadlink device
api.add_broadlink_device(
    "remote.bedroom_rm4",
    "Bedroom RM4",
    "bedroom",
    "abc123"
)

# Simulate service call
result = await api.make_request(
    "POST",
    "services/remote/learn_command",
    {
        "entity_id": "remote.bedroom_rm4",
        "device": "tv",
        "command": "power"
    }
)

# Verify service was called
calls = api.get_service_calls("remote.learn_command")
assert len(calls) == 1
```

### `broadlink_storage_mock.py` - Broadlink Storage Mock

Simulates the `~/.homeassistant/.storage/broadlink_remote_*_codes` files that store learned commands.

**Key Features:**
- Storage file creation and management
- Command addition and deletion
- Command existence checking
- Storage file listing

**Usage:**
```python
from tests.mocks import MockBroadlinkStorage
from pathlib import Path

storage = MockBroadlinkStorage(Path("/tmp/test"))

# Add command to storage
storage.add_command(
    "abc123",  # device unique_id
    "tv",      # device name
    "power",   # command name
    "JgBQAAA..."  # IR code
)

# Check if command exists
exists = storage.command_exists("abc123", "tv", "power")

# Get all commands for a device
commands = storage.get_device_commands("abc123", "tv")

# Delete command
storage.delete_command("abc123", "tv", "power")
```

### `websocket_mock.py` - WebSocket API Mock

Simulates Home Assistant's WebSocket API for area management and entity registry operations.

**Key Features:**
- Area creation and management
- Entity registry operations
- Entity-to-area assignment
- Service calls via WebSocket

**Usage:**
```python
from tests.mocks import MockWebSocketAPI

ws = MockWebSocketAPI()

# Add area
ws.add_area("bedroom", "Bedroom")

# Add entity to registry
ws.add_entity("light.bedroom_light", area_id="bedroom")

# Send WebSocket command
result = await ws.send_command(
    "config/entity_registry/update",
    entity_id="light.bedroom_light",
    area_id="bedroom"
)

# Check entity
entity = ws.get_entity("light.bedroom_light")
assert entity["area_id"] == "bedroom"
```

## Using Mocks in Tests

### Via Fixtures

The recommended way to use mocks is through pytest fixtures defined in `conftest.py`:

```python
import pytest

@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_mocks(mock_ha_api, mock_broadlink_storage, mock_websocket_api):
    # Mocks are automatically set up and cleaned up
    
    # Use mock_ha_api
    mock_ha_api.add_broadlink_device("remote.test", "Test", "test")
    
    # Use mock_broadlink_storage
    mock_broadlink_storage.add_command("test", "device", "cmd", "code")
    
    # Use mock_websocket_api
    mock_websocket_api.add_entity("light.test")
```

### Direct Instantiation

You can also create mocks directly:

```python
from tests.mocks import MockHAAPI, MockBroadlinkStorage, MockWebSocketAPI
from pathlib import Path

def test_direct():
    api = MockHAAPI()
    storage = MockBroadlinkStorage(Path("/tmp/test"))
    ws = MockWebSocketAPI()
    
    # Use mocks...
    
    # Clean up
    api.reset()
    storage.clear()
    ws.reset()
```

## Mock Behavior

### MockHAAPI

**Service Calls:**
- `learn_command` - Records call, creates notification, returns `[]`
- `delete_command` - Records call, returns `[]`
- `send_command` - Records call, returns `[]`

**State Queries:**
- `GET /api/states` - Returns all states
- `GET /api/states/{entity_id}` - Returns specific state
- `GET /api/persistent_notification` - Returns notifications

**Area Management:**
- `GET /api/config/area_registry/list` - Returns all areas

### MockBroadlinkStorage

**File Structure:**
```json
{
  "version": 1,
  "data": {
    "device_name": {
      "command_name": "IR_CODE_BASE64"
    }
  }
}
```

**Operations:**
- `create_storage_file()` - Creates/updates storage file
- `add_command()` - Adds single command
- `delete_command()` - Removes command
- `get_all_commands()` - Gets all commands
- `command_exists()` - Checks existence

### MockWebSocketAPI

**Commands:**
- `config/area_registry/list` - List all areas
- `config/area_registry/create` - Create new area
- `config/entity_registry/update` - Update entity
- `config/entity_registry/get` - Get entity
- `call_service` - Call HA service

**State:**
- Maintains in-memory registry of areas and entities
- Simulates WebSocket connection state

## Testing Patterns

### Pattern 1: Test Service Call

```python
async def test_service_call(mock_ha_api):
    result = await mock_ha_api.make_request(
        "POST",
        "services/remote/learn_command",
        {"entity_id": "remote.test", "device": "tv", "command": "power"}
    )
    
    assert result == []
    assert len(mock_ha_api.services_called) == 1
```

### Pattern 2: Test Storage Operations

```python
def test_storage(mock_broadlink_storage):
    mock_broadlink_storage.add_command("dev", "tv", "power", "CODE")
    
    assert mock_broadlink_storage.command_exists("dev", "tv", "power")
    
    commands = mock_broadlink_storage.get_device_commands("dev", "tv")
    assert "power" in commands
```

### Pattern 3: Test Area Assignment

```python
async def test_area_assignment(mock_websocket_api):
    mock_websocket_api.add_entity("light.test")
    
    result = await mock_websocket_api.send_command(
        "config/entity_registry/update",
        entity_id="light.test",
        area_id="bedroom"
    )
    
    assert result is not None
    assert result["area_id"] == "bedroom"
```

## Cleanup

All mocks provide cleanup methods:

```python
# MockHAAPI
api.reset()  # Clears all data
api.clear_service_calls()  # Clears only service calls
api.clear_notifications()  # Clears only notifications

# MockBroadlinkStorage
storage.clear()  # Removes all storage files and data

# MockWebSocketAPI
ws.reset()  # Clears all data
ws.clear_entities()  # Clears only entities
ws.clear_areas()  # Clears only areas
```

## Best Practices

1. **Use fixtures** - Let pytest manage mock lifecycle
2. **Verify calls** - Always check that expected services were called
3. **Clean state** - Ensure mocks are reset between tests
4. **Simulate reality** - Make mocks behave like real HA
5. **Test edge cases** - Use mocks to test error conditions

## Extending Mocks

To add new functionality:

1. Add method to appropriate mock class
2. Update mock's `make_request()` or `send_command()` to handle new endpoint
3. Add tests for new functionality
4. Update this README

Example:
```python
# In ha_api_mock.py
async def _mock_new_service(self, data: Dict) -> List:
    """Mock a new service"""
    self.services_called.append({
        "service": "new.service",
        "data": data
    })
    return []

# In make_request()
elif endpoint == "services/new/service":
    return await self._mock_new_service(data)
```

## Troubleshooting

### Mock not working as expected
- Check that you're using the correct fixture
- Verify mock is properly initialized
- Check cleanup is happening

### Service calls not recorded
- Ensure you're calling `make_request()` or `send_command()`
- Check endpoint path matches mock implementation
- Verify data format matches expected structure

### Storage files not created
- Check temp directory exists
- Verify unique_id is correct
- Ensure `create_storage_file()` is called

## See Also

- `tests/conftest.py` - Fixture definitions
- `docs/development/TESTING_FRAMEWORK_DESIGN.md` - Architecture
- `docs/development/TESTING_QUICK_START.md` - Quick reference
- `tests/unit/` - Example tests using mocks
