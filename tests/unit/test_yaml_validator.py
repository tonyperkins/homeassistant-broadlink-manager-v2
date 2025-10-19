#!/usr/bin/env python3
"""
Unit tests for YAML Validator
"""

import pytest
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent.parent / "app"
sys.path.insert(0, str(app_dir))

from yaml_validator import YAMLValidator


class TestDeviceConfigValidation:
    """Test device configuration validation"""

    def test_valid_climate_config(self):
        """Test valid climate device configuration"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "living_room_ac",
            "device_code": 1000,
            "controller_data": "remote.bedroom_rm4",
            "temperature_sensor": "sensor.living_room_temperature",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is True
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Test missing required field"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "living_room_ac",
            # Missing device_code
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("device_code" in error for error in errors)

    def test_wrong_platform_value(self):
        """Test wrong platform value"""
        config = {
            "platform": "wrong_platform",
            "name": "Living Room AC",
            "unique_id": "living_room_ac",
            "device_code": 1000,
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("smartir" in error.lower() for error in errors)

    def test_invalid_device_code_type(self):
        """Test invalid device_code type (string instead of int)"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "living_room_ac",
            "device_code": "1000",  # Should be int
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("device_code" in error and "int" in error for error in errors)

    def test_negative_device_code(self):
        """Test negative device_code"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "living_room_ac",
            "device_code": -1000,
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("positive" in error.lower() for error in errors)

    def test_unique_id_with_spaces(self):
        """Test unique_id with spaces (invalid)"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "living room ac",  # Spaces not allowed
            "device_code": 1000,
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("unique_id" in error and "spaces" in error.lower() for error in errors)

    def test_unique_id_with_uppercase(self):
        """Test unique_id with uppercase (invalid)"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "Living_Room_AC",  # Uppercase not allowed
            "device_code": 1000,
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("unique_id" in error and "lowercase" in error.lower() for error in errors)

    def test_invalid_entity_id_format(self):
        """Test invalid entity ID format"""
        config = {
            "platform": "smartir",
            "name": "Living Room AC",
            "unique_id": "living_room_ac",
            "device_code": 1000,
            "controller_data": "remote.bedroom rm4",  # Space in entity ID
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("entity id" in error.lower() and "controller_data" in error.lower() for error in errors)

    def test_valid_media_player_config(self):
        """Test valid media player configuration"""
        config = {
            "platform": "smartir",
            "name": "Living Room TV",
            "unique_id": "living_room_tv",
            "device_code": 2000,
            "controller_data": "remote.bedroom_rm4",
            "power_sensor": "binary_sensor.tv_power",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "media_player")
        assert is_valid is True
        assert len(errors) == 0

    def test_valid_fan_config(self):
        """Test valid fan configuration"""
        config = {
            "platform": "smartir",
            "name": "Bedroom Fan",
            "unique_id": "bedroom_fan",
            "device_code": 3000,
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "fan")
        assert is_valid is True
        assert len(errors) == 0

    def test_empty_required_field(self):
        """Test empty required field"""
        config = {
            "platform": "smartir",
            "name": "",  # Empty name
            "unique_id": "living_room_ac",
            "device_code": 1000,
            "controller_data": "remote.bedroom_rm4",
        }

        is_valid, errors = YAMLValidator.validate_device_config(config, "climate")
        assert is_valid is False
        assert any("name" in error and "empty" in error.lower() for error in errors)


class TestYAMLFileValidation:
    """Test YAML file content validation"""

    def test_valid_file_content(self):
        """Test valid file content with multiple devices"""
        devices = [
            {
                "platform": "smartir",
                "name": "Living Room AC",
                "unique_id": "living_room_ac",
                "device_code": 1000,
                "controller_data": "remote.bedroom_rm4",
            },
            {
                "platform": "smartir",
                "name": "Bedroom AC",
                "unique_id": "bedroom_ac",
                "device_code": 1001,
                "controller_data": "remote.bedroom_rm4",
            },
        ]

        is_valid, errors = YAMLValidator.validate_yaml_file_content(devices, "climate")
        assert is_valid is True
        assert len(errors) == 0

    def test_duplicate_unique_ids(self):
        """Test duplicate unique_ids in file"""
        devices = [
            {
                "platform": "smartir",
                "name": "Living Room AC",
                "unique_id": "living_room_ac",
                "device_code": 1000,
                "controller_data": "remote.bedroom_rm4",
            },
            {
                "platform": "smartir",
                "name": "Bedroom AC",
                "unique_id": "living_room_ac",  # Duplicate
                "device_code": 1001,
                "controller_data": "remote.bedroom_rm4",
            },
        ]

        is_valid, errors = YAMLValidator.validate_yaml_file_content(devices, "climate")
        assert is_valid is False
        assert any("duplicate" in error.lower() and "unique_id" in error.lower() for error in errors)

    def test_invalid_content_type(self):
        """Test invalid content type (not a list)"""
        devices = {"not": "a list"}

        is_valid, errors = YAMLValidator.validate_yaml_file_content(devices, "climate")
        assert is_valid is False
        assert any("list" in error.lower() for error in errors)

    def test_device_not_dict(self):
        """Test device that is not a dict"""
        devices = [
            {
                "platform": "smartir",
                "name": "Living Room AC",
                "unique_id": "living_room_ac",
                "device_code": 1000,
                "controller_data": "remote.bedroom_rm4",
            },
            "not a dict",
        ]

        is_valid, errors = YAMLValidator.validate_yaml_file_content(devices, "climate")
        assert is_valid is False
        assert any("dict" in error.lower() for error in errors)


class TestYAMLSyntaxValidation:
    """Test YAML syntax validation"""

    def test_valid_yaml_syntax(self):
        """Test valid YAML syntax"""
        yaml_content = """
