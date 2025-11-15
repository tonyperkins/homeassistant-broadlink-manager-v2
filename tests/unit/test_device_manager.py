"""
Unit tests for DeviceManager
"""

import pytest
from datetime import datetime


@pytest.mark.unit
class TestDeviceManager:
    """Test DeviceManager functionality"""
    
    def test_initialization(self, device_manager):
        """Test DeviceManager initializes correctly"""
        assert device_manager.storage_path.exists()
        assert device_manager.devices_file.exists()
    
    def test_create_device(self, device_manager, sample_device_data):
        """Test creating a new device"""
        result = device_manager.create_device('test_device', sample_device_data)
        
        assert result is True
        device = device_manager.get_device('test_device')
        assert device is not None
        assert device['name'] == sample_device_data['name']
        assert device['type'] == sample_device_data['type']
        assert device['device_id'] == 'test_device'
        assert 'created_at' in device
        assert 'commands' in device
    
    def test_create_duplicate_device(self, device_manager, sample_device_data):
        """Test that creating a duplicate device fails"""
        device_manager.create_device('test_device', sample_device_data)
        result = device_manager.create_device('test_device', sample_device_data)
        
        assert result is False
    
    def test_get_device(self, device_manager, sample_device_data):
        """Test retrieving a device"""
        device_manager.create_device('test_device', sample_device_data)
        device = device_manager.get_device('test_device')
        
        assert device is not None
        assert device['device_id'] == 'test_device'
    
    def test_get_nonexistent_device(self, device_manager):
        """Test retrieving a non-existent device returns None"""
        device = device_manager.get_device('nonexistent')
        assert device is None
    
    def test_get_all_devices(self, device_manager, sample_device_data):
        """Test retrieving all devices"""
        device_manager.create_device('device1', sample_device_data)
        device_manager.create_device('device2', sample_device_data)
        
        devices = device_manager.get_all_devices()
        assert len(devices) == 2
        assert 'device1' in devices
        assert 'device2' in devices
    
    def test_update_device(self, device_manager, sample_device_data):
        """Test updating device metadata"""
        device_manager.create_device('test_device', sample_device_data)
        
        updates = {'name': 'Updated Name', 'model': 'New Model'}
        result = device_manager.update_device('test_device', updates)
        
        assert result is True
        device = device_manager.get_device('test_device')
        assert device['name'] == 'Updated Name'
        assert device['model'] == 'New Model'
        assert 'updated_at' in device
    
    def test_update_preserves_commands(self, device_manager, sample_device_data, sample_command_data):
        """Test that updating device preserves commands"""
        device_manager.create_device('test_device', sample_device_data)
        device_manager.add_command('test_device', 'power', sample_command_data)
        
        device_manager.update_device('test_device', {'name': 'New Name'})
        
        device = device_manager.get_device('test_device')
        assert 'power' in device['commands']
    
    def test_delete_device(self, device_manager, sample_device_data):
        """Test deleting a device"""
        device_manager.create_device('test_device', sample_device_data)
        result = device_manager.delete_device('test_device')
        
        assert result is True
        device = device_manager.get_device('test_device')
        assert device is None
    
    def test_delete_nonexistent_device(self, device_manager):
        """Test deleting a non-existent device"""
        result = device_manager.delete_device('nonexistent')
        assert result is False
    
    def test_add_command(self, device_manager, sample_device_data, sample_command_data):
        """Test adding a command to a device"""
        device_manager.create_device('test_device', sample_device_data)
        result = device_manager.add_command('test_device', 'power', sample_command_data)
        
        assert result is True
        device = device_manager.get_device('test_device')
        assert 'power' in device['commands']
        assert device['commands']['power']['code'] == sample_command_data['code']
    
    def test_add_command_to_nonexistent_device(self, device_manager, sample_command_data):
        """Test adding a command to a non-existent device fails"""
        result = device_manager.add_command('nonexistent', 'power', sample_command_data)
        assert result is False
    
    def test_delete_command(self, device_manager, sample_device_data, sample_command_data):
        """Test deleting a command from a device"""
        device_manager.create_device('test_device', sample_device_data)
        device_manager.add_command('test_device', 'power', sample_command_data)
        
        result = device_manager.delete_command('test_device', 'power')
        
        assert result is True
        device = device_manager.get_device('test_device')
        assert 'power' not in device['commands']
    
    def test_get_device_commands(self, device_manager, sample_device_data, sample_command_data):
        """Test retrieving all commands for a device"""
        device_manager.create_device('test_device', sample_device_data)
        device_manager.add_command('test_device', 'power', sample_command_data)
        device_manager.add_command('test_device', 'volume_up', sample_command_data)
        
        commands = device_manager.get_device_commands('test_device')
        
        assert len(commands) == 2
        assert 'power' in commands
        assert 'volume_up' in commands
    
    def test_get_devices_by_broadlink(self, device_manager, sample_device_data):
        """Test filtering devices by Broadlink entity"""
        # Create devices with different Broadlink entities
        data1 = sample_device_data.copy()
        data1['broadlink_entity'] = 'remote.bedroom_rm4'
        device_manager.create_device('device1', data1)
        
        data2 = sample_device_data.copy()
        data2['broadlink_entity'] = 'remote.living_room_rm4'
        device_manager.create_device('device2', data2)
        
        data3 = sample_device_data.copy()
        data3['broadlink_entity'] = 'remote.bedroom_rm4'
        device_manager.create_device('device3', data3)
        
        devices = device_manager.get_devices_by_broadlink('remote.bedroom_rm4')
        
        assert len(devices) == 2
        assert 'device1' in devices
        assert 'device3' in devices
        assert 'device2' not in devices
    
    def test_generate_device_id(self, device_manager):
        """Test device ID generation (area_id is ignored, only device name is used)"""
        device_id = device_manager.generate_device_id('master_bedroom', 'Samsung TV')
        assert device_id == 'samsung_tv'
        
        # Test with special characters
        device_id = device_manager.generate_device_id('living_room', 'Sony A/V Receiver')
        assert device_id == 'sony_a_v_receiver'
        
        # Test with multiple spaces
        device_id = device_manager.generate_device_id('office', 'HP   Printer')
        assert device_id == 'hp_printer'
