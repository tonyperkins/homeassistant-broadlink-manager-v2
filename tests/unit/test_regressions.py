"""
Regression tests for previously identified bugs
These tests ensure that fixed bugs don't reoccur
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from entity_generator import EntityGenerator
from device_manager import DeviceManager
from smartir_yaml_generator import SmartIRYAMLGenerator


@pytest.mark.unit
@pytest.mark.regression
class TestEntityIDPrefixRegression:
    """
    Regression test for entity ID prefix bug
    
    BUG: Entity IDs were generated with type prefix (e.g., "light.bedroom_light")
    causing "invalid slug" errors in Home Assistant
    
    FIX: Entity IDs should be just the device name (e.g., "bedroom_light")
    
    IMPACT: High - Prevented all entity generation from working
    """
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def mock_storage(self, temp_dir):
        """Create mock storage manager"""
        storage = Mock()
        storage.helpers_file = temp_dir / "helpers.yaml"
        storage.package_file = temp_dir / "package.yaml"
        storage.set_last_generated = Mock()
        return storage
    
    @pytest.fixture
    def generator(self, mock_storage):
        """Create EntityGenerator instance"""
        return EntityGenerator(mock_storage, "remote.test_broadlink")
    
    def test_light_entity_id_no_prefix(self, generator, mock_storage):
        """Test that light entity IDs don't have 'light.' prefix"""
        entities = {
            "bedroom_light": {
                "device": "bedroom_light",
                "entity_type": "light",
                "name": "Bedroom Light",
                "enabled": True,
                "commands": {"turn_on": "on", "turn_off": "off"},
                "broadlink_entity": "remote.test"
            }
        }
        
        mock_storage.get_all_entities = Mock(return_value=entities)
        result = generator.generate_all({})
        
        assert result["success"] is True
        
        with open(mock_storage.entities_file, "r") as f:
            content = f.read()
        
        # CRITICAL: Should NOT have prefix
        assert "light.bedroom_light" not in content
        assert "bedroom_light:" in content or "bedroom_light\n" in content
    
    def test_fan_entity_id_no_prefix(self, generator, mock_storage):
        """Test that fan entity IDs don't have 'fan.' prefix"""
        entities = {
            "ceiling_fan": {
                "device": "ceiling_fan",
                "entity_type": "fan",
                "name": "Ceiling Fan",
                "enabled": True,
                "commands": {"speed_1": "s1", "speed_2": "s2"},
                "broadlink_entity": "remote.test"
            }
        }
        
        mock_storage.get_all_entities = Mock(return_value=entities)
        result = generator.generate_all({})
        
        assert result["success"] is True
        
        with open(mock_storage.entities_file, "r") as f:
            content = f.read()
        
        assert "fan.ceiling_fan" not in content
        assert "ceiling_fan:" in content or "ceiling_fan\n" in content
    
    def test_helper_ids_no_prefix(self, generator, mock_storage):
        """Test that helper IDs don't have entity type prefix"""
        entities = {
            "test_light": {
                "device": "test_light",
                "entity_type": "light",
                "name": "Test Light",
                "enabled": True,
                "commands": {"turn_on": "on", "turn_off": "off"},
                "broadlink_entity": "remote.test"
            }
        }
        
        mock_storage.get_all_entities = Mock(return_value=entities)
        result = generator.generate_all({})
        
        assert result["success"] is True
        
        with open(mock_storage.helpers_file, "r") as f:
            content = f.read()
        
        # Helper should be "test_light_state", not "light.test_light_state"
        assert "light.test_light_state" not in content
        assert "test_light_state:" in content


