# Testing Framework Design for Broadlink Manager v2

## Overview

This document outlines the testing strategy for mocking Home Assistant Broadlink integration API and entity generation functionality for unit and integration testing.

## Key Testing Challenges

### 1. **Broadlink Integration API Mocking**
The application interacts with Home Assistant's Broadlink integration through:
- **Learning commands**: `POST /api/services/remote/learn_command`
- **Deleting commands**: `POST /api/services/remote/delete_command`
- **Sending commands**: `POST /api/services/remote/send_command`
- **Reading Broadlink storage files**: `~/.homeassistant/.storage/broadlink_remote_*_codes`

### 2. **Entity Generation Testing**
The `EntityGenerator` creates Home Assistant YAML configurations that must:
- Write to temporary file system (not real HA config)
- Generate valid YAML structure
- Handle multiple entity types (light, fan, switch, media_player, cover)
- Create helper entities (input_boolean, input_select)

### 3. **Area Management via WebSocket**
The `AreaManager` uses WebSocket API to:
- Get/create areas
- Assign entities to areas
- Check entity existence in registry

---

## Recommended Testing Architecture

### Mock Service Layer Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── mocks/
│   ├── __init__.py
│   ├── ha_api_mock.py            # Mock HA REST API
│   ├── broadlink_storage_mock.py # Mock Broadlink storage files
│   ├── websocket_mock.py         # Mock WebSocket API
│   └── entity_registry_mock.py   # Mock entity registry
├── unit/
│   ├── test_device_manager.py    # ✅ Already exists
│   ├── test_entity_generator.py  # ✅ Already exists
│   ├── test_command_learning.py  # NEW - Test command learning flow
│   ├── test_command_deletion.py  # NEW - Test command deletion
│   └── test_area_assignment.py   # NEW - Test area management
├── integration/
│   ├── test_api_endpoints.py     # ✅ Already exists
│   ├── test_full_workflow.py     # NEW - End-to-end workflows
│   └── test_smartir_workflow.py  # NEW - SmartIR integration
└── e2e/
    └── test_accessibility.py      # ✅ Already exists
```

---

## Mock Implementation Details

### 1. Home Assistant API Mock (`ha_api_mock.py`)

```python
"""
Mock Home Assistant REST API for testing
"""
import json
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock
from datetime import datetime


