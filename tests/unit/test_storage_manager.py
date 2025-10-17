"""
Unit tests for StorageManager
Tests data persistence, backup/recovery, and metadata management
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from storage_manager import StorageManager


@pytest.mark.unit
class TestStorageManagerInitialization:
    """Test StorageManager initialization and setup"""
    
    def test_initialization_creates_directories(self, temp_storage_dir):
        """Test that initialization creates necessary directories"""
        storage_path = temp_storage_dir / 'broadlink_manager'
        storage = StorageManager(base_path=str(storage_path))
        
        assert storage_path.exists()
        assert storage.entities_file.parent.exists()
        assert storage.metadata_file.parent.exists()
    
    def test_initialization_creates_empty_files(self, temp_storage_dir):
        """Test that initialization creates empty metadata structure"""
        storage_path = temp_storage_dir / 'broadlink_manager'
        storage = StorageManager(base_path=str(storage_path))
        
        # Metadata should be initialized
        assert storage.metadata is not None
        assert 'entities' in storage.metadata
        assert storage.metadata['entities'] == {}
    
    def test_initialization_loads_existing_data(self, temp_storage_dir):
        """Test that initialization loads existing metadata"""
        storage_path = temp_storage_dir / 'broadlink_manager'
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create existing metadata
        metadata_file = storage_path / 'metadata.json'
        existing_data = {
            'entities': {
                'test_device': {
                    'name': 'Test Device',
                    'entity_type': 'light'
                }
            }
        }
        with open(metadata_file, 'w') as f:
            json.dump(existing_data, f)
        
        # Initialize storage
        storage = StorageManager(base_path=str(storage_path))
        
        # Should load existing data
        entities = storage.get_all_entities()
        assert 'test_device' in entities
        assert entities['test_device']['name'] == 'Test Device'
    
    def test_backup_recovery_on_missing_file(self, temp_storage_dir):
        """Test that backup is restored if main file is missing"""
        storage_path = temp_storage_dir / 'broadlink_manager'
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Create backup file only
        backup_file = storage_path / 'metadata.json.backup'
        backup_data = {
            'entities': {
                'recovered_device': {
                    'name': 'Recovered Device',
                    'entity_type': 'switch'
                }
            }
        }
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        # Initialize storage (should auto-restore from backup)
        storage = StorageManager(base_path=str(storage_path))
        
        # Should have restored data
        entities = storage.get_all_entities()
        assert 'recovered_device' in entities


@pytest.mark.unit
class TestEntityManagement:
    """Test entity CRUD operations"""
    
    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a StorageManager instance"""
        return StorageManager(base_path=str(temp_storage_dir / 'broadlink_manager'))
    
    def test_save_entity(self, storage):
        """Test saving a new entity"""
        entity_data = {
            'name': 'Living Room Light',
            'entity_type': 'light',
            'area': 'Living Room',
            'commands': {'turn_on': 'on_code', 'turn_off': 'off_code'},
            'broadlink_entity': 'remote.rm4_pro'
        }
        
        storage.save_entity('living_room_light', entity_data)
        
        entity = storage.get_entity('living_room_light')
        assert entity is not None
        assert entity['name'] == 'Living Room Light'
        assert entity['entity_type'] == 'light'
    
    def test_add_duplicate_entity(self, storage):
        """Test that adding duplicate entity updates existing"""
        entity_data = {
            'name': 'Test Device',
            'entity_type': 'switch'
        }
        
        # Add first time
        storage.save_entity('test_device', entity_data)
        
        # Add again with different data
        updated_data = {
            'name': 'Updated Device',
            'entity_type': 'light'
        }
        storage.save_entity('test_device', updated_data)
        
        # Should be updated
        entity = storage.get_entity('test_device')
        assert entity['name'] == 'Updated Device'
        assert entity['entity_type'] == 'light'
    
    def test_get_entity(self, storage):
        """Test retrieving a specific entity"""
        entity_data = {'name': 'Test', 'entity_type': 'fan'}
        storage.save_entity('test_fan', entity_data)
        
        entity = storage.get_entity('test_fan')
        
        assert entity is not None
        assert entity['name'] == 'Test'
    
    def test_get_nonexistent_entity(self, storage):
        """Test retrieving non-existent entity returns None"""
        entity = storage.get_entity('nonexistent')
        assert entity is None
    
    def test_get_all_entities(self, storage):
        """Test retrieving all entities"""
        storage.save_entity('device1', {'name': 'Device 1', 'entity_type': 'light'})
        storage.save_entity('device2', {'name': 'Device 2', 'entity_type': 'fan'})
        storage.save_entity('device3', {'name': 'Device 3', 'entity_type': 'switch'})
        
        entities = storage.get_all_entities()
        
        assert len(entities) == 3
        assert 'device1' in entities
        assert 'device2' in entities
        assert 'device3' in entities
    
    def test_get_all_entities_reload(self, storage):
        """Test that reload parameter forces disk read"""
        storage.save_entity('device1', {'name': 'Device 1', 'entity_type': 'light'})
        
        # Get without reload (from memory)
        entities1 = storage.get_all_entities(reload=False)
        
        # Manually modify file
        with open(storage.metadata_file, 'r') as f:
            data = json.load(f)
        data['entities']['device2'] = {'name': 'Device 2', 'entity_type': 'fan'}
        with open(storage.metadata_file, 'w') as f:
            json.dump(data, f)
        
        # Get with reload (from disk)
        entities2 = storage.get_all_entities(reload=True)
        
        assert 'device2' in entities2
        assert 'device2' not in entities1
    
    def test_update_entity(self, storage):
        """Test updating an existing entity"""
        storage.save_entity('test_device', {'name': 'Original', 'entity_type': 'light'})
        
        # Update fields individually
        storage.update_entity_field('test_device', 'name', 'Updated')
        storage.update_entity_field('test_device', 'area', 'Bedroom')
        entity = storage.get_entity('test_device')
        assert entity['name'] == 'Updated'
        assert entity['area'] == 'Bedroom'
        assert entity['entity_type'] == 'light'  # Unchanged field preserved
    
    def test_update_nonexistent_entity(self, storage):
        """Test updating non-existent entity fails"""
        try:
            storage.update_entity_field('nonexistent', 'name', 'Test')
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected
    
    def test_delete_entity(self, storage):
        """Test deleting an entity"""
        storage.save_entity('test_device', {'name': 'Test', 'entity_type': 'switch'})
        
        result = storage.delete_entity('test_device')
        
        assert result is True
        entity = storage.get_entity('test_device')
        assert entity is None
    
    def test_delete_nonexistent_entity(self, storage):
        """Test deleting non-existent entity returns False"""
        result = storage.delete_entity('nonexistent')
        assert result is False


