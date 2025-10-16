#!/usr/bin/env python3
"""
Unit tests for SmartIR YAML Generator
Tests the fix for controller_data to use entity IDs instead of IP addresses
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
from app.smartir_yaml_generator import SmartIRYAMLGenerator


class TestSmartIRYAMLGenerator:
    """Test SmartIR YAML generation with entity IDs"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def generator(self, temp_config_dir):
        """Create a SmartIR YAML generator instance"""
        return SmartIRYAMLGenerator(config_path=temp_config_dir)
    
    def test_climate_device_with_broadlink_entity(self, generator, temp_config_dir):
        """Test generating climate device config with Broadlink entity ID"""
        device_id = "living_room_ac"
        device_data = {
            "name": "Living Room AC",
            "entity_type": "climate",
            "device_code": "1000",
            "controller_device": "remote.broadlink_rm4_pro",
            "temperature_sensor": "sensor.living_room_temp",
            "humidity_sensor": "sensor.living_room_humidity"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        assert "config" in result
        
        config = result["config"]
        assert config["platform"] == "smartir"
        assert config["name"] == "Living Room AC"
        assert config["unique_id"] == device_id
        assert config["device_code"] == 1000
        # Critical: controller_data should be entity ID, not IP
        assert config["controller_data"] == "remote.broadlink_rm4_pro"
        assert config["temperature_sensor"] == "sensor.living_room_temp"
        assert config["humidity_sensor"] == "sensor.living_room_humidity"
    
    def test_climate_device_with_non_broadlink_entity(self, generator, temp_config_dir):
        """Test generating climate device config with non-Broadlink entity (Xiaomi, Harmony, etc.)"""
        device_id = "bedroom_ac"
        device_data = {
            "name": "Bedroom AC",
            "entity_type": "climate",
            "device_code": "1080",
            "controller_device": "remote.xiaomi_ir_remote",  # Non-Broadlink remote
            "temperature_sensor": "sensor.bedroom_temp"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        config = result["config"]
        # Should work with any remote entity, not just Broadlink
        assert config["controller_data"] == "remote.xiaomi_ir_remote"
    
    def test_media_player_with_harmony_hub(self, generator, temp_config_dir):
        """Test generating media player config with Harmony Hub"""
        device_id = "media_room_tv"
        device_data = {
            "name": "Media Room TV",
            "entity_type": "media_player",
            "device_code": "1500",
            "controller_device": "remote.harmony_hub",  # Harmony Hub
            "power_sensor": "binary_sensor.tv_power"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        config = result["config"]
        assert config["controller_data"] == "remote.harmony_hub"
        assert config["power_sensor"] == "binary_sensor.tv_power"
    
    def test_fan_device_minimal_config(self, generator, temp_config_dir):
        """Test generating fan device with minimal config"""
        device_id = "living_room_fan"
        device_data = {
            "name": "Living Room Fan",
            "entity_type": "fan",
            "device_code": "2000",
            "controller_device": "remote.broadlink_rm_mini"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        config = result["config"]
        assert config["controller_data"] == "remote.broadlink_rm_mini"
        # Fan doesn't require additional sensors
        assert "power_sensor" not in config
    
    def test_missing_controller_device(self, generator, temp_config_dir):
        """Test error handling when controller_device is missing"""
        device_id = "test_device"
        device_data = {
            "name": "Test Device",
            "entity_type": "climate",
            "device_code": "1000"
            # Missing controller_device
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is False
        assert "No controller_device specified" in result["error"]
    
    def test_unsupported_entity_type(self, generator, temp_config_dir):
        """Test error handling for unsupported entity types"""
        device_id = "test_device"
        device_data = {
            "name": "Test Device",
            "entity_type": "switch",  # Not supported by SmartIR
            "device_code": "1000",
            "controller_device": "remote.test"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is False
        assert "Unsupported entity type" in result["error"]
    
    def test_yaml_file_generation(self, generator, temp_config_dir):
        """Test that YAML file is created correctly"""
        device_id = "test_ac"
        device_data = {
            "name": "Test AC",
            "entity_type": "climate",
            "device_code": "1000",
            "controller_device": "remote.test_remote"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        
        # Check file was created
        yaml_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        assert yaml_file.exists()
        
        # Read and verify YAML content
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        assert isinstance(yaml_content, list)
        assert len(yaml_content) == 1
        assert yaml_content[0]["controller_data"] == "remote.test_remote"
    
    def test_multiple_devices_in_same_file(self, generator, temp_config_dir):
        """Test adding multiple devices to the same platform file"""
        # Add first device
        result1 = generator.generate_device_config(
            "ac1",
            {
                "name": "AC 1",
                "entity_type": "climate",
                "device_code": "1000",
                "controller_device": "remote.broadlink_1"
            }
        )
        assert result1["success"] is True
        
        # Add second device
        result2 = generator.generate_device_config(
            "ac2",
            {
                "name": "AC 2",
                "entity_type": "climate",
                "device_code": "1080",
                "controller_device": "remote.xiaomi_1"
            }
        )
        assert result2["success"] is True
        
        # Verify both devices are in the file
        yaml_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        assert len(yaml_content) == 2
        assert yaml_content[0]["unique_id"] == "ac1"
        assert yaml_content[0]["controller_data"] == "remote.broadlink_1"
        assert yaml_content[1]["unique_id"] == "ac2"
        assert yaml_content[1]["controller_data"] == "remote.xiaomi_1"
    
    def test_update_existing_device(self, generator, temp_config_dir):
        """Test updating an existing device in the YAML file"""
        device_id = "test_ac"
        
        # Create initial device
        result1 = generator.generate_device_config(
            device_id,
            {
                "name": "Test AC",
                "entity_type": "climate",
                "device_code": "1000",
                "controller_device": "remote.old_remote"
            }
        )
        assert result1["success"] is True
        
        # Update with new controller
        result2 = generator.generate_device_config(
            device_id,
            {
                "name": "Test AC Updated",
                "entity_type": "climate",
                "device_code": "1080",
                "controller_device": "remote.new_remote"
            }
        )
        assert result2["success"] is True
        
        # Verify only one device exists with updated data
        yaml_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        assert len(yaml_content) == 1
        assert yaml_content[0]["name"] == "Test AC Updated"
        assert yaml_content[0]["controller_data"] == "remote.new_remote"
        assert yaml_content[0]["device_code"] == 1080


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
