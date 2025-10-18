#!/usr/bin/env python3
"""
SmartIR YAML Generator for Broadlink Manager Add-on
Generates Home Assistant SmartIR device configurations
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class SmartIRYAMLGenerator:
    """Generate SmartIR device YAML configurations"""

    def __init__(self, config_path: str = "/config"):
        """
        Initialize SmartIR YAML generator

        Args:
            config_path: Path to Home Assistant config directory
        """
        self.config_path = Path(config_path)
        self.smartir_dir = self.config_path / "smartir"
        self.smartir_dir.mkdir(parents=True, exist_ok=True)

    def generate_device_config(
        self, device_id: str, device_data: Dict[str, Any], broadlink_devices: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate SmartIR device configuration

        Args:
            device_id: Device identifier
            device_data: Device metadata from device manager
            broadlink_devices: List of available Broadlink devices (deprecated, kept for compatibility)

        Returns:
            Dict with generation result
        """
        try:
            entity_type = device_data.get("entity_type")

            if entity_type not in ["climate", "fan", "media_player", "light"]:
                return {"success": False, "error": f"Unsupported entity type for SmartIR: {entity_type}"}

            # Get controller entity ID - SmartIR supports any remote entity, not just Broadlink
            controller_entity = device_data.get("controller_device")

            if not controller_entity:
                return {"success": False, "error": "No controller_device specified. Please select a remote entity."}

            # Build device configuration
            config = self._build_device_config(device_id, device_data, controller_entity)

            # Write to platform-specific file
            platform_file = self.smartir_dir / f"{entity_type}.yaml"
            success = self._append_device_to_file(platform_file, config, entity_type)

            if success:
                return {
                    "success": True,
                    "message": f"SmartIR device configuration generated",
                    "file": str(platform_file),
                    "config": config,
                }
            else:
                return {"success": False, "error": "Failed to write configuration file"}

        except Exception as e:
            logger.error(f"Error generating SmartIR config for {device_id}: {e}")
            return {"success": False, "error": str(e)}

    # Deprecated: SmartIR uses entity IDs directly, not IP addresses
    # Kept for backward compatibility but no longer used
    def _get_controller_ip(self, controller_entity: str, broadlink_devices: List[Dict[str, Any]]) -> Optional[str]:
        """
        DEPRECATED: Get IP address for a Broadlink controller entity

        SmartIR now uses entity IDs directly in controller_data.
        This method is kept for backward compatibility only.

        Args:
            controller_entity: Broadlink entity ID (e.g., "remote.master_bedroom_rm4_pro")
            broadlink_devices: List of Broadlink devices

        Returns:
            IP address or None if not found
        """
        logger.warning("_get_controller_ip is deprecated. SmartIR uses entity IDs directly.")
        for device in broadlink_devices:
            if device.get("entity_id") == controller_entity:
                return device.get("host") or device.get("ip")

        logger.warning(f"Could not find IP for controller: {controller_entity}")
        return None

    def _build_device_config(self, device_id: str, device_data: Dict[str, Any], controller_entity: str) -> Dict[str, Any]:
        """
        Build SmartIR device configuration dict

        Args:
            device_id: Device identifier
            device_data: Device metadata
            controller_entity: Remote entity ID (e.g., "remote.master_bedroom_rm4_pro")
                             Can be any HA remote entity, not just Broadlink

        Returns:
            Device configuration dict
        """
        entity_type = device_data.get("entity_type")

        # Base configuration
        # SmartIR supports entity IDs directly in controller_data
        # This works with Broadlink, Xiaomi, Harmony Hub, and any HA remote entity
        config = {
            "platform": "smartir",
            "name": device_data.get("name"),
            "unique_id": device_id,
            "device_code": int(device_data.get("device_code")),
            "controller_data": controller_entity,  # Entity ID, not IP address
        }

        # Add entity type-specific fields
        if entity_type == "climate":
            # Climate-specific fields
            if device_data.get("temperature_sensor"):
                config["temperature_sensor"] = device_data["temperature_sensor"]
            if device_data.get("humidity_sensor"):
                config["humidity_sensor"] = device_data["humidity_sensor"]

            # Optional climate settings
            if device_data.get("power_sensor"):
                config["power_sensor"] = device_data["power_sensor"]

        elif entity_type == "fan":
            # Fan-specific fields (if any in future)
            pass

        elif entity_type == "media_player":
            # Media player-specific fields
            if device_data.get("power_sensor"):
                config["power_sensor"] = device_data["power_sensor"]

        elif entity_type == "light":
            # Light-specific fields
            if device_data.get("power_sensor"):
                config["power_sensor"] = device_data["power_sensor"]

        return config

    def _append_device_to_file(self, file_path: Path, config: Dict[str, Any], entity_type: str) -> bool:
        """
        Append device configuration to platform file

        Args:
            file_path: Path to platform YAML file
            config: Device configuration
            entity_type: Entity type (climate, fan, media_player)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read existing content
            existing_devices = []
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = yaml.safe_load(f)
                    if content:
                        # Handle both list format and dict format
                        if isinstance(content, list):
                            existing_devices = content
                        elif isinstance(content, dict) and entity_type in content:
                            existing_devices = content[entity_type]

            # Check if device already exists (by unique_id)
            unique_id = config.get("unique_id")
            device_exists = False
            for i, device in enumerate(existing_devices):
                if device.get("unique_id") == unique_id:
                    # Update existing device
                    existing_devices[i] = config
                    device_exists = True
                    logger.info(f"Updated existing SmartIR device: {unique_id}")
                    break

            if not device_exists:
                # Add new device
                existing_devices.append(config)
                logger.info(f"Added new SmartIR device: {unique_id}")

            # Write back to file
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(existing_devices, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            return True

        except Exception as e:
            logger.error(f"Error writing to {file_path}: {e}")
            return False

    def remove_device_from_file(self, device_id: str, entity_type: str) -> Dict[str, Any]:
        """
        Remove a device from its platform file

        Args:
            device_id: Device identifier (unique_id)
            entity_type: Entity type (climate, fan, media_player)

        Returns:
            Dict with operation result
        """
        try:
            platform_file = self.smartir_dir / f"{entity_type}.yaml"

            if not platform_file.exists():
                return {"success": False, "error": f"Platform file does not exist: {platform_file}"}

            # Read existing content
            with open(platform_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if not content:
                return {"success": False, "error": "Platform file is empty"}

            # Handle both list and dict formats
            devices = content if isinstance(content, list) else content.get(entity_type, [])

            # Filter out the device
            original_count = len(devices)
            devices = [d for d in devices if d.get("unique_id") != device_id]
            removed_count = original_count - len(devices)

            if removed_count == 0:
                return {"success": False, "error": f"Device {device_id} not found in {platform_file}"}

            # Write back
            with open(platform_file, "w", encoding="utf-8") as f:
                yaml.dump(devices, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

            logger.info(f"Removed SmartIR device {device_id} from {platform_file}")

            return {"success": True, "message": f"Device removed from {entity_type}.yaml", "removed_count": removed_count}

        except Exception as e:
            logger.error(f"Error removing device from file: {e}")
            return {"success": False, "error": str(e)}

    def ensure_configuration_yaml_includes(self) -> Dict[str, Any]:
        """
        Ensure configuration.yaml includes SmartIR platform files

        Returns:
            Dict with check results and instructions
        """
        config_file = self.config_path / "configuration.yaml"

        if not config_file.exists():
            return {
                "success": False,
                "error": "configuration.yaml not found",
                "instructions": "Cannot automatically update configuration.yaml",
            }

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for includes
            includes_needed = []
            for entity_type in ["climate", "fan", "media_player", "light"]:
                include_line = f"!include smartir/{entity_type}.yaml"
                if include_line not in content:
                    includes_needed.append(entity_type)

            if not includes_needed:
                return {"success": True, "message": "All SmartIR includes are present in configuration.yaml"}

            # Generate instructions for manual update
            instructions = ["Add the following lines to your configuration.yaml:", ""]

            for entity_type in includes_needed:
                instructions.append(f"{entity_type}:")
                instructions.append(f"  - !include smartir/{entity_type}.yaml")
                instructions.append("")

            return {
                "success": False,
                "includes_needed": includes_needed,
                "instructions": "\n".join(instructions),
                "message": "Manual configuration.yaml update required",
            }

        except Exception as e:
            logger.error(f"Error checking configuration.yaml: {e}")
            return {"success": False, "error": str(e)}

    def get_device_config_from_file(self, device_id: str, entity_type: str) -> Optional[Dict[str, Any]]:
        """
        Get a device's configuration from its platform file

        Args:
            device_id: Device identifier (unique_id)
            entity_type: Entity type

        Returns:
            Device config dict or None if not found
        """
        try:
            platform_file = self.smartir_dir / f"{entity_type}.yaml"

            if not platform_file.exists():
                return None

            with open(platform_file, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

            if not content:
                return None

            devices = content if isinstance(content, list) else content.get(entity_type, [])

            for device in devices:
                if device.get("unique_id") == device_id:
                    return device

            return None

        except Exception as e:
            logger.error(f"Error reading device config: {e}")
            return None