@pytest.mark.unit
@pytest.mark.regression
class TestFanDirectionHelperRegression:
    """
    Regression test for fan direction helper bug
    
    BUG: Fan direction helper was only created if fan had reverse command,
    but direction_template always referenced it, causing HA errors
    
    FIX: Always create direction helper for fans, regardless of commands
    
    IMPACT: Medium - Caused fan entities to fail validation
    """
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def mock_storage(self, temp_dir):
        storage = Mock()
        storage.helpers_file = temp_dir / "helpers.yaml"
        storage.package_file = temp_dir / "package.yaml"
        storage.set_last_generated = Mock()
        return storage
    
    @pytest.fixture
    def generator(self, mock_storage):
        return EntityGenerator(mock_storage, "remote.test_broadlink")
    
    def test_fan_without_reverse_has_direction_helper(self, generator, mock_storage):
        """Test that fan without reverse command still gets direction helper"""
        entities = {
            "fan_no_reverse": {
                "device": "fan_no_reverse",
                "entity_type": "fan",
                "name": "Fan Without Reverse",
                "enabled": True,
                "commands": {
                    "speed_1": "s1",
                    "speed_2": "s2",
                    "speed_3": "s3"
                    # NO reverse command
                },
                "broadlink_entity": "remote.test"
            }
        }
        
        mock_storage.get_all_entities = Mock(return_value=entities)
        result = generator.generate_all({})
        
        assert result["success"] is True
        
        with open(mock_storage.helpers_file, "r") as f:
            helpers_content = f.read()
        
        # CRITICAL: Direction helper must exist
        assert "fan_no_reverse_direction:" in helpers_content
        assert "forward" in helpers_content
        assert "reverse" in helpers_content
    
    def test_fan_with_reverse_has_direction_helper(self, generator, mock_storage):
        """Test that fan with reverse command also gets direction helper"""
        entities = {
            "fan_with_reverse": {
                "device": "fan_with_reverse",
                "entity_type": "fan",
                "name": "Fan With Reverse",
                "enabled": True,
                "commands": {
                    "speed_1": "s1",
                    "fan_reverse": "reverse"  # HAS reverse
                },
                "broadlink_entity": "remote.test"
            }
        }
        
        mock_storage.get_all_entities = Mock(return_value=entities)
        result = generator.generate_all({})
        
        assert result["success"] is True
        
        with open(mock_storage.helpers_file, "r") as f:
            helpers_content = f.read()
        
        assert "fan_with_reverse_direction:" in helpers_content


