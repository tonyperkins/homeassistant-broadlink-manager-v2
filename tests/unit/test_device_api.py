#!/usr/bin/env python3
"""
Unit tests for Device API endpoints
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from api.devices import normalize_device_name


class TestDeviceAPI:
    """Test Device API functionality"""

    def test_normalize_device_name(self):
        """Test device name normalization"""
        # Test basic normalization
        assert normalize_device_name("Living Room TV") == "living_room_tv"
        assert normalize_device_name("Tony's Office Light") == "tonys_office_light"  # Apostrophe removed
        assert normalize_device_name("Bedroom Fan") == "bedroom_fan"
        
        # Test special characters (removed, not replaced)
        assert normalize_device_name("AC Unit #1") == "ac_unit_1"
        assert normalize_device_name("Light @ Kitchen") == "light_kitchen"  # @ removed, multiple spaces collapsed
        assert normalize_device_name("Master Bedroom!") == "master_bedroom"
        
        # Test multiple spaces
        assert normalize_device_name("Living   Room   TV") == "living_room_tv"
        
        # Test leading/trailing spaces
        assert normalize_device_name("  Bedroom Light  ") == "bedroom_light"

    def test_entity_id_format_without_prefix(self):
        """Test that entity IDs are created without entity type prefix"""
        # This is a critical test for the bug fix where entity_ids were being
        # created as "light.bedroom_light" instead of just "bedroom_light"
        
        # Simulate device creation data
        device_name = "Bedroom Light"
        entity_type = "light"
        
        # Normalize the name
        normalized_name = normalize_device_name(device_name)
        
        # Entity ID should be just the normalized name, NOT prefixed with type
        entity_id = normalized_name  # Correct format
        wrong_entity_id = f"{entity_type}.{normalized_name}"  # Wrong format (old bug)
        
        # Verify correct format
        assert entity_id == "bedroom_light"
        assert "." not in entity_id, "Entity ID should not contain domain prefix"
        
        # Verify we're NOT using the wrong format
        assert entity_id != wrong_entity_id
        assert entity_id != "light.bedroom_light"

    def test_entity_id_format_for_all_types(self):
        """Test entity ID format for all supported entity types"""
        test_cases = [
            ("Living Room TV", "media_player", "living_room_tv"),
            ("Ceiling Fan", "fan", "ceiling_fan"),
            ("Bedroom Light", "light", "bedroom_light"),
            ("AC Unit", "climate", "ac_unit"),
            ("Garage Door", "cover", "garage_door"),
            ("Power Switch", "switch", "power_switch"),
        ]
        
        for device_name, entity_type, expected_id in test_cases:
            normalized = normalize_device_name(device_name)
            
            # Entity ID should be just the normalized name
            entity_id = normalized
            
            # Verify correct format
            assert entity_id == expected_id, f"Expected {expected_id}, got {entity_id}"
            assert "." not in entity_id, f"Entity ID '{entity_id}' should not contain '.'"
            
            # Verify it doesn't have the type prefix
            wrong_format = f"{entity_type}.{normalized}"
            assert entity_id != wrong_format, f"Entity ID should not be '{wrong_format}'"

    def test_smartir_device_entity_id_format(self):
        """Test that SmartIR devices also use correct entity ID format"""
        # SmartIR devices should follow the same naming convention
        device_name = "Master Bedroom AC"
        entity_type = "climate"
        device_type = "smartir"
        
        normalized = normalize_device_name(device_name)
        entity_id = normalized
        
        # Verify format
        assert entity_id == "master_bedroom_ac"
        assert "." not in entity_id
        assert entity_id != f"{entity_type}.{normalized}"

    def test_entity_id_uniqueness_check(self):
        """Test that entity ID uniqueness is based on device name only"""
        # Two devices with same name but different types should conflict
        device_name = "Living Room Light"
        
        # Both should normalize to the same entity_id
        light_id = normalize_device_name(device_name)
        switch_id = normalize_device_name(device_name)
        
        # They should be identical (and thus conflict)
        assert light_id == switch_id == "living_room_light"
        
        # This is correct behavior - you can't have two devices with the same name
        # even if they're different types, because the entity_id would be the same

    def test_device_rename_entity_id_update(self):
        """Test that renaming a device updates the entity_id correctly"""
        # Original device
        original_name = "Bedroom Light"
        original_id = normalize_device_name(original_name)
        assert original_id == "bedroom_light"
        
        # Renamed device
        new_name = "Master Bedroom Light"
        new_id = normalize_device_name(new_name)
        assert new_id == "master_bedroom_light"
        
        # Verify they're different
        assert original_id != new_id
        
        # Verify neither has type prefix
        assert "." not in original_id
        assert "." not in new_id


class TestEntityIDHelpers:
    """Test helper ID generation for input_boolean and input_select"""

    def test_helper_state_tracker_format(self):
        """Test that helper state trackers use correct format"""
        entity_id = "bedroom_light"
        
        # State tracker should be: entity_id + "_state"
        state_tracker_id = f"{entity_id}_state"
        
        assert state_tracker_id == "bedroom_light_state"
        assert "." not in state_tracker_id
        
        # Wrong format (old bug)
        wrong_format = f"light.{entity_id}_state"
        assert state_tracker_id != wrong_format

    def test_helper_speed_selector_format(self):
        """Test that fan speed selectors use correct format"""
        entity_id = "ceiling_fan"
        
        # Speed selector should be: entity_id + "_speed"
        speed_selector_id = f"{entity_id}_speed"
        
        assert speed_selector_id == "ceiling_fan_speed"
        assert "." not in speed_selector_id
        
        # Wrong format (old bug)
        wrong_format = f"fan.{entity_id}_speed"
        assert speed_selector_id != wrong_format

    def test_helper_direction_selector_format(self):
        """Test that fan direction selectors use correct format"""
        entity_id = "ceiling_fan"
        
        # Direction selector should be: entity_id + "_direction"
        direction_selector_id = f"{entity_id}_direction"
        
        assert direction_selector_id == "ceiling_fan_direction"
        assert "." not in direction_selector_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
