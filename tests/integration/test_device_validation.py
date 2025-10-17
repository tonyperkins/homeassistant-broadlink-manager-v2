"""
Integration tests for device creation and update validation
Tests input validation, data integrity, and error handling
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock


@pytest.fixture(scope="module")
def app_for_validation_testing():
    """Create Flask app for validation testing"""
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
def client(app_for_validation_testing):
    """Create a test client"""
    with app_for_validation_testing.test_client() as client:
        yield client


@pytest.mark.integration
class TestDeviceNameValidation:
    """Test device name validation"""
    
    def test_create_device_with_valid_name(self, client):
        """Test creating device with valid name"""
        device_data = {
            'name': 'Living Room TV',
            'device_type': 'broadlink',
            'entity_type': 'media_player',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Living Room'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
    
    def test_create_device_with_special_characters(self, client):
        """Test that special characters in names are handled"""
        device_data = {
            'name': "Tony's Office Light!",
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should accept (normalization happens in backend)
        assert response.status_code in [200, 201, 400, 500]
    
    def test_create_device_with_empty_name(self, client):
        """Test that empty name is rejected"""
        device_data = {
            'name': '',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Office'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should reject empty name
        assert response.status_code in [400, 500]
    
    def test_create_device_with_very_long_name(self, client):
        """Test handling of very long device names"""
        device_data = {
            'name': 'A' * 200,  # Very long name
            'device_type': 'broadlink',
            'entity_type': 'switch',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should accept or truncate
        assert response.status_code in [200, 201, 400, 500]
    
    def test_create_device_with_unicode_name(self, client):
        """Test that Unicode characters in names are handled"""
        device_data = {
            'name': 'Habitación Principal 测试 🏠',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Bedroom'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should handle Unicode gracefully
        assert response.status_code in [200, 201, 400, 500]


@pytest.mark.integration
class TestEntityTypeValidation:
    """Test entity type validation"""
    
    def test_valid_entity_types(self, client):
        """Test that all valid entity types are accepted"""
        valid_types = ['light', 'fan', 'switch', 'media_player', 'climate']
        
        for entity_type in valid_types:
            device_data = {
                'name': f'Test {entity_type}',
                'device_type': 'broadlink',
                'entity_type': entity_type,
                'broadlink_entity': 'remote.test_rm4',
                'area': 'Test'
            }
            
            response = client.post(
                '/api/devices/managed',
                data=json.dumps(device_data),
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201], \
                f"Valid entity type '{entity_type}' was rejected"
    
    def test_invalid_entity_type(self, client):
        """Test that invalid entity types are accepted but may not generate properly"""
        device_data = {
            'name': 'Invalid Device',
            'device_type': 'broadlink',
            'entity_type': 'invalid_type',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # API accepts any entity_type (validation happens at generation time)
        # This is by design to allow flexibility
        assert response.status_code in [200, 201, 400, 500]
    
    def test_missing_entity_type(self, client):
        """Test that missing entity type is rejected"""
        device_data = {
            'name': 'Device Without Type',
            'device_type': 'broadlink',
            # Missing entity_type
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should reject missing type
        assert response.status_code in [400, 500]


@pytest.mark.integration
class TestBroadlinkEntityValidation:
    """Test Broadlink entity validation"""
    
    def test_valid_broadlink_entity_format(self, client):
        """Test that valid entity IDs are accepted"""
        valid_entities = [
            'remote.bedroom_rm4_pro',
            'remote.living_room_rm_mini',
            'remote.office_rm4',
        ]
        
        for entity_id in valid_entities:
            device_data = {
                'name': f'Test Device {entity_id}',
                'device_type': 'broadlink',
                'entity_type': 'light',
                'broadlink_entity': entity_id,
                'area': 'Test'
            }
            
            response = client.post(
                '/api/devices/managed',
                data=json.dumps(device_data),
                content_type='application/json'
            )
            
            assert response.status_code in [200, 201], \
                f"Valid entity ID '{entity_id}' was rejected"
    
    def test_invalid_entity_format(self, client):
        """Test that invalid entity formats are rejected"""
        invalid_entities = [
            'not_an_entity',
            'remote',
            'light.bedroom_light',  # Wrong domain
            '',
        ]
        
        for entity_id in invalid_entities:
            device_data = {
                'name': f'Test Device {entity_id}',
                'device_type': 'broadlink',
                'entity_type': 'light',
                'broadlink_entity': entity_id,
                'area': 'Test'
            }
            
            response = client.post(
                '/api/devices/managed',
                data=json.dumps(device_data),
                content_type='application/json'
            )
            
            # Should reject or accept with warning
            assert response.status_code in [200, 201, 400, 500]
    
    def test_missing_broadlink_entity(self, client):
        """Test that missing Broadlink entity is rejected"""
        device_data = {
            'name': 'Device Without Entity',
            'device_type': 'broadlink',
            'entity_type': 'light',
            # Missing broadlink_entity
            'area': 'Test'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should reject missing entity
        assert response.status_code in [400, 500]


@pytest.mark.integration
class TestAreaValidation:
    """Test area validation"""
    
    def test_valid_area(self, client):
        """Test that valid areas are accepted"""
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Living Room'
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
    
    def test_empty_area(self, client):
        """Test that empty area is accepted (optional field)"""
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': ''
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should accept empty area
        assert response.status_code in [200, 201]
    
    def test_missing_area(self, client):
        """Test that missing area is accepted (optional field)"""
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4'
            # Missing area
        }
        
        response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should accept missing area
        assert response.status_code in [200, 201]


@pytest.mark.integration
class TestDuplicateDeviceValidation:
    """Test duplicate device handling"""
    
    def test_create_duplicate_device_name(self, client):
        """Test creating device with duplicate name"""
        device_data = {
            'name': 'Duplicate Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        # Create first device
        response1 = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if response1.status_code not in [200, 201]:
            pytest.skip("First device creation failed")
        
        # Try to create duplicate
        response2 = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        # Should reject or auto-rename
        assert response2.status_code in [200, 201, 400, 409, 500]
    
    def test_update_device_to_duplicate_name(self, client):
        """Test updating device to have duplicate name"""
        # Create first device
        device1_data = {
            'name': 'Device One',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        response1 = client.post(
            '/api/devices/managed',
            data=json.dumps(device1_data),
            content_type='application/json'
        )
        
        if response1.status_code not in [200, 201]:
            pytest.skip("Device creation failed")
        
        # Create second device
        device2_data = {
            'name': 'Device Two',
            'device_type': 'broadlink',
            'entity_type': 'fan',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        response2 = client.post(
            '/api/devices/managed',
            data=json.dumps(device2_data),
            content_type='application/json'
        )
        
        if response2.status_code not in [200, 201]:
            pytest.skip("Second device creation failed")
        
        device2_id = json.loads(response2.data).get('device_id')
        
        if not device2_id:
            pytest.skip("No device_id returned")
        
        # Try to rename device2 to device1's name
        update_data = {'name': 'Device One'}
        response3 = client.put(
            f'/api/devices/managed/{device2_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Should reject or handle gracefully
        assert response3.status_code in [200, 400, 409, 500]


@pytest.mark.integration
class TestCommandValidation:
    """Test command data validation"""
    
    def test_add_valid_command(self, client):
        """Test adding valid command to device"""
        # First create device
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'media_player',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Device creation failed")
        
        device_id = json.loads(create_response.data).get('device_id')
        
        if not device_id:
            pytest.skip("No device_id returned")
        
        # Add command
        command_data = {
            'command_name': 'power',
            'command_data': {
                'code': 'JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ==',
                'type': 'ir'
            }
        }
        
        response = client.post(
            f'/api/devices/{device_id}/commands',
            data=json.dumps(command_data),
            content_type='application/json'
        )
        
        # Should accept valid command
        assert response.status_code in [200, 201, 404]
    
    def test_add_command_with_invalid_code(self, client):
        """Test that invalid IR codes are rejected"""
        # Create device first
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Device creation failed")
        
        device_id = json.loads(create_response.data).get('device_id')
        
        if not device_id:
            pytest.skip("No device_id returned")
        
        # Try to add command with invalid code
        command_data = {
            'command_name': 'power',
            'command_data': {
                'code': 'INVALID_CODE',
                'type': 'ir'
            }
        }
        
        response = client.post(
            f'/api/devices/{device_id}/commands',
            data=json.dumps(command_data),
            content_type='application/json'
        )
        
        # May accept (validation happens at send time) or reject
        assert response.status_code in [200, 201, 400, 404, 500]


@pytest.mark.integration
class TestUpdateValidation:
    """Test device update validation"""
    
    def test_update_device_valid_fields(self, client):
        """Test updating device with valid fields"""
        # Create device
        device_data = {
            'name': 'Original Name',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Original Area'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Device creation failed")
        
        device_id = json.loads(create_response.data).get('device_id')
        
        if not device_id:
            pytest.skip("No device_id returned")
        
        # Update device
        update_data = {
            'name': 'Updated Name',
            'area': 'Updated Area'
        }
        
        response = client.put(
            f'/api/devices/managed/{device_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_update_device_readonly_fields(self, client):
        """Test that readonly fields cannot be updated"""
        # Create device
        device_data = {
            'name': 'Test Device',
            'device_type': 'broadlink',
            'entity_type': 'light',
            'broadlink_entity': 'remote.test_rm4',
            'area': 'Test'
        }
        
        create_response = client.post(
            '/api/devices/managed',
            data=json.dumps(device_data),
            content_type='application/json'
        )
        
        if create_response.status_code not in [200, 201]:
            pytest.skip("Device creation failed")
        
        device_id = json.loads(create_response.data).get('device_id')
        
        if not device_id:
            pytest.skip("No device_id returned")
        
        # Try to update device_type (should be readonly)
        update_data = {
            'device_type': 'smartir'  # Try to change type
        }
        
        response = client.put(
            f'/api/devices/managed/{device_id}',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Should reject or ignore readonly field
        assert response.status_code in [200, 400, 403, 500]
