"""
Pytest configuration and shared fixtures for Broadlink Manager tests
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add app directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'app'))

from device_manager import DeviceManager
from area_manager import AreaManager
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
def device_manager(temp_storage_dir):
    """Create a DeviceManager instance with temporary storage"""
    return DeviceManager(storage_path=temp_storage_dir)


@pytest.fixture
def area_manager():
    """Create an AreaManager instance for testing"""
    return AreaManager(ha_url="http://localhost:8123", ha_token="test_token")


# StorageManager fixture removed - no longer using metadata.json
# All device data is now managed through DeviceManager and devices.json


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
def sample_area_data():
    """Sample area data for testing"""
    return {
        'name': 'Master Bedroom',
        'icon': 'mdi:bed',
        'floor': 'upstairs'
    }


@pytest.fixture
def mock_ha_api():
    """Mock Home Assistant API responses"""
    mock = Mock()
    mock.get_states.return_value = [
        {
            'entity_id': 'remote.master_bedroom_rm4_pro',
            'state': 'idle',
            'attributes': {
                'friendly_name': 'Master Bedroom RM4 Pro'
            }
        },
        {
            'entity_id': 'remote.living_room_rm_mini',
            'state': 'idle',
            'attributes': {
                'friendly_name': 'Living Room RM Mini'
            }
        }
    ]
    return mock


@pytest.fixture
def mock_broadlink_device():
    """Mock Broadlink device for testing"""
    device = MagicMock()
    device.host = ('192.168.1.100', 80)
    device.mac = b'\xe8\x70\x72\x9e\x9e\x5f'
    device.devtype = 0x5f36  # RM4 Pro
    device.timeout = 10
    device.auth.return_value = True
    device.check_data.return_value = b'JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=='
    return device


@pytest.fixture
def populated_device_manager(device_manager, sample_device_data, sample_command_data):
    """Device manager with pre-populated test data"""
    # Create a device
    device_manager.create_device('master_bedroom_tv', sample_device_data)
    
    # Add some commands
    device_manager.add_command('master_bedroom_tv', 'power', sample_command_data)
    device_manager.add_command('master_bedroom_tv', 'volume_up', sample_command_data)
    device_manager.add_command('master_bedroom_tv', 'volume_down', sample_command_data)
    
    return device_manager


@pytest.fixture
def flask_app():
    """Create a Flask app instance for testing"""
    from web_server import BroadlinkWebServer
    from config_loader import ConfigLoader
    from pathlib import Path
    
    # Mock config loader
    config_loader = Mock(spec=ConfigLoader)
    config_loader.mode = 'standalone'
    config_loader.get_ha_url.return_value = 'http://localhost:8123'
    config_loader.get_ha_token.return_value = 'test_token'
    temp_storage = Path(tempfile.mkdtemp())
    config_loader.get_config_path.return_value = temp_storage
    config_loader.get_storage_path.return_value = temp_storage
    config_loader.get_broadlink_manager_path.return_value = temp_storage / 'broadlink_manager'
    
    server = BroadlinkWebServer(port=8099, config_loader=config_loader)
    server.app.config['TESTING'] = True
    
    yield server.app
    
    # Cleanup
    shutil.rmtree(str(temp_storage))


@pytest.fixture
def client(flask_app):
    """Create a test client for the Flask app"""
    return flask_app.test_client()


@pytest.fixture
def runner(flask_app):
    """Create a test CLI runner for the Flask app"""
    return flask_app.test_cli_runner()


# ============================================================================
# Mock Fixtures for HA Integration Testing
# ============================================================================

@pytest.fixture
def mock_ha_api():
    """Mock Home Assistant REST API"""
    api = MockHAAPI()
    
    # Add default Broadlink devices
    api.add_broadlink_device(
        "remote.master_bedroom_rm4_pro",
        "Master Bedroom RM4 Pro",
        "master_bedroom",
        "abc123"  # unique_id for storage file mapping
    )
    api.add_broadlink_device(
        "remote.living_room_rm_mini",
        "Living Room RM Mini",
        "living_room",
        "def456"
    )
    
    # Add default areas
    api.add_area("master_bedroom", "Master Bedroom")
    api.add_area("living_room", "Living Room")
    api.add_area("office", "Office")
    
    yield api
    
    # Cleanup
    api.reset()


@pytest.fixture
def mock_broadlink_storage(temp_storage_dir):
    """Mock Broadlink storage file system"""
    storage = MockBroadlinkStorage(temp_storage_dir)
    
    # Add some default commands for testing
    storage.create_storage_file(
        "abc123",  # device unique_id
        "samsung_tv",  # device name
        {
            "power": "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ==",
            "volume_up": "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ==",
            "volume_down": "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3LAANBQ=="
        }
    )
    
    yield storage
    
    # Cleanup
    storage.clear()


@pytest.fixture
def mock_websocket_api():
    """Mock WebSocket API for area management"""
    ws = MockWebSocketAPI()
    
    # Add default areas
    ws.add_area("master_bedroom", "Master Bedroom")
    ws.add_area("living_room", "Living Room")
    ws.add_area("office", "Office")
    
    yield ws
    
    # Cleanup
    ws.reset()


@pytest.fixture
def entity_generator(device_manager):
    """Create an EntityGenerator instance"""
    return EntityGenerator(
        device_manager=device_manager,
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
def web_server_with_mocks(temp_storage_dir, mock_ha_api, mock_broadlink_storage, device_manager):
    """Create a mock BroadlinkWebServer with mocked dependencies"""
    # Create a minimal mock server object with async methods
    # We don't call the real implementation to avoid event loop issues
    server = Mock()
    server.device_manager = device_manager
    server.ha_url = 'http://localhost:8123'
    server.ha_token = 'test_token'
    server.storage_path = temp_storage_dir
    
    # Create simple async mock methods that use the mock HA API
    async def _learn_command(data):
        """Mock learn command that simulates the behavior"""
        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        command_type = data.get("command_type", "ir")
        
        # Call the mock HA API to simulate service call
        await mock_ha_api.make_request(
            "POST",
            "services/remote/learn_command",
            {
                "target": {"entity_id": entity_id},
                "data": {
                    "device": device,
                    "command": command,
                    "command_type": command_type
                }
            }
        )
        
        # Create a notification like the real implementation would
        mock_ha_api.add_notification(
            f"Broadlink: Command Learned",
            f"Successfully learned command '{command}' for device '{device}'"
        )
        
        return {"success": True, "message": f"Command {command} learned successfully"}
    
    async def _delete_command(data):
        """Mock delete command that simulates the behavior"""
        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        
        # Call the mock HA API to simulate service call
        await mock_ha_api.make_request(
            "POST",
            "services/remote/delete_command",
            {
                "entity_id": entity_id,
                "device": device,
                "command": command
            }
        )
        
        return {"success": True, "message": f"Command {command} deleted successfully"}
    
    server._learn_command = _learn_command
    server._delete_command = _delete_command
    server._make_ha_request = mock_ha_api.make_request
    
    yield server


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


@pytest.fixture
def sample_ir_code():
    """Sample IR code for testing"""
    return "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
