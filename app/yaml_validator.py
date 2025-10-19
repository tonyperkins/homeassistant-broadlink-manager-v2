#!/usr/bin/env python3
"""
YAML Validator for Home Assistant SmartIR configurations
Validates YAML files before writing to prevent HA boot failures
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import yaml
import re

logger = logging.getLogger(__name__)


class YAMLValidator:
    """Validates Home Assistant SmartIR YAML configurations"""

    # Required fields for each platform
    REQUIRED_FIELDS = {
        "climate": ["platform", "name", "unique_id", "device_code", "controller_data"],
        "media_player": ["platform", "name", "unique_id", "device_code", "controller_data"],
        "fan": ["platform", "name", "unique_id", "device_code", "controller_data"],
        "light": ["platform", "name", "unique_id", "device_code", "controller_data"],
    }

    # Optional fields for each platform
    OPTIONAL_FIELDS = {
        "climate": ["temperature_sensor", "humidity_sensor", "power_sensor"],
        "media_player": ["power_sensor", "source_names"],
        "fan": ["power_sensor"],
        "light": ["power_sensor"],
    }

    # Field type validation
    FIELD_TYPES = {
        "platform": str,
        "name": str,
        "unique_id": str,
        "device_code": int,
        "controller_data": str,
        "temperature_sensor": str,
        "humidity_sensor": str,
        "power_sensor": str,
        "source_names": dict,
    }

    @staticmethod
    def validate_device_config(config: Dict[str, Any], platform: str) -> Tuple[bool, List[str]]:
        """
        Validate a single device configuration

        Args:
            config: Device configuration dict
            platform: Platform type (climate, media_player, fan, light)

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        # Check platform is valid
        if platform not in YAMLValidator.REQUIRED_FIELDS:
            errors.append(f"Invalid platform: {platform}")
            return False, errors

        # Check required fields
        required = YAMLValidator.REQUIRED_FIELDS[platform]
        for field in required:
            if field not in config:
                errors.append(f"Missing required field: {field}")
            elif config[field] is None or config[field] == "":
                errors.append(f"Field '{field}' cannot be empty")

        # Check platform value
        if config.get("platform") != "smartir":
            errors.append(f"Platform must be 'smartir', got: {config.get('platform')}")

        # Validate field types
        for field, value in config.items():
            if field in YAMLValidator.FIELD_TYPES:
                expected_type = YAMLValidator.FIELD_TYPES[field]
                if not isinstance(value, expected_type):
                    errors.append(
                        f"Field '{field}' must be {expected_type.__name__}, got {type(value).__name__}: {value}"
                    )

        # Validate device_code is positive integer
        if "device_code" in config:
            try:
                code = int(config["device_code"])
                if code <= 0:
                    errors.append(f"device_code must be positive, got: {code}")
            except (ValueError, TypeError):
                errors.append(f"device_code must be an integer, got: {config['device_code']}")

        # Validate unique_id format (no spaces, valid characters)
        if "unique_id" in config:
            unique_id = str(config["unique_id"])
            if " " in unique_id:
                errors.append(f"unique_id cannot contain spaces: {unique_id}")
            if not re.match(r"^[a-z0-9_]+$", unique_id):
                errors.append(f"unique_id must contain only lowercase letters, numbers, and underscores: {unique_id}")

        # Validate entity IDs (controller_data, sensors)
        entity_fields = ["controller_data", "temperature_sensor", "humidity_sensor", "power_sensor"]
        for field in entity_fields:
            if field in config and config[field]:
                entity_id = str(config[field])
                if not YAMLValidator._is_valid_entity_id(entity_id):
                    errors.append(f"Invalid entity ID format for '{field}': {entity_id}")

        # Check for unknown fields (warn but don't fail)
        allowed_fields = set(required + YAMLValidator.OPTIONAL_FIELDS.get(platform, []))
        for field in config.keys():
            if field not in allowed_fields:
                logger.warning(f"Unknown field in {platform} config: {field}")

        return len(errors) == 0, errors

    @staticmethod
    def _is_valid_entity_id(entity_id: str) -> bool:
        """
        Check if entity ID follows Home Assistant format (domain.entity_name)

        Args:
            entity_id: Entity ID to validate

        Returns:
            True if valid format
        """
        # HA entity ID format: domain.entity_name
        # domain: lowercase letters only
        # entity_name: lowercase letters, numbers, underscores
        pattern = r"^[a-z]+\.[a-z0-9_]+$"
        return bool(re.match(pattern, entity_id))

    @staticmethod
    def validate_yaml_syntax(content: str) -> Tuple[bool, Optional[str]]:
        """
        Validate YAML syntax by attempting to parse

        Args:
            content: YAML content string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            yaml.safe_load(content)
            return True, None
        except yaml.YAMLError as e:
            return False, str(e)

    @staticmethod
    def validate_yaml_file_content(devices: List[Dict[str, Any]], platform: str) -> Tuple[bool, List[str]]:
        """
        Validate entire YAML file content (list of devices)

        Args:
            devices: List of device configurations
            platform: Platform type

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        all_errors = []

        if not isinstance(devices, list):
            all_errors.append(f"YAML content must be a list, got {type(devices).__name__}")
            return False, all_errors

        # Validate each device
        unique_ids = set()
        for i, device in enumerate(devices):
            if not isinstance(device, dict):
                all_errors.append(f"Device {i} must be a dict, got {type(device).__name__}")
                continue

            # Validate device config
            is_valid, errors = YAMLValidator.validate_device_config(device, platform)
            if not is_valid:
                for error in errors:
                    all_errors.append(f"Device {i} ({device.get('name', 'unknown')}): {error}")

            # Check for duplicate unique_ids
            unique_id = device.get("unique_id")
            if unique_id:
                if unique_id in unique_ids:
                    all_errors.append(f"Duplicate unique_id found: {unique_id}")
                unique_ids.add(unique_id)

        return len(all_errors) == 0, all_errors

    @staticmethod
    def validate_and_format_yaml(devices: List[Dict[str, Any]], platform: str) -> Tuple[bool, Optional[str], List[str]]:
        """
        Validate devices and generate formatted YAML string

        Args:
            devices: List of device configurations
            platform: Platform type

        Returns:
            Tuple of (is_valid, yaml_string, list_of_errors)
        """
        # First validate the content
        is_valid, errors = YAMLValidator.validate_yaml_file_content(devices, platform)

        if not is_valid:
            return False, None, errors

        # Generate YAML string
        try:
            yaml_string = yaml.dump(devices, default_flow_style=False, allow_unicode=True, sort_keys=False)

            # Validate the generated YAML syntax
            syntax_valid, syntax_error = YAMLValidator.validate_yaml_syntax(yaml_string)
            if not syntax_valid:
                errors.append(f"Generated YAML has syntax error: {syntax_error}")
                return False, None, errors

            return True, yaml_string, []

        except Exception as e:
            errors.append(f"Error generating YAML: {str(e)}")
            return False, None, errors

    @staticmethod
    def validate_existing_file(file_path: str, platform: str) -> Tuple[bool, List[str]]:
        """
        Validate an existing YAML file

        Args:
            file_path: Path to YAML file
            platform: Platform type

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check syntax first
            syntax_valid, syntax_error = YAMLValidator.validate_yaml_syntax(content)
            if not syntax_valid:
                return False, [f"YAML syntax error: {syntax_error}"]

            # Parse and validate content
            devices = yaml.safe_load(content)
            if devices is None:
                return True, []  # Empty file is valid

            return YAMLValidator.validate_yaml_file_content(devices, platform)

        except Exception as e:
            return False, [f"Error reading file: {str(e)}"]
