"""
Broadlink device connection management

Handles device discovery, connection info retrieval, and mapping between
Home Assistant entities and physical Broadlink devices.
"""

import broadlink
import logging
import requests
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class BroadlinkDeviceManager:
    """
    Manage Broadlink device connections and discovery
    """

    def __init__(self, ha_url: str, ha_token: str):
        """
        Initialize device manager

        Args:
            ha_url: Home Assistant URL (e.g., "http://homeassistant.local:8123")
            ha_token: Long-lived access token
        """
        self.ha_url = ha_url.rstrip("/")
        self.ha_token = ha_token

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
            devices = broadlink.discover(timeout=timeout)

            device_list = []
            for device in devices:
                device_info = {
                    "host": device.host[0],
                    "port": device.host[1],
                    "mac": device.mac.hex(":"),
                    "mac_bytes": device.mac,
                    "type": device.type,
                    "type_hex": hex(device.type),
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

        except Exception as e:
            logger.error(f"Error discovering devices: {e}")
            return []

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
        Get device connection info from HA entity

        Extracts host, MAC, and device type from entity attributes
        for use with python-broadlink.

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

        # Extract connection info
        host = attributes.get("host")
        mac_str = attributes.get("mac")
        device_type = attributes.get("type")

        if not all([host, mac_str, device_type]):
            logger.error(f"Missing connection info in entity attributes")
            logger.debug(f"host={host}, mac={mac_str}, type={device_type}")
            return None

        # Convert MAC string to bytes
        try:
            mac_bytes = bytes.fromhex(mac_str.replace(":", ""))
        except Exception as e:
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
            except Exception as e:
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