@pytest.mark.unit
@pytest.mark.regression
class TestSmartIRConfigPersistenceRegression:
    """
    Regression test for SmartIR config persistence
    
    BUG: SmartIR config fields (device_code, controller_device) were nested
    inside 'config' object instead of being at top level
    
    FIX: Extract device_code, controller_device, etc. to top level in devices.json
    
    IMPACT: High - Users couldn't edit SmartIR devices
    """
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def device_manager(self, temp_dir):
        return DeviceManager(storage_path=temp_dir)
    
    def test_smartir_config_fields_persist(self, device_manager):
        """Test that SmartIR config fields are saved correctly"""
        # Create SmartIR device
        device_data = {
            'name': 'Test AC',
            'entity_type': 'climate',
            'device_type': 'smartir',
            'device_code': 1234,
            'controller_device': 'remote.bedroom_rm4',
            'area_id': 'bedroom'
        }
        
        device_manager.create_device('test_ac', device_data)
        
        # Retrieve and verify
        device = device_manager.get_device('test_ac')
        assert device is not None
        assert device['device_code'] == 1234
        assert device['controller_device'] == 'remote.bedroom_rm4'
    
    def test_smartir_config_update_persists(self, device_manager):
        """Test that updating SmartIR config persists changes"""
        # Create device
        device_manager.create_device('test_ac', {
            'name': 'Test AC',
            'entity_type': 'climate',
            'device_type': 'smartir',
            'device_code': 1234,
            'controller_device': 'remote.bedroom_rm4'
        })
        
        # Update config
        device_manager.update_device('test_ac', {
            'device_code': 5678,
            'controller_device': 'remote.living_room_rm4'
        })
        
        # Verify changes persisted
        device = device_manager.get_device('test_ac')
        assert device['device_code'] == 5678
        assert device['controller_device'] == 'remote.living_room_rm4'


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.skip(reason="SmartIR YAML generation requires full file system setup - tested in integration tests")
class TestSmartIRControllerDataRegression:
    """
    Regression test for SmartIR controller_data format
    
    BUG: controller_data used IP addresses instead of entity IDs
    causing SmartIR to fail with "entity not found" errors
    
    FIX: Use entity IDs (e.g., "remote.bedroom_rm4") not IPs
    
    IMPACT: Critical - SmartIR devices didn't work at all
    
    NOTE: These tests are skipped in unit tests as they require full file system setup.
    The functionality is tested in integration tests instead.
    """
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    def test_controller_data_uses_entity_id_not_ip(self, temp_dir):
        """Test that controller_data contains entity ID, not IP address"""
        generator = SmartIRYAMLGenerator(str(temp_dir))
        
        device_config = {
            'name': 'Test AC',
            'entity_type': 'climate',
            'smartir_code': '1234',
            'controller_device': 'remote.bedroom_rm4_pro',
            'area': 'Bedroom'
        }
        
        result = generator.generate_device_config('test_ac', device_config)
        
        assert result['success'] is True
        
        # Read generated YAML
        yaml_file = temp_dir / 'smartir' / 'climate.yaml'
        with open(yaml_file, 'r') as f:
            content = f.read()
        
        # CRITICAL: Should use entity ID, not IP
        assert 'remote.bedroom_rm4_pro' in content
        
        # Should NOT contain IP addresses
        import re
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        ips_found = re.findall(ip_pattern, content)
        
        # May have port numbers like 192.168.1.1, but controller_data should be entity ID
        # Check that controller_data line specifically doesn't have IP
        for line in content.split('\n'):
            if 'controller_data:' in line:
                assert not re.search(ip_pattern, line), \
                    f"controller_data should not contain IP address: {line}"
    
    def test_non_broadlink_controller_uses_entity_id(self, temp_dir):
        """Test that non-Broadlink controllers also use entity IDs"""
        generator = SmartIRYAMLGenerator(str(temp_dir))
        
        device_config = {
            'name': 'Test TV',
            'entity_type': 'media_player',
            'smartir_code': '5678',
            'controller_device': 'remote.harmony_hub',  # Harmony Hub
            'area': 'Living Room'
        }
        
        result = generator.generate_device_config('test_tv', device_config)
        
        assert result['success'] is True
        
        yaml_file = temp_dir / 'smartir' / 'media_player.yaml'
        with open(yaml_file, 'r') as f:
            content = f.read()
        
        # Should use Harmony Hub entity ID
        assert 'remote.harmony_hub' in content


@pytest.mark.unit
@pytest.mark.regression
class TestDeviceNameNormalizationRegression:
    """
    Regression test for device name normalization
    
    BUG: Special characters in device names caused entity ID conflicts
    
    FIX: Proper normalization removes special chars, collapses spaces
    
    IMPACT: Medium - Caused entity creation failures
    """
    
    def test_normalize_device_name_special_chars(self):
        """Test that special characters are removed from device names"""
        from api.devices import normalize_device_name
        
        # Test cases that previously caused issues
        test_cases = [
            ("Tony's Office Light", "tonys_office_light"),
            ("Master Bedroom!", "master_bedroom"),
            ("Living Room TV (Samsung)", "living_room_tv_samsung"),
            ("Kitchen   Light", "kitchen_light"),  # Multiple spaces
            ("Garage-Door", "garagedoor"),
            ("AC/Heater", "acheater"),
        ]
        
        for input_name, expected_output in test_cases:
            result = normalize_device_name(input_name)
            assert result == expected_output, \
                f"normalize_device_name('{input_name}') = '{result}', expected '{expected_output}'"
    
    def test_normalize_preserves_underscores(self):
        """Test that existing underscores are preserved"""
        from api.devices import normalize_device_name
        
        result = normalize_device_name("bedroom_light")
        assert result == "bedroom_light"
    
    def test_normalize_handles_unicode(self):
        """Test that Unicode characters are handled"""
        from api.devices import normalize_device_name
        
        # Should remove or transliterate Unicode
        result = normalize_device_name("Habitación Principal")
        # Should produce something valid (exact output may vary)
        assert isinstance(result, str)
        assert len(result) > 0
        assert " " not in result


