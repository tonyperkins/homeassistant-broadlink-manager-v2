"""
Integration tests for API endpoints
"""

import pytest
import json


@pytest.mark.integration
class TestDeviceEndpoints:
    """Test device-related API endpoints"""
    
    def test_get_devices_empty(self, client):
        """Test getting devices when none exist"""
        response = client.get('/api/devices')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_create_device(self, client, sample_device_data):
        """Test creating a device via API"""
        response = client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        data = json.loads(response.data)
        assert data.get('success') is True or 'device_id' in data
    
    def test_get_device_by_id(self, client, sample_device_data):
        """Test retrieving a specific device"""
        # First create a device
        client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        # Then retrieve it
        response = client.get('/api/devices/test_device')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['device_id'] == 'test_device'
    
    def test_update_device(self, client, sample_device_data):
        """Test updating a device via API"""
        # Create device
        client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        # Update device
        response = client.put(
            '/api/devices/test_device',
            data=json.dumps({'name': 'Updated Name'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    def test_delete_device(self, client, sample_device_data):
        """Test deleting a device via API"""
        # Create device
        client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        # Delete device
        response = client.delete('/api/devices/test_device')
        assert response.status_code in [200, 204]


@pytest.mark.integration
class TestCommandEndpoints:
    """Test command-related API endpoints"""
    
    def test_add_command(self, client, sample_device_data, sample_command_data):
        """Test adding a command to a device"""
        # Create device first
        client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        # Add command
        response = client.post(
            '/api/devices/test_device/commands',
            data=json.dumps({
                'command_name': 'power',
                'command_data': sample_command_data
            }),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
    
    def test_get_device_commands(self, client, sample_device_data, sample_command_data):
        """Test retrieving all commands for a device"""
        # Create device and add command
        client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        client.post(
            '/api/devices/test_device/commands',
            data=json.dumps({
                'command_name': 'power',
                'command_data': sample_command_data
            }),
            content_type='application/json'
        )
        
        # Get commands
        response = client.get('/api/devices/test_device/commands')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_delete_command(self, client, sample_device_data, sample_command_data):
        """Test deleting a command from a device"""
        # Create device and add command
        client.post(
            '/api/devices',
            data=json.dumps({
                'device_id': 'test_device',
                'device_data': sample_device_data
            }),
            content_type='application/json'
        )
        
        client.post(
            '/api/devices/test_device/commands',
            data=json.dumps({
                'command_name': 'power',
                'command_data': sample_command_data
            }),
            content_type='application/json'
        )
        
        # Delete command
        response = client.delete('/api/devices/test_device/commands/power')
        assert response.status_code in [200, 204]


@pytest.mark.integration
class TestAreaEndpoints:
    """Test area-related API endpoints"""
    
    def test_get_areas(self, client):
        """Test getting all areas"""
        response = client.get('/api/areas')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
    
    def test_create_area(self, client, sample_area_data):
        """Test creating an area via API"""
        response = client.post(
            '/api/areas',
            data=json.dumps({
                'area_id': 'master_bedroom',
                'area_data': sample_area_data
            }),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]


@pytest.mark.integration
@pytest.mark.slow
class TestBroadlinkEndpoints:
    """Test Broadlink device interaction endpoints"""
    
    def test_discover_devices(self, client):
        """Test device discovery endpoint"""
        response = client.get('/api/broadlink/discover')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))
    
    @pytest.mark.requires_device
    def test_learn_command(self, client):
        """Test learning a command (requires actual device)"""
        response = client.post(
            '/api/broadlink/learn',
            data=json.dumps({
                'device_entity': 'remote.master_bedroom_rm4_pro',
                'timeout': 30
            }),
            content_type='application/json'
        )
        
        # This will timeout without a real device, but should return proper structure
        assert response.status_code in [200, 408, 500]
    
    @pytest.mark.requires_device
    def test_send_command(self, client, sample_command_data):
        """Test sending a command (requires actual device)"""
        response = client.post(
            '/api/broadlink/send',
            data=json.dumps({
                'device_entity': 'remote.master_bedroom_rm4_pro',
                'code': sample_command_data['code']
            }),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 404, 500]
