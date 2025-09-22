"""Constants for the Broadlink integration."""

from homeassistant.const import Platform

# The domain of the integration.
DOMAIN = "broadlink_plus"

# A mapping of Home Assistant platforms to the supported Broadlink device types.
# This dictionary defines which device types are handled by each platform (e.g., climate, light).
DOMAINS_AND_TYPES = {
    Platform.CLIMATE: {"HYS"},
    Platform.LIGHT: {"LB1", "LB2"},
    Platform.REMOTE: {"RM4MINI", "RM4PRO", "RMMINI", "RMMINIB", "RMPRO"},
    Platform.SELECT: {"HYS"},
    Platform.SENSOR: {
        "A1",
        "A2",
        "MP1S",
        "RM4MINI",
        "RM4PRO",
        "RMPRO",
        "SP2S",
        "SP3S",
        "SP4",
        "SP4B",
    },
    Platform.SWITCH: {
        "BG1",
        "MP1",
        "MP1S",
        "RM4MINI",
        "RM4PRO",
        "RMMINI",
        "RMMINIB",
        "RMPRO",
        "SP1",
        "SP2",
        "SP2S",
        "SP3",
        "SP3S",
        "SP4",
        "SP4B",
    },
    Platform.TIME: {"HYS"},
}
# A set of all supported device types, created by taking the union of all device type sets.
DEVICE_TYPES = set.union(*DOMAINS_AND_TYPES.values())

# The default port used for communication with Broadlink devices.
DEFAULT_PORT = 80
# The default timeout in seconds for network operations with Broadlink devices.
DEFAULT_TIMEOUT = 5
