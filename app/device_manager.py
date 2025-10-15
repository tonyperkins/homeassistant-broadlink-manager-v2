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

logger = logging.getLogger(__name__)


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

        # Ensure devices file exists
        if not self.devices_file.exists():
            self._save_devices({})

    def _load_devices(self) -> Dict[str, Any]:
        """Load devices from storage"""
        try:
            with open(self.devices_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading devices: {e}")
            return {}

    def _save_devices(self, devices: Dict[str, Any]) -> bool:
        """
        Save devices to storage

        Args:
            devices: Device data to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.devices_file, "w") as f:
                json.dump(devices, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving devices: {e}")
            return False

    def create_device(self, device_id: str, device_data: Dict[str, Any]) -> bool:
        """
        Create a new device

        Args:
            device_id: Unique device identifier (e.g., "master_bedroom_stereo")
            device_data: Device metadata
                Required fields:
                - name: Device display name
                - entity_type: Entity type (climate, fan, media_player, switch)
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
            
            # Initialize commands for Broadlink devices
            if device_type == "broadlink":
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

            # Update fields (preserve commands)
            commands = devices[device_id].get("commands", {})
            devices[device_id].update(updates)
            devices[device_id]["commands"] = commands
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
        Generate a device ID from area and device name

        Args:
            area_id: Area identifier (e.g., "master_bedroom")
            device_name: Device name (e.g., "Stereo")

        Returns:
            Device ID (e.g., "master_bedroom_stereo")
        """
        # Convert to lowercase and replace spaces/special chars with underscores
        clean_name = device_name.lower().replace(" ", "_")
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in clean_name)
        clean_name = "_".join(
            filter(None, clean_name.split("_"))
        )  # Remove multiple underscores

        return f"{area_id}_{clean_name}"
    
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
    
    def validate_smartir_device(self, device_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
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
        if entity_type not in ["climate", "fan", "media_player"]:
            return False, f"Invalid entity_type for SmartIR: {entity_type}"
        
        # Validate device_code is numeric
        try:
            int(device_data["device_code"])
        except (ValueError, TypeError):
            return False, "device_code must be a valid number"
        
        return True, None
