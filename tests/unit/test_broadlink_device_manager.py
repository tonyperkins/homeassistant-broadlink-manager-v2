"""
Unit tests for BroadlinkDeviceManager
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from broadlink_device_manager import BroadlinkDeviceManager


@pytest.fixture
def device_manager():
    """Create a BroadlinkDeviceManager instance"""
    return BroadlinkDeviceManager(
        ha_url="http://localhost:8123",
        ha_token="test_token"
    )


@pytest.mark.unit
class TestBroadlinkDeviceManagerInit:
    """Test initialization"""

    def test_init_stores_config(self):
        """Test that initialization stores HA URL and token"""
        manager = BroadlinkDeviceManager(
            ha_url="http://homeassistant.local:8123/",  # With trailing slash
            ha_token="my_token"
        )
        assert manager.ha_url == "http://homeassistant.local:8123"  # Trailing slash removed
        assert manager.ha_token == "my_token"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is removed from HA URL"""
        manager = BroadlinkDeviceManager(
            ha_url="http://localhost:8123///",
            ha_token="token"
        )
        assert manager.ha_url == "http://localhost:8123"


@pytest.mark.unit
class TestGetHeaders:
    """Test _get_headers method"""

    def test_get_headers_format(self, device_manager):
        """Test that headers are correctly formatted"""
        headers = device_manager._get_headers()
        
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"


@pytest.mark.unit
class TestDiscoverDevices:
    """Test discover_devices method"""

    @patch('broadlink_device_manager.broadlink.discover')
    def test_discover_devices_success(self, mock_discover, device_manager):
        """Test successful device discovery"""
        # Create mock device
        mock_device = Mock()
        mock_device.host = ("192.168.1.100", 80)
        mock_device.mac = bytes.fromhex("aabbccddeeff")
        mock_device.devtype = 0x2787
        mock_device.model = "RM4 Pro"
        mock_device.manufacturer = "Broadlink"
        
        mock_discover.return_value = [mock_device]
        
        devices = device_manager.discover_devices(timeout=5)
        
        assert len(devices) == 1
        assert devices[0]["host"] == "192.168.1.100"
        assert devices[0]["port"] == 80
        assert devices[0]["mac"] == "aa:bb:cc:dd:ee:ff"
        assert devices[0]["type"] == 0x2787
        assert devices[0]["type_hex"] == "0x2787"
        assert devices[0]["model"] == "RM4 Pro"
        assert devices[0]["manufacturer"] == "Broadlink"
        
        mock_discover.assert_called_once_with(timeout=5)

    @patch('broadlink_device_manager.broadlink.discover')
    def test_discover_devices_fallback_to_type(self, mock_discover, device_manager):
        """Test device discovery when devtype is not available"""
        # Create mock device without devtype
        mock_device = Mock()
        mock_device.host = ("192.168.1.100", 80)
        mock_device.mac = bytes.fromhex("aabbccddeeff")
        mock_device.devtype = None
        mock_device.type = 0x2787  # Fallback to type
        mock_device.model = "RM4 Pro"
        
        # Remove devtype attribute
        del mock_device.devtype
        
        mock_discover.return_value = [mock_device]
        
        devices = device_manager.discover_devices()
        
        assert len(devices) == 1
        assert devices[0]["type"] == 0x2787

    @patch('broadlink_device_manager.broadlink.discover')
    def test_discover_devices_skips_invalid_type(self, mock_discover, device_manager):
        """Test that devices with invalid type are skipped"""
        # Create mock device with invalid type
        mock_device = Mock()
        mock_device.host = ("192.168.1.100", 80)
        mock_device.mac = bytes.fromhex("aabbccddeeff")
        mock_device.devtype = "invalid"  # Not an int
        mock_device.type = "also_invalid"
        mock_device.model = "RM4 Pro"
        
        mock_discover.return_value = [mock_device]
        
        devices = device_manager.discover_devices()
        
        assert len(devices) == 0  # Device should be skipped

    @patch('broadlink_device_manager.broadlink.discover')
    def test_discover_devices_empty_result(self, mock_discover, device_manager):
        """Test discovery with no devices found"""
        mock_discover.return_value = []
        
        devices = device_manager.discover_devices()
        
        assert devices == []

    @patch('broadlink_device_manager.broadlink.discover')
    def test_discover_devices_exception_handling(self, mock_discover, device_manager):
        """Test that exceptions during discovery are handled"""
        mock_discover.side_effect = Exception("Network error")
        
        devices = device_manager.discover_devices()
        
        assert devices == []

    @patch('broadlink_device_manager.broadlink.discover')
    def test_discover_devices_multiple_devices(self, mock_discover, device_manager):
        """Test discovery of multiple devices"""
        # Create multiple mock devices
        mock_device1 = Mock()
        mock_device1.host = ("192.168.1.100", 80)
        mock_device1.mac = bytes.fromhex("aabbccddeeff")
        mock_device1.devtype = 0x2787
        mock_device1.model = "RM4 Pro"
        mock_device1.manufacturer = "Broadlink"
        
        mock_device2 = Mock()
        mock_device2.host = ("192.168.1.101", 80)
        mock_device2.mac = bytes.fromhex("112233445566")
        mock_device2.devtype = 0x2712
        mock_device2.model = "RM Mini 3"
        mock_device2.manufacturer = "Broadlink"
        
        mock_discover.return_value = [mock_device1, mock_device2]
        
        devices = device_manager.discover_devices()
        
        assert len(devices) == 2
        assert devices[0]["host"] == "192.168.1.100"
        assert devices[1]["host"] == "192.168.1.101"


