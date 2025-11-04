#!/usr/bin/env python3
"""
Unit tests for command storage format consistency

REGRESSION: Commands stored as metadata dicts instead of code strings
causing test command to fail with "Bad Request" from Home Assistant.

This test ensures commands are stored and retrieved correctly regardless
of whether they're stored as strings or metadata objects.

NOTE: This test is deprecated - StorageManager (metadata.json) has been removed
in favor of DeviceManager (devices.json). See SYSTEM-RETRIEVED-MEMORY[0d325394].
"""

import pytest

pytestmark = pytest.mark.skip(reason="StorageManager removed - test deprecated")


@pytest.mark.unit
class TestCommandStorageFormat:
    """Test command storage format handling"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def storage(self, temp_dir):
        return StorageManager(base_path=str(temp_dir / 'broadlink_manager'))
    
    def test_command_stored_as_string(self, storage):
        """Test that commands stored as strings are retrieved correctly"""
        device_data = {
            'name': 'Test Device',
            'entity_type': 'light',
            'device_type': 'broadlink',
            'broadlink_entity': 'remote.test_rm4',
            'commands': {
                'power': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                'toggle': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU='
            }
        }
        
        storage.save_entity('test_device', device_data)
        
        # Retrieve and verify
        entity = storage.get_entity('test_device')
        assert entity is not None
        assert 'commands' in entity
        assert isinstance(entity['commands']['power'], str)
        assert entity['commands']['power'].startswith('JgBQ')
    
    def test_command_stored_as_metadata_dict(self, storage):
        """Test that commands stored as metadata dicts are handled correctly"""
        device_data = {
            'name': 'Test Device',
            'entity_type': 'light',
            'device_type': 'broadlink',
            'broadlink_entity': 'remote.test_rm4',
            'commands': {
                'power': {
                    'code': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                    'command_type': 'ir',
                    'learned_at': '2025-10-17T18:00:00Z'
                },
                'toggle': {
                    'code': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                    'command_type': 'rf',
                    'learned_at': None
                }
            }
        }
        
        storage.save_entity('test_device', device_data)
        
        # Retrieve and verify
        entity = storage.get_entity('test_device')
        assert entity is not None
        assert 'commands' in entity
        
        # Commands should be stored as-is (metadata dict)
        assert isinstance(entity['commands']['power'], dict)
        assert 'code' in entity['commands']['power']
        assert entity['commands']['power']['code'].startswith('JgBQ')
        assert entity['commands']['power']['command_type'] == 'ir'
    
    def test_extract_code_from_metadata(self, storage):
        """Test extracting actual code from metadata structure"""
        device_data = {
            'name': 'Test Device',
            'entity_type': 'light',
            'commands': {
                'power': {
                    'code': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                    'command_type': 'ir'
                }
            }
        }
        
        storage.save_entity('test_device', device_data)
        entity = storage.get_entity('test_device')
        
        # Simulate what the API should do
        command_data = entity['commands']['power']
        
        if isinstance(command_data, dict):
            actual_code = command_data.get('code', command_data.get('data'))
        else:
            actual_code = command_data
        
        assert actual_code is not None
        assert isinstance(actual_code, str)
        assert actual_code.startswith('JgBQ')
    
    def test_command_without_code_field(self, storage):
        """Test handling metadata dict without 'code' field (invalid)"""
        device_data = {
            'name': 'Test Device',
            'entity_type': 'light',
            'commands': {
                'power': {
                    'command_type': 'ir',
                    'learned_at': None
                    # Missing 'code' field!
                }
            }
        }
        
        storage.save_entity('test_device', device_data)
        entity = storage.get_entity('test_device')
        
        # Simulate extraction
        command_data = entity['commands']['power']
        
        if isinstance(command_data, dict):
            actual_code = command_data.get('code', command_data.get('data'))
        else:
            actual_code = command_data
        
        # Should be None since no code field exists
        assert actual_code is None
    
    def test_mixed_command_formats(self, storage):
        """Test device with both string and metadata command formats"""
        device_data = {
            'name': 'Test Device',
            'entity_type': 'light',
            'commands': {
                'power': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                'toggle': {
                    'code': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                    'command_type': 'rf'
                }
            }
        }
        
        storage.save_entity('test_device', device_data)
        entity = storage.get_entity('test_device')
        
        # Both formats should be preserved
        assert isinstance(entity['commands']['power'], str)
        assert isinstance(entity['commands']['toggle'], dict)
        
        # Extract codes
        power_code = entity['commands']['power']
        toggle_data = entity['commands']['toggle']
        toggle_code = toggle_data.get('code') if isinstance(toggle_data, dict) else toggle_data
        
        assert power_code.startswith('JgBQ')
        assert toggle_code.startswith('JgBQ')


@pytest.mark.unit
class TestCommandRetrievalAPI:
    """Test command retrieval logic matches API expectations"""
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def storage(self, temp_dir):
        return StorageManager(base_path=str(temp_dir / 'broadlink_manager'))
    
    def test_api_command_extraction_logic(self, storage):
        """Test the exact logic used in /api/commands/test endpoint"""
        # Store command with metadata (the problematic case)
        device_data = {
            'name': 'Test Device',
            'entity_type': 'light',
            'commands': {
                'toggle': {
                    'code': 'JgBQAAABKZIVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBUQFRAVEBU=',
                    'command_type': 'rf',
                    'learned_at': None
                }
            }
        }
        
        storage.save_entity('test_device', device_data)
        entity = storage.get_entity('test_device')
        
        # Simulate API logic (from commands.py line 268-280)
        command = 'toggle'
        commands_mapping = entity.get('commands', {})
        command_data = commands_mapping.get(command, command)
        
        # Extract actual command
        if isinstance(command_data, dict):
            actual_command = command_data.get('code', command_data.get('data', command))
        else:
            actual_command = command_data
        
        # Verify we got the actual code, not the metadata dict
        assert isinstance(actual_command, str)
        assert actual_command.startswith('JgBQ')
        assert actual_command != str(command_data)  # Not the dict representation
    
    def test_api_handles_missing_code_gracefully(self, storage):
        """Test API handles metadata without code field"""
        device_data = {
            'name': 'Test Device',
            'commands': {
                'toggle': {
                    'command_type': 'rf',
                    'learned_at': None
                    # No 'code' field
                }
            }
        }
        
        storage.save_entity('test_device', device_data)
        entity = storage.get_entity('test_device')
        
        command = 'toggle'
        commands_mapping = entity.get('commands', {})
        command_data = commands_mapping.get(command, command)
        
        if isinstance(command_data, dict):
            actual_command = command_data.get('code', command_data.get('data', command))
        else:
            actual_command = command_data
        
        # Should fall back to original command name
        assert actual_command == 'toggle'
