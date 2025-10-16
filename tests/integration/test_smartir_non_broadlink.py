#!/usr/bin/env python3
"""
Integration test for SmartIR with non-Broadlink controllers
Verifies that the system can work with any Home Assistant remote entity
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml
from app.smartir_yaml_generator import SmartIRYAMLGenerator


class TestSmartIRNonBroadlinkIntegration:
    """Test SmartIR integration with various remote types"""
    
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
    
    def test_scenario_user_has_xiaomi_remote_only(self, generator, temp_config_dir):
        """
        Scenario: User has a Xiaomi IR remote but no Broadlink device
        They want to use SmartIR climate profiles with their existing remote
        """
        device_id = "bedroom_ac"
        device_data = {
            "name": "Bedroom Air Conditioner",
            "entity_type": "climate",
            "device_code": "1080",  # SmartIR climate code
            "controller_device": "remote.xiaomi_ir_remote",  # Non-Broadlink
            "temperature_sensor": "sensor.bedroom_temperature",
            "humidity_sensor": "sensor.bedroom_humidity"
        }
        
        # Generate configuration
        result = generator.generate_device_config(device_id, device_data)
        
        # Should succeed without requiring Broadlink device
        assert result["success"] is True
        assert "SmartIR device configuration generated" in result["message"]
        
        # Verify YAML file
        yaml_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        assert yaml_file.exists()
        
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        # Verify the generated YAML is correct for SmartIR
        device_config = yaml_content[0]
        assert device_config["platform"] == "smartir"
        assert device_config["name"] == "Bedroom Air Conditioner"
        assert device_config["unique_id"] == "bedroom_ac"
        assert device_config["device_code"] == 1080
        # Critical: controller_data must be entity ID, not IP
        assert device_config["controller_data"] == "remote.xiaomi_ir_remote"
        assert device_config["temperature_sensor"] == "sensor.bedroom_temperature"
        assert device_config["humidity_sensor"] == "sensor.bedroom_humidity"
    
    def test_scenario_harmony_hub_for_media_player(self, generator, temp_config_dir):
        """
        Scenario: User has Harmony Hub and wants to control TV with SmartIR
        """
        device_id = "living_room_tv"
        device_data = {
            "name": "Living Room TV",
            "entity_type": "media_player",
            "device_code": "1500",
            "controller_device": "remote.harmony_hub",
            "power_sensor": "binary_sensor.tv_power"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        
        yaml_file = Path(temp_config_dir) / "smartir" / "media_player.yaml"
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        device_config = yaml_content[0]
        assert device_config["controller_data"] == "remote.harmony_hub"
        assert device_config["power_sensor"] == "binary_sensor.tv_power"
    
    def test_scenario_mixed_controllers(self, generator, temp_config_dir):
        """
        Scenario: User has multiple remote types and uses them for different devices
        - Broadlink for bedroom AC
        - Xiaomi for living room AC
        - Harmony Hub for TV
        """
        devices = [
            {
                "id": "bedroom_ac",
                "data": {
                    "name": "Bedroom AC",
                    "entity_type": "climate",
                    "device_code": "1080",
                    "controller_device": "remote.broadlink_rm4_pro"
                }
            },
            {
                "id": "living_room_ac",
                "data": {
                    "name": "Living Room AC",
                    "entity_type": "climate",
                    "device_code": "1000",
                    "controller_device": "remote.xiaomi_ir_remote"
                }
            },
            {
                "id": "media_room_tv",
                "data": {
                    "name": "Media Room TV",
                    "entity_type": "media_player",
                    "device_code": "1500",
                    "controller_device": "remote.harmony_hub"
                }
            }
        ]
        
        # Generate all devices
        for device in devices:
            result = generator.generate_device_config(device["id"], device["data"])
            assert result["success"] is True
        
        # Verify climate devices
        climate_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        with open(climate_file, 'r') as f:
            climate_content = yaml.safe_load(f)
        
        assert len(climate_content) == 2
        assert climate_content[0]["controller_data"] == "remote.broadlink_rm4_pro"
        assert climate_content[1]["controller_data"] == "remote.xiaomi_ir_remote"
        
        # Verify media player
        media_file = Path(temp_config_dir) / "smartir" / "media_player.yaml"
        with open(media_file, 'r') as f:
            media_content = yaml.safe_load(f)
        
        assert len(media_content) == 1
        assert media_content[0]["controller_data"] == "remote.harmony_hub"
    
    def test_scenario_generic_remote_entity(self, generator, temp_config_dir):
        """
        Scenario: User has a custom remote integration
        """
        device_id = "office_ac"
        device_data = {
            "name": "Office AC",
            "entity_type": "climate",
            "device_code": "1000",
            "controller_device": "remote.custom_ir_blaster"  # Generic remote entity
        }
        
        result = generator.generate_device_config(device_id, device_data)
        
        assert result["success"] is True
        
        yaml_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        # Should work with any remote entity that implements remote.send_command
        assert yaml_content[0]["controller_data"] == "remote.custom_ir_blaster"
    
    def test_generated_yaml_is_valid_smartir_format(self, generator, temp_config_dir):
        """
        Verify the generated YAML matches SmartIR's expected format
        """
        device_id = "test_ac"
        device_data = {
            "name": "Test AC",
            "entity_type": "climate",
            "device_code": "1000",
            "controller_device": "remote.any_remote",
            "temperature_sensor": "sensor.temp",
            "humidity_sensor": "sensor.humidity",
            "power_sensor": "binary_sensor.power"
        }
        
        result = generator.generate_device_config(device_id, device_data)
        assert result["success"] is True
        
        yaml_file = Path(temp_config_dir) / "smartir" / "climate.yaml"
        with open(yaml_file, 'r') as f:
            yaml_content = yaml.safe_load(f)
        
        config = yaml_content[0]
        
        # Verify all required SmartIR fields are present
        assert "platform" in config
        assert config["platform"] == "smartir"
        assert "name" in config
        assert "unique_id" in config
        assert "device_code" in config
        assert "controller_data" in config
        
        # Verify controller_data is a string (entity ID), not a dict or IP
        assert isinstance(config["controller_data"], str)
        assert config["controller_data"].startswith("remote.")
        
        # Verify optional sensors are included
        assert "temperature_sensor" in config
        assert "humidity_sensor" in config
        assert "power_sensor" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