@pytest.mark.unit
class TestGetHAEntityInfo:
    """Test get_ha_entity_info method"""

    @patch('broadlink_device_manager.requests.get')
    def test_get_entity_info_success(self, mock_get, device_manager):
        """Test successful entity info retrieval"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "entity_id": "remote.living_room_rm4",
            "state": "idle",
            "attributes": {
                "friendly_name": "Living Room RM4",
                "host": "192.168.1.100",
                "mac": "aa:bb:cc:dd:ee:ff",
                "type": 0x2787
            }
        }
        mock_get.return_value = mock_response
        
        entity_info = device_manager.get_ha_entity_info("remote.living_room_rm4")
        
        assert entity_info is not None
        assert entity_info["entity_id"] == "remote.living_room_rm4"
        assert entity_info["state"] == "idle"
        assert "host" in entity_info["attributes"]
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "http://localhost:8123/api/states/remote.living_room_rm4"
        assert kwargs["headers"]["Authorization"] == "Bearer test_token"

    @patch('broadlink_device_manager.requests.get')
    def test_get_entity_info_not_found(self, mock_get, device_manager):
        """Test entity not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        entity_info = device_manager.get_ha_entity_info("remote.nonexistent")
        
        assert entity_info is None

    @patch('broadlink_device_manager.requests.get')
    def test_get_entity_info_exception(self, mock_get, device_manager):
        """Test exception handling"""
        mock_get.side_effect = Exception("Connection error")
        
        entity_info = device_manager.get_ha_entity_info("remote.test")
        
        assert entity_info is None


