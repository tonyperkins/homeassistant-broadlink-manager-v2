#!/usr/bin/env python3
"""
Migration utility for Broadlink Manager v2
Migrates devices from metadata.json (v1) to devices.json (v2)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DataMigration:
    """Handles migration from v1 to v2 data format"""

    def __init__(self, storage_path: str = "/config/broadlink_manager"):
        self.storage_path = Path(storage_path)
        self.metadata_file = self.storage_path / "metadata.json"
        self.devices_file = self.storage_path / "devices.json"

    def needs_migration(self) -> bool:
        """
        Check if migration is needed

        Returns:
            True if metadata.json has entities but devices.json is empty
        """
        try:
            # Check if metadata.json exists and has entities
            if not self.metadata_file.exists():
                logger.info("No metadata.json found - no migration needed")
                return False

            with open(self.metadata_file, "r") as f:
                metadata = json.load(f)
                entities = metadata.get("entities", {})
                if not entities:
                    logger.info("metadata.json has no entities - no migration needed")
                    return False

            # Check if devices.json is empty or missing
            if not self.devices_file.exists():
                logger.info("devices.json missing - migration needed")
                return True

            with open(self.devices_file, "r") as f:
                devices = json.load(f)
                if not devices or devices == {}:
                    logger.info("devices.json is empty - migration needed")
                    return True

            logger.info("devices.json already populated - no migration needed")
            return False

        except Exception as e:
            logger.error(f"Error checking migration status: {e}")
            return False

    def migrate_entity_to_device(
        self, entity_id: str, entity_data: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Convert v1 entity format to v2 device format

        Args:
            entity_id: Entity ID (e.g., "switch.task_light")
            entity_data: Entity metadata from v1

        Returns:
            Tuple of (device_id, device_data)
        """
        # Extract device_id from entity_id (remove domain prefix)
        device_id = entity_id.split(".", 1)[1] if "." in entity_id else entity_id

        # Build v2 device data
        device_data = {
            "device_id": device_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", device_id),
            "entity_type": entity_data.get("entity_type", "switch"),
            "device_type": "broadlink",  # v1 only had broadlink devices
            "broadlink_entity": entity_data.get("broadlink_entity", ""),
            "area": entity_data.get("area", ""),
            "icon": entity_data.get("icon", ""),
            "commands": entity_data.get("commands", {}),
            "enabled": entity_data.get("enabled", True),
            "created_at": datetime.now().isoformat(),
            "migrated_from_v1": True,
            "original_entity_id": entity_id,
        }

        # Add device field if present (for command storage reference)
        if "device" in entity_data:
            device_data["device"] = entity_data["device"]

        return device_id, device_data

    def migrate(self) -> Tuple[bool, str, List[str]]:
        """
        Perform migration from v1 to v2 format

        Returns:
            Tuple of (success, message, migrated_device_ids)
        """
        try:
            if not self.needs_migration():
                return True, "No migration needed", []

            logger.info("Starting migration from v1 to v2 format...")

            # Load metadata.json
            with open(self.metadata_file, "r") as f:
                metadata = json.load(f)
                entities = metadata.get("entities", {})

            if not entities:
                return True, "No entities to migrate", []

            # Convert entities to devices
            devices = {}
            migrated_ids = []

            for entity_id, entity_data in entities.items():
                try:
                    device_id, device_data = self.migrate_entity_to_device(
                        entity_id, entity_data
                    )
                    devices[device_id] = device_data
                    migrated_ids.append(device_id)
                    logger.info(f"Migrated: {entity_id} -> {device_id}")
                except Exception as e:
                    logger.error(f"Error migrating entity {entity_id}: {e}")
                    continue

            # Save to devices.json
            with open(self.devices_file, "w") as f:
                json.dump(devices, f, indent=2)

            message = f"Successfully migrated {len(migrated_ids)} devices from v1 to v2"
            logger.info(message)
            return True, message, migrated_ids

        except Exception as e:
            error_msg = f"Migration failed: {e}"
            logger.error(error_msg)
            return False, error_msg, []

    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status

        Returns:
            Dict with migration status information
        """
        try:
            status = {
                "needs_migration": self.needs_migration(),
                "metadata_exists": self.metadata_file.exists(),
                "devices_exists": self.devices_file.exists(),
                "metadata_entity_count": 0,
                "devices_count": 0,
            }

            if self.metadata_file.exists():
                with open(self.metadata_file, "r") as f:
                    metadata = json.load(f)
                    status["metadata_entity_count"] = len(metadata.get("entities", {}))

            if self.devices_file.exists():
                with open(self.devices_file, "r") as f:
                    devices = json.load(f)
                    status["devices_count"] = (
                        len(devices) if isinstance(devices, dict) else 0
                    )

            return status

        except Exception as e:
            logger.error(f"Error getting migration status: {e}")
            return {
                "error": str(e),
                "needs_migration": False,
            }
