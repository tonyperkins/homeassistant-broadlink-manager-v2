"""
Broadlink learned-code format helpers.

A learned Broadlink code is laid out as:

    byte 0:    code type (0x26 = IR, 0xB0-0xBF = RF 433MHz, 0xD7 = RF 315MHz)
    byte 1:    repeat count (0-255)
    bytes 2-3: pulse data length (little-endian)
    byte 4+:   pulse timings

The repeat count byte tells the Broadlink hardware how many extra times to
transmit the frame, back-to-back with no network round-trips in between.
Raising it makes a single send transmit continuously, which is what devices
that expect a held button (TV lifts, RF motors, some blinds) need.

See https://github.com/mjg59/python-broadlink/blob/master/protocol.md
("Sending data") and issues #60/#61.
"""

import base64
from typing import Dict, Any

TYPE_IR = 0x26
RF433_MIN = 0xB0
RF433_MAX = 0xBF
TYPE_RF315 = 0xD7

REPEAT_MIN = 0
REPEAT_MAX = 255


def _decode(base64_data: str) -> bytearray:
    """Decode base64 code data and check it can hold a repeat byte"""
    if not base64_data or not isinstance(base64_data, str):
        raise ValueError("Command has no code data")
    try:
        raw = bytearray(base64.b64decode(base64_data.strip()))
    except Exception:
        raise ValueError("Command code is not valid base64")
    if len(raw) < 2:
        raise ValueError("Command code is too short to contain a repeat byte")
    return raw


def _validate_type_byte(type_byte: int) -> str:
    """Return the type label, or raise if the type byte is unrecognized"""
    if type_byte == TYPE_IR:
        return "ir"
    if RF433_MIN <= type_byte <= RF433_MAX:
        return "rf433"
    if type_byte == TYPE_RF315:
        return "rf315"
    raise ValueError(
        f"Unrecognized code type byte 0x{type_byte:02x} - only Broadlink "
        f"IR (0x26) and RF (0xb0-0xbf, 0xd7) codes are supported"
    )


def parse_code(base64_data: str) -> Dict[str, Any]:
    """
    Parse a learned Broadlink code.

    Args:
        base64_data: Base64 encoded command data

    Returns:
        Dict with type_byte (hex string), type ("ir"/"rf433"/"rf315"),
        repeat (int), and data_length (int)

    Raises:
        ValueError: If the data is not a decodable Broadlink code
    """
    raw = _decode(base64_data)
    type_label = _validate_type_byte(raw[0])
    return {
        "type_byte": f"0x{raw[0]:02x}",
        "type": type_label,
        "repeat": raw[1],
        "data_length": len(raw),
    }


def set_repeat_count(base64_data: str, repeat: int) -> str:
    """
    Return a copy of the code with the repeat byte patched.

    Args:
        base64_data: Base64 encoded command data
        repeat: New repeat count (0-255)

    Returns:
        Base64 encoded code with the new repeat count

    Raises:
        ValueError: If repeat is out of range or the code is invalid
    """
    if isinstance(repeat, bool) or not isinstance(repeat, int):
        raise ValueError("Repeat count must be an integer")
    if not REPEAT_MIN <= repeat <= REPEAT_MAX:
        raise ValueError(f"Repeat count must be between {REPEAT_MIN} and {REPEAT_MAX}")

    raw = _decode(base64_data)
    _validate_type_byte(raw[0])
    raw[1] = repeat
    return base64.b64encode(bytes(raw)).decode("ascii")