class MockHAAPI:
    """Mock Home Assistant REST API"""
    
    def __init__(self):
        self.states = []
        self.services_called = []
        self.notifications = []
        self.areas = []
        self.entities = {}
        
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Mock _make_ha_request method"""
        
        # Service calls
        if endpoint == "services/remote/learn_command":
            return await self._mock_learn_command(data)
        elif endpoint == "services/remote/delete_command":
            return await self._mock_delete_command(data)
        elif endpoint == "services/remote/send_command":
            return await self._mock_send_command(data)
        
        # State queries
        elif endpoint == "states":
            return self.states
        elif endpoint.startswith("states/"):
            entity_id = endpoint.replace("states/", "")
            return self._get_state(entity_id)
        
        # Notifications
        elif endpoint == "persistent_notification":
            return self.notifications
        
        # Areas
        elif endpoint == "config/area_registry/list":
            return self.areas
        
        return None
    
    async def _mock_learn_command(self, data: Dict) -> List:
        """Mock learning a command"""
        entity_id = data.get("target", {}).get("entity_id") or data.get("entity_id")
        device = data.get("data", {}).get("device") or data.get("device")
        command = data.get("data", {}).get("command") or data.get("command")
        command_type = data.get("data", {}).get("command_type", "ir")
        
        # Record the service call
        self.services_called.append({
            "service": "remote.learn_command",
            "entity_id": entity_id,
            "device": device,
            "command": command,
            "command_type": command_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create a notification (simulating HA behavior)
        self.notifications.append({
            "notification_id": f"broadlink_learn_{len(self.notifications)}",
            "title": "Learn Command",
            "message": f"Press the button to learn '{command}' for device '{device}'",
            "created_at": datetime.now().isoformat()
        })
        
        # Return empty list (HA returns [] on success)
        return []
    
    async def _mock_delete_command(self, data: Dict) -> List:
        """Mock deleting a command"""
        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        
        self.services_called.append({
            "service": "remote.delete_command",
            "entity_id": entity_id,
            "device": device,
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        return []
    
    async def _mock_send_command(self, data: Dict) -> List:
        """Mock sending a command"""
        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        
        self.services_called.append({
            "service": "remote.send_command",
            "entity_id": entity_id,
            "device": device,
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        return []
    
    def _get_state(self, entity_id: str) -> Optional[Dict]:
        """Get state for an entity"""
        for state in self.states:
            if state.get("entity_id") == entity_id:
                return state
        return None
    
    def add_broadlink_device(self, entity_id: str, name: str, area_id: str = None):
        """Add a mock Broadlink device"""
        self.states.append({
            "entity_id": entity_id,
            "state": "idle",
            "attributes": {
                "friendly_name": name,
                "supported_features": 0
            },
            "area_id": area_id
        })
    
    def add_area(self, area_id: str, name: str):
        """Add a mock area"""
        self.areas.append({
            "area_id": area_id,
            "name": name
        })
```

### 2. Broadlink Storage Mock (`broadlink_storage_mock.py`)

```python
"""
Mock Broadlink storage files for testing
"""
import json
from pathlib import Path
from typing import Dict, Any


class MockBroadlinkStorage:
    """Mock Broadlink storage file system"""
    
    def __init__(self, temp_dir: Path):
        self.storage_path = temp_dir
        self.storage_files = {}  # {device_unique_id: {device_name: {command: code}}}
        
    def create_storage_file(self, device_unique_id: str, device_name: str, commands: Dict[str, str]):
        """Create a mock Broadlink storage file"""
        filename = f"broadlink_remote_{device_unique_id}_codes"
        filepath = self.storage_path / filename
        
        # Initialize or update storage
        if device_unique_id not in self.storage_files:
            self.storage_files[device_unique_id] = {}
        
        if device_name not in self.storage_files[device_unique_id]:
            self.storage_files[device_unique_id][device_name] = {}
        
        # Add commands
        self.storage_files[device_unique_id][device_name].update(commands)
        
        # Write to file
        data = {
            "version": 1,
            "data": self.storage_files[device_unique_id]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_command(self, device_unique_id: str, device_name: str, command_name: str, code: str):
        """Add a single command to storage"""
        commands = {command_name: code}
        self.create_storage_file(device_unique_id, device_name, commands)
    
    def delete_command(self, device_unique_id: str, device_name: str, command_name: str):
        """Delete a command from storage"""
        if device_unique_id in self.storage_files:
            if device_name in self.storage_files[device_unique_id]:
                if command_name in self.storage_files[device_unique_id][device_name]:
                    del self.storage_files[device_unique_id][device_name][command_name]
                    
                    # Rewrite file
                    filename = f"broadlink_remote_{device_unique_id}_codes"
                    filepath = self.storage_path / filename
                    data = {
                        "version": 1,
                        "data": self.storage_files[device_unique_id]
                    }
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2)
    
    def get_all_commands(self, device_unique_id: str = None) -> Dict:
        """Get all commands from storage"""
        if device_unique_id:
            return self.storage_files.get(device_unique_id, {})
        return self.storage_files
    
    def clear(self):
        """Clear all storage"""
        self.storage_files = {}
        for file in self.storage_path.glob("broadlink_remote_*_codes"):
            file.unlink()
```

### 3. WebSocket Mock (`websocket_mock.py`)

```python
"""
Mock WebSocket API for area management
"""
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock


class MockWebSocketAPI:
    """Mock Home Assistant WebSocket API"""
    
    def __init__(self):
        self.areas = {}
        self.entities = {}
        self.message_id = 1
        
    async def send_command(self, command_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Mock _send_ws_command method"""
        
        if command_type == "config/area_registry/list":
            return list(self.areas.values())
        
        elif command_type == "config/area_registry/create":
            area_name = kwargs.get("name")
            area_id = area_name.lower().replace(" ", "_")
            area = {
                "area_id": area_id,
                "name": area_name
            }
            self.areas[area_id] = area
            return area
        
        elif command_type == "config/entity_registry/update":
            entity_id = kwargs.get("entity_id")
            area_id = kwargs.get("area_id")
            
            if entity_id in self.entities:
                self.entities[entity_id]["area_id"] = area_id
                return self.entities[entity_id]
            return None
        
        elif command_type == "config/entity_registry/get":
            entity_id = kwargs.get("entity_id")
            return self.entities.get(entity_id)
        
        return None
    
    def add_entity(self, entity_id: str, area_id: str = None, **kwargs):
        """Add a mock entity to registry"""
        self.entities[entity_id] = {
            "entity_id": entity_id,
            "area_id": area_id,
            **kwargs
        }
    
    def add_area(self, area_id: str, name: str):
        """Add a mock area"""
        self.areas[area_id] = {
            "area_id": area_id,
            "name": name
        }