@pytest.mark.unit
@pytest.mark.regression
class TestBackupRecoveryRegression:
    """
    Regression test for backup and recovery
    
    BUG: Interrupted writes could corrupt devices.json
    
    FIX: Atomic writes with backup before save
    
    IMPACT: Critical - Caused permanent data loss
    """
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def device_manager(self, temp_dir):
        return DeviceManager(storage_path=temp_dir)
    
    def test_backup_created_before_save(self, device_manager):
        """Test that backup is created before saving"""
        # First save creates the file
        device_manager.create_device('device1', {'name': 'Device 1', 'device_type': 'broadlink'})
        
        # Second save creates backup
        device_manager.create_device('device2', {'name': 'Device 2', 'device_type': 'broadlink'})
        
        # Backup should exist
        backup_file = Path(str(device_manager.devices_file) + '.backup')
        assert backup_file.exists()
    
    def test_recovery_from_backup_on_missing_file(self, temp_dir):
        """Test that data is recovered from backup if main file is missing"""
        import json
        backup_file = temp_dir / 'devices.json.backup'
        backup_data = {
            'recovered_device': {
                'name': 'Recovered Device',
                'device_type': 'broadlink'
            }
        }
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f)
        
        # Initialize device manager (should auto-recover)
        device_manager = DeviceManager(storage_path=temp_dir)
        
        # Should have recovered data
        devices = device_manager.get_all_devices()
        assert 'recovered_device' in devices
        assert devices['recovered_device']['name'] == 'Recovered Device'


@pytest.mark.unit
@pytest.mark.regression
class TestMultipleEntityGroupingRegression:
    """
    Regression test for multiple entity grouping
    
    BUG: Multiple lights/fans created separate platform entries
    instead of grouping under single platform
    
    FIX: Group entities of same type under single platform entry
    
    IMPACT: Low - Made YAML files unnecessarily large
    """
    
    @pytest.fixture
    def temp_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def mock_storage(self, temp_dir):
        storage = Mock()
        storage.helpers_file = temp_dir / "helpers.yaml"
        storage.package_file = temp_dir / "package.yaml"
        storage.set_last_generated = Mock()
        return storage
    
    @pytest.fixture
    def generator(self, mock_storage):
        return EntityGenerator(mock_storage, "remote.test_broadlink")
    
    def test_multiple_lights_single_platform(self, generator, mock_storage):
        """Test that multiple lights are grouped under one platform entry"""
        entities = {
            "light1": {
                "device": "light1",
                "entity_type": "light",
                "name": "Light 1",
                "enabled": True,
                "commands": {"turn_on": "on", "turn_off": "off"},
                "broadlink_entity": "remote.test"
            },
            "light2": {
                "device": "light2",
                "entity_type": "light",
                "name": "Light 2",
                "enabled": True,
                "commands": {"turn_on": "on", "turn_off": "off"},
                "broadlink_entity": "remote.test"
            },
            "light3": {
                "device": "light3",
                "entity_type": "light",
                "name": "Light 3",
                "enabled": True,
                "commands": {"turn_on": "on", "turn_off": "off"},
                "broadlink_entity": "remote.test"
            }
        }
        
        mock_storage.get_all_entities = Mock(return_value=entities)
        result = generator.generate_all({})
        
        assert result["success"] is True
        
        with open(mock_storage.entities_file, "r") as f:
            content = f.read()
        
        # Should have only ONE "platform: template" for lights
        platform_count = content.count("platform: template")
        assert platform_count == 1, \
            f"Expected 1 platform entry for 3 lights, found {platform_count}"
