"""
Entity Generator V2 - Works with device_manager and devices.json

Uses the v1 EntityGenerator logic but adapts devices.json format to v1 entity metadata format.
This preserves all the sophisticated v1 features (state tracking, helpers, smart entities).
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Handle both package and script imports
try:
    from .entity_generator import EntityGenerator
except ImportError:
    from entity_generator import EntityGenerator

logger = logging.getLogger(__name__)


class DeviceManagerAdapter:
    """Adapter to make device_manager work with v1 EntityGenerator"""

    def __init__(self, device_manager, config_path: Path):
        self.device_manager = device_manager
        self.config_path = Path(config_path)
        self.entities_file = self.config_path / "broadlink_manager_entities.yaml"
        self.helpers_file = self.config_path / "broadlink_manager" / "helpers.yaml"
        self.package_file = self.config_path / "broadlink_manager" / "package.yaml"

    def get_all_entities(self) -> Dict[str, Dict[str, Any]]:
        """
        Convert devices.json format to v1 entity metadata format

        Returns dict of {entity_id: entity_data} where entity_data has:
        - entity_type: 'light', 'switch', 'fan', etc.
        - device: device name for Broadlink commands
        - commands: dict of {command_name: command_name} (v1 uses names, not base64)
        - broadlink_entity: HA entity ID of the Broadlink remote
        - friendly_name: Display name
        - enabled: True
        """
        devices = self.device_manager.get_all_devices()
        entities = {}

        for device_id, device_data in devices.items():
            commands = device_data.get("commands", {})
            if not commands:
                continue

            # Get broadlink entity from device
            broadlink_entity = device_data.get("broadlink_entity", "")
            device_name = device_data.get("name", device_id)

            # Infer entity type from commands and device info
            entity_type = self._infer_entity_type(commands, device_id, device_data)

            # Create entity metadata in v1 format
            entity_id = device_id
            entities[entity_id] = {
                "entity_type": entity_type,
                "device": device_id,  # Device name for Broadlink commands
                "commands": self._convert_commands_to_v1_format(commands),
                "broadlink_entity": broadlink_entity,
                "friendly_name": device_name,
                "enabled": True,
            }

        return entities

    def _infer_entity_type(
        self,
        commands: Dict[str, Any],
        device_id: str = "",
        device_data: Dict[str, Any] = None,
    ) -> str:
        """Infer entity type from command names and device info"""
        command_names = set(commands.keys())

        # Check explicit entity_type in device_data
        if device_data and device_data.get("entity_type"):
            return device_data["entity_type"]

        # Check for fan patterns
        fan_patterns = {
            "fan_speed_1",
            "fan_speed_2",
            "fan_speed_3",
            "fan_speed_4",
            "fan_speed_5",
            "fan_speed_6",
            "fan_off",
            "fan_reverse",
        }
        if command_names & fan_patterns:
            return "fan"

        # Check for light patterns in commands or device name
        light_patterns = {"brightness_up", "brightness_down", "dim", "bright"}
        if command_names & light_patterns or "light" in device_id.lower():
            return "light"

        # Default to switch
        return "switch"

    def _convert_commands_to_v1_format(
        self, commands: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Convert commands to v1 format
        V1 uses {command_name: command_name} because it references Broadlink storage
        V2 has {command_name: {data: base64, type: ir/rf}}
        """
        v1_commands = {}
        for cmd_name in commands.keys():
            v1_commands[cmd_name] = cmd_name  # V1 just uses command names
        return v1_commands

    def set_last_generated(self, timestamp: str):
        """Store last generated timestamp (optional)"""
        pass


class EntityGeneratorV2:
    """Generate Home Assistant entity YAML configurations from devices.json using v1 logic"""

    def __init__(self, device_manager, config_path: str):
        """
        Initialize the entity generator

        Args:
            device_manager: DeviceManager instance with access to devices.json
            config_path: Path to Home Assistant config directory
        """
        self.device_manager = device_manager
        self.config_path = Path(config_path)
        self.broadlink_manager_dir = self.config_path / "broadlink_manager"

        # Create adapter and v1 generator
        self.adapter = DeviceManagerAdapter(device_manager, config_path)
        self.v1_generator = EntityGenerator(self.adapter)

    def generate_all_devices(self, devices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate entities for all Broadlink devices using v1 logic

        Args:
            devices: Dictionary of device_id -> device_data

        Returns:
            Dictionary with success status and entity count
        """
        try:
            # Build broadlink_commands dict for v1 generator
            # Format: {device_name: {command_name: command_code}}
            broadlink_commands = {}

            for device_id, device_data in devices.items():
                commands = device_data.get("commands", {})
                if not commands:
                    continue

                # Build command dict with base64 codes
                device_commands = {}
                for cmd_name, cmd_data in commands.items():
                    if isinstance(cmd_data, dict):
                        device_commands[cmd_name] = cmd_data.get("data", "")
                    else:
                        device_commands[cmd_name] = cmd_data

                broadlink_commands[device_id] = device_commands

            # Delegate to v1 generator
            logger.info(
                f"Generating entities using v1 logic for {len(broadlink_commands)} devices"
            )
            result = self.v1_generator.generate_all(broadlink_commands)

            # Ensure broadlink_manager directory exists
            self.broadlink_manager_dir.mkdir(parents=True, exist_ok=True)

            return result

        except Exception as e:
            logger.error(f"Error generating entities: {e}", exc_info=True)
            return {"success": False, "message": str(e)}
