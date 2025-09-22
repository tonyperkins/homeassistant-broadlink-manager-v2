"""Support for Broadlink remotes, including IR/RF learning and sending commands."""
from __future__ import annotations
import asyncio
from base64 import b64encode
from collections import defaultdict
from collections.abc import Iterable
from datetime import timedelta
from itertools import product
import logging
from typing import Any

from broadlink.exceptions import (
    AuthorizationError,
    BroadlinkException,
    NetworkTimeoutError,
    ReadError,
    StorageError,
)
import voluptuous as vol

from homeassistant.components import persistent_notification
from homeassistant.components.remote import (
    ATTR_ALTERNATIVE,
    ATTR_COMMAND_TYPE,
    ATTR_DELAY_SECS,
    ATTR_DEVICE,
    ATTR_NUM_REPEATS,
    DEFAULT_DELAY_SECS,
    DOMAIN as RM_DOMAIN,
    SERVICE_DELETE_COMMAND,
    SERVICE_LEARN_COMMAND,
    SERVICE_SEND_COMMAND,
    RemoteEntity,
    RemoteEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_COMMAND, STATE_OFF
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .device import BroadlinkDevice
from .entity import BroadlinkEntity
from .helpers import data_packet

_LOGGER = logging.getLogger(__name__)

LEARNING_TIMEOUT = timedelta(seconds=30)
COMMAND_TYPE_IR = "ir"
COMMAND_TYPE_RF = "rf"
COMMAND_TYPES = [COMMAND_TYPE_IR, COMMAND_TYPE_RF]
CODE_STORAGE_VERSION = 1
FLAG_STORAGE_VERSION = 1
CODE_SAVE_DELAY = 15
FLAG_SAVE_DELAY = 15

COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_COMMAND): vol.All(
            cv.ensure_list, [vol.All(cv.string, vol.Length(min=1))], vol.Length(min=1)
        ),
    },
    extra=vol.ALLOW_EXTRA,
)
SERVICE_SEND_SCHEMA = COMMAND_SCHEMA.extend(
    {
        vol.Optional(ATTR_DEVICE): vol.All(cv.string, vol.Length(min=1)),
        vol.Optional(ATTR_DELAY_SECS, default=DEFAULT_DELAY_SECS): vol.Coerce(float),
    }
)
SERVICE_LEARN_SCHEMA = COMMAND_SCHEMA.extend(
    {
        vol.Required(ATTR_DEVICE): vol.All(cv.string, vol.Length(min=1)),
        vol.Optional(ATTR_COMMAND_TYPE, default=COMMAND_TYPE_IR): vol.In(COMMAND_TYPES),
        vol.Optional(ATTR_ALTERNATIVE, default=False): cv.boolean,
    }
)
SERVICE_DELETE_SCHEMA = COMMAND_SCHEMA.extend(
    {vol.Required(ATTR_DEVICE): vol.All(cv.string, vol.Length(min=1))}
)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a Broadlink remote from a config entry."""
    device: BroadlinkDevice = hass.data[DOMAIN].devices[config_entry.entry_id]
    remote = BroadlinkRemote(
        device,
        config_entry,
        Store(hass, CODE_STORAGE_VERSION, f"broadlink_remote_{device.unique_id}_codes"),
        Store(hass, FLAG_STORAGE_VERSION, f"broadlink_remote_{device.unique_id}_flags"),
    )
    async_add_entities([remote])



class BroadlinkRemote(BroadlinkEntity, RemoteEntity, RestoreEntity):
    """Representation of a Broadlink remote, handling command learning, sending, and storage."""

    _attr_has_entity_name = True
    _attr_name = None


    async def list_commands(self) -> dict:
        """List stored commands for this device, create a notification, and return the commands."""
        await self._async_load_storage(force_reload=True)
        stored_codes = self._get_codes()
        message_list = []

        for device_name, commands in stored_codes.items():
            message_list.append(f"**Device: {device_name}**")
            for command_name in sorted(commands.keys()):
                message_list.append(f"  - `{command_name}`")

        message = "\n".join(message_list) if message_list else "No commands have been learned for this device."

        # persistent_notification.async_create(
        #     self.hass,
        #     message,
        #     title=f"{self.name} Stored Commands",
        #     notification_id=f"broadlink_commands_{self.unique_id}",
        # )

        result = {}
        for device_name, commands in stored_codes.items():
            result[device_name] = list(sorted(commands.keys()))

        return result

    def __init__(self, device, config_entry, codes, flags):
        """Initialize the remote entity.

        Args:
            device: The Broadlink device object.
            config_entry: The config entry.
            codes: The code storage object.
            flags: The flag storage object for toggle commands.
        """
        super().__init__(device)
        self.config_entry = config_entry
        self._code_storage = codes
        self._flag_storage = flags
        self._storage_loaded = False
        self._codes = {}
        self._flags = defaultdict(int)
        self._lock = asyncio.Lock()
        self._attr_is_on = True
        self._attr_supported_features = (
            RemoteEntityFeature.LEARN_COMMAND | RemoteEntityFeature.DELETE_COMMAND
        )
        self._attr_unique_id = device.unique_id

    def _extract_codes(self, commands, device=None):
        """Extract and decode a list of command codes.

        Args:
            commands: A list of command names or base64-encoded codes.
            device: The target sub-device for named commands.

        Returns:
            A list of decoded command packets.

        Raises:
            ValueError: If a command is not found or a code is invalid.
        """
        code_list = []
        for cmd in commands:
            if cmd.startswith("b64:"):
                codes = [cmd[4:]]
            else:
                if device is None:
                    raise ValueError("You need to specify a device")
                try:
                    codes = self._codes[device][cmd]
                except KeyError as err:
                    raise ValueError(f"Command not found: {cmd!r}") from err
                if isinstance(codes, list):
                    codes = codes[:]
                else:
                    codes = [codes]
            for idx, code in enumerate(codes):
                try:
                    codes[idx] = data_packet(code)
                except ValueError as err:
                    raise ValueError(f"Invalid code: {code!r}") from err
            code_list.append(codes)
        return code_list

    @callback
    def _get_codes(self):
        """Return the dictionary of stored command codes."""
        return self._codes

    @callback
    def _get_flags(self):
        """Return the dictionary of toggle flags."""
        return self._flags

    async def async_added_to_hass(self) -> None:
        """Call when the remote is added to hass to restore its state."""
        state = await self.async_get_last_state()
        self._attr_is_on = state is None or state.state != STATE_OFF
        await super().async_added_to_hass()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the remote entity, allowing commands to be sent."""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable the remote entity, preventing commands from being sent."""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def _async_load_storage(self, force_reload=False):
        """Load the command codes and toggle flags from storage."""
        _LOGGER.debug("Attempting to load storage for %s. Path: %s", self.entity_id, self._code_storage.path)
        if self._storage_loaded and not force_reload:
            _LOGGER.debug("Storage already loaded for %s.", self.entity_id)
            return

        try:
            stored_codes = await self._code_storage.async_load()
            if stored_codes:
                _LOGGER.debug("Code storage data found for %s. Loading codes.", self.entity_id)
                self._codes = stored_codes
            else:
                _LOGGER.debug("No code storage data found for %s.", self.entity_id)
                self._codes = {}

            stored_flags = await self._flag_storage.async_load()
            if stored_flags:
                _LOGGER.debug("Flag data found for %s. Loading flags.", self.entity_id)
                self._flags.clear()
                self._flags.update(stored_flags)
            else:
                _LOGGER.debug("No flag storage data found for %s.", self.entity_id)
                self._flags.clear()

            self._storage_loaded = True

        except Exception as e:
            _LOGGER.error("Failed to load storage for %s: %s", self.entity_id, e)
            self._codes = {}
            self._flags = defaultdict(int)

    async def async_send_command(self, command: Iterable[str], **kwargs: Any) -> None:
        """Send a sequence of commands to a device."""
        kwargs[ATTR_COMMAND] = command
        kwargs = SERVICE_SEND_SCHEMA(kwargs)
        commands = kwargs[ATTR_COMMAND]
        subdevice = kwargs.get(ATTR_DEVICE)
        repeat = kwargs[ATTR_NUM_REPEATS]
        delay = kwargs[ATTR_DELAY_SECS]
        service = f"{RM_DOMAIN}.{SERVICE_SEND_COMMAND}"
        device = self._device
        if not self._attr_is_on:
            _LOGGER.warning(
                "%s canceled: %s entity is turned off", service, self.entity_id
            )
            return
        await self._async_load_storage()
        try:
            code_list = self._extract_codes(commands, subdevice)
        except ValueError as err:
            _LOGGER.error("Failed to call %s: %s", service, err)
            raise
        rf_flags = {0xB2, 0xD7}
        if not hasattr(device.api, "sweep_frequency") and any(
            c[0] in rf_flags for codes in code_list for c in codes
        ):
            err_msg = f"{self.entity_id} doesn't support sending RF commands"
            _LOGGER.error("Failed to call %s: %s", service, err_msg)
            raise ValueError(err_msg)
        at_least_one_sent = False
        for _, codes in product(range(repeat), code_list):
            if at_least_one_sent:
                await asyncio.sleep(delay)
            if len(codes) > 1:
                code = codes[self._flags[subdevice]]
            else:
                code = codes[0]
            try:
                await device.async_request(device.api.send_data, code)
            except (BroadlinkException, OSError) as err:
                _LOGGER.error("Error during %s: %s", service, err)
                break
            if len(codes) > 1:
                self._flags[subdevice] ^= 1
            at_least_one_sent = True
        if at_least_one_sent:
            self._flag_storage.async_delay_save(self._get_flags, FLAG_SAVE_DELAY)

    async def async_learn_command(self, **kwargs: Any) -> None:
        """Learn a sequence of commands from a remote."""
        kwargs = SERVICE_LEARN_SCHEMA(kwargs)
        commands = kwargs[ATTR_COMMAND]
        command_type = kwargs[ATTR_COMMAND_TYPE]
        subdevice = kwargs[ATTR_DEVICE]
        toggle = kwargs[ATTR_ALTERNATIVE]
        service = f"{RM_DOMAIN}.{SERVICE_LEARN_COMMAND}"
        device = self._device
        if not self._attr_is_on:
            _LOGGER.warning(
                "%s canceled: %s entity is turned off", service, self.entity_id
            )
            return
        await self._async_load_storage()
        async with self._lock:
            if command_type == COMMAND_TYPE_IR:
                learn_command = self._async_learn_ir_command
            elif hasattr(device.api, "sweep_frequency"):
                learn_command = self._async_learn_rf_command
            else:
                err_msg = f"{self.entity_id} doesn't support learning RF commands"
                _LOGGER.error("Failed to call %s: %s", service, err_msg)
                raise ValueError(err_msg)
            should_store = False
            for command in commands:
                try:
                    code = await learn_command(command)
                    if toggle:
                        code = [code, await learn_command(command)]
                except (AuthorizationError, NetworkTimeoutError, OSError) as err:
                    _LOGGER.error("Failed to learn '%s': %s", command, err)
                    break
                except BroadlinkException as err:
                    _LOGGER.error("Failed to learn '%s': %s", command, err)
                    continue
                self._codes.setdefault(subdevice, {}).update({command: code})
                should_store = True
            if should_store:
                await self._code_storage.async_save(self._codes)

    async def _async_learn_ir_command(self, command):
        """Learn a single infrared (IR) command.

        Args:
            command: The name of the command to learn.

        Returns:
            The learned command code, base64-encoded.

        Raises:
            TimeoutError: If no command is received within the timeout period.
        """
        device = self._device
        try:
            await device.async_request(device.api.enter_learning)
        except (BroadlinkException, OSError) as err:
            _LOGGER.debug("Failed to enter learning mode: %s", err)
            raise
        persistent_notification.async_create(
            self.hass,
            f"Press the '{command}' button.",
            title="Learn command",
            notification_id="learn_command",
        )
        try:
            start_time = dt_util.utcnow()
            while (dt_util.utcnow() - start_time) < LEARNING_TIMEOUT:
                await asyncio.sleep(1)
                try:
                    code = await device.async_request(device.api.check_data)
                except (ReadError, StorageError):
                    continue
                return b64encode(code).decode("utf8")
            raise TimeoutError(
                "No infrared code received within "
                f"{LEARNING_TIMEOUT.total_seconds()} seconds"
            )
        finally:
            persistent_notification.async_dismiss(
                self.hass, notification_id="learn_command"
            )

    async def _async_learn_rf_command(self, command):
        """Learn a single radiofrequency (RF) command.

        This involves a two-step process: sweeping for the frequency and then learning the code.

        Args:
            command: The name of the command to learn.

        Returns:
            The learned command code, base64-encoded.

        Raises:
            TimeoutError: If no command is received within the timeout period.
        """
        device = self._device
        try:
            await device.async_request(device.api.sweep_frequency)
        except (BroadlinkException, OSError) as err:
            _LOGGER.debug("Failed to sweep frequency: %s", err)
            raise
        persistent_notification.async_create(
            self.hass,
            f"Press and hold the '{command}' button.",
            title="Sweep frequency",
            notification_id="sweep_frequency",
        )
        try:
            start_time = dt_util.utcnow()
            while (dt_util.utcnow() - start_time) < LEARNING_TIMEOUT:
                await asyncio.sleep(1)
                is_found, frequency = await device.async_request(
                    device.api.check_frequency
                )
                if is_found:
                    _LOGGER.debug("Radiofrequency detected: %s MHz", frequency)
                    break
            else:
                await device.async_request(device.api.cancel_sweep_frequency)
                raise TimeoutError(
                    "No radiofrequency found within "
                    f"{LEARNING_TIMEOUT.total_seconds()} seconds"
                )
        finally:
            persistent_notification.async_dismiss(
                self.hass, notification_id="sweep_frequency"
            )
        await asyncio.sleep(1)
        try:
            await device.async_request(device.api.find_rf_packet)
        except (BroadlinkException, OSError) as err:
            _LOGGER.debug("Failed to enter learning mode: %s", err)
            raise
        persistent_notification.async_create(
            self.hass,
            f"Press the '{command}' button again.",
            title="Learn command",
            notification_id="learn_command",
        )
        try:
            start_time = dt_util.utcnow()
            while (dt_util.utcnow() - start_time) < LEARNING_TIMEOUT:
                await asyncio.sleep(1)
                try:
                    code = await device.async_request(device.api.check_data)
                except (ReadError, StorageError):
                    continue
                return b64encode(code).decode("utf8")
            raise TimeoutError(
                "No radiofrequency code received within "
                f"{LEARNING_TIMEOUT.total_seconds()} seconds"
            )
        finally:
            persistent_notification.async_dismiss(
                self.hass, notification_id="learn_command"
            )

    async def async_delete_command(self, **kwargs: Any) -> None:
        """Delete a sequence of commands from storage."""
        kwargs = SERVICE_DELETE_SCHEMA(kwargs)
        commands = kwargs[ATTR_COMMAND]
        subdevice = kwargs[ATTR_DEVICE]
        service = f"{RM_DOMAIN}.{SERVICE_DELETE_COMMAND}"
        if not self._attr_is_on:
            _LOGGER.warning(
                "%s canceled: %s entity is turned off",
                service,
                self.entity_id,
            )
            return
        await self._async_load_storage()
        try:
            codes = self._codes[subdevice]
        except KeyError as err:
            err_msg = f"Device not found: {subdevice!r}"
            _LOGGER.error("Failed to call %s. %s", service, err_msg)
            raise ValueError(err_msg) from err
        cmds_not_found = []
        for command in commands:
            try:
                del codes[command]
            except KeyError:
                cmds_not_found.append(command)
        if cmds_not_found:
            if len(cmds_not_found) == 1:
                err_msg = f"Command not found: {cmds_not_found[0]!r}"
            else:
                err_msg = f"Commands not found: {cmds_not_found!r}"
            if len(cmds_not_found) == len(commands):
                _LOGGER.error("Failed to call %s. %s", service, err_msg)
                raise ValueError(err_msg)
            _LOGGER.error("Error during %s. %s", service, err_msg)
        if not codes:
            del self._codes[subdevice]
            if self._flags.pop(subdevice, None) is not None:
                self._flag_storage.async_delay_save(self._get_flags, FLAG_SAVE_DELAY)
        self._code_storage.async_delay_save(self._get_codes, CODE_SAVE_DELAY)