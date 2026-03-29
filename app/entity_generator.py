#!/usr/bin/env python3
"""
Entity Generator for Broadlink Manager Add-on
Generates Home Assistant YAML entity configurations
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


def sanitize_slug(name: str) -> str:
    """
    Sanitize a name to create a valid Home Assistant slug.
    Converts to lowercase, replaces spaces and invalid chars with underscores.

    Args:
        name: The name to sanitize

    Returns:
        A valid slug (lowercase, underscores only)
    """
    # Convert to lowercase
    slug = name.lower()
    # Replace spaces, hyphens, and other invalid chars with underscores
    slug = re.sub(r"[^a-z0-9_]", "_", slug)
    # Remove consecutive underscores
    slug = re.sub(r"_+", "_", slug)
    # Remove leading/trailing underscores
    slug = slug.strip("_")
    return slug


class EntityGenerator:
    """Generate Home Assistant entity YAML configurations"""

    def __init__(self, storage_manager, broadlink_device_id: str = None):
        """
        Initialize entity generator

        Args:
            storage_manager: StorageManager instance
            broadlink_device_id: Optional default HA device ID for the Broadlink device (for backward compatibility)
        """
        self.storage = storage_manager
        self.default_device_id = broadlink_device_id

    def _detect_color_temp_variants(
        self, commands: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """
        Detect color temperature variant commands with shared turn_off.

        Pattern: Multiple color temp commands (warm, cold, etc.) + shared turn_off
        Common in CCT LED lights with multiple color temperature presets.

        Args:
            commands: Dictionary of command names

        Returns:
            Dict with 'variants' (list of variant command names) and 'default' (default variant)
            Returns None if pattern not detected

        Example:
            Commands: {warm, cold, mid_tone, turn_off, turn_on}
            Returns: {'variants': ['warm', 'cold', 'mid_tone'], 'default': 'mid_tone'}
        """
        command_names = set(commands.keys())

        # Must have turn_off command
        if "turn_off" not in command_names:
            return None

        # Common color temperature variant names
        color_temp_patterns = {
            "warm",
            "warm_white",
            "warm_tone",
            "cold",
            "cool",
            "cool_white",
            "cold_white",
            "cool_tone",
            "mid",
            "mid_tone",
            "mid_white",
            "middle",
            "neutral",
            "natural",
            "daylight",
            "day",
            "bright",
            "soft",
            "soft_white",
        }

        # Find variant commands (color temp commands that exist)
        variants = []
        for cmd in command_names:
            # Skip standard control commands
            if cmd in {
                "turn_on",
                "turn_off",
                "toggle",
                "brightness_up",
                "brightness_down",
                "bright",
                "dim",
            }:
                continue
            # Check if it matches color temp patterns
            if cmd.lower() in color_temp_patterns:
                variants.append(cmd)

        # Need at least 2 variants to create variant entities
        # (If only 1, it's just the standard turn_on command)
        if len(variants) < 2:
            return None

        # Determine default variant (prefer mid_tone, neutral, or first alphabetically)
        default_variant = None
        for preferred in ["mid_tone", "mid", "neutral", "natural", "middle"]:
            if preferred in variants:
                default_variant = preferred
                break
        if not default_variant:
            default_variant = sorted(variants)[0]

        logger.info(
            f"Detected color temp variants: {variants} (default: {default_variant})"
        )

        return {"variants": variants, "default": default_variant}

    def _get_broadlink_entity(self, entity_data: Dict[str, Any]) -> Optional[str]:
        """
        Get the Broadlink entity ID from entity data.
        Checks both 'broadlink_entity' and 'device_id' fields for compatibility.

        Args:
            entity_data: Entity configuration dictionary

        Returns:
            Broadlink entity ID or None if not found
        """
        return (
            entity_data.get("broadlink_entity")
            or entity_data.get("device_id")
            or self.default_device_id
        )

    def generate_all(
        self, broadlink_commands: Dict[str, Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Generate all entity YAML files

        Args:
            broadlink_commands: Dict of {device_name: {command_name: command_code}}

        Returns:
            Dict with generation results
        """
        try:
            # Get all entities from metadata
            entities = self.storage.get_all_entities()

            if not entities:
                logger.warning("No entities configured for generation")
                return {
                    "success": False,
                    "message": "No entities configured. Please configure entities first.",
                    "entities_count": 0,
                }

            # Build YAML structures
            entities_yaml = self._build_entities_yaml(entities, broadlink_commands)
            helpers_yaml = self._build_helpers_yaml(entities)

            # Merge entities and helpers for packages compatibility
            package_yaml = {**entities_yaml, **helpers_yaml}

            # Write files
            self._write_yaml_file(self.storage.helpers_file, helpers_yaml)
            self._write_yaml_file(self.storage.package_file, package_yaml)

            # Update last generated timestamp
            timestamp = datetime.now().isoformat()
            self.storage.set_last_generated(timestamp)

            # Count entities by type
            entity_counts = {}
            for entity_data in entities.values():
                entity_type = entity_data.get("entity_type", "unknown")
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1

            logger.info(f"Generated entities: {entity_counts}")

            return {
                "success": True,
                "message": "Entity files generated successfully",
                "entities_count": len(entities),
                "entity_counts": entity_counts,
                "files": {
                    "package": str(self.storage.package_file),
                    "helpers": str(self.storage.helpers_file),
                },
                "timestamp": timestamp,
                "instructions": self._get_setup_instructions(),
                "validation_warnings": getattr(self, "validation_warnings", []),
            }

        except Exception as e:
            logger.error(f"Failed to generate entities: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "entities_count": 0,
            }

    def _build_entities_yaml(
        self,
        entities: Dict[str, Dict[str, Any]],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Dict[str, Any]:
        """
        Build the entities YAML structure using modern template syntax (HA 2021.4+).

        Modern syntax structure:
        template:
          - light:
              - unique_id: ...
                name: ...
          - fan:
              - unique_id: ...
                name: ...
        """
        yaml_structure = {}
        # Storage for template entities by type (lists of entity configs)
        template_entities = {
            "light": [],
            "fan": [],
            "switch": [],
            "cover": [],
            "button": [],
        }

        # Track validation warnings for devices with missing required commands
        self.validation_warnings = []

        for entity_id, entity_data in entities.items():
            if not entity_data.get("enabled", True):
                continue

            entity_type = entity_data["entity_type"]
            is_stateless = entity_data.get("stateless", False)

            # For stateless devices, generate buttons instead of stateful entities
            if is_stateless:
                button_configs = self._generate_stateless_buttons(
                    entity_id, entity_data, broadlink_commands
                )
                if button_configs:
                    template_entities["button"].extend(button_configs)
                continue

            if entity_type == "light":
                # Check for color temperature variants
                commands = entity_data.get("commands", {})
                variant_info = self._detect_color_temp_variants(commands)

                if variant_info:
                    # Generate master light + variant lights
                    light_configs = self._generate_light_with_variants(
                        entity_id, entity_data, broadlink_commands, variant_info
                    )
                    if light_configs:
                        template_entities["light"].extend(light_configs)
                    config = None  # Already added
                else:
                    # Standard light generation
                    config = self._generate_light(
                        entity_id, entity_data, broadlink_commands
                    )
            elif entity_type == "fan":
                config = self._generate_fan(entity_id, entity_data, broadlink_commands)
            elif entity_type == "switch":
                config = self._generate_switch(
                    entity_id, entity_data, broadlink_commands
                )
            elif entity_type == "media_player":
                config = self._generate_media_player(
                    entity_id, entity_data, broadlink_commands
                )
            elif entity_type == "climate":
                # Climate entities are not supported - template.climate platform removed from HA
                # Users should use SmartIR custom integration for AC control
                logger.warning(
                    f"Climate entity type not supported for {entity_id}. "
                    "Use SmartIR custom integration for AC control: "
                    "https://github.com/smartHomeHub/SmartIR"
                )
                continue
            elif entity_type == "cover":
                config = self._generate_cover(
                    entity_id, entity_data, broadlink_commands
                )
            else:
                logger.warning(f"Unknown entity type: {entity_type} for {entity_id}")
                continue

            if config:
                # Media players use universal platform (not template), so handle differently
                if entity_type == "media_player":
                    # Universal media players are separate entries (not grouped under template:)
                    if "media_player" not in yaml_structure:
                        yaml_structure["media_player"] = []
                    yaml_structure["media_player"].append(config)

                    # Also generate companion switch for power control
                    switch_config = self._generate_media_player_switch(
                        entity_id, entity_data, broadlink_commands
                    )
                    if switch_config:
                        # Add to template switches list
                        template_entities["switch"].append(switch_config)
                else:
                    # Template platforms: add entity config directly to list
                    # Generators now return entity configs directly (not wrapped)
                    if entity_type in template_entities:
                        template_entities[entity_type].append(config)

            # Generate button entities for custom commands
            custom_buttons = self._generate_custom_command_buttons(
                entity_id, entity_data, broadlink_commands
            )
            if custom_buttons:
                template_entities["button"].extend(custom_buttons)

        # Build the modern template: structure
        # Only include entity types that have entities
        template_list = []
        for entity_type, entity_configs in template_entities.items():
            if entity_configs:
                # Each type gets its own entry in the template list
                template_list.append({entity_type: entity_configs})

        if template_list:
            yaml_structure["template"] = template_list

        return yaml_structure

    def _generate_light_with_variants(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
        variant_info: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Generate master light entity + color temperature variant entities.
        All variants share the same state helper for synchronized state tracking.

        Args:
            entity_id: Base entity ID
            entity_data: Entity configuration
            broadlink_commands: Command data
            variant_info: Dict with 'variants' list and 'default' variant name

        Returns:
            List of light entity configurations (master + variants)
        """
        device = entity_data["device"]
        commands = entity_data["commands"]
        variants = variant_info["variants"]
        default_variant = variant_info["default"]

        # Sanitize entity_id for use in helper references
        sanitized_id = sanitize_slug(entity_id)

        # Get the Broadlink entity to use
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return []

        # Get turn_off command (shared by all variants)
        turn_off_cmd = broadlink_commands.get(device, {}).get(
            commands.get("turn_off", ""), ""
        )
        if not turn_off_cmd:
            logger.warning(f"Light {entity_id} missing turn_off command")
            return []

        light_configs = []

        # 1. Generate MASTER light entity (uses default variant for turn_on)
        default_cmd = broadlink_commands.get(device, {}).get(
            commands.get(default_variant, ""), ""
        )

        master_config = {
            "unique_id": entity_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", entity_id.replace("_", " ").title()),
            "state": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
            "turn_on": [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{default_cmd}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ],
            "turn_off": [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_off_cmd}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ],
        }

        # Add icon if specified
        if entity_data.get("icon"):
            master_config["icon_template"] = entity_data["icon"]

        light_configs.append(master_config)
        logger.info(f"Generated master light: {entity_id} (default: {default_variant})")

        # 2. Generate VARIANT light entities (one for each color temp)
        for variant in variants:
            variant_cmd = broadlink_commands.get(device, {}).get(
                commands.get(variant, ""), ""
            )
            if not variant_cmd:
                logger.warning(f"Skipping variant {variant}: no command data")
                continue

            # Create variant entity ID and name
            variant_entity_id = f"{entity_id}_{variant}"
            variant_name_base = entity_data.get("name") or entity_data.get(
                "friendly_name", entity_id.replace("_", " ").title()
            )
            variant_display_name = variant.replace("_", " ").title()
            variant_name = f"{variant_name_base} {variant_display_name}"

            variant_config = {
                "unique_id": variant_entity_id,
                "name": variant_name,
                # Share the same state helper as master light
                "state": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
                "turn_on": [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{variant_cmd}"},
                    },
                    {
                        "service": "input_boolean.turn_on",
                        "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                    },
                ],
                "turn_off": [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{turn_off_cmd}"},
                    },
                    {
                        "service": "input_boolean.turn_off",
                        "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                    },
                ],
            }

            light_configs.append(variant_config)
            logger.info(f"Generated variant light: {variant_entity_id}")

        return light_configs

    def _generate_light(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Generate template light configuration"""
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Sanitize entity_id for use in helper references
        sanitized_id = sanitize_slug(entity_id)

        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return None

        # Get configurable brightness steps (default 100 for backward compatibility)
        brightness_steps = entity_data.get("brightness_steps", 100)

        # Check if we have the required commands
        has_on_off = "turn_on" in commands and "turn_off" in commands
        has_toggle = "toggle" in commands
        has_brightness = any(
            k in commands for k in ["brightness_up", "brightness_down", "bright", "dim"]
        )
        has_color_temp = any(k in commands for k in ["cooler", "warmer"])

        if not (has_on_off or has_toggle):
            logger.warning(f"Light {entity_id} missing required commands")
            return None

        # Modern template syntax (HA 2021.4+) - return light config directly
        light_config = {
            "unique_id": entity_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", entity_id.replace("_", " ").title()),
            "state": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
        }

        # Add icon if specified
        if entity_data.get("icon"):
            light_config["icon_template"] = entity_data["icon"]

        # Add brightness support if brightness commands exist
        if has_brightness:
            # Convert helper's 0-N steps to HA's 0-255 brightness scale
            light_config["level"] = (
                f"{{{{ (states('input_number.{sanitized_id}_brightness') | int * 255 / {brightness_steps}) | int }}}}"
            )

        # Add color temperature support if color temp commands exist
        if has_color_temp:
            light_config["temperature"] = (
                f"{{{{ states('input_number.{sanitized_id}_color_temp') | int }}}}"
            )

        if has_on_off:
            # Separate on/off commands - use raw base64 data
            turn_on_cmd = broadlink_commands.get(device, {}).get(
                commands["turn_on"], ""
            )
            turn_off_cmd = broadlink_commands.get(device, {}).get(
                commands["turn_off"], ""
            )

            light_config["turn_on"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_on_cmd}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

            light_config["turn_off"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_off_cmd}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]
        else:
            # Toggle command - use raw base64 data
            toggle_cmd = broadlink_commands.get(device, {}).get(commands["toggle"], "")

            light_config["turn_on"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{toggle_cmd}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

            light_config["turn_off"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{toggle_cmd}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

        # Add brightness control if brightness commands exist
        if has_brightness:
            # Set brightness action
            brightness_actions = []

            # Determine which brightness command to use based on direction
            if "brightness_up" in commands and "brightness_down" in commands:
                brightness_up_cmd = broadlink_commands.get(device, {}).get(
                    commands["brightness_up"], ""
                )
                brightness_down_cmd = broadlink_commands.get(device, {}).get(
                    commands["brightness_down"], ""
                )

                brightness_actions.append(
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {
                            "command": (
                                "{% if brightness > states('input_number."
                                + sanitized_id
                                + "_brightness') | int %}\n"
                                f"  b64:{brightness_up_cmd}\n"
                                "{% else %}\n"
                                f"  b64:{brightness_down_cmd}\n"
                                "{% endif %}"
                            )
                        },
                    }
                )
            elif "bright" in commands and "dim" in commands:
                bright_cmd = broadlink_commands.get(device, {}).get(
                    commands["bright"], ""
                )
                dim_cmd = broadlink_commands.get(device, {}).get(commands["dim"], "")

                brightness_actions.append(
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {
                            "command": (
                                "{% if brightness > states('input_number."
                                + sanitized_id
                                + "_brightness') | int %}\n"
                                f"  b64:{bright_cmd}\n"
                                "{% else %}\n"
                                f"  b64:{dim_cmd}\n"
                                "{% endif %}"
                            )
                        },
                    }
                )

            # Update the brightness helper
            # Convert HA's 0-255 brightness to 0-N steps for the helper
            brightness_actions.append(
                {
                    "service": "input_number.set_value",
                    "target": {"entity_id": f"input_number.{sanitized_id}_brightness"},
                    "data": {
                        "value": f"{{{{ (brightness * {brightness_steps} / 255) | int }}}}"
                    },
                }
            )

            light_config["set_level"] = brightness_actions

        # Add color temperature control if color temp commands exist
        if has_color_temp:
            cooler_cmd = broadlink_commands.get(device, {}).get(
                commands.get("cooler", ""), ""
            )
            warmer_cmd = broadlink_commands.get(device, {}).get(
                commands.get("warmer", ""), ""
            )

            color_temp_actions = []

            if cooler_cmd and warmer_cmd:
                color_temp_actions.append(
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {
                            "command": (
                                "{% if temperature < states('input_number."
                                + sanitized_id
                                + "_color_temp') | int %}\n"
                                f"  b64:{cooler_cmd}\n"
                                "{% else %}\n"
                                f"  b64:{warmer_cmd}\n"
                                "{% endif %}"
                            )
                        },
                    }
                )

                # Update the color temp helper
                color_temp_actions.append(
                    {
                        "service": "input_number.set_value",
                        "target": {
                            "entity_id": f"input_number.{sanitized_id}_color_temp"
                        },
                        "data": {"value": "{{ temperature }}"},
                    }
                )

                light_config["set_temperature"] = color_temp_actions

        return light_config

    def _generate_fan(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Generate template fan configuration"""
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Sanitize entity_id for use in helper references
        sanitized_id = sanitize_slug(entity_id)

        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return None

        # Count speed commands - support both 'speed_N' and 'fan_speed_N' patterns
        # Also support named speeds like 'speed_low', 'speed_medium', 'speed_high'
        speed_commands = {}
        named_speed_map = {
            "off": 0,  # Some fans have speed_off
            "low": 1,
            "lowmedium": 2,  # Support RF fan custom speeds
            "medium": 3,
            "mediumhigh": 4,  # Support RF fan custom speeds
            "high": 5,
            "med": 3,  # Alias for medium
            "quiet": 1,  # Some fans use 'quiet' for lowest speed
            "auto": 3,  # Some fans have auto mode as medium speed
        }

        for k, v in commands.items():
            if k.startswith("speed_") or k.startswith("fan_speed_"):
                # Extract speed identifier from command name
                if k.startswith("fan_speed_"):
                    speed_id = k.replace("fan_speed_", "")
                else:
                    speed_id = k.replace("speed_", "")

                # Convert to numeric if it's a digit, or map named speeds
                if speed_id.isdigit():
                    speed_num = speed_id
                elif speed_id.lower() in named_speed_map:
                    speed_num = str(named_speed_map[speed_id.lower()])
                else:
                    # Unknown speed name, skip it
                    logger.debug(f"Skipping unknown speed command: {k}")
                    continue

                # Store with normalized key 'speed_N' (skip speed_0/off)
                if speed_num != "0":
                    speed_commands[f"speed_{speed_num}"] = v

        speed_count = len(speed_commands)

        if speed_count == 0:
            logger.warning(
                f"Fan {entity_id} has no speed commands (found commands: {list(commands.keys())})"
            )
            return None

        # Check if reverse/direction command exists (support fan_reverse too)
        has_direction = (
            "reverse" in commands
            or "direction" in commands
            or "fan_reverse" in commands
            or "fan_direction_forward" in commands
            or "fan_direction_reverse" in commands
        )

        # Modern template syntax (HA 2021.4+) - return fan config directly
        fan_config = {
            "unique_id": entity_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", entity_id.replace("_", " ").title()),
            "state": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
            "speed_count": speed_count,
        }

        # Note: icon_template is not supported for fan entities in HA
        # Icons must be set via entity customization in HA UI or entity registry

        # Percentage template
        percentage_conditions = []
        for i in range(1, speed_count + 1):
            percentage = int((i / speed_count) * 100)
            percentage_conditions.append(
                f"{{%- elif is_state('input_select.{sanitized_id}_speed', '{i}') -%}}"
            )
            percentage_conditions.append(f"  {percentage}")

        fan_config["percentage"] = (
            f"{{%- if is_state('input_select.{sanitized_id}_speed', 'off') -%}}\n"
            f"  0\n" + "\n".join(percentage_conditions) + f"\n{{%- endif -%}}"
        )

        # Turn on (default to medium speed) - use raw base64 data
        # Get sorted list of actual speed numbers and pick the middle one
        speed_numbers = sorted([int(k.split("_")[1]) for k in speed_commands.keys()])
        default_speed_idx = (len(speed_numbers) + 1) // 2  # Middle speed (1-indexed)
        default_speed_num = speed_numbers[default_speed_idx - 1]  # Convert to 0-indexed
        default_speed_cmd_name = speed_commands.get(
            f"speed_{default_speed_num}", list(speed_commands.values())[0]
        )
        default_speed_cmd = broadlink_commands.get(device, {}).get(
            default_speed_cmd_name, ""
        )

        fan_config["turn_on"] = [
            {
                "service": "remote.send_command",
                "target": {"entity_id": broadlink_entity},
                "data": {"command": f"b64:{default_speed_cmd}"},
            },
            {
                "service": "input_boolean.turn_on",
                "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
            },
            {
                "service": "input_select.select_option",
                "target": {"entity_id": f"input_select.{sanitized_id}_speed"},
                "data": {"option": str(default_speed_idx)},
            },
        ]

        # Turn off (required for fan entities) - use raw base64 data
        # Prefer fan_off, then turn_off, then fallback to lowest speed
        turn_off_command_name = commands.get("fan_off") or commands.get(
            "turn_off", speed_commands.get("speed_1", list(speed_commands.values())[0])
        )
        turn_off_cmd = broadlink_commands.get(device, {}).get(turn_off_command_name, "")

        fan_config["turn_off"] = [
            {
                "service": "remote.send_command",
                "target": {"entity_id": broadlink_entity},
                "data": {"command": f"b64:{turn_off_cmd}"},
            },
            {
                "service": "input_boolean.turn_off",
                "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
            },
            {
                "service": "input_select.select_option",
                "target": {"entity_id": f"input_select.{sanitized_id}_speed"},
                "data": {"option": "off"},
            },
        ]

        # Set percentage - use raw base64 commands
        set_percentage_option_conditions = []  # For input_select (speed numbers)
        set_percentage_command_conditions = []  # For remote commands (base64)

        # Get sorted list of actual speed numbers (e.g., [1, 3, 5] not [1, 2, 3])
        speed_numbers = sorted([int(k.split("_")[1]) for k in speed_commands.keys()])

        for idx, speed_num in enumerate(speed_numbers, start=1):
            percentage = int((idx / speed_count) * 100)

            # Template for input_select option (use sequential index)
            set_percentage_option_conditions.append(
                f"{{%- elif percentage <= {percentage} -%}}\n" f"  {idx}"
            )

            # Template for remote command (use actual speed number)
            speed_cmd_name = speed_commands.get(f"speed_{speed_num}", "")
            speed_cmd_data = broadlink_commands.get(device, {}).get(speed_cmd_name, "")
            set_percentage_command_conditions.append(
                f"{{%- elif percentage <= {percentage} -%}}\n" f"  b64:{speed_cmd_data}"
            )

        # Get turn off command base64
        turn_off_cmd_name = commands.get("fan_off") or commands.get("turn_off", "")
        turn_off_cmd_data = broadlink_commands.get(device, {}).get(
            turn_off_cmd_name, ""
        )

        fan_config["set_percentage"] = [
            {
                "service": "input_select.select_option",
                "target": {"entity_id": f"input_select.{sanitized_id}_speed"},
                "data": {
                    "option": (
                        "{% if percentage == 0 %}\n"
                        "  off\n"
                        + "\n".join(set_percentage_option_conditions)
                        + "\n{% endif %}"
                    )
                },
            },
            {
                "service": "remote.send_command",
                "target": {"entity_id": broadlink_entity},
                "data": {
                    "command": (
                        "{% if percentage == 0 %}\n"
                        f"  b64:{turn_off_cmd_data}\n"
                        + "\n".join(set_percentage_command_conditions)
                        + "\n{% endif %}"
                    ),
                },
            },
            {
                "choose": [
                    {
                        "conditions": "{{ percentage == 0 }}",
                        "sequence": [
                            {
                                "service": "input_boolean.turn_off",
                                "target": {
                                    "entity_id": f"input_boolean.{sanitized_id}_state"
                                },
                            }
                        ],
                    },
                    {
                        "conditions": "{{ percentage > 0 }}",
                        "sequence": [
                            {
                                "service": "input_boolean.turn_on",
                                "target": {
                                    "entity_id": f"input_boolean.{sanitized_id}_state"
                                },
                            }
                        ],
                    },
                ]
            },
        ]

        # Add direction support if reverse/direction command exists
        if has_direction:
            # Direction template
            fan_config["direction"] = (
                f"{{{{ states('input_select.{sanitized_id}_direction') }}}}"
            )

            # Set direction action - use raw base64 data
            direction_command_name = (
                commands.get("reverse")
                or commands.get("direction")
                or commands.get("fan_reverse")
            )

            # Build set_direction actions
            set_direction_actions = []

            # Only send remote command if direction command exists
            if direction_command_name:
                direction_cmd_data = broadlink_commands.get(device, {}).get(
                    direction_command_name, ""
                )
                set_direction_actions.append(
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{direction_cmd_data}"},
                    }
                )

            # Always update the input_select to track direction state
            set_direction_actions.append(
                {
                    "service": "input_select.select_option",
                    "target": {"entity_id": f"input_select.{sanitized_id}_direction"},
                    "data": {
                        "option": (
                            "{% if direction == 'forward' %}\n"
                            "  reverse\n"
                            "{% else %}\n"
                            "  forward\n"
                            "{% endif %}"
                        )
                    },
                }
            )

            fan_config["set_direction"] = set_direction_actions

        return fan_config

    def _generate_switch(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Generate template switch configuration"""
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Sanitize entity_id for use in helper references
        sanitized_id = sanitize_slug(entity_id)

        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return None

        # Check if we have the required commands
        has_on_off = "turn_on" in commands and "turn_off" in commands
        has_toggle = "toggle" in commands

        if not (has_on_off or has_toggle):
            logger.warning(f"Switch {entity_id} missing required commands")
            return None

        # Modern template syntax (HA 2021.4+) - return switch config directly
        switch_config = {
            "unique_id": entity_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", entity_id.replace("_", " ").title()),
            "state": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
        }

        # Add icon if specified
        if entity_data.get("icon"):
            switch_config["icon_template"] = entity_data["icon"]

        if has_on_off:
            # Separate on/off commands - use raw base64 data
            turn_on_cmd = broadlink_commands.get(device, {}).get(
                commands["turn_on"], ""
            )
            turn_off_cmd = broadlink_commands.get(device, {}).get(
                commands["turn_off"], ""
            )

            switch_config["turn_on"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_on_cmd}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

            switch_config["turn_off"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_off_cmd}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]
        else:
            # Toggle command - use raw base64 data
            toggle_cmd = broadlink_commands.get(device, {}).get(commands["toggle"], "")

            switch_config["turn_on"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{toggle_cmd}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

            switch_config["turn_off"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{toggle_cmd}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

        return switch_config

    def _generate_media_player(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """
        Generate universal media player configuration.

        Note: Home Assistant does not support template.media_player platform.
        Instead, we generate a universal media player that uses a companion switch
        for power control and direct remote commands for media functions.
        """
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return None

        # Check for basic power commands
        # Accept either separate on/off commands OR a toggle command
        has_separate_power = ("turn_on" in commands or "power_on" in commands) and (
            "turn_off" in commands or "power_off" in commands
        )
        has_toggle = "toggle" in commands or "power_toggle" in commands

        if not (has_separate_power or has_toggle):
            logger.warning(f"Media player {entity_id} missing power commands")
            # Add validation warning
            missing_commands = []
            if not has_toggle:
                if "turn_on" not in commands and "power_on" not in commands:
                    missing_commands.append("turn_on or power_on")
                if "turn_off" not in commands and "power_off" not in commands:
                    missing_commands.append("turn_off or power_off")
                missing_commands.append("OR toggle/power_toggle")

            self.validation_warnings.append(
                {
                    "device": entity_id,
                    "device_name": entity_data.get("friendly_name", entity_id),
                    "entity_type": "media_player",
                    "missing_commands": missing_commands,
                    "message": f"Media player requires power commands: {', '.join(missing_commands)}",
                }
            )
            return None

        # Build the universal media player configuration
        friendly_name = entity_data.get("name") or entity_data.get(
            "friendly_name", entity_id.replace("_", " ").title()
        )

        # The companion switch entity ID
        switch_entity_id = f"switch.{entity_id}_power"

        config = {
            "platform": "universal",
            "name": friendly_name,
            "unique_id": entity_id,
            "children": [switch_entity_id],
            "commands": {},
            "attributes": {
                "state": switch_entity_id,
            },
        }

        # Power commands (via companion switch)
        config["commands"]["turn_on"] = {
            "service": "switch.turn_on",
            "target": {"entity_id": switch_entity_id},
        }

        config["commands"]["turn_off"] = {
            "service": "switch.turn_off",
            "target": {"entity_id": switch_entity_id},
        }

        # Volume up command
        if "volume_up" in commands:
            volume_up_data = broadlink_commands.get(device, {}).get(
                commands["volume_up"], ""
            )
            if volume_up_data:
                config["commands"]["volume_up"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{volume_up_data}"},
                }

        # Volume down command
        if "volume_down" in commands:
            volume_down_data = broadlink_commands.get(device, {}).get(
                commands["volume_down"], ""
            )
            if volume_down_data:
                config["commands"]["volume_down"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{volume_down_data}"},
                }

        # Mute command
        if "mute" in commands or "volume_mute" in commands:
            mute_cmd = commands.get("mute") or commands.get("volume_mute")
            mute_data = broadlink_commands.get(device, {}).get(mute_cmd, "")
            if mute_data:
                config["commands"]["volume_mute"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{mute_data}"},
                }

        # Play command
        if "play" in commands:
            play_data = broadlink_commands.get(device, {}).get(commands["play"], "")
            if play_data:
                config["commands"]["media_play"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{play_data}"},
                }

        # Pause command
        if "pause" in commands:
            pause_data = broadlink_commands.get(device, {}).get(commands["pause"], "")
            if pause_data:
                config["commands"]["media_pause"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{pause_data}"},
                }

        # Play/Pause toggle command
        if "play_pause" in commands:
            play_pause_data = broadlink_commands.get(device, {}).get(
                commands["play_pause"], ""
            )
            if play_pause_data:
                config["commands"]["media_play_pause"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{play_pause_data}"},
                }

        # Stop command
        if "stop" in commands:
            stop_data = broadlink_commands.get(device, {}).get(commands["stop"], "")
            if stop_data:
                config["commands"]["media_stop"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{stop_data}"},
                }

        # Next track command
        if "next" in commands or "next_track" in commands:
            next_cmd = commands.get("next") or commands.get("next_track")
            next_data = broadlink_commands.get(device, {}).get(next_cmd, "")
            if next_data:
                config["commands"]["media_next_track"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{next_data}"},
                }

        # Previous track command
        if "previous" in commands or "previous_track" in commands:
            prev_cmd = commands.get("previous") or commands.get("previous_track")
            prev_data = broadlink_commands.get(device, {}).get(prev_cmd, "")
            if prev_data:
                config["commands"]["media_previous_track"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{prev_data}"},
                }

        # Source selection (if source commands exist)
        source_commands = {k: v for k, v in commands.items() if k.startswith("source_")}
        if source_commands:
            # Build a mapping of source names to base64 commands for template
            # We'll use a Jinja2 template to select the right command based on source
            source_map = {}
            for source_cmd_name, source_cmd_ref in source_commands.items():
                # Extract source name (e.g., "source_aux" -> "AUX")
                source_name = source_cmd_name.replace("source_", "").upper()
                source_data = broadlink_commands.get(device, {}).get(source_cmd_ref, "")
                if source_data:
                    source_map[source_name] = source_data

            if source_map:
                # Create a template that maps source names to base64 commands
                # Format: {% if source == 'AUX' %}b64:...{% elif source == 'TV' %}b64:...{% endif %}
                template_parts = []
                for idx, (source_name, source_data) in enumerate(source_map.items()):
                    if idx == 0:
                        template_parts.append(f"{{% if source == '{source_name}' %}}")
                    else:
                        template_parts.append(f"{{% elif source == '{source_name}' %}}")
                    template_parts.append(f"b64:{source_data}")
                template_parts.append("{% endif %}")

                command_template = "\n  ".join(template_parts)

                config["commands"]["select_source"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": command_template},
                }

                # Add source list to attributes via input_select
                config["attributes"]["source"] = f"input_select.{entity_id}_source"
                config["attributes"][
                    "source_list"
                ] = f"input_select.{entity_id}_source|options"

        logger.info(
            f"Generated universal media player configuration for {entity_id} with {len(commands)} commands"
        )
        return config

    def _generate_media_player_switch(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """
        Generate companion switch for media player power control.

        This switch is used by the universal media player for power on/off.
        """
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Sanitize entity_id for use in helper references
        sanitized_id = sanitize_slug(entity_id)

        # Get the Broadlink entity to use
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            return None

        # Get power commands - support both separate on/off and toggle
        turn_on_cmd = commands.get("turn_on") or commands.get("power_on")
        turn_off_cmd = commands.get("turn_off") or commands.get("power_off")
        toggle_cmd = commands.get("toggle") or commands.get("power_toggle")

        # Need either separate commands OR toggle
        if not ((turn_on_cmd and turn_off_cmd) or toggle_cmd):
            return None

        # Create switch entity ID (will be switch.{entity_id}_power)
        switch_entity_id = f"{entity_id}_power"

        friendly_name = entity_data.get("name") or entity_data.get(
            "friendly_name", entity_id.replace("_", " ").title()
        )

        # Modern template syntax (HA 2021.4+) - return switch config directly
        config = {
            "unique_id": switch_entity_id,
            "name": f"{friendly_name} Power",
            "state": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
        }

        # If we have separate on/off commands, use them
        if turn_on_cmd and turn_off_cmd:
            # Get the actual base64 command data
            turn_on_data = broadlink_commands.get(device, {}).get(turn_on_cmd, "")
            turn_off_data = broadlink_commands.get(device, {}).get(turn_off_cmd, "")

            if not turn_on_data or not turn_off_data:
                logger.warning(
                    f"Missing command data for {device}: turn_on={bool(turn_on_data)}, turn_off={bool(turn_off_data)}"
                )
                return None

            config["turn_on"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_on_data}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]
            config["turn_off"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{turn_off_data}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]
        # Otherwise use toggle command for both on and off
        elif toggle_cmd:
            # Get the actual base64 command data
            toggle_data = broadlink_commands.get(device, {}).get(toggle_cmd, "")

            if not toggle_data:
                logger.warning(
                    f"Missing command data for {device}: toggle={bool(toggle_data)}"
                )
                return None

            config["turn_on"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{toggle_data}"},
                },
                {
                    "service": "input_boolean.turn_on",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]
            config["turn_off"] = [
                {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{toggle_data}"},
                },
                {
                    "service": "input_boolean.turn_off",
                    "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                },
            ]

        logger.info(f"Generated companion switch for media player {entity_id}")
        return config

    def _generate_climate(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Generate template climate configuration for IR/RF AC units"""
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Sanitize entity_id for use in helper references
        sanitized_id = sanitize_slug(entity_id)

        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return None

        # Check for basic on/off commands
        has_on = "turn_on" in commands
        has_off = "turn_off" in commands

        if not (has_on or has_off):
            logger.warning(f"Climate {entity_id} missing turn_on or turn_off commands")
            return None

        # Build the climate configuration using template platform
        config = {
            "platform": "template",
            "climates": {
                entity_id: {
                    "unique_id": entity_id,
                    "friendly_name": entity_data.get("name")
                    or entity_data.get(
                        "friendly_name", entity_id.replace("_", " ").title()
                    ),
                    "value_template": f"{{{{ is_state('input_boolean.{sanitized_id}_state', 'on') }}}}",
                    "current_temperature_template": "{{ 22 }}",  # Static temperature since IR/RF has no feedback
                    "target_temperature_template": "{{ states('input_number.{}_target_temp'.format('"
                    + entity_id
                    + "')) | float }}",
                    "min_temp": 16,
                    "max_temp": 30,
                }
            },
        }

        climate_config = config["climates"][entity_id]

        # Add icon if specified
        if entity_data.get("icon"):
            climate_config["icon_template"] = entity_data["icon"]

        # Add turn_on action
        if has_on:
            turn_on_data = broadlink_commands.get(device, {}).get(
                commands["turn_on"], ""
            )
            if turn_on_data:
                climate_config["turn_on"] = [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{turn_on_data}"},
                    },
                    {
                        "service": "input_boolean.turn_on",
                        "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                    },
                ]

        # Add turn_off action
        if has_off:
            turn_off_data = broadlink_commands.get(device, {}).get(
                commands["turn_off"], ""
            )
            if turn_off_data:
                climate_config["turn_off"] = [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{turn_off_data}"},
                    },
                    {
                        "service": "input_boolean.turn_off",
                        "target": {"entity_id": f"input_boolean.{sanitized_id}_state"},
                    },
                ]

        # Add set_temperature action (uses turn_on for now)
        if has_on:
            turn_on_data = broadlink_commands.get(device, {}).get(
                commands["turn_on"], ""
            )
            if turn_on_data:
                climate_config["set_temperature"] = [
                    {
                        "service": "input_number.set_value",
                        "target": {
                            "entity_id": f"input_number.{entity_id}_target_temp"
                        },
                        "data": {"value": "{{ temperature }}"},
                    },
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{turn_on_data}"},
                    },
                ]

        logger.info(f"Generated template climate configuration for {entity_id}")

        return config

    def _generate_cover(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Generate template cover configuration"""
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return None

        # Check for required commands
        has_open = "open" in commands
        has_close = "close" in commands
        has_stop = "stop" in commands

        if not (has_open or has_close):
            logger.warning(f"Cover {entity_id} missing open or close commands")
            return None

        # Modern template syntax (HA 2021.4+) - return cover config directly
        cover_config = {
            "unique_id": entity_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", entity_id.replace("_", " ").title()),
            "state": f"{{{{ is_state('input_select.{entity_id}_position', 'open') }}}}",
        }

        # Add icon if specified
        if entity_data.get("icon"):
            cover_config["icon_template"] = entity_data["icon"]

        # Open cover command
        if has_open:
            open_data = broadlink_commands.get(device, {}).get(commands["open"], "")
            if open_data:
                cover_config["open_cover"] = [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{open_data}"},
                    },
                    {
                        "service": "input_select.select_option",
                        "target": {"entity_id": f"input_select.{entity_id}_position"},
                        "data": {"option": "open"},
                    },
                ]

        # Close cover command
        if has_close:
            close_data = broadlink_commands.get(device, {}).get(commands["close"], "")
            if close_data:
                cover_config["close_cover"] = [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{close_data}"},
                    },
                    {
                        "service": "input_select.select_option",
                        "target": {"entity_id": f"input_select.{entity_id}_position"},
                        "data": {"option": "closed"},
                    },
                ]

        # Stop cover command (optional but recommended)
        if has_stop:
            stop_data = broadlink_commands.get(device, {}).get(commands["stop"], "")
            if stop_data:
                cover_config["stop_cover"] = {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{stop_data}"},
                }

        # Check for position commands
        position_commands = {
            k: v for k, v in commands.items() if k.startswith("position_")
        }
        if position_commands:
            # Add position template (modern syntax uses 'position' not 'position_template')
            cover_config["position"] = (
                f"{{{{ states('input_number.{entity_id}_position') | int }}}}"
            )

            # Add set position action
            position_conditions = []
            for pos_key in sorted(position_commands.keys()):
                pos_value = int(pos_key.split("_")[1])
                position_conditions.append(
                    f"{{%- elif position == {pos_value} -%}}\n"
                    f"  {position_commands[pos_key]}"
                )

            cover_config["set_cover_position"] = {
                "service": "remote.send_command",
                "target": {"entity_id": broadlink_entity},
                "data": {
                    "device": device,
                    "command": (
                        "{% if position == 0 %}\n"
                        f"  {commands.get('close', '')}\n"
                        + "\n".join(position_conditions)
                        + "\n{% elif position == 100 %}\n"
                        f"  {commands.get('open', '')}\n"
                        "{% endif %}"
                    ),
                },
            }

        # Check for tilt commands
        has_open_tilt = "open_tilt" in commands
        has_close_tilt = "close_tilt" in commands

        if has_open_tilt or has_close_tilt:
            if has_open_tilt:
                open_tilt_data = broadlink_commands.get(device, {}).get(
                    commands["open_tilt"], ""
                )
                if open_tilt_data:
                    cover_config["open_cover_tilt"] = {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{open_tilt_data}"},
                    }

            if has_close_tilt:
                close_tilt_data = broadlink_commands.get(device, {}).get(
                    commands["close_tilt"], ""
                )
                if close_tilt_data:
                    cover_config["close_cover_tilt"] = {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{close_tilt_data}"},
                    }

        logger.info(
            f"Generated cover configuration for {entity_id} with {len(commands)} commands"
        )
        return cover_config

    def _generate_stateless_buttons(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """
        Generate button entities for stateless devices (no state tracking).
        This is useful for devices like IR blinds, RF garage doors, etc. that
        cannot report their state back to Home Assistant.

        Instead of creating a stateful entity (cover, light, etc.) with incorrect
        state tracking, we create simple buttons that are always available.
        """
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Get the Broadlink entity to use
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(
                f"No broadlink_entity specified for {entity_id} and no default device_id"
            )
            return []

        button_configs = []
        display_name = entity_data.get("name") or entity_data.get(
            "friendly_name", entity_id.replace("_", " ").title()
        )

        # Generate a button for each command
        for command_name, command_key in commands.items():
            # Get the IR/RF code for this command
            command_data = broadlink_commands.get(device, {}).get(command_key, "")
            if not command_data:
                logger.warning(f"No command data found for {entity_id}.{command_name}")
                continue

            # Create a unique button ID
            button_id = f"{entity_id}_{command_name}"

            # Format the command name for display
            button_name = f"{display_name} {command_name.replace('_', ' ').title()}"

            button_config = {
                "unique_id": button_id,
                "name": button_name,
                "press": {
                    "service": "remote.send_command",
                    "target": {"entity_id": broadlink_entity},
                    "data": {"command": f"b64:{command_data}"},
                },
            }

            # Add icon if specified (use same icon for all buttons)
            if entity_data.get("icon"):
                button_config["icon"] = entity_data["icon"]

            button_configs.append(button_config)

        logger.info(
            f"Generated {len(button_configs)} stateless buttons for {entity_id}"
        )
        return button_configs

    def _generate_custom_command_buttons(
        self,
        entity_id: str,
        entity_data: Dict[str, Any],
        broadlink_commands: Dict[str, Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """
        Generate button entities for custom commands that don't fit standard patterns.
        This allows users to trigger any learned command, even if it's not part of the
        main entity's standard controls (like custom light tones, special modes, etc.)
        """
        device = entity_data["device"]
        commands = entity_data["commands"]

        # Get the Broadlink entity to use
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            return []

        # Define standard command names that are already handled by main entities
        standard_commands = {
            # Light commands
            "turn_on",
            "turn_off",
            "toggle",
            "brightness_up",
            "brightness_down",
            "bright",
            "dim",
            "cooler",
            "warmer",
            # Fan commands
            "fan_on",
            "fan_off",
            "fan_toggle",
            "fan_reverse",
            # Switch commands
            "on",
            "off",
            # Cover commands
            "open",
            "close",
            "stop",
            "open_tilt",
            "close_tilt",
            # Media player commands
            "power",
            "volume_up",
            "volume_down",
            "mute",
            "play",
            "pause",
            "stop",
            "next",
            "previous",
            "source_hdmi1",
            "source_hdmi2",
            "source_hdmi3",
            "source_hdmi4",
            "source_tv",
            "source_av",
            "source_usb",
        }

        # Detect color temp variants to exclude them from buttons
        variant_info = self._detect_color_temp_variants(commands)
        variant_commands = set()
        if variant_info:
            variant_commands = set(variant_info["variants"])

        # Also exclude speed/position commands (handled by main entity)
        def is_standard_command(cmd_name):
            if cmd_name in standard_commands:
                return True
            if cmd_name in variant_commands:  # Exclude color temp variants
                return True
            if cmd_name.startswith("speed_") or cmd_name.startswith("fan_speed_"):
                return True
            if cmd_name.startswith("position_"):
                return True
            if cmd_name.startswith("source_"):
                return True
            return False

        # Find custom commands
        custom_commands = {
            k: v for k, v in commands.items() if not is_standard_command(k)
        }

        if not custom_commands:
            return []

        # Generate button entities for each custom command
        buttons = []

        for cmd_name, cmd_ref in custom_commands.items():
            # Get the actual command code
            cmd_code = broadlink_commands.get(device, {}).get(cmd_ref, "")
            if not cmd_code:
                logger.warning(f"No command code found for {device}.{cmd_name}")
                continue

            # Create a friendly name from the command name
            friendly_cmd_name = cmd_name.replace("_", " ").title()

            # Get the parent entity's display name
            parent_name = entity_data.get("name") or entity_data.get(
                "friendly_name", entity_id.replace("_", " ").title()
            )

            button_config = {
                "unique_id": f"{entity_id}_{cmd_name}_button",
                "name": f"{parent_name} {friendly_cmd_name}",
                "press": [
                    {
                        "service": "remote.send_command",
                        "target": {"entity_id": broadlink_entity},
                        "data": {"command": f"b64:{cmd_code}"},
                    }
                ],
            }

            buttons.append(button_config)
            logger.info(f"Generated button for custom command: {entity_id}.{cmd_name}")

        return buttons

    def _build_helpers_yaml(
        self, entities: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build helper entities (input_boolean, input_select)"""
        helpers = {"input_boolean": {}, "input_select": {}}

        for entity_id, entity_data in entities.items():
            if not entity_data.get("enabled", True):
                continue

            # Skip helpers for stateless devices (they use buttons, no state tracking)
            if entity_data.get("stateless", False):
                continue

            entity_type = entity_data["entity_type"]

            # Get display name (prefer 'name' over 'friendly_name')
            display_name = entity_data.get("name") or entity_data.get(
                "friendly_name", entity_id
            )

            # All entities need a state tracker
            # Sanitize entity_id to ensure valid slug
            sanitized_id = sanitize_slug(entity_id)
            helpers["input_boolean"][f"{sanitized_id}_state"] = {
                "name": f"{display_name} State",
                "initial": False,
            }

            # Lights need brightness and color temperature helpers
            if entity_type == "light":
                commands = entity_data.get("commands", {})

                # Get configurable brightness steps (default 100)
                brightness_steps = entity_data.get("brightness_steps", 100)

                # Add brightness helper if brightness commands exist
                has_brightness = any(
                    k in commands
                    for k in ["brightness_up", "brightness_down", "bright", "dim"]
                )
                if has_brightness:
                    if "input_number" not in helpers:
                        helpers["input_number"] = {}
                    helpers["input_number"][f"{sanitized_id}_brightness"] = {
                        "name": f"{display_name} Brightness",
                        "min": 0,
                        "max": brightness_steps,
                        "step": 1,
                        "initial": brightness_steps // 2,
                        "unit_of_measurement": (
                            "%" if brightness_steps == 100 else "steps"
                        ),
                    }

                # Add color temperature helper if color temp commands exist
                has_color_temp = any(k in commands for k in ["cooler", "warmer"])
                if has_color_temp:
                    if "input_number" not in helpers:
                        helpers["input_number"] = {}
                    helpers["input_number"][f"{sanitized_id}_color_temp"] = {
                        "name": f"{display_name} Color Temperature",
                        "min": 153,  # Warm white (6500K)
                        "max": 500,  # Cool white (2000K)
                        "step": 1,
                        "initial": 326,  # Mid-range (~3000K)
                        "unit_of_measurement": "mireds",
                    }

            # Fans need speed selector
            elif entity_type == "fan":
                # Count speed commands - support both 'speed_N' and 'fan_speed_N' patterns
                # Also support named speeds like 'speed_low', 'speed_medium', 'speed_high'
                # This must match the logic in _generate_fan()
                named_speed_map = {
                    "off": 0,
                    "low": 1,
                    "lowmedium": 2,
                    "medium": 3,
                    "mediumhigh": 4,
                    "high": 5,
                    "med": 3,
                    "quiet": 1,
                    "auto": 3,
                }

                speed_commands = {}
                for k in entity_data["commands"].keys():
                    if k.startswith("speed_") or k.startswith("fan_speed_"):
                        # Extract speed identifier from command name
                        if k.startswith("fan_speed_"):
                            speed_id = k.replace("fan_speed_", "")
                        else:
                            speed_id = k.replace("speed_", "")

                        # Convert to numeric if it's a digit, or map named speeds
                        if speed_id.isdigit():
                            speed_num = speed_id
                        elif speed_id.lower() in named_speed_map:
                            speed_num = str(named_speed_map[speed_id.lower()])
                        else:
                            # Unknown speed name, skip it
                            continue

                        # Store with normalized key 'speed_N' (skip speed_0/off)
                        if speed_num != "0":
                            speed_commands[f"speed_{speed_num}"] = k

                speed_count = len(speed_commands)
                options = ["off"] + [str(i) for i in range(1, speed_count + 1)]

                helpers["input_select"][f"{sanitized_id}_speed"] = {
                    "name": f"{display_name} Speed",
                    "options": options,
                    "initial": "off",
                }

                # Only add direction selector if direction commands exist
                entity_commands = entity_data.get("commands", {})
                has_direction_commands = (
                    "reverse" in entity_commands
                    or "direction" in entity_commands
                    or "fan_reverse" in entity_commands
                    or "fan_direction_forward" in entity_commands
                    or "fan_direction_reverse" in entity_commands
                )
                if has_direction_commands:
                    helpers["input_select"][f"{sanitized_id}_direction"] = {
                        "name": f"{display_name} Direction",
                        "options": ["forward", "reverse"],
                        "initial": "forward",
                    }

            # Climate entities are not supported (template.climate removed from HA)
            # Users should use SmartIR custom integration for AC control
            elif entity_type == "climate":
                # Skip - no helpers needed for unsupported entity type
                pass

            # Media player entities need source selection
            elif entity_type == "media_player":
                commands = entity_data.get("commands", {})

                # Add source selector if source commands exist
                source_commands = {
                    k: v for k, v in commands.items() if k.startswith("source_")
                }
                if source_commands:
                    # Extract source names from command keys (e.g., "source_hdmi1" -> "HDMI1")
                    sources = [
                        k.replace("source_", "").upper() for k in source_commands.keys()
                    ]

                    helpers["input_select"][f"{sanitized_id}_source"] = {
                        "name": f"{display_name} Source",
                        "options": sources,
                        "initial": sources[0] if sources else "HDMI1",
                    }

            # Cover entities need position tracking
            elif entity_type == "cover":
                commands = entity_data.get("commands", {})

                # Add position selector
                helpers["input_select"][f"{sanitized_id}_position"] = {
                    "name": f"{display_name} Position",
                    "options": ["open", "closed", "partial"],
                    "initial": "closed",
                }

                # Add position slider if position commands exist
                position_commands = {
                    k: v for k, v in commands.items() if k.startswith("position_")
                }
                if position_commands:
                    helpers["input_number"] = helpers.get("input_number", {})
                    helpers["input_number"][f"{sanitized_id}_position"] = {
                        "name": f"{display_name} Position",
                        "min": 0,
                        "max": 100,
                        "step": 1,
                        "initial": 0,
                        "unit_of_measurement": "%",
                    }

        return helpers

    def _write_yaml_file(self, file_path: Path, data: Dict[str, Any]):
        """Write YAML file with proper formatting"""
        try:
            with open(file_path, "w") as f:
                f.write("# Auto-generated by Broadlink Manager\n")
                f.write(
                    f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(
                    "# DO NOT EDIT THIS FILE MANUALLY - Changes will be overwritten\n\n"
                )
                yaml.dump(
                    data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                )

            logger.info(f"Written YAML file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write YAML file {file_path}: {e}")
            raise

    def _get_setup_instructions(self) -> Dict[str, str]:
        """Get setup instructions for the user"""
        return {
            "step1": "Add these lines to your configuration.yaml:",
            "code": (
                "homeassistant:\n"
                "  packages:\n"
                "    broadlink_manager: !include broadlink_manager/package.yaml"
            ),
            "step2": "Check your configuration (Developer Tools → YAML → Check Configuration)",
            "step3": "Restart Home Assistant",
            "step4": "Your entities will appear in Home Assistant!",
            "note": "Requires Home Assistant 2021.4 or newer for modern template syntax support",
        }
