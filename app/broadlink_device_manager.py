"""
Broadlink device connection management

Handles device discovery, connection info retrieval, and mapping between
Home Assistant entities and physical Broadlink devices.
"""

import broadlink
import json
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BroadlinkDeviceManager:
    """
    Manage Broadlink device connections and discovery
    """

    def __init__(self, ha_url: str, ha_token: str, config_path: str = "/config"):
        """
        Initialize device manager

        Args:
            ha_url: Home Assistant URL (e.g., "http://homeassistant.local:8123")
            ha_token: Long-lived access token
            config_path: Path to HA config directory (e.g., "/config" or "\\\\192.168.1.1\\config")
        """
        self.ha_url = ha_url.rstrip("/")
        self.ha_token = ha_token
        self.config_path = config_path

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for HA API requests"""
        return {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json",
        }

    def discover_devices(self, timeout: int = 5) -> List[Dict]:
        """
        Discover Broadlink devices on the network

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered devices with connection info
        """
        logger.info(f"Discovering Broadlink devices (timeout: {timeout}s)")

        try:
            # broadlink.discover() expects timeout in seconds as a number
            # It will broadcast and wait for responses
            logger.debug(f"Calling broadlink.discover with timeout={timeout}")
            devices = broadlink.discover(timeout=timeout)

            device_list = []
            for device in devices:
                # Get numeric device type - try devtype first, then type
                device_type = None
                if hasattr(device, "devtype"):
                    device_type = device.devtype
                elif hasattr(device, "type") and isinstance(device.type, int):
                    device_type = device.type

                # If we still don't have a numeric type, log warning and skip
                if device_type is None or not isinstance(device_type, int):
                    logger.warning(
                        f"Could not get numeric device type for "
                        f"{device.model if hasattr(device, 'model') else 'unknown device'}"
                    )
                    logger.debug(
                        f"device.type = {device.type if hasattr(device, 'type') else 'N/A'}, "
                        f"device.devtype = {device.devtype if hasattr(device, 'devtype') else 'N/A'}"
                    )
                    continue

                device_info = {
                    "host": device.host[0],
                    "port": device.host[1],
                    "mac": device.mac.hex(":"),
                    "mac_bytes": device.mac,
                    "type": device_type,
                    "type_hex": hex(device_type),
                    "model": device.model if hasattr(device, "model") else "Unknown",
                    "manufacturer": (
                        device.manufacturer
                        if hasattr(device, "manufacturer")
                        else "Broadlink"
                    ),
                }
                device_list.append(device_info)
                logger.debug(
                    f"Discovered: {device_info['model']} at {device_info['host']}"
                )

            logger.info(f"Discovered {len(device_list)} device(s)")
            return device_list

        except Exception:
            logger.error("Error discovering devices", exc_info=True)
            return []

    def get_ha_config_entry(self, entity_id: str) -> Optional[Dict]:
        """
        Get Broadlink config entry from HA storage

        Args:
            entity_id: Entity ID (e.g., "remote.living_room_rm4_pro")

        Returns:
            Config entry dict with host, mac, type, or None if error
        """
        try:
            # Try multiple possible file locations using the configured config path
            import os
            config_files = [
                os.path.join(self.config_path, ".storage", "core.config_entries"),
                os.path.join(self.config_path, "core.config_entries"),  # Fallback location
            ]

            entries = None
            for config_file in config_files:
                try:
                    with open(config_file, "r") as f:
                        config_data = json.load(f)
                    entries = config_data.get("data", {}).get("entries", [])
                    logger.debug(
                        f"Successfully read {len(entries)} entries from {config_file}"
                    )
                    break
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.debug(f"Could not read {config_file}: {e}")
                    continue

            if not entries:
                logger.warning("Could not read config entries from any location")
                return None

            # Extract device name from entity_id
            device_name = entity_id.replace("remote.", "").replace("_", " ").title()
            entity_parts = entity_id.lower().replace("remote.", "").split("_")

            # Look for matching Broadlink config entry with multiple strategies
            for entry in entries:
                if entry.get("domain") != "broadlink":
                    continue

                entry_title = entry.get("title", "").lower()
                entry_data = entry.get("data", {})

                # Strategy 1: Exact match on normalized name
                if device_name.lower() == entry_title:
                    logger.info(f"Found exact match: {entry.get('title')}")
                    return self._extract_config_data(entry, entry_data)

                # Strategy 2: Check if all entity parts are in the title
                if all(part in entry_title for part in entity_parts if part):
                    logger.info(f"Found partial match: {entry.get('title')}")
                    return self._extract_config_data(entry, entry_data)

                # Strategy 3: Check for common patterns
                if (
                    "rm4" in entry_title
                    and "office" in entry_title
                    and "tony" in entry_title
                ) or (
                    "rm4" in entry_title
                    and "bedroom" in entry_title
                    and "master" in entry_title
                ):
                    logger.info(f"Found pattern match: {entry.get('title')}")
                    return self._extract_config_data(entry, entry_data)

            logger.warning(f"No matching Broadlink config entry found for {entity_id}")
            return None

        except Exception as e:
            logger.error(f"Error reading config entries: {e}")
            return None

    def _extract_config_data(self, entry: Dict, entry_data: Dict) -> Optional[Dict]:
        """Extract connection data from config entry with validation"""
        try:
            # Validate required fields
            if not all(key in entry_data for key in ["host", "mac", "type"]):
                logger.warning(
                    f"Config entry missing required fields: {list(entry_data.keys())}"
                )
                return None

            # Validate MAC format
            mac = entry_data["mac"]
            if isinstance(mac, str):
                # Remove colons if present
                mac = mac.replace(":", "")
                # Validate hex format
                try:
                    int(mac, 16)
                except ValueError:
                    logger.warning(f"Invalid MAC format: {mac}")
                    return None

            # Validate type
            device_type = entry_data["type"]
            if isinstance(device_type, str):
                device_type = int(device_type)

            logger.info(f"Found config entry: {entry.get('title')}")
            logger.info(f"  Host: {entry_data['host']}")
            logger.info(f"  MAC: {mac}")
            logger.info(f"  Type: {device_type}")

            return {
                "host": entry_data["host"],
                "mac": mac,
                "type": device_type,
                "title": entry.get("title", "Unknown"),
            }

        except Exception as e:
            logger.error(f"Error extracting config data: {e}")
            return None

    def get_ha_device_info(self, entity_id: str) -> Optional[Dict]:
        """
        Get device information from HA device registry

        Args:
            entity_id: Entity ID (e.g., "remote.living_room_rm4_pro")

        Returns:
            Device info dict with MAC address in connections, or None if error
        """
        try:
            # First get the entity to find its device ID
            entity_url = f"{self.ha_url}/api/states/{entity_id}"
            entity_response = requests.get(
                entity_url, headers=self._get_headers(), timeout=10
            )

            if entity_response.status_code != 200:
                logger.error(
                    f"Failed to get entity: HTTP {entity_response.status_code}"
                )
                return None

            entity_data = entity_response.json()

            # Debug: Log what we got
            logger.debug(f"Entity data keys: {list(entity_data.keys())}")
            logger.debug(
                f"Entity attributes keys: {list(entity_data.get('attributes', {}).keys())}"
            )
            if entity_data.get("context"):
                logger.debug(
                    f"Entity context keys: {list(entity_data['context'].keys())}"
                )

            # Try multiple ways to get the device ID
            device_id = None

            # Method 1: Check attributes for device_id
            device_id = entity_data.get("attributes", {}).get("device_id")
            if device_id:
                logger.debug(f"Found device_id in attributes: {device_id}")

            # Method 2: Check context if available
            if not device_id and entity_data.get("context"):
                device_id = entity_data["context"].get("device_id")
                if device_id:
                    logger.debug(f"Found device_id in context: {device_id}")

            # Method 3: Use the entity registry to find the device
            if not device_id:
                # Get entity registry entry - HA uses GET for single entity
                entity_registry_url = (
                    f"{self.ha_url}/api/config/entity_registry/{entity_id}"
                )
                logger.info(f"Trying entity registry: {entity_registry_url}")
                registry_response = requests.get(
                    entity_registry_url, headers=self._get_headers(), timeout=10
                )

                if registry_response.status_code == 200:
                    registry_data = registry_response.json()
                    logger.info(f"Registry data keys: {list(registry_data.keys())}")
                    device_id = registry_data.get("device_id")
                    if device_id:
                        logger.info(f"Found device_id in registry: {device_id}")
                else:
                    logger.info(f"Registry response: {registry_response.status_code}")
                    # Try the list endpoint as fallback
                    list_url = f"{self.ha_url}/api/config/entity_registry/list"
                    list_response = requests.get(
                        list_url, headers=self._get_headers(), timeout=10
                    )
                    if list_response.status_code == 200:
                        entities = list_response.json()
                        for entity in entities:
                            if entity.get("entity_id") == entity_id:
                                device_id = entity.get("device_id")
                                if device_id:
                                    logger.info(
                                        f"Found device_id via list: {device_id}"
                                    )
                                break

            if not device_id:
                logger.warning(f"No device_id found for entity {entity_id}")
                logger.info(f"Entity data keys: {list(entity_data.keys())}")
                logger.info(
                    f"Entity attributes keys: {list(entity_data.get('attributes', {}).keys())}"
                )
                if entity_data.get("context"):
                    logger.info(
                        f"Entity context keys: {list(entity_data['context'].keys())}"
                    )
                return None

            # Get device info from device registry
            device_url = f"{self.ha_url}/api/devices/{device_id}"
            device_response = requests.get(
                device_url, headers=self._get_headers(), timeout=10
            )

            if device_response.status_code != 200:
                logger.error(
                    f"Failed to get device: HTTP {device_response.status_code}"
                )
                return None

            return device_response.json()

        except Exception as e:
            logger.error(f"Error getting device info: {e}")
            return None

    def get_ha_entity_info(self, entity_id: str) -> Optional[Dict]:
        """
        Get entity information from Home Assistant

        Args:
            entity_id: Entity ID (e.g., "remote.living_room_rm4_pro")

        Returns:
            Entity info dict with state and attributes, or None if error
        """
        try:
            url = f"{self.ha_url}/api/states/{entity_id}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get entity info: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting entity info: {e}")
            return None

    def get_device_connection_info(self, entity_id: str) -> Optional[Dict]:
        """
        Get device connection info from HA entity or network discovery

        Tries to extract from entity attributes first, then falls back to
        network discovery to find the device.

        Args:
            entity_id: Entity ID (e.g., "remote.living_room_rm4_pro")

        Returns:
            Connection info dict, or None if error
        """
        logger.info(f"Getting connection info for {entity_id}")

        entity = self.get_ha_entity_info(entity_id)
        if not entity:
            return None

        attributes = entity.get("attributes", {})

        # Try to extract connection info from attributes
        host = attributes.get("host")
        mac_str = attributes.get("mac")
        device_type = attributes.get("type")

        logger.info(
            f"Entity attributes check: host={host}, mac={mac_str}, type={device_type}"
        )

        # If not in attributes, try config entry
        if not all([host, mac_str, device_type]):
            logger.info(
                f"Connection info not in entity attributes, trying config entry"
            )

            # Try to get connection info from HA config entry
            config_entry = self.get_ha_config_entry(entity_id)

            if config_entry:
                host = config_entry.get("host")
                mac_str = config_entry.get("mac")
                device_type = config_entry.get("type")
                logger.info(
                    f"Found connection info in config entry: {config_entry.get('title')}"
                )
            else:
                logger.warning(
                    f"No config entry found and no connection info in attributes"
                )
                return None

        # Convert MAC string to bytes
        try:
            mac_bytes = bytes.fromhex(mac_str.replace(":", ""))
        except Exception:
            logger.error(f"Invalid MAC address format: {mac_str}")
            return None

        # Convert device type to int if it's a string
        if isinstance(device_type, str):
            try:
                # Handle hex strings like "0x2787"
                device_type = (
                    int(device_type, 16)
                    if device_type.startswith("0x")
                    else int(device_type)
                )
            except Exception:
                logger.error(f"Invalid device type format: {device_type}")
                return None

        connection_info = {
            "host": host,
            "mac": mac_str,
            "mac_bytes": mac_bytes,
            "type": device_type,
            "type_hex": hex(device_type),
            "model": attributes.get("model", "Unknown"),
            "friendly_name": attributes.get("friendly_name", entity_id),
        }

        logger.info(f"Connection info: {connection_info['model']} at {host}")
        return connection_info

    def match_discovered_to_ha_entity(
        self, entity_id: str, discovered_devices: List[Dict]
    ) -> Optional[Dict]:
        """
        Match a discovered device to an HA entity by MAC address

        Args:
            entity_id: HA entity ID
            discovered_devices: List from discover_devices()

        Returns:
            Matched device dict, or None if no match
        """
        entity_info = self.get_device_connection_info(entity_id)
        if not entity_info:
            return None

        entity_mac = entity_info["mac"].replace(":", "").lower()

        for device in discovered_devices:
            device_mac = device["mac"].replace(":", "").lower()
            if device_mac == entity_mac:
                logger.info(
                    f"Matched {entity_id} to discovered device at {device['host']}"
                )
                return device

        logger.warning(f"No discovered device matches {entity_id}")
        return None
