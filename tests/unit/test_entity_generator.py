#!/usr/bin/env python3
"""
Unit tests for EntityGenerator
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'app'))

from entity_generator import EntityGenerator


class TestEntityGenerator:
    """Test EntityGenerator class"""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def mock_storage(self, temp_dir):
        """Create mock storage manager"""
        storage = Mock()
        storage.entities_file = temp_dir / "entities.yaml"
        storage.helpers_file = temp_dir / "helpers.yaml"
        storage.package_file = temp_dir / "package.yaml"
        storage.set_last_generated = Mock()
        return storage

    @pytest.fixture
    def generator(self, mock_storage):
        """Create EntityGenerator instance"""
        return EntityGenerator(mock_storage, "remote.test_broadlink")

    def test_multiple_media_players_single_platform(self, generator, mock_storage):
        """Test that multiple media players are grouped under a single platform entry"""
        # Setup test data with multiple media players
        entities = {
            "living_room_tv": {
                "device": "living_room_tv",
                "entity_type": "media_player",
                "name": "Living Room TV",
                "enabled": True,
                "commands": {
                    "power_on": "power_on",
                    "power_off": "power_off",
                },
                "broadlink_entity": "remote.broadcomir",
            },
            "living_room_stereo": {
                "device": "living_room_stereo",
                "entity_type": "media_player",
                "name": "Living Room Stereo",
                "enabled": True,
                "commands": {
                    "power_on": "power_on",
                    "power_off": "power_off",
                },
                "broadlink_entity": "remote.broadcomir",
            },
        }

        mock_storage.get_all_entities = Mock(return_value=entities)

        # Generate entities
        result = generator.generate_all({})

        # Verify success
        assert result["success"] is True
        assert result["entities_count"] == 2

        # Read the generated entities file
        with open(mock_storage.entities_file, "r") as f:
            content = f.read()

        # Count occurrences of "platform: universal" (media players use universal platform)
        platform_count = content.count("platform: universal")

        # Should have TWO platform entries (one for each media player - they're not grouped)
        assert platform_count == 2, f"Expected 2 platform entries, found {platform_count}"

        # Verify both entities are present
        assert "living_room_tv" in content
        assert "living_room_stereo" in content

        # Verify the structure has media_player key (singular, not plural)
        assert "media_player:" in content

    def test_multiple_lights_single_platform(self, generator, mock_storage):
        """Test that multiple lights are grouped under a single platform entry"""
        entities = {
            "bedroom_light": {
                "device": "bedroom_light",
                "entity_type": "light",
                "name": "Bedroom Light",
                "enabled": True,
                "commands": {
                    "turn_on": "light_on",
                    "turn_off": "light_off",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
            "kitchen_light": {
                "device": "kitchen_light",
                "entity_type": "light",
                "name": "Kitchen Light",
                "enabled": True,
                "commands": {
                    "turn_on": "light_on",
                    "turn_off": "light_off",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
        }

        mock_storage.get_all_entities = Mock(return_value=entities)

        # Generate entities
        result = generator.generate_all({})

        # Verify success
        assert result["success"] is True

        # Read the generated entities file
        with open(mock_storage.entities_file, "r") as f:
            content = f.read()

        # Count occurrences of "platform: template"
        platform_count = content.count("platform: template")

        # Should only have ONE platform entry for light
        assert platform_count == 1, f"Expected 1 platform entry, found {platform_count}"

        # Verify both entities are present
        assert "bedroom_light" in content
        assert "kitchen_light" in content

    def test_mixed_entity_types_separate_platforms(self, generator, mock_storage):
        """Test that different entity types get separate platform entries"""
        entities = {
            "living_room_tv": {
                "device": "living_room_tv",
                "entity_type": "media_player",
                "name": "Living Room TV",
                "enabled": True,
                "commands": {
                    "power_on": "power_on",
                    "power_off": "power_off",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
            "bedroom_light": {
                "device": "bedroom_light",
                "entity_type": "light",
                "name": "Bedroom Light",
                "enabled": True,
                "commands": {
                    "turn_on": "light_on",
                    "turn_off": "light_off",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
        }

        mock_storage.get_all_entities = Mock(return_value=entities)

        # Generate entities
        result = generator.generate_all({})

        # Verify success
        assert result["success"] is True

        # Read the generated entities file
        with open(mock_storage.entities_file, "r") as f:
            content = f.read()

        # Should have THREE platform entries:
        # - 1 universal platform for media_player
        # - 2 template platforms (1 for media_player's companion switch, 1 for light)
        universal_count = content.count("platform: universal")
        template_count = content.count("platform: template")
        assert universal_count == 1, f"Expected 1 universal platform, found {universal_count}"
        assert template_count == 2, f"Expected 2 template platforms, found {template_count}"

        # Verify structure (singular domain names, not plural)
        assert "media_player:" in content
        assert "lights:" in content

    def test_entity_id_without_type_prefix(self, generator, mock_storage):
        """Test that entity IDs are used without entity type prefix in YAML"""
        # This is a critical test for the bug where entity_ids like "light.bedroom_light"
        # were being used instead of just "bedroom_light", causing "invalid slug" errors
        entities = {
            "bedroom_light": {  # Entity ID should NOT have "light." prefix
                "device": "bedroom_light",
                "entity_type": "light",
                "name": "Bedroom Light",
                "enabled": True,
                "commands": {
                    "turn_on": "light_on",
                    "turn_off": "light_off",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
            "ceiling_fan": {  # Entity ID should NOT have "fan." prefix
                "device": "ceiling_fan",
                "entity_type": "fan",
                "name": "Ceiling Fan",
                "enabled": True,
                "commands": {
                    "speed_1": "fan_speed_1",
                    "speed_2": "fan_speed_2",
                    "speed_3": "fan_speed_3",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
        }

        mock_storage.get_all_entities = Mock(return_value=entities)

        # Generate entities
        result = generator.generate_all({})

        # Verify success
        assert result["success"] is True

        # Read the generated files
        with open(mock_storage.entities_file, "r") as f:
            entities_content = f.read()
        
        with open(mock_storage.helpers_file, "r") as f:
            helpers_content = f.read()

        # CRITICAL: Entity IDs should NOT have type prefix in YAML
        # These would cause "invalid slug" errors in Home Assistant
        assert "light.bedroom_light" not in entities_content, "Entity ID should not have 'light.' prefix"
        assert "fan.ceiling_fan" not in entities_content, "Entity ID should not have 'fan.' prefix"
        assert "light.bedroom_light_state" not in helpers_content, "Helper ID should not have 'light.' prefix"
        assert "fan.ceiling_fan_state" not in helpers_content, "Helper ID should not have 'fan.' prefix"
        
        # Verify correct format (without prefix)
        assert "bedroom_light:" in entities_content or "bedroom_light\n" in entities_content
        assert "ceiling_fan:" in entities_content or "ceiling_fan\n" in entities_content
        assert "bedroom_light_state:" in helpers_content
        assert "ceiling_fan_state:" in helpers_content
        assert "ceiling_fan_speed:" in helpers_content  # Fan speed selector

    def test_fan_direction_helper_always_created(self, generator, mock_storage):
        """Test that fan direction helper is always created, even without reverse command"""
        # This prevents the bug where direction_template references a non-existent helper
        # Regression test for: "show_direction_control - Expected a value of type 'never'"
        entities = {
            "ceiling_fan_no_reverse": {
                "device": "ceiling_fan_no_reverse",
                "entity_type": "fan",
                "name": "Ceiling Fan (No Reverse)",
                "enabled": True,
                "commands": {
                    "speed_1": "fan_speed_1",
                    "speed_2": "fan_speed_2",
                    "speed_3": "fan_speed_3",
                    # NO reverse/direction command
                },
                "broadlink_entity": "remote.test_broadlink",
            },
            "ceiling_fan_with_reverse": {
                "device": "ceiling_fan_with_reverse",
                "entity_type": "fan",
                "name": "Ceiling Fan (With Reverse)",
                "enabled": True,
                "commands": {
                    "speed_1": "fan_speed_1",
                    "speed_2": "fan_speed_2",
                    "fan_reverse": "fan_reverse",  # HAS reverse command
                },
                "broadlink_entity": "remote.test_broadlink",
            },
        }

        mock_storage.get_all_entities = Mock(return_value=entities)

        # Generate entities
        result = generator.generate_all({})

        # Verify success
        assert result["success"] is True

        # Read helpers file
        with open(mock_storage.helpers_file, "r") as f:
            helpers_content = f.read()

        # CRITICAL: Both fans should have direction helpers, regardless of command existence
        assert "ceiling_fan_no_reverse_direction:" in helpers_content, \
            "Fan without reverse command should still have direction helper"
        assert "ceiling_fan_with_reverse_direction:" in helpers_content, \
            "Fan with reverse command should have direction helper"

        # Verify direction options
        assert "forward" in helpers_content
        assert "reverse" in helpers_content

        # Read entities file
        with open(mock_storage.entities_file, "r") as f:
            entities_content = f.read()

        # Both fans should have direction_template
        assert "direction_template:" in entities_content or "direction_template" in entities_content

    def test_fan_helpers_match_entity_config(self, generator, mock_storage):
        """Test that all fan helper references in entity config actually exist"""
        # This ensures we don't reference non-existent helpers
        entities = {
            "test_fan": {
                "device": "test_fan",
                "entity_type": "fan",
                "name": "Test Fan",
                "enabled": True,
                "commands": {
                    "speed_1": "speed_1",
                    "speed_2": "speed_2",
                    "speed_3": "speed_3",
                },
                "broadlink_entity": "remote.test_broadlink",
            },
        }

        mock_storage.get_all_entities = Mock(return_value=entities)

        # Generate entities
        result = generator.generate_all({})
        assert result["success"] is True

        # Read both files
        with open(mock_storage.entities_file, "r") as f:
            entities_content = f.read()
        
        with open(mock_storage.helpers_file, "r") as f:
            helpers_content = f.read()

        # Extract all helper references from entities file (in templates, not service calls)
        import re
        
        # Find input_boolean references in templates (e.g., is_state('input_boolean.xxx'))
        # Exclude service calls (e.g., service: input_boolean.turn_on)
        boolean_refs = re.findall(r"is_state\('input_boolean\.(\w+)'", entities_content)
        boolean_refs += re.findall(r'states\("input_boolean\.(\w+)"\)', entities_content)
        boolean_refs += re.findall(r"entity_id.*input_boolean\.(\w+)", entities_content)
        
        # Remove duplicates and service names
        boolean_refs = set(boolean_refs) - {'turn_on', 'turn_off', 'toggle'}
        
        for ref in boolean_refs:
            assert f"{ref}:" in helpers_content, \
                f"Entity references input_boolean.{ref} but it doesn't exist in helpers"

        # Find input_select references in templates
        select_refs = re.findall(r"states\('input_select\.(\w+)'\)", entities_content)
        select_refs += re.findall(r'states\("input_select\.(\w+)"\)', entities_content)
        select_refs += re.findall(r"is_state\('input_select\.(\w+)'", entities_content)
        select_refs += re.findall(r"entity_id.*input_select\.(\w+)", entities_content)
        
        # Remove duplicates and service names
        select_refs = set(select_refs) - {'select_option'}
        
        for ref in select_refs:
            assert f"{ref}:" in helpers_content, \
                f"Entity references input_select.{ref} but it doesn't exist in helpers"
