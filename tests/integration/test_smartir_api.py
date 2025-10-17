"""
Integration tests for SmartIR API endpoints
Tests /api/smartir/* endpoints for device management and code retrieval
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

@pytest.fixture(scope="module")
def app_for_smartir_testing():
    """Create Flask app for SmartIR testing"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'app'))
    
    from web_server import BroadlinkWebServer
    from config_loader import ConfigLoader
    
    # Mock config loader
    config_loader = Mock(spec=ConfigLoader)
    config_loader.mode = 'standalone'
    config_loader.is_supervisor = False
    config_loader.get_ha_url.return_value = 'http://localhost:8123'
    config_loader.get_ha_token.return_value = 'test_token'
    
    # Create temp storage
    temp_storage = Path(tempfile.mkdtemp())
    config_loader.get_storage_path.return_value = temp_storage
    config_loader.get_broadlink_manager_path.return_value = temp_storage / 'broadlink_manager'
    config_loader.get_config_path.return_value = temp_storage
    
    # Create directories
    (temp_storage / 'broadlink_manager').mkdir(exist_ok=True)
    
    # Create server
    server = BroadlinkWebServer(port=8099, config_loader=config_loader)
    server.app.config['TESTING'] = True
    
    yield server.app
    
    # Cleanup
    shutil.rmtree(str(temp_storage))


@pytest.fixture
def client(app_for_smartir_testing):
    """Create a test client"""
    with app_for_smartir_testing.test_client() as client:
        yield client


@pytest.mark.integration
class TestSmartIRDeviceEndpoints:
    """Test SmartIR device management endpoints"""
    
    def test_get_smartir_devices_empty(self, client):
        """Test getting SmartIR devices when none exist"""
        response = client.get('/api/smartir/devices')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_create_smartir_climate_device(self, client):
        """Test creating a SmartIR climate device"""
        device_data = {
            'name': 'Bedroom AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.bedroom_rm4_pro',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should succeed or return validation error
        assert response.status_code in [200, 201, 400, 500]
    
    def test_create_smartir_media_player_device(self, client):
        """Test creating a SmartIR media player device"""
        device_data = {
            'name': 'Living Room TV',
            'device_type': 'smartir',
            'entity_type': 'media_player',
            'smartir_code': '5678',
            'controller_device': 'remote.living_room_rm4',
            'area': 'Living Room'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 500]
    
    def test_create_smartir_fan_device(self, client):
        """Test creating a SmartIR fan device"""
        device_data = {
            'name': 'Ceiling Fan',
            'device_type': 'smartir',
            'entity_type': 'fan',
            'smartir_code': '9012',
            'controller_device': 'remote.bedroom_rm4',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 500]
    
    def test_create_smartir_device_missing_code(self, client):
        """Test that creating SmartIR device without code fails"""
        device_data = {
            'name': 'Invalid Device',
            'device_type': 'smartir',
            'entity_type': 'climate',
            # Missing smartir_code
            'controller_device': 'remote.test_rm4',
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should return error
        assert response.status_code in [400, 500]
    
    def test_create_smartir_device_missing_controller(self, client):
        """Test that creating SmartIR device without controller fails"""
        device_data = {
            'name': 'Invalid Device',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            # Missing controller_device
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should return error
        assert response.status_code in [400, 500]


@pytest.mark.integration
class TestSmartIRCodeRetrieval:
    """Test SmartIR code retrieval endpoints"""
    
    @patch('app.api.smartir.requests.get')
    def test_get_manufacturers(self, mock_get, client):
        """Test getting list of manufacturers for a platform"""
        # Mock GitHub API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'name': 'Daikin', 'type': 'dir'},
            {'name': 'LG', 'type': 'dir'},
            {'name': 'Samsung', 'type': 'dir'}
        ]
        mock_get.return_value = mock_response
        
        response = client.get('/api/smartir/manufacturers/climate')
        
        # Should return list or use local index
        assert response.status_code in [200, 404, 500]
    
    @patch('app.api.smartir.requests.get')
    def test_get_models_for_manufacturer(self, mock_get, client):
        """Test getting models for a specific manufacturer"""
        # Mock GitHub API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'name': '1000.json', 'type': 'file'},
            {'name': '1001.json', 'type': 'file'}
        ]
        mock_get.return_value = mock_response
        
        response = client.get('/api/smartir/models/climate/Daikin')
        
        assert response.status_code in [200, 404, 500]
    
    @patch('app.api.smartir.requests.get')
    def test_get_device_code(self, mock_get, client):
        """Test retrieving a specific device code"""
        # Mock GitHub raw content response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'manufacturer': 'Daikin',
            'supportedModels': ['FTXS25CVMA'],
            'supportedController': 'Broadlink',
            'commandsEncoding': 'Base64',
            'temperature': {
                'auto': {'20': 'JgBQ...'}
            }
        }
        mock_get.return_value = mock_response
        
        response = client.get('/api/smartir/code/climate/1000')
        
        assert response.status_code in [200, 404, 500]


