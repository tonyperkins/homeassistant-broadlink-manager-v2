#!/usr/bin/env python3
"""
Unit tests for color temperature variant detection and generation.
Tests the new feature that creates master + variant light entities for CCT lights.
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.entity_generator import EntityGenerator, sanitize_slug


class TestColorTempVariantDetection:
    """Test color temperature variant pattern detection"""

    @pytest.fixture
    def generator(self):
        """Create EntityGenerator instance with mock storage"""
        mock_storage = Mock()
        mock_storage.package_file = "/config/broadlink_manager/entities.yaml"
        mock_storage.helpers_file = "/config/broadlink_manager/helpers.yaml"
        return EntityGenerator(mock_storage, "remote.broadlink_device")

    def test_detect_variants_with_warm_cold_midtone(self, generator):
        """Test detection with warm, cold, mid_tone commands"""
        commands = {
            "warm": "warm_cmd",
            "cold": "cold_cmd",
            "mid_tone": "mid_cmd",
            "turn_off": "off_cmd",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result is not None
        assert "variants" in result
        assert "default" in result
        assert set(result["variants"]) == {"warm", "cold", "mid_tone"}
        assert result["default"] == "mid_tone"

    def test_detect_variants_with_daylight_soft_cool(self, generator):
        """Test detection with different color temp names"""
        commands = {
            "daylight": "day_cmd",
            "soft": "soft_cmd",
            "cool": "cool_cmd",
            "turn_off": "off_cmd",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result is not None
        assert set(result["variants"]) == {"daylight", "soft", "cool"}
        # Should pick first alphabetically when no preferred name
        assert result["default"] in result["variants"]

    def test_no_detection_without_turn_off(self, generator):
        """Test that variants are not detected without turn_off command"""
        commands = {
            "warm": "warm_cmd",
            "cold": "cold_cmd",
            "mid_tone": "mid_cmd",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result is None

    def test_no_detection_with_only_one_variant(self, generator):
        """Test that variants are not detected with only 1 color temp command"""
        commands = {
            "warm": "warm_cmd",
            "turn_off": "off_cmd",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result is None

    def test_no_detection_with_standard_light(self, generator):
        """Test that standard light commands don't trigger variant detection"""
        commands = {
            "turn_on": "on_cmd",
            "turn_off": "off_cmd",
            "brightness_up": "bright_up",
            "brightness_down": "bright_down",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result is None

    def test_variants_excluded_from_standard_commands(self, generator):
        """Test that variant commands are properly identified and excluded"""
        commands = {
            "warm": "warm_cmd",
            "cold": "cold_cmd",
            "mid_tone": "mid_cmd",
            "turn_on": "on_cmd",
            "turn_off": "off_cmd",
            "brightness_up": "bright_up",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result is not None
        # turn_on, turn_off, brightness_up should NOT be in variants
        assert "turn_on" not in result["variants"]
        assert "turn_off" not in result["variants"]
        assert "brightness_up" not in result["variants"]
        # Only color temp commands should be variants
        assert set(result["variants"]) == {"warm", "cold", "mid_tone"}

    def test_default_variant_selection_prefers_midtone(self, generator):
        """Test that mid_tone is preferred as default variant"""
        commands = {
            "warm": "warm_cmd",
            "cold": "cold_cmd",
            "mid_tone": "mid_cmd",
            "daylight": "day_cmd",
            "turn_off": "off_cmd",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result["default"] == "mid_tone"

    def test_default_variant_selection_prefers_neutral(self, generator):
        """Test that neutral is preferred when mid_tone not available"""
        commands = {
            "warm": "warm_cmd",
            "cold": "cold_cmd",
            "neutral": "neutral_cmd",
            "daylight": "day_cmd",
            "turn_off": "off_cmd",
        }

        result = generator._detect_color_temp_variants(commands)

        assert result["default"] == "neutral"


class TestColorTempVariantGeneration:
    """Test generation of master + variant light entities"""

    @pytest.fixture
    def generator(self):
        """Create EntityGenerator instance with mock storage"""
        mock_storage = Mock()
        mock_storage.package_file = "/config/broadlink_manager/entities.yaml"
        mock_storage.helpers_file = "/config/broadlink_manager/helpers.yaml"
        return EntityGenerator(mock_storage, "remote.broadlink_device")

    @pytest.fixture
    def entity_data(self):
        """Sample entity data for testing"""
        return {
            "device": "bedroom_light",
            "name": "Bedroom Light",
            "entity_type": "light",
            "commands": {
                "warm": "warm",
                "cold": "cold",
                "mid_tone": "mid_tone",
                "turn_off": "turn_off",
            },
        }

    @pytest.fixture
    def broadlink_commands(self):
        """Sample Broadlink command data"""
        return {
            "bedroom_light": {
                "warm": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FDoUOhQSFBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FAANBQ==",
                "cold": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FDoUOhQSFBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FAANBR==",
                "mid_tone": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FDoUOhQSFBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FAANBS==",
                "turn_off": "JgBQAAABKZIUEhQSFBIUEhQ6FBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FDoUOhQSFBIUEhQSFBIUEhQSFBIUEhQSFDoUOhQ6FAANBQ==",
            }
        }

    def test_generate_master_and_variant_lights(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that master + variant lights are generated correctly"""
        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        # Should generate 4 lights: 1 master + 3 variants
        assert len(light_configs) == 4

        # Check master light
        master = light_configs[0]
        assert master["unique_id"] == "bedroom_light"
        assert master["name"] == "Bedroom Light"
        assert "input_boolean.bedroom_light_state" in master["state"]

        # Check variant lights
        variant_ids = [config["unique_id"] for config in light_configs[1:]]
        assert "bedroom_light_warm" in variant_ids
        assert "bedroom_light_cold" in variant_ids
        assert "bedroom_light_mid_tone" in variant_ids

    def test_all_lights_share_same_state_helper(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that all lights share the same state helper"""
        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        # All lights should reference the same state helper
        for config in light_configs:
            assert "input_boolean.bedroom_light_state" in config["state"]

    def test_all_lights_share_same_turn_off_command(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that all lights use the same turn_off command"""
        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        turn_off_cmd = broadlink_commands["bedroom_light"]["turn_off"]

        # All lights should use the same turn_off command
        for config in light_configs:
            assert config["turn_off"][0]["data"]["command"] == f"b64:{turn_off_cmd}"

    def test_master_uses_default_variant_for_turn_on(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that master light uses default variant command for turn_on"""
        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        master = light_configs[0]
        mid_tone_cmd = broadlink_commands["bedroom_light"]["mid_tone"]

        assert master["turn_on"][0]["data"]["command"] == f"b64:{mid_tone_cmd}"

    def test_variants_use_specific_commands_for_turn_on(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that variant lights use their specific commands for turn_on"""
        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        # Find warm variant
        warm_light = next(
            (c for c in light_configs if c["unique_id"] == "bedroom_light_warm"), None
        )
        assert warm_light is not None

        warm_cmd = broadlink_commands["bedroom_light"]["warm"]
        assert warm_light["turn_on"][0]["data"]["command"] == f"b64:{warm_cmd}"

    def test_variant_naming_convention(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that variant lights follow proper naming convention"""
        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        # Check variant names
        warm_light = next(
            (c for c in light_configs if c["unique_id"] == "bedroom_light_warm"), None
        )
        assert warm_light["name"] == "Bedroom Light Warm"

        cold_light = next(
            (c for c in light_configs if c["unique_id"] == "bedroom_light_cold"), None
        )
        assert cold_light["name"] == "Bedroom Light Cold"

        mid_light = next(
            (c for c in light_configs if c["unique_id"] == "bedroom_light_mid_tone"),
            None,
        )
        assert mid_light["name"] == "Bedroom Light Mid Tone"

    def test_missing_turn_off_returns_empty_list(
        self, generator, entity_data, broadlink_commands
    ):
        """Test that missing turn_off command returns empty list"""
        entity_data["commands"] = {
            "warm": "warm",
            "cold": "cold",
            "mid_tone": "mid_tone",
        }

        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator._generate_light_with_variants(
            "bedroom_light", entity_data, broadlink_commands, variant_info
        )

        assert light_configs == []

    def test_missing_broadlink_entity_returns_empty_list(self, generator):
        """Test that missing broadlink entity returns empty list"""
        # Create generator without default device ID
        generator_no_device = EntityGenerator(Mock(), None)

        entity_data = {
            "device": "bedroom_light",
            "name": "Bedroom Light",
            "entity_type": "light",
            "commands": {
                "warm": "warm",
                "cold": "cold",
                "mid_tone": "mid_tone",
                "turn_off": "turn_off",
            },
        }

        variant_info = {
            "variants": ["warm", "cold", "mid_tone"],
            "default": "mid_tone",
        }

        light_configs = generator_no_device._generate_light_with_variants(
            "bedroom_light", entity_data, {}, variant_info
        )

        assert light_configs == []


class TestSanitizeSlug:
    """Test the sanitize_slug helper function"""

    def test_sanitize_basic_name(self):
        """Test sanitizing a basic name"""
        assert sanitize_slug("bedroom_light") == "bedroom_light"

    def test_sanitize_with_spaces(self):
        """Test sanitizing name with spaces"""
        assert sanitize_slug("Bedroom Light") == "bedroom_light"

    def test_sanitize_with_special_chars(self):
        """Test sanitizing name with special characters"""
        assert sanitize_slug("Bedroom-Light!@#") == "bedroom_light"

    def test_sanitize_consecutive_underscores(self):
        """Test that consecutive underscores are collapsed"""
        assert sanitize_slug("bedroom___light") == "bedroom_light"

    def test_sanitize_leading_trailing_underscores(self):
        """Test that leading/trailing underscores are removed"""
        assert sanitize_slug("_bedroom_light_") == "bedroom_light"