```

---

## Updated conftest.py

```python
"""
Enhanced pytest configuration with comprehensive mocks
"""
import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, AsyncMock, patch

# Add app directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from device_manager import DeviceManager
from area_manager import AreaManager
from storage_manager import StorageManager
from entity_generator import EntityGenerator

# Import mocks
from tests.mocks.ha_api_mock import MockHAAPI
from tests.mocks.broadlink_storage_mock import MockBroadlinkStorage
from tests.mocks.websocket_mock import MockWebSocketAPI


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_ha_api():
    """Mock Home Assistant REST API"""
    api = MockHAAPI()
    
    # Add default Broadlink devices
    api.add_broadlink_device(
        "remote.master_bedroom_rm4_pro",
        "Master Bedroom RM4 Pro",
        "master_bedroom"
    )
    api.add_broadlink_device(
        "remote.living_room_rm_mini",
        "Living Room RM Mini",
        "living_room"
    )
    
    # Add default areas
    api.add_area("master_bedroom", "Master Bedroom")
    api.add_area("living_room", "Living Room")
    api.add_area("office", "Office")
    
    return api


@pytest.fixture
def mock_broadlink_storage(temp_storage_dir):
    """Mock Broadlink storage file system"""
    storage = MockBroadlinkStorage(temp_storage_dir)
    
    # Add some default commands
    storage.create_storage_file(
        "abc123",  # device unique_id
        "samsung_tv",  # device name
        {
            "power": "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ==",
            "volume_up": "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ==",
            "volume_down": "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3LAANBQ=="
        }
    )
    
    return storage


@pytest.fixture
def mock_websocket_api():
    """Mock WebSocket API for area management"""
    ws = MockWebSocketAPI()
    
    # Add default areas
    ws.add_area("master_bedroom", "Master Bedroom")
    ws.add_area("living_room", "Living Room")
    
    return ws


