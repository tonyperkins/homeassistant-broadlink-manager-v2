#!/usr/bin/env python3
"""
Device Manager for Broadlink Manager Add-on
Handles device metadata and command organization
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

# Global lock for file writes (shared across all DeviceManager instances)
_global_write_lock = threading.Lock()


class DeviceManager:
    """Manage device metadata and commands"""

    def __init__(self, storage_path: str = "/config/broadlink_manager"):
        """
        Initialize device manager

        Args:
            storage_path: Path to storage directory
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.devices_file = self.storage_path / "devices.json"
        self.backup_file = self.storage_path / "devices.json.backup"

        # Ensure devices file exists
        if not self.devices_file.exists():
            # Check if backup exists
            if self.backup_file.exists():
                logger.warning(
                    "devices.json missing but backup found - restoring from backup"
                )
                try:
                    import shutil

                    shutil.copy2(self.backup_file, self.devices_file)
                    logger.info("Successfully restored devices.json from backup")
                except Exception as e:
                    logger.error(f"Failed to restore from backup: {e}")
                    self._save_devices({})
            else:
                self._save_devices({})

    def _load_devices(self) -> Dict[str, Any]:
        """Load devices from storage"""
        # On Windows, editors often replace files atomically which can briefly
        # lock the target or leave a partially-written file. Retry a few times
        # on PermissionError or JSONDecodeError before giving up.
        import time
        from json import JSONDecodeError

        max_retries = 5
        for attempt in range(max_retries):
            try:
                with open(self.devices_file, "r") as f:
                    return json.load(f)
            except (PermissionError, JSONDecodeError) as e:
                if attempt < max_retries - 1:
                    backoff = 0.05 * (attempt + 1)
                    logger.debug(
                        f"Load devices retry due to {type(e).__name__}: waiting {backoff:.2f}s (attempt {attempt+1}/{max_retries})"
                    )
                    time.sleep(backoff)
                    continue
                logger.error(f"Error loading devices after retries: {e}")
                return {}
            except FileNotFoundError:
                # If file truly doesn't exist yet, return empty
                logger.warning("devices.json not found when loading; returning empty set")
                return {}
            except Exception as e:
                logger.error(f"Unexpected error loading devices: {e}")
                return {}

    def _save_devices(self, devices: Dict[str, Any]) -> bool:
        """
        Save devices to storage with automatic backup and thread-safe locking

        Args:
            devices: Device data to save

        Returns:
            True if successful, False otherwise
        """
        import shutil

        # Use global lock to prevent concurrent writes across all instances
        with _global_write_lock:
            try:
                # Create backup of existing file before modifying
                if self.devices_file.exists():
                    try:
                        shutil.copy2(self.devices_file, self.backup_file)
                        logger.debug("Created backup of devices.json")
                    except Exception as e:
                        logger.warning(f"Failed to create backup: {e}")
                        # Continue anyway - backup failure shouldn't stop the save

                # Write to temporary file first, then rename (atomic operation)
                temp_file = self.devices_file.with_suffix(".tmp")

                # Write and explicitly close before rename
                with open(temp_file, "w") as f:
                    json.dump(devices, f, indent=2)
                    f.flush()  # Ensure data is written
                # File is now closed

                # Small delay to ensure Windows releases the file handle
                import time

                time.sleep(0.01)

                # Atomic rename with retry for Windows file locking issues
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        temp_file.replace(self.devices_file)
                        break
                    except PermissionError:
                        if attempt < max_retries - 1:
                            logger.warning(
                                f"File locked, retrying... (attempt {attempt + 1}/{max_retries})"
                            )
                            time.sleep(0.1 * (attempt + 1))  # Exponential backoff
                        else:
                            raise
                logger.debug(f"Successfully saved devices.json")
                return True
            except Exception as e:
                logger.error(f"Error saving devices: {e}")
                # Clean up temp file if it exists
                temp_file = self.devices_file.with_suffix(".tmp")
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except Exception:
                        pass

                # If save failed and we have a backup, restore it
                if self.backup_file.exists() and not self.devices_file.exists():
                    logger.warning("Save failed - restoring from backup")
                    try:
                        shutil.copy2(self.backup_file, self.devices_file)
                        logger.info(
                            "Restored devices.json from backup after failed save"
                        )
                    except Exception as restore_error:
                        logger.error(f"Failed to restore from backup: {restore_error}")

                return False

    def create_device(self, device_id: str, device_data: Dict[str, Any]) -> bool:
        """
        Create a new device

        Args:
            device_id: Unique device identifier (e.g., "master_bedroom_stereo")
            device_data: Device metadata
                Required fields:
                - name: Device display name
                - entity_type: Entity type (climate, fan, media_player, light, switch)
                - device_type: 'broadlink' or 'smartir'

                For Broadlink devices:
                - broadlink_entity: Broadlink remote entity ID

                For SmartIR devices:
                - manufacturer: Device manufacturer
                - model: Device model
                - device_code: SmartIR code ID
                - controller_device: Broadlink entity that sends codes
                - temperature_sensor: (optional, for climate) Temperature sensor entity
                - humidity_sensor: (optional, for climate) Humidity sensor entity

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id in devices:
                logger.warning(f"Device {device_id} already exists")
                return False

            # Validate device_type
            device_type = device_data.get("device_type", "broadlink")
            if device_type not in ["broadlink", "smartir"]:
                logger.error(f"Invalid device_type: {device_type}")
                return False

            # Add metadata
            device_data["device_id"] = device_id
            device_data["device_type"] = device_type
            device_data["created_at"] = datetime.now().isoformat()

            # Initialize commands for Broadlink devices (only if not already provided)
            if device_type == "broadlink" and "commands" not in device_data:
                device_data["commands"] = {}

            devices[device_id] = device_data

            if self._save_devices(devices):
                logger.info(f"Created {device_type} device: {device_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error creating device {device_id}: {e}")
            return False

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device by ID

        Args:
            device_id: Device identifier

        Returns:
            Device data or None if not found
        """
        devices = self._load_devices()
        return devices.get(device_id)

    def get_all_devices(self) -> Dict[str, Any]:
        """Get all devices"""
        return self._load_devices()

    def get_devices_by_broadlink(self, broadlink_entity: str) -> Dict[str, Any]:
        """
        Get all devices controlled by a specific Broadlink

        Args:
            broadlink_entity: Broadlink entity ID (e.g., "remote.master_bedroom_rm4_pro")

        Returns:
            Dict of devices
        """
        all_devices = self._load_devices()
        return {
            device_id: device_data
            for device_id, device_data in all_devices.items()
            if device_data.get("broadlink_entity") == broadlink_entity
        }

    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update device metadata

        Args:
            device_id: Device identifier
            updates: Fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id not in devices:
                logger.warning(f"Device {device_id} not found")
                return False

            # Update fields (preserve commands unless explicitly updated)
            old_commands = devices[device_id].get("commands", {})
            devices[device_id].update(updates)

            # Only restore old commands if not explicitly updated
            if "commands" not in updates:
                devices[device_id]["commands"] = old_commands

            devices[device_id]["updated_at"] = datetime.now().isoformat()

            if self._save_devices(devices):
                logger.info(f"Updated device: {device_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating device {device_id}: {e}")
            return False

    def delete_device(self, device_id: str) -> bool:
        """
        Delete a device and all its commands

        Args:
            device_id: Device identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id not in devices:
                logger.warning(f"Device {device_id} not found")
                return False

            del devices[device_id]

            if self._save_devices(devices):
                logger.info(f"Deleted device: {device_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deleting device {device_id}: {e}")
            return False

    def add_command(
        self, device_id: str, command_name: str, command_data: Dict[str, Any]
    ) -> bool:
        """
        Add a command to a device

        Args:
            device_id: Device identifier
            command_name: Command name (e.g., "power_on")
            command_data: Command metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id not in devices:
                logger.warning(f"Device {device_id} not found")
                logger.debug(f"Available devices: {list(devices.keys())}")
                return False

            if "commands" not in devices[device_id]:
                devices[device_id]["commands"] = {}

            devices[device_id]["commands"][command_name] = command_data
            devices[device_id]["updated_at"] = datetime.now().isoformat()

            if self._save_devices(devices):
                logger.info(f"Added command {command_name} to device {device_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error adding command to device {device_id}: {e}")
            return False

    def delete_command(self, device_id: str, command_name: str) -> bool:
        """
        Delete a command from a device

        Args:
            device_id: Device identifier
            command_name: Command name

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id not in devices:
                logger.warning(f"Device {device_id} not found")
                return False

            if command_name in devices[device_id].get("commands", {}):
                del devices[device_id]["commands"][command_name]
                devices[device_id]["updated_at"] = datetime.now().isoformat()

                if self._save_devices(devices):
                    logger.info(
                        f"Deleted command {command_name} from device {device_id}"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Error deleting command from device {device_id}: {e}")
            return False

    def get_device_commands(self, device_id: str) -> Dict[str, Any]:
        """
        Get all commands for a device

        Args:
            device_id: Device identifier

        Returns:
            Dict of commands
        """
        device = self.get_device(device_id)
        if device:
            return device.get("commands", {})
        return {}

    def generate_device_id(self, area_id: str, device_name: str) -> str:
        """
        Generate a device ID from device name only.
        
        NOTE: area_id parameter is kept for backward compatibility but is NOT used.
        Area is stored as metadata only and does not affect the device ID.

        Args:
            area_id: Area identifier (IGNORED - kept for compatibility)
            device_name: Device name (e.g., "Ceiling Fan Light")

        Returns:
            Device ID (e.g., "ceiling_fan_light")
        """
        # Convert to lowercase and replace spaces/special chars with underscores
        clean_name = device_name.lower().replace(" ", "_")
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in clean_name)
        clean_name = "_".join(
            filter(None, clean_name.split("_"))
        )  # Remove multiple underscores

        # Return just the normalized device name - area is NOT part of device ID
        return clean_name

    def get_devices_by_type(self, device_type: str) -> Dict[str, Any]:
        """
        Get all devices of a specific type

        Args:
            device_type: Device type ('broadlink' or 'smartir')

        Returns:
            Dict of devices matching the type
        """
        all_devices = self._load_devices()
        return {
            device_id: device_data
            for device_id, device_data in all_devices.items()
            if device_data.get("device_type", "broadlink") == device_type
        }

    def get_smartir_devices(self) -> Dict[str, Any]:
        """Get all SmartIR devices"""
        return self.get_devices_by_type("smartir")

    def get_broadlink_devices(self) -> Dict[str, Any]:
        """Get all Broadlink devices"""
        return self.get_devices_by_type("broadlink")

    def is_smartir_device(self, device_id: str) -> bool:
        """
        Check if a device is a SmartIR device

        Args:
            device_id: Device identifier

        Returns:
            True if device is SmartIR type, False otherwise
        """
        device = self.get_device(device_id)
        if not device:
            return False
        return device.get("device_type", "broadlink") == "smartir"

    def validate_smartir_device(
        self, device_data: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate SmartIR device data

        Args:
            device_data: Device data to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        required_fields = ["manufacturer", "model", "device_code", "controller_device"]

        for field in required_fields:
            if field not in device_data or not device_data[field]:
                return False, f"Missing required field: {field}"

        # Validate entity_type for SmartIR
        entity_type = device_data.get("entity_type")
        if entity_type not in ["climate", "fan", "media_player", "light"]:
            return False, f"Invalid entity_type for SmartIR: {entity_type}"

        # Validate device_code is numeric
        try:
            int(device_data["device_code"])
        except (ValueError, TypeError):
            return False, "device_code must be a valid number"

        return True, None

    # Enhanced command management for direct learning

    def add_learned_command(
        self,
        device_id: str,
        command_name: str,
        command_data: str,
        command_type: str,
        frequency: Optional[float] = None,
    ) -> bool:
        """
        Add a learned command with base64 data

        Args:
            device_id: Device identifier
            command_name: Command name (e.g., "power")
            command_data: Base64 encoded command data
            command_type: "ir" or "rf"
            frequency: RF frequency in MHz (for RF commands only)

        Returns:
            True if successful, False otherwise
        """
        try:
            command_dict = {
                "name": command_name,
                "type": command_type,
                "data": command_data,
                "learned_at": datetime.now().isoformat(),
                "tested": False,
                "test_method": None,
            }

            if command_type == "rf" and frequency:
                command_dict["frequency"] = frequency

            return self.add_command(device_id, command_name, command_dict)

        except Exception as e:
            logger.error(f"Error adding learned command: {e}")
            return False

    def update_command_test_status(
        self, device_id: str, command_name: str, test_method: str
    ) -> bool:
        """
        Update command test status

        Args:
            device_id: Device identifier
            command_name: Command name
            test_method: "direct" or "ha"

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id not in devices:
                logger.warning(f"Device {device_id} not found")
                return False

            commands = devices[device_id].get("commands", {})
            if command_name not in commands:
                logger.warning(
                    f"Command {command_name} not found in device {device_id}"
                )
                return False

            commands[command_name]["tested"] = True
            commands[command_name]["test_method"] = test_method
            commands[command_name]["tested_at"] = datetime.now().isoformat()

            devices[device_id]["updated_at"] = datetime.now().isoformat()

            if self._save_devices(devices):
                logger.info(f"Updated test status for command {command_name}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating command test status: {e}")
            return False

    def get_command_data(self, device_id: str, command_name: str) -> Optional[str]:
        """
        Get base64 command data

        Args:
            device_id: Device identifier
            command_name: Command name

        Returns:
            Base64 command data, or None if not found
        """
        device = self.get_device(device_id)
        if not device:
            return None

        commands = device.get("commands", {})
        command = commands.get(command_name)

        if command:
            return command.get("data")

        return None

    def update_device_connection_info(
        self, device_id: str, connection_info: Dict[str, Any]
    ) -> bool:
        """
        Update device connection info for direct learning

        Args:
            device_id: Device identifier
            connection_info: Dict with host, mac, type, model

        Returns:
            True if successful, False otherwise
        """
        try:
            devices = self._load_devices()

            if device_id not in devices:
                logger.warning(f"Device {device_id} not found")
                return False

            devices[device_id]["connection"] = connection_info
            devices[device_id]["updated_at"] = datetime.now().isoformat()

            if self._save_devices(devices):
                logger.info(f"Updated connection info for device {device_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating connection info: {e}")
            return False
    
    def migrate_device_field(self) -> int:
        """
        Migrate existing Broadlink devices to add 'device' field if missing.
        The 'device' field stores the normalized device name for Broadlink storage lookups.
        
        Since device IDs should already be normalized device names (without area),
        the 'device' field should just match the device_id.
        
        Returns:
            Number of devices migrated
        """
        try:
            devices = self._load_devices()
            migrated_count = 0
            
            for device_id, device_data in devices.items():
                # Only migrate Broadlink devices that don't have the 'device' field
                device_type = device_data.get("device_type", "broadlink")
                if device_type == "broadlink" and "device" not in device_data:
                    # For Broadlink devices, the 'device' field should match device_id
                    # since device IDs are normalized device names (area is metadata only)
                    device_data["device"] = device_id
                    migrated_count += 1
                    logger.info(f"Migrated device '{device_id}': added device field = '{device_id}'")
            
            if migrated_count > 0:
                if self._save_devices(devices):
                    logger.info(f"Successfully migrated {migrated_count} device(s)")
                    return migrated_count
                else:
                    logger.error("Failed to save migrated devices")
                    return 0
            else:
                logger.debug("No devices needed migration")
                return 0
                
        except Exception as e:
            logger.error(f"Error during device migration: {e}")
            return 0
