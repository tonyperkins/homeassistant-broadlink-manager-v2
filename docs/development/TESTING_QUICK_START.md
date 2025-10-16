# Testing Quick Start Guide

## Overview

This guide provides quick examples for writing tests using the mocked Home Assistant services.

## Running Tests

```bash
# Install dependencies
pip install -r requirements-test.txt

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_command_learning.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Run tests matching a pattern
pytest tests/ -k "learning" -v
```

## Available Mock Fixtures

### 1. `mock_ha_api` - Mock Home Assistant REST API

Simulates HA's REST API for service calls and state queries.

```python
async def test_example(mock_ha_api):
    # Mock already has default Broadlink devices and areas
    
    # Add custom device
    mock_ha_api.add_broadlink_device(
        "remote.office_rm4",
        "Office RM4",
        "office",
        "xyz789"
    )
    
    # Add custom area
    mock_ha_api.add_area("garage", "Garage")
    
    # Check service calls
    calls = mock_ha_api.get_service_calls("remote.learn_command")
    assert len(calls) == 1
```

### 2. `mock_broadlink_storage` - Mock Broadlink Storage Files

Simulates the `~/.homeassistant/.storage/broadlink_remote_*_codes` files.

```python
def test_example(mock_broadlink_storage):
    # Add commands to storage
    mock_broadlink_storage.add_command(
        "abc123",  # device unique_id
        "tv",      # device name
        "power",   # command name
        "JgBQAAA..."  # IR code
    )
    
    # Check if command exists
    exists = mock_broadlink_storage.command_exists("abc123", "tv", "power")
    assert exists is True
    
    # Get all commands for a device
    commands = mock_broadlink_storage.get_device_commands("abc123", "tv")
    assert "power" in commands
    
    # Delete command
    mock_broadlink_storage.delete_command("abc123", "tv", "power")
```

### 3. `mock_websocket_api` - Mock WebSocket API

Simulates HA's WebSocket API for area management.

```python
async def test_example(mock_websocket_api):
    # Add entity to registry
    mock_websocket_api.add_entity(
        "light.bedroom_light",
        area_id="master_bedroom"
    )
    
    # Check if entity exists
    exists = mock_websocket_api.entity_exists("light.bedroom_light")
    assert exists is True
    
    # Get entity
    entity = mock_websocket_api.get_entity("light.bedroom_light")
    assert entity["area_id"] == "master_bedroom"
```

### 4. `web_server_with_mocks` - Full Web Server with Mocks

Complete BroadlinkWebServer instance with all dependencies mocked.

```python
async def test_example(web_server_with_mocks, mock_ha_api):
    server = web_server_with_mocks
    
    # Use server methods
    result = await server._learn_command({
        "entity_id": "remote.master_bedroom_rm4_pro",
        "device": "tv",
        "command": "power"
    })
    
    assert result["success"] is True
    
    # Check that HA API was called
    assert len(mock_ha_api.services_called) == 1
```

## Common Test Patterns

### Testing Command Learning

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_learn_command(web_server_with_mocks, mock_ha_api):
    server = web_server_with_mocks
    
    result = await server._learn_command({
        "entity_id": "remote.master_bedroom_rm4_pro",
        "device": "tv",
        "command": "power",
        "command_type": "ir"
    })
    
    # Verify success
    assert result["success"] is True
    
    # Verify HA service was called
    calls = mock_ha_api.get_service_calls("remote.learn_command")
    assert len(calls) == 1
    assert calls[0]["command"] == "power"
    
    # Verify notification was created
    assert len(mock_ha_api.notifications) == 1
```

### Testing Command Deletion

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_delete_command(
    web_server_with_mocks,
    mock_ha_api,
    mock_broadlink_storage
):
    server = web_server_with_mocks
    
    # Verify command exists
    assert mock_broadlink_storage.command_exists("abc123", "samsung_tv", "power")
    
    # Delete command
    result = await server._delete_command({
        "entity_id": "remote.master_bedroom_rm4_pro",
        "device": "samsung_tv",
        "command": "power"
    })
    
    assert result["success"] is True
    
    # Simulate storage deletion
    mock_broadlink_storage.delete_command("abc123", "samsung_tv", "power")
    
    # Verify deletion
    assert not mock_broadlink_storage.command_exists("abc123", "samsung_tv", "power")
```

### Testing Entity Generation