- platform: smartir
  name: Living Room AC
  unique_id: living_room_ac
  device_code: 1000
  controller_data: remote.bedroom_rm4
"""

        is_valid, error = YAMLValidator.validate_yaml_syntax(yaml_content)
        assert is_valid is True
        assert error is None

    def test_invalid_yaml_syntax(self):
        """Test invalid YAML syntax"""
        yaml_content = """
- platform: smartir
  name: Living Room AC
  unique_id: living_room_ac
  device_code: 1000
  controller_data: remote.bedroom_rm4
    invalid_indentation: true
"""

        is_valid, error = YAMLValidator.validate_yaml_syntax(yaml_content)
        assert is_valid is False
        assert error is not None


class TestEntityIDValidation:
    """Test entity ID validation"""

    def test_valid_entity_ids(self):
        """Test valid entity ID formats"""
        valid_ids = [
            "remote.bedroom_rm4",
            "sensor.living_room_temperature",
            "binary_sensor.tv_power",
            "climate.living_room_ac",
        ]

        for entity_id in valid_ids:
            assert YAMLValidator._is_valid_entity_id(entity_id) is True

    def test_invalid_entity_ids(self):
        """Test invalid entity ID formats"""
        invalid_ids = [
            "remote.bedroom rm4",  # Space
            "remote.Bedroom_RM4",  # Uppercase
            "remote",  # No domain separator
            "remote.",  # Empty entity name
            ".bedroom_rm4",  # Empty domain
            "REMOTE.bedroom_rm4",  # Uppercase domain
        ]

        for entity_id in invalid_ids:
            assert YAMLValidator._is_valid_entity_id(entity_id) is False


class TestYAMLGeneration:
    """Test YAML generation and validation"""

    def test_generate_valid_yaml(self):
        """Test generating valid YAML string"""
        devices = [
            {
                "platform": "smartir",
                "name": "Living Room AC",
                "unique_id": "living_room_ac",
                "device_code": 1000,
                "controller_data": "remote.bedroom_rm4",
            }
        ]

        is_valid, yaml_string, errors = YAMLValidator.validate_and_format_yaml(devices, "climate")
        assert is_valid is True
        assert yaml_string is not None
        assert len(errors) == 0
        assert "platform: smartir" in yaml_string
        assert "living_room_ac" in yaml_string

    def test_generate_invalid_yaml(self):
        """Test generating YAML from invalid devices"""
        devices = [
            {
                "platform": "smartir",
                "name": "Living Room AC",
                # Missing required fields
            }
        ]

        is_valid, yaml_string, errors = YAMLValidator.validate_and_format_yaml(devices, "climate")
        assert is_valid is False
        assert yaml_string is None
        assert len(errors) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
