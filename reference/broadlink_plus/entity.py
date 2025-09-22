"""Base classes for Broadlink entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .device import BroadlinkDevice


class BroadlinkEntity(Entity):
    """A base class for Broadlink entities."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, device: BroadlinkDevice) -> None:
        """Initialize the entity.

        Args:
            device: The Broadlink device.
        """
        self._device = device
        self._attr_device_info = DeviceInfo(
            connections={("mac", device.mac_address)},
            identifiers={(DOMAIN, device.unique_id)},
            manufacturer=device.api.manufacturer,
            model=device.api.model,
            name=device.name,
            sw_version=device.fw_version,
        )

    @property
    def available(self) -> bool:
        """Return True if the entity is available."""
        return self._device.available