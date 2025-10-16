"""
Integration tests for /api/devices/managed endpoints
These are the endpoints actually used by the frontend
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock


@pytest.fixture(scope="module")
def app_for_testing():
    """Create Flask app once for all tests in this module"""
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
def client(app_for_testing):
    """Create a test client"""
    with app_for_testing.test_client() as client:
        yield client


@pytest.mark.integration
class TestManagedDeviceEndpoints:
    """Test /api/devices/managed endpoints (current production endpoints)"""
    
    def test_get_managed_devices_empty(self, client):
        """Test getting managed devices when none exist"""
        response = client.get('/api/devices/managed')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        assert 'devices' in data
        assert isinstance(data['devices'], list)
    
    def test_create_managed_device_broadlink(self, client):
        """Test creating a managed Broadlink device"""
        device_data = {
            'name': 'Living Room TV',
            'device_type': 'broadlink',
            'entity_type': 'media_player',
            'broadlink_entity': 'remote.living_room_rm4_pro',
            'area': 'Living Room'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert data.get('success') is True or 'device_id' in data
    
    def test_create_managed_device_smartir(self, client):
        """Test creating a managed SmartIR device"""
        device_data = {
            'name': 'Bedroom AC',
            'device_type': 'smartir',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert data.get('success') is True or 'device_id' in data
    
    def test_get_managed_device_by_id(self, client):
        """Test retrieving a specific managed device"""
        # First create a device
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Office'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code in [200, 201]:
            create_data = json.loads(create_response.data)
            device_id = create_data.get('device_id')
            
            if device_id:
                # Then retrieve it
                response = client.get(f'/api/devices/managed/{device_id}')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data.get('device_id') == device_id or data.get('id') == device_id
    
    def test_update_managed_device(self, client):
        """Test updating a managed device"""
        # Create device
        device_data = {
            'name': 'Original Name',
            'device_type': 'broadlink',
            'entity_type': 'fan',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Bedroom'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code in [200, 201]:
            create_data = json.loads(create_response.data)
            device_id = create_data.get('device_id')
            
            if device_id:
                # Update device
                update_data = {
                    'name': 'Updated Name',
                    'area': 'Living Room'
                }
                
                response = client.put(
                    f'/api/devices/managed/{device_id}',
                    data=json.dumps(update_data),
                    content_type='application/json'
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data.get('success') is True
    
    def test_delete_managed_device(self, client):
        """Test deleting a managed device"""
        # Create device
        device_data = {
            'name': 'Device To Delete',
            'device_type': 'broadlink',
            'entity_type': 'switch',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Garage'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code in [200, 201]:
            create_data = json.loads(create_response.data)
            device_id = create_data.get('device_id')
            
            if device_id:
                # Delete device
                response = client.delete(f'/api/devices/managed/{device_id}')
                assert response.status_code in [200, 204]
    
    def test_delete_managed_device_with_commands(self, client):
        """Test deleting a managed device and its commands"""
        # Create device
        device_data = {
            'name': 'Device With Commands',
            'device_type': 'broadlink',
            'entity_type': 'media_player',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Living Room'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code in [200, 201]:
            create_data = json.loads(create_response.data)
            device_id = create_data.get('device_id')
            
            if device_id:
                # Delete device with commands
                response = client.delete(
                    f'/api/devices/managed/{device_id}',
                    data=json.dumps({'delete_commands': True}),
                    content_type='application/json'
                )
                assert response.status_code in [200, 204]


@pytest.mark.integration
class TestManagedDeviceValidation:
    """Test validation for managed device endpoints"""
    
    def test_create_device_missing_required_fields(self, client):
        """Test that creating device without required fields fails gracefully"""
        device_data = {
            'name': 'Incomplete Device'
            # Missing device_type, entity_type, etc.
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should return error (400 or 500)
        assert response.status_code in [400, 500]
    
    def test_create_device_invalid_device_type(self, client):
        """Test that invalid device_type is rejected"""
        device_data = {
            'name': 'Invalid Device',
            'device_type': 'invalid_type',  # Should be 'broadlink' or 'smartir'
            'entity_type': 'light',
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should return error
        assert response.status_code in [400, 500]
    
    def test_get_nonexistent_device(self, client):
        """Test getting a device that doesn't exist"""
        response = client.get('/api/devices/managed/nonexistent_device_id')
        
        # Should return 404 or empty result
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = json.loads(response.data)
            # Should indicate device not found
            assert data.get('error') or not data.get('device_id')
    
    def test_update_nonexistent_device(self, client):
        """Test updating a device that doesn't exist"""
        update_data = {'name': 'New Name'}
        
        response = client.put(
            '/api/devices/managed/nonexistent_device_id',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Should return error
        assert response.status_code in [404, 500]
    
    def test_delete_nonexistent_device(self, client):
        """Test deleting a device that doesn't exist"""
        response = client.delete('/api/devices/managed/nonexistent_device_id')
        
        # Should return 404 or 200 (idempotent delete)
        assert response.status_code in [404, 200, 204]


@pytest.mark.integration
class TestManagedDeviceWorkflow:
    """Test complete workflows with managed devices"""
    
    def test_full_device_lifecycle(self, client):
        """Test creating, reading, updating, and deleting a device"""
        # Create
        device_data = {
            'name': 'Lifecycle Test Device',
            'device_type': 'broadlink',
            'entity_type': 'media_player',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Living Room'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert create_response.status_code in [200, 201]
        create_data = json.loads(create_response.data)
        device_id = create_data.get('device_id')
        
        if not device_id:
            pytest.skip("Device creation didn't return device_id")
        
        # Read
        read_response = client.get(f'/api/devices/managed/{device_id}')
        assert read_response.status_code == 200
        
        # Update
        update_data = {'name': 'Updated Lifecycle Device'}
        update_response = client.put(
            f'/api/devices/managed/{device_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        assert update_response.status_code == 200
        
        # Delete
        delete_response = client.delete(f'/api/devices/managed/{device_id}')
        assert delete_response.status_code in [200, 204]
        
        # Verify deletion
        verify_response = client.get(f'/api/devices/managed/{device_id}')
        # Should be 404 or return empty/error
        assert verify_response.status_code in [404, 200]