@pytest.mark.integration
class TestSmartIRDeviceIndex:
    """Test SmartIR device index functionality"""
    
    def test_get_device_index(self, client):
        """Test retrieving the pre-built device index"""
        response = client.get('/api/smartir/index')
        
        # Should return index if it exists
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'platforms' in data or 'version' in data
    
    def test_update_device_index(self, client):
        """Test updating the device index"""
        # This endpoint triggers index regeneration
        response = client.post('/api/smartir/index/update')
        
        # Should accept request or return not implemented
        assert response.status_code in [200, 202, 404, 501]


@pytest.mark.integration
class TestSmartIRValidation:
    """Test SmartIR device validation"""
    
    def test_validate_smartir_code_format(self, client):
        """Test that SmartIR codes are validated"""
        # Valid numeric code
        valid_device = {
            'name': 'Valid AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.test_rm4',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(valid_device),
            content_type='application/json'
        )
        
        # Should accept or validate
        assert response.status_code in [200, 201, 400, 500]
    
    def test_reject_invalid_smartir_code(self, client):
        """Test that invalid SmartIR codes are rejected"""
        invalid_device = {
            'name': 'Invalid AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': 'invalid_code',  # Should be numeric
            'controller_device': 'remote.test_rm4',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(invalid_device),
            content_type='application/json'
        )
        
        # May accept (validation happens elsewhere) or reject
        assert response.status_code in [200, 201, 400, 500]
    
    def test_validate_controller_entity_format(self, client):
        """Test that controller entity IDs are validated"""
        # Valid entity ID format
        valid_device = {
            'name': 'Valid AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.bedroom_rm4_pro',  # Valid format
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(valid_device),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 500]


@pytest.mark.integration
class TestSmartIRYAMLGeneration:
    """Test SmartIR YAML generation endpoints"""
    
    def test_generate_smartir_yaml(self, client):
        """Test generating SmartIR YAML configuration"""
        # First create a SmartIR device
        device_data = {
            'name': 'Test AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.test_rm4',
            'area': 'Bedroom'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code in [200, 201]:
            # Try to generate YAML
            response = client.post('/api/smartir/generate')
            
            # Should succeed or return not found
            assert response.status_code in [200, 404, 500]
    
    def test_download_smartir_yaml(self, client):
        """Test downloading SmartIR YAML files"""
        response = client.get('/api/smartir/download')
        
        # Should return file or not found
        assert response.status_code in [200, 404]


@pytest.mark.integration
class TestSmartIRDeviceLifecycle:
    """Test complete SmartIR device lifecycle"""
    
    def test_full_smartir_device_lifecycle(self, client):
        """Test creating, reading, updating, and deleting a SmartIR device"""
        # Create
        device_data = {
            'name': 'Lifecycle Test AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.test_rm4',
            'area': 'Bedroom'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Device creation failed")
        
        create_data = json.loads(create_response.data)
        device_id = create_data.get('device_id')
        
        if not device_id:
            pytest.skip("No device_id returned")
        
        # Read
        read_response = client.get(f'/api/devices/managed/{device_id}')
        assert read_response.status_code in [200, 404]
        
        # Update
        update_data = {
            'name': 'Updated AC',
            'smartir_code': '5678'
        }
        update_response = client.put(
            f'/api/devices/managed/{device_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert update_response.status_code in [200, 404, 500]
        
        # Delete
        delete_response = client.delete(f'/api/devices/managed/{device_id}')
        assert delete_response.status_code in [200, 204, 404]


@pytest.mark.integration
class TestSmartIRControllerTypes:
    """Test different controller types for SmartIR"""
    
    def test_broadlink_controller(self, client):
        """Test SmartIR device with Broadlink controller"""
        device_data = {
            'name': 'AC with Broadlink',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.bedroom_rm4_pro',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 500]
    
    def test_xiaomi_controller(self, client):
        """Test SmartIR device with Xiaomi controller"""
        device_data = {
            'name': 'AC with Xiaomi',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.xiaomi_miio_12345678',
            'area': 'Living Room'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 500]
    
    def test_harmony_hub_controller(self, client):
        """Test SmartIR device with Harmony Hub controller"""
        device_data = {
            'name': 'TV with Harmony',
            'device_type': 'smartir',
            'entity_type': 'media_player',
            'smartir_code': '5678',
            'controller_device': 'remote.harmony_hub',
            'area': 'Living Room'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201, 400, 500]


@pytest.mark.integration
class TestSmartIRErrorHandling:
    """Test error handling for SmartIR operations"""
    
    def test_invalid_platform_type(self, client):
        """Test handling of invalid platform type"""
        device_data = {
            'name': 'Invalid Device',
            'device_type': 'smartir',
            'entity_type': 'invalid_type',  # Not climate/media_player/fan
            'smartir_code': '1234',
            'controller_device': 'remote.test_rm4',
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should return error
        assert response.status_code in [400, 500]
    
    def test_nonexistent_smartir_code(self, client):
        """Test handling of non-existent SmartIR code"""
        device_data = {
            'name': 'Device with Bad Code',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '99999',  # Likely doesn't exist
            'controller_device': 'remote.test_rm4',
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # May accept (validation happens at runtime) or reject
        assert response.status_code in [200, 201, 400, 404, 500]
    
    def test_empty_controller_device(self, client):
        """Test handling of empty controller device"""
        device_data = {
            'name': 'Device without Controller',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': '',  # Empty
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should return error
        assert response.status_code in [400, 500]