@pytest.mark.unit
class TestGetDeviceConnectionInfo:
    """Test get_device_connection_info method"""

    @patch.object(BroadlinkDeviceManager, 'get_ha_entity_info')
    def test_get_connection_info_from_attributes(self, mock_get_entity, device_manager):
        """Test getting connection info from entity attributes"""
        mock_get_entity.return_value = {
            "entity_id": "remote.living_room_rm4",
            "state": "idle",
            "attributes": {
                "friendly_name": "Living Room RM4",
                "host": "192.168.1.100",
                "mac": "aa:bb:cc:dd:ee:ff",
                "type": 0x2787,
                "model": "RM4 Pro"
            }
        }
        
        conn_info = device_manager.get_device_connection_info("remote.living_room_rm4")
        
        assert conn_info is not None
        assert conn_info["host"] == "192.168.1.100"
        assert conn_info["mac"] == "aa:bb:cc:dd:ee:ff"
        assert conn_info["type"] == 0x2787
        assert conn_info["model"] == "RM4 Pro"
        assert conn_info["friendly_name"] == "Living Room RM4"

    @patch.object(BroadlinkDeviceManager, 'get_ha_entity_info')
    @patch.object(BroadlinkDeviceManager, 'discover_devices')
    def test_get_connection_info_from_discovery(self, mock_discover, mock_get_entity, device_manager):
        """Test getting connection info from network discovery when not in attributes"""
        mock_get_entity.return_value = {
            "entity_id": "remote.living_room_rm4",
            "state": "idle",
            "attributes": {
                "friendly_name": "Living Room RM4"
                # Missing host, mac, type
            }
        }
        
        mock_discover.return_value = [{
            "host": "192.168.1.100",
            "port": 80,
            "mac": "aa:bb:cc:dd:ee:ff",
            "type": 0x2787,
            "type_hex": "0x2787",
            "model": "RM4 Pro"
        }]
        
        conn_info = device_manager.get_device_connection_info("remote.living_room_rm4")
        
        assert conn_info is not None
        assert conn_info["host"] == "192.168.1.100"
        mock_discover.assert_called_once_with(timeout=5)

    @patch.object(BroadlinkDeviceManager, 'get_ha_entity_info')
    def test_get_connection_info_invalid_mac(self, mock_get_entity, device_manager):
        """Test handling of invalid MAC address"""
        mock_get_entity.return_value = {
            "entity_id": "remote.test",
            "attributes": {
                "host": "192.168.1.100",
                "mac": "invalid_mac",
                "type": 0x2787
            }
        }
        
        conn_info = device_manager.get_device_connection_info("remote.test")
        
        assert conn_info is None

    @patch.object(BroadlinkDeviceManager, 'get_ha_entity_info')
    def test_get_connection_info_hex_device_type(self, mock_get_entity, device_manager):
        """Test handling of hex string device type"""
        mock_get_entity.return_value = {
            "entity_id": "remote.test",
            "attributes": {
                "host": "192.168.1.100",
                "mac": "aa:bb:cc:dd:ee:ff",
                "type": "0x2787"  # Hex string
            }
        }
        
        conn_info = device_manager.get_device_connection_info("remote.test")
        
        assert conn_info is not None
        assert conn_info["type"] == 0x2787


@pytest.mark.unit
class TestMatchDiscoveredToHAEntity:
    """Test match_discovered_to_ha_entity method"""

    @patch.object(BroadlinkDeviceManager, 'get_device_connection_info')
    def test_match_by_mac_address(self, mock_get_conn_info, device_manager):
        """Test matching device by MAC address"""
        mock_get_conn_info.return_value = {
            "host": "192.168.1.100",
            "mac": "aa:bb:cc:dd:ee:ff",
            "type": 0x2787
        }
        
        discovered_devices = [
            {
                "host": "192.168.1.100",
                "mac": "aa:bb:cc:dd:ee:ff",
                "type": 0x2787,
                "model": "RM4 Pro"
            },
            {
                "host": "192.168.1.101",
                "mac": "11:22:33:44:55:66",
                "type": 0x2712,
                "model": "RM Mini 3"
            }
        ]
        
        matched = device_manager.match_discovered_to_ha_entity(
            "remote.living_room_rm4",
            discovered_devices
        )
        
        assert matched is not None
        assert matched["host"] == "192.168.1.100"
        assert matched["model"] == "RM4 Pro"

    @patch.object(BroadlinkDeviceManager, 'get_device_connection_info')
    def test_match_no_match_found(self, mock_get_conn_info, device_manager):
        """Test when no matching device is found"""
        mock_get_conn_info.return_value = {
            "host": "192.168.1.100",
            "mac": "aa:bb:cc:dd:ee:ff",
            "type": 0x2787
        }
        
        discovered_devices = [
            {
                "host": "192.168.1.101",
                "mac": "11:22:33:44:55:66",  # Different MAC
                "type": 0x2712,
                "model": "RM Mini 3"
            }
        ]
        
        matched = device_manager.match_discovered_to_ha_entity(
            "remote.living_room_rm4",
            discovered_devices
        )
        
        assert matched is None

    @patch.object(BroadlinkDeviceManager, 'get_device_connection_info')
    def test_match_entity_not_found(self, mock_get_conn_info, device_manager):
        """Test when entity info cannot be retrieved"""
        mock_get_conn_info.return_value = None
        
        discovered_devices = [
            {
                "host": "192.168.1.100",
                "mac": "aa:bb:cc:dd:ee:ff",
                "type": 0x2787,
                "model": "RM4 Pro"
            }
        ]
        
        matched = device_manager.match_discovered_to_ha_entity(
            "remote.nonexistent",
            discovered_devices
        )
        
        assert matched is None
