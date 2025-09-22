"""Support for the Broadlink device time entity."""

from __future__ import annotations

from datetime import time
from typing import Any

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from . import BroadlinkDevice
from .const import DOMAIN
from .entity import BroadlinkEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Broadlink time entity from a config entry."""
    device = hass.data[DOMAIN].devices[config_entry.entry_id]
    async_add_entities([BroadlinkTime(device)])


class BroadlinkTime(BroadlinkEntity, TimeEntity):
    """Representation of a Broadlink device's internal clock."""

    _attr_has_entity_name = True
    _attr_native_value: time | None = None

    def __init__(self, device: BroadlinkDevice) -> None:
        """Initialize the time entity.

        Args:
            device: The Broadlink device object.
        """
        super().__init__(device)

        self._attr_unique_id = f"{device.unique_id}-device_time"

    def _update_state(self, data: dict[str, Any]) -> None:
        """Update the state of the entity from device data.

        Args:
            data: The state data from the device.
        """
        if data is None or "hour" not in data or "min" not in data or "sec" not in data:
            self._attr_native_value = None
        else:
            self._attr_native_value = time(
                hour=data["hour"],
                minute=data["min"],
                second=data["sec"],
                tzinfo=dt_util.get_default_time_zone(),
            )

    async def async_set_value(self, value: time) -> None:
        """Set the time on the device.

        Args:
            value: The new time to set.
        """
        await self._device.async_request(
            self._device.api.set_time,
            hour=value.hour,
            minute=value.minute,
            second=value.second,
            day=self._coordinator.data["dayofweek"],
        )
        self._attr_native_value = value
        self.async_write_ha_state()
