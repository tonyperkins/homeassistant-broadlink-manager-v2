"""Provides a wrapper class for Broadlink devices to manage their state and interactions within Home Assistant."""

from contextlib import suppress
from functools import partial
import logging

import broadlink as blk
from broadlink.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BroadlinkException,
    ConnectionClosedError,
    NetworkTimeoutError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_MAC,
    CONF_NAME,
    CONF_TIMEOUT,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr

from .const import DEFAULT_PORT, DOMAIN, DOMAINS_AND_TYPES
from .updater import BroadlinkUpdateManager, get_update_manager

_LOGGER = logging.getLogger(__name__)


def get_domains(device_type: str) -> set[Platform]:
    """Return the Home Assistant platforms (domains) that a given device type belongs to."""
    return {d for d, t in DOMAINS_AND_TYPES.items() if device_type in t}


class BroadlinkDevice[_ApiT: blk.Device = blk.Device]:
    """Manages a Broadlink device, handling setup, updates, and communication."""

    api: _ApiT

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize the Broadlink device wrapper.

        Args:
            hass: The Home Assistant instance.
            config: The config entry for the device.
        """
        self.hass = hass
        self.config = config
        self.update_manager: BroadlinkUpdateManager[_ApiT] | None = None
        self.fw_version: int | None = None
        self.authorized: bool | None = None
        self.reset_jobs: list[CALLBACK_TYPE] = []

    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self.config.title

    @property
    def unique_id(self) -> str | None:
        """Return the unique id of the device."""
        return self.config.unique_id

    @property
    def mac_address(self) -> str:
        """Return the mac address of the device."""
        return self.config.data[CONF_MAC]

    @property
    def available(self) -> bool | None:
        """Return True if the device is available."""
        if self.update_manager is None:
            return False
        return self.update_manager.available

    @staticmethod
    async def async_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle config entry updates.

        This is called when the config entry is updated (e.g., a new name is set).
        It reloads the config entry to apply the changes.

        Args:
            hass: The Home Assistant instance.
            entry: The updated config entry.
        """
        device_registry = dr.async_get(hass)
        assert entry.unique_id
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, entry.unique_id)}
        )
        assert device_entry
        device_registry.async_update_device(device_entry.id, name=entry.title)
        await hass.config_entries.async_reload(entry.entry_id)

    def _get_firmware_version(self) -> int | None:
        """Get the firmware version of the device."""
        self.api.auth()
        with suppress(BroadlinkException, OSError):
            return self.api.get_fwversion()
        return None

    async def async_setup(self) -> bool:
        """Set up the Broadlink device.

        This method creates the device API object, authenticates with the device,
        retrieves the firmware version, and sets up the update manager.

        Returns:
            True if setup is successful, False otherwise.
        """
        config = self.config

        api = blk.gendevice(
            config.data[CONF_TYPE],
            (config.data[CONF_HOST], DEFAULT_PORT),
            bytes.fromhex(config.data[CONF_MAC]),
            name=config.title,
        )
        api.timeout = config.data[CONF_TIMEOUT]
        self.api = api

        try:
            self.fw_version = await self.hass.async_add_executor_job(
                self._get_firmware_version
            )

        except AuthenticationError:
            await self._async_handle_auth_error()
            return False

        except (NetworkTimeoutError, OSError) as err:
            raise ConfigEntryNotReady from err

        except BroadlinkException as err:
            _LOGGER.error(
                "Failed to authenticate to the device at %s: %s", api.host[0], err
            )
            return False

        self.authorized = True

        update_manager = get_update_manager(self)
        coordinator = update_manager.coordinator
        await coordinator.async_config_entry_first_refresh()

        self.update_manager = update_manager
        self.hass.data[DOMAIN].devices[config.entry_id] = self
        self.reset_jobs.append(config.add_update_listener(self.async_update))

        # THIS IS THE PART THAT IS NOW REMOVED.
        # Platform setup is now handled centrally in __init__.py.

        return True

    async def async_unload(self) -> bool:
        """Unload the device and clean up resources.

        Returns:
            True, as the core unloading is handled by __init__.py.
        """
        if self.update_manager is None:
            return True

        while self.reset_jobs:
            self.reset_jobs.pop()()

        # Unloading is also handled by __init__.py now, so we just return True.
        return True

    async def async_auth(self) -> bool:
        """Authenticate with the device.

        Returns:
            True if authentication is successful, False otherwise.
        """
        try:
            await self.hass.async_add_executor_job(self.api.auth)
        except (BroadlinkException, OSError) as err:
            _LOGGER.debug(
                "Failed to authenticate to the device at %s: %s", self.api.host[0], err
            )
            if isinstance(err, AuthenticationError):
                await self._async_handle_auth_error()
            return False
        return True

    async def async_request(self, function, *args, **kwargs):
        """Send a request to the device and handle re-authentication if needed."""
        request = partial(function, *args, **kwargs)
        try:
            return await self.hass.async_add_executor_job(request)
        except (AuthorizationError, ConnectionClosedError):
            if not await self.async_auth():
                raise
            return await self.hass.async_add_executor_job(request)

    async def _async_handle_auth_error(self) -> None:
        """Handle an authentication error by starting the reauth flow."""
        if self.authorized is False:
            return

        self.authorized = False

        _LOGGER.error(
            (
                "%s (%s at %s) is locked. Click Configuration in the sidebar, "
                "click Integrations, click Configure on the device and follow "
                "the instructions to unlock it"
            ),
            self.name,
            self.api.model,
            self.api.host[0],
        )

        self.config.async_start_reauth(self.hass, data={CONF_NAME: self.name})