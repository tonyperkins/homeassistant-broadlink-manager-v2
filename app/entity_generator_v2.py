"""
Entity Generator V2 - Works with device_manager and devices.json

This replaces the old entity_generator.py which used storage_manager.
Commands are now stored in devices.json with the device metadata.
"""

import logging
import yaml
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EntityGeneratorV2:
    """Generate Home Assistant entity YAML configurations from devices.json"""

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
        self.entities_file = self.config_path / "broadlink_manager_entities.yaml"
        self.package_file = self.broadlink_manager_dir / "package.yaml"

    def generate_all_devices(self, devices: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate entities for all Broadlink devices

        Args:
            devices: Dictionary of device_id -> device_data

        Returns:
            Dictionary with success status and entity count
        """
        try:
            all_entities = []
            entity_count = 0

            for device_id, device_data in devices.items():
                commands = device_data.get("commands", {})

                if not commands:
                    logger.warning(f"No commands found for device {device_id}")
                    continue

                # Get device info
                device_name = device_data.get("name", device_id)
                entity_type = device_data.get("entity_type", "switch")
                broadlink_entity = device_data.get("broadlink_entity")

                if not broadlink_entity:
                    logger.warning(f"No broadlink_entity for device {device_id}")
                    continue

                # Generate entities for each command
                for command_name, command_data in commands.items():
                    # Extract base64 data
                    if isinstance(command_data, dict):
                        base64_code = command_data.get("data")
                    else:
                        base64_code = command_data

                    if not base64_code:
                        logger.warning(
                            f"No data for command {command_name} in device {device_id}"
                        )
                        continue

                    # Create entity configuration
                    # Template entities use plural keys: lights, switches, etc.
                    entity_id_name = f"{device_id}_{command_name}"
                    entity_type_plural = (
                        f"{entity_type}s"  # light -> lights, switch -> switches
                    )

                    entity_config = {
                        "platform": "template",
                        entity_type_plural: {
                            entity_id_name: {
                                "friendly_name": f"{device_name} {command_name.replace('_', ' ').title()}",
                                "turn_on": {
                                    "service": "remote.send_command",
                                    "target": {"entity_id": broadlink_entity},
                                    "data": {"command": base64_code},
                                },
                            }
                        },
                    }

                    # For switches, add turn_off (same as turn_on for toggle devices)
                    if entity_type == "switch":
                        entity_config[entity_type_plural][entity_id_name][
                            "turn_off"
                        ] = entity_config[entity_type_plural][entity_id_name]["turn_on"]

                    all_entities.append(entity_config)
                    entity_count += 1

            # Write to YAML files
            if all_entities:
                self._write_yaml_file(all_entities)
                self._write_package_file(all_entities)
                logger.info(
                    f"✅ Generated {entity_count} entities in {self.entities_file} and {self.package_file}"
                )
                return {
                    "success": True,
                    "entities_count": entity_count,
                    "file": str(self.entities_file),
                    "package_file": str(self.package_file),
                }
            else:
                return {"success": False, "message": "No entities to generate"}

        except Exception as e:
            logger.error(f"Error generating entities: {e}", exc_info=True)
            return {"success": False, "message": str(e)}

    def _write_yaml_file(self, entities):
        """Write entities to YAML file"""
        try:
            # Create header comment
            header = [
                "# Broadlink Manager - Generated Entities",
                "# This file is auto-generated. Do not edit manually.",
                "# Generated from devices.json",
                "",
            ]

            with open(self.entities_file, "w") as f:
                # Write header
                for line in header:
                    f.write(f"{line}\n")

                # Write entities
                yaml.dump(entities, f, default_flow_style=False, sort_keys=False)

            logger.info(
                f"Wrote {len(entities)} entity configurations to {self.entities_file}"
            )

        except Exception as e:
            logger.error(f"Error writing YAML file: {e}")
            raise

    def _write_package_file(self, entities):
        """Write entities to package file for HA package structure"""
        try:
            # Create broadlink_manager directory if it doesn't exist
            self.broadlink_manager_dir.mkdir(parents=True, exist_ok=True)

            # Convert list of entity configs to proper package structure
            # Package needs to be a dictionary with entity type keys containing lists
            package = {}

            for entity_config in entities:
                # Get the entity type plural key (lights, switches, etc.)
                entity_type_plural = None
                for key in entity_config:
                    if key != "platform":
                        entity_type_plural = key
                        break

                if not entity_type_plural:
                    continue

                # Convert plural back to singular for package grouping (lights -> light)
                entity_type = entity_type_plural.rstrip("s")

                # Initialize entity type list if not exists
                if entity_type not in package:
                    package[entity_type] = []

                # Add the entire entity config (includes platform and entity definitions)
                package[entity_type].append(entity_config)

            # Create header comment
            header = [
                "# Broadlink Manager - Generated Entities Package",
                "# This file is auto-generated. Do not edit manually.",
                "# Generated from devices.json",
                "",
                "# To use this package, add to your configuration.yaml:",
                "# homeassistant:",
                "#   packages:",
                "#     broadlink_manager: !include broadlink_manager/package.yaml",
                "",
            ]

            with open(self.package_file, "w") as f:
                # Write header
                for line in header:
                    f.write(f"{line}\n")

                # Write package structure
                yaml.dump(package, f, default_flow_style=False, sort_keys=False)

            logger.info(
                f"Wrote {len(entities)} entity configurations to package file {self.package_file}"
            )

        except Exception as e:
            logger.error(f"Error writing package file: {e}")
            # Don't raise - package file is optional
            logger.warning(
                "Package file creation failed, but entities file was created successfully"
            )
