"""Helper functions for the Broadlink integration."""

from base64 import b64decode

from homeassistant import config_entries
from homeassistant.const import CONF_HOST
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN


def data_packet(value):
    """Decode a base64-encoded data packet for a Broadlink remote.

    Args:
        value: The base64-encoded string.

    Returns:
        The decoded data as bytes.
    """
    value = cv.string(value)
    extra = len(value) % 4
    if extra > 0:
        value = value + ("=" * (4 - extra))
    return b64decode(value)


def mac_address(mac):
    """Validate and convert a MAC address string to bytes.

    Args:
        mac: The MAC address string (e.g., 'AA:BB:CC:DD:EE:FF' or 'AABBCCDDEEFF').

    Returns:
        The MAC address as bytes.

    Raises:
        ValueError: If the MAC address is invalid.
    """
    mac = cv.string(mac)
    if len(mac) == 17:
        mac = "".join(mac[i : i + 2] for i in range(0, 17, 3))
    elif len(mac) == 14:
        mac = "".join(mac[i : i + 4] for i in range(0, 14, 5))
    elif len(mac) != 12:
        raise ValueError("Invalid MAC address")
    return bytes.fromhex(mac)


def format_mac(mac):
    """Format a MAC address from bytes to a colon-separated string.

    Args:
        mac: The MAC address in bytes.

    Returns:
        The formatted MAC address string.
    """
    return ":".join([format(octet, "02x") for octet in mac])


def import_device(hass, host):
    """Create a config flow to import a device from configuration.yaml.

    This function is used to migrate devices from YAML configuration to UI-based config entries.

    Args:
        hass: The Home Assistant instance.
        host: The IP address or hostname of the device.
    """
    configured_hosts = {
        entry.data.get(CONF_HOST) for entry in hass.config_entries.async_entries(DOMAIN)
    }

    if host not in configured_hosts:
        task = hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={CONF_HOST: host},
        )
        hass.async_create_task(task)
