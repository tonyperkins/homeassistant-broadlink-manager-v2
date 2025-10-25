"""
Direct Broadlink device learning using python-broadlink

This module handles learning IR and RF commands directly from Broadlink devices
without relying on Home Assistant's Broadlink integration.
"""

import broadlink
import base64
import time
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class BroadlinkLearner:
    """
    Direct learning from Broadlink devices

    Implements the same approach as Home Assistant's Broadlink integration:
    - Catches StorageError and ReadError, continues looping
    - 30 second timeout for all operations
    - 1 second sleep between polling attempts
    - Returns base64 encoded command data
    """

    def __init__(self, host: str, mac: bytes, device_type: str):
        """
        Initialize learner with device connection info

        Args:
            host: Device IP address
            mac: Device MAC address as bytes
            device_type: Device type code (e.g., 0x2787 for RM4 Pro)
        """
        self.host = host
        self.mac = mac
        self.device_type = device_type
        self.device = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        Connect and authenticate with the device

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            logger.info(f"Connecting to device at {self.host}")
            self.device = broadlink.gendevice(
                self.device_type, (self.host, 80), self.mac
            )

            logger.info("Authenticating with device")
            self.device.auth()
            self._authenticated = True
            logger.info("Authentication successful")
            return True

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            self._authenticated = False
            return False

    def learn_ir_command(self, timeout: int = 30) -> Optional[str]:
        """
        Learn an IR command (1-step process)

        Process:
        1. Enter learning mode
        2. Wait for user to press button
        3. Poll check_data() until command received
        4. Return base64 encoded data

        Args:
            timeout: Maximum seconds to wait for command

        Returns:
            Base64 encoded command data, or None if timeout/error
        """
        if not self._authenticated:
            logger.error("Device not authenticated")
            return None

        try:
            # Step 1: Enter learning mode
            logger.info("Entering IR learning mode")
            self.device.enter_learning()

            # Step 2: Poll for data
            start_time = time.time()
            storage_errors = 0

            while time.time() - start_time < timeout:
                time.sleep(1)
                elapsed = int(time.time() - start_time)

                try:
                    packet = self.device.check_data()
                except (
                    broadlink.exceptions.ReadError,
                    broadlink.exceptions.StorageError,
                ) as e:
                    # Ignore errors from old commands in buffer (like HA does)
                    storage_errors += 1
                    if storage_errors == 1:
                        logger.debug(
                            "Ignoring storage errors from old commands in buffer"
                        )
                    continue

                if packet:
                    logger.info(f"IR command captured ({len(packet)} bytes)")
                    if storage_errors > 0:
                        logger.debug(f"Ignored {storage_errors} storage errors")

                    # Convert to base64
                    base64_data = base64.b64encode(packet).decode("utf-8")
                    logger.info(f"Command encoded to base64 ({len(base64_data)} chars)")
                    return base64_data

            logger.warning(f"Timeout - no IR signal detected after {timeout} seconds")
            return None

        except Exception as e:
            logger.error(f"Error during IR learning: {e}")
            return None

    def learn_rf_command(self, timeout: int = 30) -> Optional[Tuple[str, float]]:
        """
        Learn an RF command (2-step process)

        Process:
        1. Sweep frequency (user holds button)
        2. Lock frequency
        3. Sleep 1 second (let user release)
        4. Find RF packet (user presses again)
        5. Poll check_data() until command received
        6. Return base64 encoded data

        Args:
            timeout: Maximum seconds to wait for each step

        Returns:
            Tuple of (base64 data, frequency in MHz), or None if timeout/error
        """
        if not self._authenticated:
            logger.error("Device not authenticated")
            return None

        try:
            # Step 1: Sweep frequency
            logger.info("Starting RF frequency sweep")
            self.device.sweep_frequency()

            start_time = time.time()
            frequency = None

            while time.time() - start_time < timeout:
                time.sleep(1)

                # Check if frequency was found (returns tuple: is_found, frequency)
                is_found, freq = self.device.check_frequency()
                if is_found:
                    frequency = freq
                    logger.info(f"RF frequency locked: {frequency} MHz")
                    break

            if frequency is None:
                logger.warning(
                    f"Timeout - no RF frequency found after {timeout} seconds"
                )
                self.device.cancel_sweep_frequency()
                return None

            # Sleep 1 second (let user release button, like HA does)
            time.sleep(1)

            # Step 2: Find and capture RF packet
            logger.info("Capturing RF packet")
            self.device.find_rf_packet()

            start_time = time.time()
            storage_errors = 0

            while time.time() - start_time < timeout:
                time.sleep(1)

                try:
                    packet = self.device.check_data()
                except (
                    broadlink.exceptions.ReadError,
                    broadlink.exceptions.StorageError,
                ) as e:
                    # Ignore errors from old commands in buffer (like HA does)
                    storage_errors += 1
                    if storage_errors == 1:
                        logger.debug(
                            "Ignoring storage errors from old commands in buffer"
                        )
                    continue

                if packet:
                    logger.info(f"RF command captured ({len(packet)} bytes)")
                    if storage_errors > 0:
                        logger.debug(f"Ignored {storage_errors} storage errors")

                    # Convert to base64
                    base64_data = base64.b64encode(packet).decode("utf-8")
                    logger.info(f"Command encoded to base64 ({len(base64_data)} chars)")
                    return (base64_data, frequency)

            logger.warning(f"Timeout - no RF signal detected after {timeout} seconds")
            return None

        except Exception as e:
            logger.error(f"Error during RF learning: {e}")
            return None

    def test_command(self, base64_data: str) -> bool:
        """
        Test a command by sending it directly to the device

        Args:
            base64_data: Base64 encoded command data

        Returns:
            True if command sent successfully, False otherwise
        """
        if not self._authenticated:
            logger.error("Device not authenticated")
            return False

        try:
            # Decode base64 to bytes
            packet = base64.b64decode(base64_data)

            logger.info(f"Sending test command ({len(packet)} bytes)")
            self.device.send_data(packet)
            logger.info("Command sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return False
