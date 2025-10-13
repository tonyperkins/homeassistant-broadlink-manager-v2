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

        # Count occurrences of "platform: template"
        platform_count = content.count("platform: template")

        # Should only have ONE platform entry for media_player
        assert platform_count == 1, f"Expected 1 platform entry, found {platform_count}"

        # Verify both entities are present
        assert "living_room_tv" in content
        assert "living_room_stereo" in content

        # Verify the structure has media_players key (not multiple entries)
        assert content.count("media_players:") == 1

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

        # Should have TWO platform entries (one for media_player, one for light)
        platform_count = content.count("platform: template")
        assert platform_count == 2, f"Expected 2 platform entries, found {platform_count}"

        # Verify structure
        assert "media_players:" in content
        assert "lights:" in content