@pytest.fixture
def device_manager(temp_storage_dir):
    """Create a DeviceManager instance with temporary storage"""
    return DeviceManager(storage_path=temp_storage_dir)


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a StorageManager instance with temporary storage"""
    return StorageManager(storage_path=str(temp_storage_dir))


@pytest.fixture
def entity_generator(storage_manager):
    """Create an EntityGenerator instance"""
    return EntityGenerator(
        storage_manager=storage_manager,
        broadlink_device_id="remote.test_rm4_pro"
    )


@pytest.fixture
def area_manager_with_mock(mock_websocket_api):
    """Create an AreaManager with mocked WebSocket"""
    manager = AreaManager(
        ha_url="http://localhost:8123",
        ha_token="test_token"
    )
    
    # Patch the _send_ws_command method
    manager._send_ws_command = mock_websocket_api.send_command
    
    return manager


@pytest.fixture
def web_server_with_mocks(temp_storage_dir, mock_ha_api, mock_broadlink_storage):
    """Create a BroadlinkWebServer with mocked dependencies"""
    from web_server import BroadlinkWebServer
    from config_loader import ConfigLoader
    
    # Mock config loader
    config_loader = Mock(spec=ConfigLoader)
    config_loader.mode = 'standalone'
    config_loader.get_ha_url.return_value = 'http://localhost:8123'
    config_loader.get_ha_token.return_value = 'test_token'
    config_loader.get_storage_path.return_value = temp_storage_dir
    config_loader.get_broadlink_manager_path.return_value = temp_storage_dir / 'broadlink_manager'
    config_loader.get_config_path.return_value = temp_storage_dir / 'config'
    
    server = BroadlinkWebServer(port=8099, config_loader=config_loader)
    
    # Patch the _make_ha_request method
    server._make_ha_request = mock_ha_api.make_request
    
    server.app.config['TESTING'] = True
    
    return server


@pytest.fixture
def sample_device_data():
    """Sample device data for testing"""
    return {
        'name': 'Master Bedroom TV',
        'type': 'tv',
        'area_id': 'master_bedroom',
        'broadlink_entity': 'remote.master_bedroom_rm4_pro',
        'manufacturer': 'Samsung',
        'model': 'UN55RU7100'
    }


@pytest.fixture
def sample_command_data():
    """Sample command data for testing"""
    return {
        'code': 'JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ==',
        'type': 'ir',
        'learned_at': '2025-01-10T12:00:00'
    }


@pytest.fixture
def sample_entity_config():
    """Sample entity configuration for testing"""
    return {
        "bedroom_light": {
            "device": "bedroom_light",
            "entity_type": "light",
            "name": "Bedroom Light",
            "area": "Master Bedroom",
            "enabled": True,
            "commands": {
                "turn_on": "bedroom_light_on",
                "turn_off": "bedroom_light_off"
            },
            "broadlink_entity": "remote.master_bedroom_rm4_pro"
        }
    }
```

---

## Example Test Cases

### Test Command Learning

```python
"""
Test command learning with mocked HA API
"""
import pytest
from datetime import datetime


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandLearning:
    """Test command learning functionality"""
    
    async def test_learn_command_success(self, web_server_with_mocks, mock_ha_api):
        """Test successful command learning"""
        server = web_server_with_mocks
        
        # Learn a command
        result = await server._learn_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "power",
            "command_type": "ir"
        })
        
        # Verify success
        assert result["success"] is True
        
        # Verify service was called
        assert len(mock_ha_api.services_called) == 1
        service_call = mock_ha_api.services_called[0]
        assert service_call["service"] == "remote.learn_command"
        assert service_call["device"] == "samsung_tv"
        assert service_call["command"] == "power"
        
        # Verify notification was created
        assert len(mock_ha_api.notifications) == 1
        notification = mock_ha_api.notifications[0]
        assert "power" in notification["message"]
    
    async def test_learn_command_rf_type(self, web_server_with_mocks, mock_ha_api):
        """Test learning RF command"""
        server = web_server_with_mocks
        
        result = await server._learn_command({
            "entity_id": "remote.living_room_rm_mini",
            "device": "ceiling_fan",
            "command": "fan_on",
            "command_type": "rf"
        })
        
        assert result["success"] is True
        service_call = mock_ha_api.services_called[0]
        assert service_call["command_type"] == "rf"
    
    async def test_learn_command_missing_entity(self, web_server_with_mocks):
        """Test learning command with missing entity_id"""
        server = web_server_with_mocks
        
        result = await server._learn_command({
            "device": "samsung_tv",
            "command": "power"
        })
        
        # Should handle gracefully
        assert result["success"] is False or "error" in result
```

### Test Command Deletion

```python
"""
Test command deletion with mocked storage
"""
import pytest


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandDeletion:
    """Test command deletion functionality"""
    
    async def test_delete_command_success(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage
    ):
        """Test successful command deletion"""
        server = web_server_with_mocks
        
        # Verify command exists
        commands = mock_broadlink_storage.get_all_commands("abc123")
        assert "power" in commands.get("samsung_tv", {})
        
        # Delete the command
        result = await server._delete_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "power"
        })
        
        assert result["success"] is True
        
        # Verify service was called
        service_call = mock_ha_api.services_called[0]
        assert service_call["service"] == "remote.delete_command"
        assert service_call["command"] == "power"
    
    async def test_delete_nonexistent_command(
        self,
        web_server_with_mocks,
        mock_ha_api
    ):
        """Test deleting a command that doesn't exist"""
        server = web_server_with_mocks
        
        result = await server._delete_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "nonexistent"
        })
        
        # Should still succeed (HA behavior)
        assert result["success"] is True
```

### Test Entity Generation

```python
"""
Test entity generation with temporary file system
"""
import pytest
import yaml


