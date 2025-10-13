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
from storage_manager import StorageManager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary storage directory for tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def device_manager(temp_storage_dir):
    """Create a DeviceManager instance with temporary storage"""
    return DeviceManager(storage_path=temp_storage_dir)


@pytest.fixture
def area_manager():
    """Create an AreaManager instance for testing"""
    return AreaManager(ha_url="http://localhost:8123", ha_token="test_token")


@pytest.fixture
def storage_manager(temp_storage_dir):
    """Create a StorageManager instance with temporary storage"""
    return StorageManager(storage_path=temp_storage_dir)


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