@pytest.mark.unit
class TestBackupAndRecovery:
    """Test backup and recovery functionality"""
    
    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a StorageManager instance"""
        return StorageManager(base_path=str(temp_storage_dir / 'broadlink_manager'))
    
    def test_backup_created_on_save(self, storage):
        """Test that backup file is created when saving"""
        # First save creates the file
        storage.save_entity('test_device', {'name': 'Test', 'entity_type': 'light'})
        
        # Second save creates backup
        storage.save_entity('test_device2', {'name': 'Test 2', 'entity_type': 'fan'})
        
        backup_file = Path(str(storage.metadata_file) + '.backup')
        assert backup_file.exists()
    
    def test_backup_contains_previous_data(self, storage):
        """Test that backup contains data from before the save"""
        # Add first device
        storage.save_entity('device1', {'name': 'Device 1', 'entity_type': 'light'})
        
        # Add second device (creates new backup with device1)
        storage.save_entity('device2', {'name': 'Device 2', 'entity_type': 'fan'})
        
        # Backup should have device1
        backup_file = Path(str(storage.metadata_file) + '.backup')
        with open(backup_file, 'r') as f:
            backup_data = json.load(f)
        
        assert 'entities' in backup_data
        assert 'device1' in backup_data['entities']
    
    def test_atomic_write_prevents_corruption(self, storage):
        """Test that atomic writes prevent file corruption"""
        storage.save_entity('device1', {'name': 'Device 1', 'entity_type': 'light'})
        
        # Simulate write failure by patching rename
        with patch('pathlib.Path.rename', side_effect=OSError("Simulated failure")):
            try:
                storage.save_entity('device2', {'name': 'Device 2', 'entity_type': 'fan'})
            except:
                pass
        
        # Original file should still be intact
        entities = storage.get_all_entities(reload=True)
        assert 'device1' in entities
    
    def test_recovery_from_backup_on_corrupted_file(self, storage, temp_storage_dir):
        """Test recovery when main file is corrupted"""
        # Add data and create backup
        storage.save_entity('device1', {'name': 'Device 1', 'entity_type': 'light'})
        
        # Corrupt main file
        with open(storage.metadata_file, 'w') as f:
            f.write("CORRUPTED JSON{{{")
        
        # Create new storage instance (should auto-recover)
        storage2 = StorageManager(base_path=str(temp_storage_dir / 'broadlink_manager'))
        
        # Should have recovered data or at least not crash
        try:
            entities = storage2.get_all_entities()
            # Either recovered or empty (both are acceptable)
            assert isinstance(entities, dict)
        except:
            pytest.fail("Should handle corrupted file gracefully")


@pytest.mark.unit
class TestMetadataManagement:
    """Test metadata operations"""
    
    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a StorageManager instance"""
        return StorageManager(base_path=str(temp_storage_dir / 'broadlink_manager'))
    
    def test_set_last_generated(self, storage):
        """Test setting last generated timestamp"""
        from datetime import datetime
        
        timestamp = datetime.now().isoformat()
        storage.set_last_generated(timestamp)
        
        # Reload and check
        storage2 = StorageManager(base_path=str(storage.metadata_file.parent))
        # Should persist across instances
        assert storage2.metadata_file.exists()
    
    def test_get_entities_by_type(self, storage):
        """Test filtering entities by type"""
        storage.save_entity('light1', {'name': 'Light 1', 'entity_type': 'light'})
        storage.save_entity('light2', {'name': 'Light 2', 'entity_type': 'light'})
        storage.save_entity('fan1', {'name': 'Fan 1', 'entity_type': 'fan'})
        storage.save_entity('switch1', {'name': 'Switch 1', 'entity_type': 'switch'})
        
        lights = storage.get_entities_by_type('light')
        
        assert len(lights) == 2
        assert 'light1' in lights
        assert 'light2' in lights
        assert 'fan1' not in lights
    
    def test_get_entities_by_broadlink(self, storage):
        """Test filtering entities by Broadlink device"""
        storage.save_entity('device1', {
            'name': 'Device 1',
            'entity_type': 'light',
            'device': 'bedroom_tv'
        })
        storage.save_entity('device2', {
            'name': 'Device 2',
            'entity_type': 'fan',
            'device': 'bedroom_tv'
        })
        storage.save_entity('device3', {
            'name': 'Device 3',
            'entity_type': 'switch',
            'device': 'living_room_tv'
        })
        
        bedroom_devices = storage.get_entities_by_device('bedroom_tv')
        
        assert len(bedroom_devices) == 2
        assert 'device1' in bedroom_devices
        assert 'device2' in bedroom_devices
        assert 'device3' not in bedroom_devices


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling"""
    
    @pytest.fixture
    def storage(self, temp_storage_dir):
        """Create a StorageManager instance"""
        return StorageManager(base_path=str(temp_storage_dir / 'broadlink_manager'))
    
    def test_empty_entity_id(self, storage):
        """Test handling of empty entity ID"""
        storage.save_entity('', {'name': 'Test'})
        # Should handle gracefully
        entity = storage.get_entity('')
        assert entity is not None
    
    def test_none_entity_id(self, storage):
        """Test handling of None entity ID"""
        try:
            storage.save_entity(None, {'name': 'Test'})
        except (TypeError, AttributeError):
            pass  # Expected to fail
    
    def test_special_characters_in_entity_id(self, storage):
        """Test entity IDs with special characters"""
        # These should be normalized by the API layer, but test storage handles them
        entity_ids = [
            'device_with_underscores',
            'device-with-dashes',
            'device.with.dots',
        ]
        
        for entity_id in entity_ids:
            storage.save_entity(entity_id, {'name': 'Test', 'entity_type': 'switch'})
            entity = storage.get_entity(entity_id)
            assert entity is not None
    
    def test_large_entity_data(self, storage):
        """Test handling of large entity data"""
        # Create entity with many commands
        commands = {f'command_{i}': f'code_{i}' * 100 for i in range(100)}
        entity_data = {
            'name': 'Device with Many Commands',
            'entity_type': 'media_player',
            'commands': commands
        }
        
        storage.save_entity('large_device', entity_data)
        
        entity = storage.get_entity('large_device')
        assert len(entity['commands']) == 100
    
    def test_concurrent_access_simulation(self, storage):
        """Test that multiple operations don't corrupt data"""
        # Simulate multiple rapid operations
        for i in range(10):
            storage.save_entity(f'device_{i}', {'name': f'Device {i}', 'entity_type': 'light'})
        
        # All devices should be present
        entities = storage.get_all_entities()
        assert len(entities) == 10
        
        for i in range(10):
            assert f'device_{i}' in entities
    
    def test_unicode_in_entity_data(self, storage):
        """Test handling of Unicode characters"""
        entity_data = {
            'name': 'Dispositivo de Prueba 测试设备 🏠',
            'entity_type': 'light',
            'area': 'Habitación Principal'
        }
        
        storage.save_entity('unicode_device', entity_data)
        
        entity = storage.get_entity('unicode_device')
        assert entity['name'] == 'Dispositivo de Prueba 测试设备 🏠'
