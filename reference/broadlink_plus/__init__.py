"""The Broadlink Plus integration.

This file is responsible for setting up the Broadlink integration, managing device
configurations, and handling the lifecycle of the integration.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import async_extract_entity_ids
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.remote import DOMAIN as RM_DOMAIN

from .const import DOMAIN
from .device import BroadlinkDevice
from .heartbeat import BroadlinkHeartbeat

_LOGGER = logging.getLogger(__name__)

# Platforms to support in this integration.
PLATFORMS: list[Platform] = [Platform.REMOTE]
# Configuration schema for the integration.
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

@dataclass
class BroadlinkData:
    """Manages shared data for the Broadlink integration."""
    devices: dict[str, BroadlinkDevice] = field(default_factory=dict)
    platforms: dict = field(default_factory=dict)
    heartbeat: BroadlinkHeartbeat | None = None

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Broadlink integration.

    Initializes the integration's data structure.

    Args:
        hass: The Home Assistant instance.
        config: The configuration data.

    Returns:
        True if setup is successful.
    """
    hass.data[DOMAIN] = BroadlinkData()
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Broadlink device from a config entry.

    Initializes a Broadlink device, sets up a heartbeat for monitoring, and
    forwards the setup to the relevant platforms.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.

    Returns:
        True if the setup is successful, False otherwise.
    """
    data: BroadlinkData = hass.data[DOMAIN]
    device = BroadlinkDevice(hass, entry)
    if not await device.async_setup():
        return False

    if data.heartbeat is None:
        data.heartbeat = BroadlinkHeartbeat(hass)
        hass.async_create_task(data.heartbeat.async_setup())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register the service if it doesn't exist.
    if not hass.services.has_service(DOMAIN, "list_commands"):
        hass.services.async_register(
            DOMAIN, "list_commands", async_list_commands_service, supports_response="only"
        )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    Unloads the device from the platforms, removes it from the shared data,
    and stops the heartbeat if no devices are left.

    Args:
        hass: The Home Assistant instance.
        entry: The config entry.

    Returns:
        True if the unload is successful, False otherwise.
    """
    if not await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        return False
    data: BroadlinkData = hass.data[DOMAIN]
    data.devices.pop(entry.entry_id)
    if data.heartbeat and not data.devices:
        await data.heartbeat.async_unload()
        data.heartbeat = None
    return True

async def async_list_commands_service(call: ServiceCall) -> ServiceResponse:
    """Service handler to list commands for a remote entity."""
    hass = call.hass
    entity_ids = await async_extract_entity_ids(hass, call)
    if not entity_ids:
        raise ValueError("No target entity specified for list_commands service call.")

    # We only handle one entity at a time for this service.
    target_entity_id = next(iter(entity_ids))

    remote_component = hass.data.get(RM_DOMAIN)
    if not remote_component:
        raise ValueError("Remote component not loaded")

    target_remote = remote_component.get_entity(target_entity_id)
    if not target_remote or not hasattr(target_remote, 'list_commands'):
        raise ValueError(f"Entity '{target_entity_id}' not found or does not support list_commands")

    commands = await target_remote.list_commands()
    _LOGGER.debug("Final commands being returned by API: %s", commands)

    return commands