@pytest.mark.unit
class TestEntityGeneration:
    """Test entity YAML generation"""
    
    def test_generate_entities_to_temp_dir(
        self,
        entity_generator,
        storage_manager,
        sample_entity_config,
        temp_storage_dir
    ):
        """Test generating entities writes to temp directory, not real HA"""
        # Setup entity in storage
        for entity_id, entity_data in sample_entity_config.items():
            storage_manager.save_entity(entity_id, entity_data)
        
        # Generate entities
        result = entity_generator.generate_all({})
        
        assert result["success"] is True
        
        # Verify files were created in temp directory
        entities_file = storage_manager.entities_file
        assert entities_file.exists()
        assert str(temp_storage_dir) in str(entities_file)
        
        # Verify YAML content
        with open(entities_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        assert "light" in yaml_content
        assert yaml_content["light"][0]["platform"] == "template"
        
        # Verify entity ID format (no prefix)
        lights = yaml_content["light"][0]["lights"]
        assert "bedroom_light" in lights
        assert "light.bedroom_light" not in lights
    
    def test_generate_helpers_file(
        self,
        entity_generator,
        storage_manager,
        sample_entity_config
    ):
        """Test helper entities are generated correctly"""
        for entity_id, entity_data in sample_entity_config.items():
            storage_manager.save_entity(entity_id, entity_data)
        
        result = entity_generator.generate_all({})
        
        helpers_file = storage_manager.helpers_file
        assert helpers_file.exists()
        
        with open(helpers_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        # Verify input_boolean for state tracking
        assert "input_boolean" in yaml_content
        assert "bedroom_light_state" in yaml_content["input_boolean"]
```

---

## Integration Test Example

```python
"""
Full workflow integration test
"""
import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestFullWorkflow:
    """Test complete device creation and entity generation workflow"""
    
    async def test_create_device_learn_commands_generate_entities(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage,
        temp_storage_dir
    ):
        """
        Test full workflow:
        1. Create device
        2. Learn commands
        3. Generate entities
        4. Verify YAML files
        """
        server = web_server_with_mocks
        storage = server.storage_manager
        generator = server.entity_generator
        
        # Step 1: Create device
        device_id = "office_lamp"
        device_data = {
            "name": "Office Lamp",
            "area": "Office",
            "entity_type": "light",
            "broadlink_entity": "remote.master_bedroom_rm4_pro"
        }
        
        result = server.device_manager.create_device(device_id, device_data)
        assert result is True
        
        # Step 2: Learn commands
        for command in ["turn_on", "turn_off"]:
            result = await server._learn_command({
                "entity_id": "remote.master_bedroom_rm4_pro",
                "device": device_id,
                "command": command,
                "command_type": "ir"
            })
            assert result["success"] is True
            
            # Simulate HA writing to storage
            mock_broadlink_storage.add_command(
                "abc123",
                device_id,
                command,
                "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
            )
            
            # Add to device manager
            server.device_manager.add_command(device_id, command, {
                "command_type": "ir",
                "learned_at": "2025-01-10T12:00:00"
            })
        
        # Step 3: Save entity metadata
        entity_data = {
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
        }
        storage.save_entity(device_id, entity_data)
        
        # Step 4: Generate entities
        broadlink_commands = mock_broadlink_storage.get_all_commands()
        result = generator.generate_all(broadlink_commands)
        
        assert result["success"] is True
        assert result["entities_count"] == 1
        
        # Step 5: Verify YAML files exist and are valid
        assert storage.entities_file.exists()
        assert storage.helpers_file.exists()
        
        # Verify content
        import yaml
        with open(storage.entities_file, 'r') as f:
            entities_yaml = yaml.safe_load(f)
        
        assert "light" in entities_yaml
        assert office_lamp" in entities_yaml["light"][0]["lights"]
```

---

## Running the Tests

### Install Dependencies
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Tests with mocked HA API
pytest tests/ -k "mock_ha_api" -v

# Async tests only
pytest tests/ -k "asyncio" -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

---

## Key Benefits of This Approach

1. **No Real HA Required**: Tests run completely isolated without needing a running Home Assistant instance
2. **Fast Execution**: Mock services respond instantly
3. **Deterministic**: Tests produce consistent results
4. **Safe**: No risk of corrupting real HA configuration
5. **Comprehensive**: Can test error conditions and edge cases easily
6. **Maintainable**: Mocks are centralized and reusable

---

## Next Steps

1. **Create mock modules** in `tests/mocks/`
2. **Update conftest.py** with new fixtures
3. **Write test cases** for command learning, deletion, and entity generation
4. **Add integration tests** for full workflows
5. **Update CI/CD** to run tests automatically
6. **Document test patterns** for future contributors