```python
@pytest.mark.unit
def test_generate_entities(
    entity_generator,
    storage_manager,
    sample_entity_config,
    temp_storage_dir
):
    # Save entity config
    for entity_id, entity_data in sample_entity_config.items():
        storage_manager.save_entity(entity_id, entity_data)
    
    # Generate entities
    result = entity_generator.generate_all({})
    
    assert result["success"] is True
    assert result["entities_count"] == 1
    
    # Verify files were created
    assert storage_manager.entities_file.exists()
    assert storage_manager.helpers_file.exists()
    
    # Verify YAML content
    import yaml
    with open(storage_manager.entities_file, 'r') as f:
        yaml_content = yaml.safe_load(f)
    
    assert "light" in yaml_content
    assert "bedroom_light" in yaml_content["light"][0]["lights"]
    
    # CRITICAL: Verify no entity type prefix
    assert "light.bedroom_light" not in str(yaml_content)
```

### Testing Area Assignment

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_assign_to_area(area_manager_with_mock, mock_websocket_api):
    manager = area_manager_with_mock
    
    # Add entity to registry
    mock_websocket_api.add_entity("light.bedroom_light")
    
    # Assign to area
    success = await manager.assign_entity_to_area(
        "light.bedroom_light",
        "master_bedroom"
    )
    
    assert success is True
    
    # Verify assignment
    entity = mock_websocket_api.get_entity("light.bedroom_light")
    assert entity["area_id"] == "master_bedroom"
```

### Testing Full Workflow

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow(
    web_server_with_mocks,
    mock_ha_api,
    mock_broadlink_storage
):
    server = web_server_with_mocks
    device_id = "office_lamp"
    
    # 1. Create device
    server.device_manager.create_device(device_id, {
        "name": "Office Lamp",
        "area": "Office",
        "entity_type": "light",
        "broadlink_entity": "remote.master_bedroom_rm4_pro"
    })
    
    # 2. Learn commands
    for cmd in ["turn_on", "turn_off"]:
        result = await server._learn_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": device_id,
            "command": cmd
        })
        assert result["success"] is True
        
        # Simulate HA storage
        mock_broadlink_storage.add_command(
            "abc123", device_id, cmd,
            "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
        )
        
        server.device_manager.add_command(device_id, cmd, {
            "command_type": "ir"
        })
    
    # 3. Save entity metadata
    server.storage_manager.save_entity(device_id, {
        "device": device_id,
        "entity_type": "light",
        "name": "Office Lamp",
        "area": "Office",
        "enabled": True,
        "commands": {
            "turn_on": f"{device_id}_turn_on",
            "turn_off": f"{device_id}_turn_off"
        },
        "broadlink_entity": "remote.master_bedroom_rm4_pro"
    })
    
    # 4. Generate entities
    from entity_generator import EntityGenerator
    generator = EntityGenerator(
        storage_manager=server.storage_manager,
        broadlink_device_id="remote.master_bedroom_rm4_pro"
    )
    
    result = generator.generate_all(mock_broadlink_storage.get_all_commands())
    
    assert result["success"] is True
    assert result["entities_count"] == 1
    
    # 5. Verify YAML files
    assert server.storage_manager.entities_file.exists()
```

## Test Markers

Use pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.e2e          # End-to-end test
@pytest.mark.asyncio      # Async test
@pytest.mark.slow         # Slow test
```

Run tests by marker:
```bash
pytest -m unit -v
pytest -m integration -v
pytest -m "not slow" -v
```

## Debugging Tests

```bash
# Show print statements
pytest tests/unit/test_command_learning.py -s

# Drop into debugger on failure
pytest tests/unit/test_command_learning.py --pdb

# Run specific test
pytest tests/unit/test_command_learning.py::TestCommandLearning::test_learn_command_success -v

# Show detailed output
pytest tests/unit/test_command_learning.py -vv
```

## Best Practices

1. **Use descriptive test names** - Test name should describe what's being tested
2. **One assertion per concept** - Group related assertions, but keep tests focused
3. **Use fixtures** - Reuse common setup via fixtures
4. **Clean up** - Fixtures should clean up after themselves (use `yield`)
5. **Test edge cases** - Test both success and failure paths
6. **Mock external dependencies** - Never hit real HA API in tests
7. **Verify entity ID format** - Always check that entity IDs don't have type prefix

## Common Pitfalls

### ❌ Wrong: Entity ID with prefix
```python
entity_id = f"light.{device_name}"  # WRONG!
```

### ✅ Correct: Entity ID without prefix
```python
entity_id = device_name  # CORRECT!
```

### ❌ Wrong: Not cleaning up mocks
```python
def test_example(mock_ha_api):
    # Test code...
    # No cleanup - state persists to next test
```

### ✅ Correct: Using yield for cleanup
```python
@pytest.fixture
def mock_ha_api():
    api = MockHAAPI()
    yield api
    api.reset()  # Cleanup
```

## Getting Help

- See `TESTING_FRAMEWORK_DESIGN.md` for detailed architecture
- See `TESTING_GUIDE.md` for comprehensive testing information
- Check existing tests in `tests/unit/` for examples
- Run `pytest --fixtures` to see all available fixtures
