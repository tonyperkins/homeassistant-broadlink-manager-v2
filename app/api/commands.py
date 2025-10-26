"""
Command API endpoints
"""

import logging
import asyncio
import json
import time
from pathlib import Path
from flask import jsonify, request, current_app
from . import api_bp

logger = logging.getLogger(__name__)


def get_web_server():
    """Get web server instance from Flask app context"""
    return current_app.config.get("web_server")


async def verify_command_in_storage(
    web_server,
    device_name: str,
    command_name: str,
    max_retries: int = 10,
    delay: float = 1.0,
) -> bool:
    """
    Verify that a command exists in Broadlink storage by polling.

    Args:
        web_server: BroadlinkWebServer instance
        device_name: Device name (storage key)
        command_name: Command name to verify
        max_retries: Maximum number of retry attempts (default: 10)
        delay: Delay in seconds between retries (default: 1.0)
    """
    import asyncio

    try:
        for attempt in range(max_retries):
            # Get all Broadlink commands from storage
            all_commands = await web_server._get_all_broadlink_commands()

            # Check if the device has commands
            device_commands = all_commands.get(device_name, {})

            # Check if the specific command exists
            if command_name in device_commands:
                if attempt > 0:
                    logger.info(
                        f"✅ Verified command '{command_name}' exists for device '{device_name}' (after {attempt + 1} attempts)"
                    )
                else:
                    logger.info(
                        f"✅ Verified command '{command_name}' exists for device '{device_name}'"
                    )
                return True

            # Command not found yet, wait and retry
            if attempt < max_retries - 1:
                logger.debug(
                    f"Command '{command_name}' not found yet, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(delay)

        # All retries exhausted
        logger.warning(
            f"⚠️ Command '{command_name}' not found in storage for device '{device_name}' after {max_retries} attempts"
        )
        return False

    except Exception as e:
        logger.error(f"Error verifying command: {e}")
        return False


@api_bp.route("/commands/learn", methods=["POST"])
def learn_command():
    """Start learning a new command (synchronous call to HA)"""
    try:
        data = request.json
        logger.info(f"Learn command request data: {data}")

        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        command_type = data.get("command_type", "ir")
        device_id = data.get("device_id")  # For managed devices
        save_destination = data.get(
            "save_destination", "manager_only"
        )  # manager_only, integration_only, both

        logger.info(
            f"Parsed: entity_id={entity_id}, device={device}, command={command}, type={command_type}, device_id={device_id}, save_destination={save_destination}"
        )

        # If device is not provided, try to derive it from device_id
        if not device and device_id:
            # For managed devices, use the device_id as the device name
            # Remove entity_type prefix if present (e.g., "switch.office_lamp" -> "office_lamp")
            device = device_id.split(".")[-1] if "." in device_id else device_id
            logger.info(f"Derived device name from device_id: {device}")

        if not all([entity_id, device, command]):
            missing = []
            if not entity_id:
                missing.append("entity_id")
            if not device:
                missing.append("device (or device_id)")
            if not command:
                missing.append("command")

            error_msg = f'Missing required fields: {", ".join(missing)}'
            logger.error(error_msg)
            return jsonify({"success": False, "error": error_msg}), 400

        # Update data with derived device name if it was derived
        if device and not data.get("device"):
            data["device"] = device
            logger.info(f"Updated data with derived device: {device}")

        # Get web server instance to use its _learn_command method
        web_server = get_web_server()
        if not web_server:
            return jsonify({"error": "Web server not available"}), 500

        # Call the existing async learn_command method synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(web_server._learn_command(data))

        # If HA API returned success, fetch the learned code immediately
        if result.get("success"):
            logger.info(
                f"✅ Learn command API call succeeded for '{command}' on device '{device}'"
            )

            # Fetch the learned code from Broadlink storage immediately
            # The code is available right away, even though the file write may lag
            try:
                import time

                # Give HA a moment to process (usually instant, but be safe)
                time.sleep(0.5)

                # Fetch all commands from storage
                all_commands = loop.run_until_complete(
                    web_server._get_all_broadlink_commands()
                )

                # Get the specific command we just learned
                device_commands = all_commands.get(device, {})
                learned_code = device_commands.get(command)

                if learned_code:
                    logger.info(
                        f"✅ Successfully fetched learned code for '{command}' (length: {len(learned_code)} chars)"
                    )
                    result["code"] = learned_code
                    result["message"] = f"✅ Command '{command}' learned successfully!"
                else:
                    logger.warning(
                        f"⚠️ Command learned but code not yet available in storage, using pending"
                    )
                    result["code"] = "pending"
                    result["message"] = (
                        f"✅ Command '{command}' learned! Code will be available shortly."
                    )

            except Exception as fetch_error:
                logger.error(f"Error fetching learned code: {fetch_error}")
                result["code"] = "pending"
                result["message"] = (
                    f"✅ Command '{command}' learned! Code will be available shortly."
                )
            finally:
                loop.close()

            # Update devices.json if this is a managed device and save_destination allows it
            if device_id and save_destination in ["manager_only", "both"]:
                try:
                    device_manager = current_app.config.get("device_manager")
                    if device_manager:
                        managed_device = device_manager.get_device(device_id)
                        if managed_device:
                            # Add the new command to the device's commands
                            if "commands" not in managed_device:
                                managed_device["commands"] = {}

                            # Store the learned code so we don't depend on .storage files
                            managed_device["commands"][command] = {
                                "data": learned_code if learned_code else "pending",
                                "type": command_type,
                                "name": command,
                            }

                            # Save updated device
                            device_manager.update_device(device_id, managed_device)
                            logger.info(
                                f"✅ Updated devices.json for {device_id} with new command '{command}' (save_destination={save_destination})"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Device {device_id} not found in device manager"
                            )
                    else:
                        logger.warning("⚠️ Device manager not available")
                except Exception as save_error:
                    logger.error(f"❌ Error updating devices.json: {save_error}")
                    # Don't fail the request if devices.json update fails
            elif device_id and save_destination == "integration_only":
                logger.info(
                    f"ℹ️ Skipping devices.json update for '{command}' - save_destination=integration_only"
                )

            return jsonify(result)
        else:
            loop.close()
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"Error learning command: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/send-raw", methods=["POST"])
def send_raw_command():
    """Send a raw IR/RF code directly to Broadlink device"""
    try:
        data = request.json
        logger.info(f"Send raw command request data: {data}")

        entity_id = data.get("entity_id")
        command = data.get("command")  # Raw base64 IR/RF code
        command_type = data.get("command_type", "ir")  # 'ir' or 'rf'

        if not entity_id or not command:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required fields: entity_id, command",
                    }
                ),
                400,
            )

        # Check if the command is a placeholder (e.g., "pending")
        if command.lower() in ["pending", "null", "none", ""]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Command has not been learned yet (status: {command})",
                    }
                ),
                400,
            )

        # Get web server for HA API calls
        web_server = get_web_server()
        if not web_server:
            return jsonify({"success": False, "error": "Web server not available"}), 500

        # Send raw code directly to Home Assistant
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # For raw codes, prefix with 'b64:' to tell Broadlink it's a base64-encoded raw command
        # This allows sending raw codes without learning them first
        service_payload = {
            "entity_id": entity_id,
            "command": f"b64:{command}",
        }  # Prefix with b64: for raw codes

        # Log what we're sending
        if command_type == "rf":
            logger.info(
                f"Sending raw RF code to HA (code length: {len(command)} chars)"
            )
        else:
            logger.info(
                f"Sending raw IR code to HA (code length: {len(command)} chars)"
            )

        logger.info(f"Service payload: {service_payload}")

        result = loop.run_until_complete(
            web_server._make_ha_request(
                "POST", "services/remote/send_command", service_payload
            )
        )
        loop.close()

        # HA service calls return empty dict/list on success, None on failure
        logger.info(f"HA API result: {result} (type: {type(result)})")
        if result is not None:
            logger.info("✅ Raw command sent successfully")
            return jsonify({"success": True, "message": "Command sent successfully"})
        else:
            logger.error("❌ HA API returned None - command failed")
            return jsonify({"success": False, "error": "Failed to send command"}), 400

    except Exception as e:
        logger.error(f"Error sending raw command: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/test", methods=["POST"])
def test_command():
    """Test a learned command by sending it"""
    try:
        data = request.json
        logger.info(f"Test command request data: {data}")

        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        device_id = data.get("device_id")  # Entity ID to look up command mapping

        logger.info(
            f"Parsed - entity_id: {entity_id}, device: {device}, command: {command}, device_id: {device_id}"
        )

        # If device is not provided, try to derive it from device_id
        if not device and device_id:
            # For managed devices, use the device_id as the device name
            # Remove entity_type prefix if present (e.g., "switch.office_lamp" -> "office_lamp")
            device = device_id.split(".")[-1] if "." in device_id else device_id
            logger.info(f"Derived device name from device_id: {device}")

        if not all([entity_id, device, command]):
            missing = []
            if not entity_id:
                missing.append("entity_id")
            if not device:
                missing.append("device")
            if not command:
                missing.append("command")

            error_msg = f'Missing required fields: {", ".join(missing)}'
            logger.error(f"{error_msg}. Received data: {data}")
            return jsonify({"success": False, "error": error_msg}), 400

        # Get device manager to look up command mapping and device type
        device_manager = current_app.config.get("device_manager")
        is_smartir = False
        entity_data = None

        if device_id and device_manager:
            entity_data = device_manager.get_device(device_id)
            if entity_data:
                logger.info(f"Found device in device_manager: {device_id}")

        if entity_data:
            is_smartir = entity_data.get("device_type") == "smartir"
            logger.info(
                f"Device type detected: {'SmartIR' if is_smartir else 'Broadlink'}"
            )
            commands_mapping = entity_data.get("commands", {})

            # Look up the actual command code from the mapping
            command_data = commands_mapping.get(command, command)

            # If command_data is a dict (metadata), extract the actual code
            if isinstance(command_data, dict):
                # Command stored with metadata: {'code': 'JgBQAAA...', 'command_type': 'ir', ...}
                actual_command = command_data.get(
                    "code", command_data.get("data", command)
                )
                logger.info(
                    f"Command mapping: '{command}' -> extracted code from metadata"
                )
            else:
                # Command stored as string directly
                actual_command = command_data
                logger.info(f"Command mapping: '{command}' -> '{actual_command}'")

            command = actual_command
        else:
            logger.warning(f"Entity data not found for device_id: {device_id}")

        # Get web server instance
        web_server = get_web_server()
        if not web_server:
            return jsonify({"error": "Web server not available"}), 500

        # Call HA service to send the command
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # For SmartIR devices, we need to look up the raw IR code from the SmartIR code file
        if is_smartir:
            logger.info(
                f"SmartIR device detected - looking up raw IR code for command '{command}'"
            )

            # Get SmartIR code service to look up the raw code
            smartir_code_service = current_app.config.get("smartir_code_service")
            if not smartir_code_service:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "SmartIR code service not available",
                        }
                    ),
                    500,
                )

            # Get device code and entity type
            device_code = entity_data.get("device_code")
            entity_type = entity_data.get("entity_type", "climate")

            if not device_code:
                return (
                    jsonify(
                        {"success": False, "error": "SmartIR device_code not found"}
                    ),
                    400,
                )

            # Look up the raw IR code from SmartIR code file
            try:
                code_data = smartir_code_service.fetch_full_code(
                    entity_type, device_code
                )
                if not code_data:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"SmartIR code file {device_code} not found",
                            }
                        ),
                        404,
                    )

                # Extract the raw code for this command
                commands_data = code_data.get("commands", {})

                # Check if command is in format "mode_temp_fan" (e.g., "cool_24_auto") or "mode_temp" (e.g., "cool_24")
                if "_" in command:
                    parts = command.split("_")
                    if len(parts) >= 2:
                        mode = parts[0]
                        temp = parts[1] if parts[1].isdigit() else None
                        fan = parts[2] if len(parts) > 2 else None

                        logger.info(
                            f"Parsing command: mode='{mode}', temp='{temp}', fan='{fan}'"
                        )

                        # Try to find the command in nested structure
                        mode_data = commands_data.get(mode)
                        if isinstance(mode_data, dict):
                            if temp and temp in mode_data:
                                temp_data = mode_data[temp]
                                if isinstance(temp_data, dict) and fan:
                                    # Nested by fan mode: cool -> 24 -> auto
                                    raw_code = temp_data.get(fan)
                                    logger.info(
                                        f"Found code for {mode} at {temp}°C, fan {fan}"
                                    )
                                else:
                                    # Just temperature nested: cool -> 24
                                    raw_code = temp_data
                                    logger.info(f"Found code for {mode} at {temp}°C")
                            else:
                                # No specific temp, use default or first available
                                default_temp = "24"
                                if default_temp in mode_data:
                                    temp_data = mode_data[default_temp]
                                else:
                                    temp_data = (
                                        next(iter(mode_data.values()))
                                        if mode_data
                                        else None
                                    )

                                if isinstance(temp_data, dict) and fan:
                                    raw_code = temp_data.get(fan)
                                else:
                                    raw_code = temp_data
                                logger.info(
                                    f"Using default/first temperature for {mode}"
                                )
                        else:
                            raw_code = mode_data
                    else:
                        raw_code = commands_data.get(command)
                else:
                    # Direct command lookup
                    raw_code = commands_data.get(command)

                # For climate devices, commands may still be nested by temperature
                # e.g., {"cool": {"16": "code1", "17": "code2"}}
                if isinstance(raw_code, dict):
                    # Still nested - might have fan modes or other parameters
                    # Try to get the first available value (usually the default fan mode)
                    logger.info(
                        f"Command '{command}' has additional nesting (fan modes?), extracting first value"
                    )
                    raw_code = next(iter(raw_code.values())) if raw_code else None

                    # If still a dict, try one more level
                    if isinstance(raw_code, dict):
                        logger.info(
                            f"Command '{command}' has multiple levels of nesting, extracting first value again"
                        )
                        raw_code = next(iter(raw_code.values())) if raw_code else None

                if not raw_code or not isinstance(raw_code, str):
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f'Command "{command}" not found or invalid in SmartIR code file {device_code}',
                            }
                        ),
                        404,
                    )

                # Check if the code is a placeholder (e.g., "pending")
                if raw_code.lower() in ["pending", "null", "none", ""]:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f'Command "{command}" has not been learned yet (status: {raw_code})',
                            }
                        ),
                        400,
                    )

                logger.info(
                    f"Found raw IR code for command '{command}' in SmartIR code file {device_code}"
                )

                # Send the raw code directly with b64: prefix
                # The b64: prefix tells Broadlink it's a base64-encoded raw command
                service_payload = {
                    "entity_id": entity_id,
                    "command": f"b64:{raw_code}",
                }  # Prefix with b64: for raw codes
                logger.info(
                    f"Sending SmartIR raw code to HA (code length: {len(raw_code)} chars)"
                )

            except Exception as e:
                logger.error(f"Error looking up SmartIR code: {e}")
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": f"Failed to look up SmartIR code: {str(e)}",
                        }
                    ),
                    500,
                )
        else:
            # Broadlink device - send raw code with b64: prefix
            # This allows us to control commands in devices.json without relying on .storage files
            service_payload = {
                "entity_id": entity_id,
                "command": f"b64:{command}",
            }
            logger.info(
                f"Sending Broadlink raw code to HA (code length: {len(command)} chars)"
            )

        result = loop.run_until_complete(
            web_server._make_ha_request(
                "POST", "services/remote/send_command", service_payload
            )
        )
        loop.close()

        # HA service calls return empty dict/list on success, None on failure
        logger.info(f"HA API result: {result} (type: {type(result)})")
        if result is not None:
            logger.info("✅ Command sent successfully")
            return jsonify({"success": True, "message": "Command sent successfully"})
        else:
            logger.error("❌ HA API returned None - command failed")
            return jsonify({"success": False, "error": "Failed to send command"}), 400

    except Exception as e:
        logger.error(f"Error testing command: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/<device_id>/<command_name>", methods=["DELETE"])
def delete_command(device_id, command_name):
    """Delete a command from a device"""
    try:
        device_manager = current_app.config.get("device_manager")
        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        # Get device
        device = device_manager.get_device(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Check command exists
        commands = device.get("commands", {})
        if command_name not in commands:
            return jsonify({"error": "Command not found"}), 404

        logger.info(f"Delete command request:")
        logger.info(f"  device_id: {device_id}")
        logger.info(f"  command_name: {command_name}")

        # Delete from devices.json
        if device_manager.delete_command(device_id, command_name):
            logger.info(f"✅ Command '{command_name}' deleted successfully")
            return jsonify(
                {
                    "success": True,
                    "message": f"Command '{command_name}' deleted successfully",
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to delete command"}), 500

    except Exception as e:
        logger.error(f"Error deleting command: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/delete-from-storage", methods=["POST"])
def delete_command_from_storage():
    """Delete a command from Broadlink Integration storage (.storage files)"""
    try:
        data = request.json
        logger.info(f"🗑️ Delete from storage request: {data}")

        device = data.get("device")
        command = data.get("command")

        if not device or not command:
            error_msg = f"Missing device or command parameter: device={device}, command={command}"
            logger.error(f"❌ {error_msg}")
            return (
                jsonify({"success": False, "error": error_msg}),
                400,
            )

        logger.info(
            f"🗑️ Deleting command '{command}' from Broadlink storage for device '{device}'"
        )

        # Get web server instance
        web_server = get_web_server()
        if not web_server:
            logger.error("❌ Web server not available")
            return jsonify({"success": False, "error": "Web server not available"}), 500

        # Call HA API to delete the command
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Use HA's remote.delete_command service
        # The device parameter should be the storage key (e.g., "tony_s_office_workbench_lamp")
        # We need to find the corresponding entity_id
        device_manager = current_app.config.get("device_manager")
        entity_id = None

        if device_manager:
            # Try to find the device by its storage name
            all_devices = device_manager.get_all_devices()
            for dev_id, dev_data in all_devices.items():
                # Check if device field matches, or if device_id matches (when device field is missing)
                storage_key = dev_data.get("device") or dev_id
                if storage_key == device:
                    entity_id = dev_data.get("broadlink_entity")
                    logger.info(
                        f"🔍 Found entity_id '{entity_id}' for storage key '{device}' (device_id: {dev_id})"
                    )
                    break

        if not entity_id:
            # Fallback: assume device is already the entity name part
            entity_id = f"remote.{device}"
            logger.warning(f"⚠️ Could not find entity_id, using fallback: {entity_id}")

        service_payload = {"entity_id": entity_id, "command": command}
        logger.info(f"🔧 Calling HA service with payload: {service_payload}")

        result = loop.run_until_complete(
            web_server._make_ha_request(
                "POST", "services/remote/delete_command", service_payload
            )
        )
        loop.close()

        logger.info(f"📥 HA API response: {result}")

        if result is not None:
            logger.info(
                f"✅ Command '{command}' deleted from Broadlink storage via {entity_id}"
            )
            return jsonify(
                {
                    "success": True,
                    "message": f"Command '{command}' deleted from Broadlink storage",
                }
            )
        else:
            logger.error("❌ HA API returned None - delete failed")
            return (
                jsonify({"success": False, "error": "Failed to delete from storage"}),
                400,
            )

    except Exception as e:
        logger.error(f"Error deleting command from storage: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/<device_id>", methods=["GET"])
def get_device_commands(device_id):
    """Get all commands for a device"""
    try:
        device_manager = current_app.config.get("device_manager")
        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        device = device_manager.get_device(device_id)
        if not device:
            logger.warning(f"Device '{device_id}' not found")
            return jsonify({"error": "Device not found"}), 404

        commands = device.get("commands", {})
        logger.info(f"Returning {len(commands)} commands for device '{device_id}'")

        return jsonify({"commands": commands, "device_id": device_id})

    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/commands/broadlink/<device_name>", methods=["GET"])
def get_broadlink_commands(device_name):
    """Get learned commands from Broadlink storage files"""
    try:
        web_server = get_web_server()
        if not web_server:
            return jsonify({"error": "Web server not available"}), 500

        # Get all Broadlink commands
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        all_commands = loop.run_until_complete(web_server._get_all_broadlink_commands())
        loop.close()

        # Get commands for specific device
        device_commands = all_commands.get(device_name, {})

        return jsonify({"commands": device_commands, "device_name": device_name})

    except Exception as e:
        logger.error(f"Error getting Broadlink commands: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/commands/untracked", methods=["GET"])
def get_untracked_commands():
    """Get commands that exist in Broadlink storage but not in metadata"""
    try:
        web_server = get_web_server()
        device_manager = current_app.config.get("device_manager")

        if not device_manager or not web_server:
            return jsonify({"error": "Device manager or web server not available"}), 500

        # Get all commands from Broadlink storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(
            web_server._get_all_broadlink_commands()
        )
        loop.close()

        # Get all tracked commands from devices.json
        all_devices = device_manager.get_all_devices()
        tracked_commands = {}

        # Build a map of device_name -> tracked command names
        for device_id, device_data in all_devices.items():
            # Use the 'device' field which is the Broadlink storage key
            # This is what's used when learning commands via HA API
            device_name = device_data.get("device", device_id)

            logger.debug(f"Mapping device {device_id} -> storage key {device_name}")

            # Commands is a dict like {"turn_on": {"data": "...", "type": "rf"}}
            commands_dict = device_data.get("commands", {})
            tracked_commands[device_name] = set(commands_dict.keys())

            logger.debug(
                f"  Tracked commands for {device_name}: {tracked_commands[device_name]}"
            )

        # Cleanup expired deletion cache entries
        web_server._cleanup_deletion_cache()

        # Find untracked commands (excluding recently deleted ones)
        untracked = {}
        for device_name, commands in broadlink_commands.items():
            tracked = tracked_commands.get(device_name, set())
            untracked_for_device = {
                cmd: data
                for cmd, data in commands.items()
                if cmd not in tracked
                and not web_server._is_recently_deleted(device_name, cmd)
            }

            if untracked_for_device:
                untracked[device_name] = {
                    "commands": untracked_for_device,
                    "count": len(untracked_for_device),
                }

        return jsonify(
            {
                "untracked": untracked,
                "total_count": sum(d["count"] for d in untracked.values()),
            }
        )

    except Exception as e:
        logger.error(f"Error getting untracked commands: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/commands/import", methods=["POST"])
def import_commands():
    """Import untracked commands into a device's metadata"""
    try:
        data = request.json
        logger.info(f"📥 Import request data: {data}")

        device_id = data.get("device_id")  # Target device to import into
        source_device = data.get("source_device")  # Broadlink device name
        commands = data.get("commands", [])  # List of command names to import

        logger.info(
            f"📥 Parsed: device_id={device_id}, source_device={source_device}, commands={commands}"
        )

        if not device_id or not source_device or not commands:
            error_msg = f"Missing required fields: device_id={device_id}, source_device={source_device}, commands={commands}"
            logger.error(f"❌ {error_msg}")
            return (
                jsonify(
                    {
                        "success": False,
                        "error": error_msg,
                    }
                ),
                400,
            )

        device_manager = current_app.config.get("device_manager")
        web_server = get_web_server()

        if not device_manager or not web_server:
            logger.error("❌ Device manager or web server not available")
            return jsonify({"error": "Required services not available"}), 500

        # Get device from device_manager
        entity_data = device_manager.get_device(device_id)

        if not entity_data:
            logger.error(f"❌ Device '{device_id}' not found")
            return (
                jsonify({"error": f"Device '{device_id}' not found in device manager"}),
                404,
            )

        # Get commands from Broadlink storage
        logger.info(
            f"📦 Fetching commands from Broadlink storage for device '{source_device}'..."
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(
            web_server._get_all_broadlink_commands()
        )
        loop.close()

        storage_commands = broadlink_commands.get(source_device, {})
        logger.info(
            f"📦 Found {len(storage_commands)} commands in storage for '{source_device}'"
        )

        # Add commands to device metadata with proper data
        device_commands = entity_data.get("commands", {})
        imported_count = 0

        for cmd in commands:
            if cmd in storage_commands:
                cmd_data = storage_commands[cmd]
                cmd_type = detect_command_type(cmd_data)
                device_commands[cmd] = {
                    "data": cmd_data,
                    "type": cmd_type,
                    "command_type": cmd_type,
                    "name": cmd,
                }
                imported_count += 1
                logger.info(f"  ✅ Imported '{cmd}' ({cmd_type})")
            else:
                logger.warning(f"  ⚠️ Command '{cmd}' not found in storage")

        entity_data["commands"] = device_commands

        # Save to device_manager
        device_manager.update_device(device_id, entity_data)

        logger.info(
            f"✅ Imported {imported_count} commands from '{source_device}' to device '{device_id}'"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Imported {imported_count} commands successfully",
                "imported_count": imported_count,
            }
        )

    except Exception as e:
        logger.error(f"❌ Error importing commands: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/sync", methods=["POST"])
def sync_commands():
    """Sync all device commands with Broadlink storage"""
    try:
        logger.info("🔄 Starting command sync...")
        device_manager = current_app.config.get("device_manager")
        web_server = get_web_server()

        if not all([device_manager, web_server]):
            logger.error("❌ Required services not available")
            return jsonify({"error": "Required services not available"}), 500

        # Get all commands from Broadlink storage
        logger.info("📦 Fetching commands from Broadlink storage...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(
            web_server._get_all_broadlink_commands()
        )
        loop.close()

        logger.info(f"📦 Found commands for devices: {list(broadlink_commands.keys())}")

        synced_devices = []
        total_added = 0
        total_removed = 0
        total_updated = 0  # Track commands that had type updated

        # Sync managed devices (from device_manager - devices.json)
        managed_devices = device_manager.get_all_devices()
        logger.info(
            f"📋 Found {len(managed_devices)} managed devices: {list(managed_devices.keys())}"
        )

        for device_id, device_data in managed_devices.items():
            device_name = device_data.get("device") or device_id
            logger.info(
                f"🔍 Checking managed device '{device_id}' (storage name: '{device_name}')"
            )

            storage_commands = broadlink_commands.get(device_name, {})
            tracked_commands = device_data.get("commands", {})

            commands_to_add = {}
            commands_to_update = {}

            for cmd_name, cmd_data in storage_commands.items():
                cmd_type = detect_command_type(cmd_data)

                if cmd_name not in tracked_commands:
                    # New command - add it
                    commands_to_add[cmd_name] = {
                        "command_type": cmd_type,
                        "type": cmd_type,
                    }
                else:
                    # Existing command - check if type needs updating
                    existing_cmd = tracked_commands[cmd_name]
                    if isinstance(existing_cmd, dict):
                        existing_type = existing_cmd.get(
                            "command_type"
                        ) or existing_cmd.get("type")
                    else:
                        existing_type = None

                    if existing_type != cmd_type:
                        # Type mismatch - update it
                        commands_to_update[cmd_name] = {
                            "command_type": cmd_type,
                            "type": cmd_type,
                        }

            commands_to_remove = [
                cmd_name
                for cmd_name in tracked_commands.keys()
                if cmd_name not in storage_commands
            ]

            if commands_to_add or commands_to_remove or commands_to_update:
                updated_commands = {**tracked_commands}

                for cmd_name, cmd_data in commands_to_add.items():
                    updated_commands[cmd_name] = cmd_data
                    total_added += 1

                for cmd_name, cmd_data in commands_to_update.items():
                    updated_commands[cmd_name] = cmd_data
                    total_updated += 1
                    logger.info(
                        f"  ✏️ Updated type for '{cmd_name}' to {cmd_data['type']}"
                    )

                for cmd_name in commands_to_remove:
                    del updated_commands[cmd_name]
                    total_removed += 1

                device_data["commands"] = updated_commands
                device_manager.update_device(device_id, device_data)

                synced_devices.append(
                    {
                        "device_id": device_id,
                        "device_name": device_name,
                        "added": len(commands_to_add),
                        "updated": len(commands_to_update),
                        "removed": len(commands_to_remove),
                    }
                )

        logger.info(
            f"✅ Command sync complete: {len(synced_devices)} devices updated, "
            f"{total_added} added, {total_updated} updated, {total_removed} removed"
        )

        return jsonify(
            {
                "success": True,
                "synced_devices": synced_devices,
                "total_devices": len(synced_devices),
                "total_added": total_added,
                "total_updated": total_updated,
                "total_removed": total_removed,
            }
        )

    except Exception as e:
        logger.error(f"Error syncing commands: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def detect_command_type(command_data):
    """
    Detect command type (IR/RF) from Broadlink command data.

    RF commands can start with various byte patterns:
    - 0x26 0x01+ (base64: Jg but NOT JgA) - Standard RF
    - 0xb2 (base64: sg, sc, etc.) - RF 433MHz
    - 0xd7 (base64: 1w, 10, etc.) - RF 315MHz

    IR commands:
    - 0x26 0x00 (base64: JgA) - Standard IR

    More reliable detection based on byte analysis.
    """
    if isinstance(command_data, str):
        import base64

        try:
            # Decode base64 to get raw bytes
            raw_bytes = base64.b64decode(command_data)

            if len(raw_bytes) < 2:
                return "ir"  # Too short, default to IR

            # Check first byte
            first_byte = raw_bytes[0]
            second_byte = raw_bytes[1] if len(raw_bytes) > 1 else 0x00

            # RF command patterns
            # 0xb0-0xbf range = RF 433MHz (base64 starts with 's')
            if 0xB0 <= first_byte <= 0xBF:
                logger.debug(f"Detected RF 433MHz command (0x{first_byte:02x} prefix)")
                return "rf"
            # 0xd7 = RF 315MHz
            elif first_byte == 0xD7:
                logger.debug(f"Detected RF 315MHz command (0xd7 prefix)")
                return "rf"
            elif first_byte == 0x26:
                if second_byte == 0x00:
                    # IR command (0x26 0x00)
                    return "ir"
                else:
                    # RF command (0x26 followed by non-zero)
                    logger.debug(
                        f"Detected RF command (0x26 0x{second_byte:02x} prefix)"
                    )
                    return "rf"

            # Fallback: check base64 prefix patterns
            # IR: Starts with 'JgA'
            if command_data.startswith("JgA"):
                return "ir"
            # RF: Various patterns
            elif (
                command_data.startswith("Jg")
                or command_data.startswith("Jh")
                or command_data.startswith("sg")
                or command_data.startswith("sc")
                or command_data.startswith("1w")
                or command_data.startswith("10")
            ):
                return "rf"

            # Additional heuristic: RF commands are typically longer
            if len(command_data) > 200:
                return "rf"

        except Exception as e:
            logger.debug(f"Error decoding command for type detection: {e}")
            # Fallback to simple heuristic
            if command_data.startswith("JgA"):
                return "ir"
            elif (
                command_data.startswith("Jg")
                or command_data.startswith("Jh")
                or command_data.startswith("sg")
                or command_data.startswith("sc")
                or command_data.startswith("1w")
                or command_data.startswith("10")
            ):
                return "rf"

    return "ir"  # Default to IR if we can't determine


# Direct Learning Endpoints (New Hybrid Approach)


@api_bp.route("/commands/learn/direct/stream", methods=["POST"])
def learn_command_direct_stream():
    """Learn a command with SSE progress updates"""
    from flask import Response, stream_with_context

    data = request.json
    device_id = data.get("device_id")
    entity_id = data.get("entity_id")
    command_name = data.get("command_name")
    command_type = data.get("command_type", "ir")

    def generate():
        try:
            from broadlink_learner import BroadlinkLearner
            from broadlink_device_manager import BroadlinkDeviceManager
            from device_manager import DeviceManager

            yield f"data: {json.dumps({'status': 'starting', 'message': 'Initializing...'})}\n\n"

            if not all([device_id, entity_id, command_name]):
                yield f"data: {json.dumps({'status': 'error', 'message': 'Missing required fields'})}\n\n"
                return

            # Get HA config
            web_server = get_web_server()
            ha_url = web_server.ha_url
            ha_token = web_server.ha_token

            # Get device connection info (try cache first)
            connection_info = web_server.get_cached_connection_info(entity_id)

            if not connection_info:
                yield f"data: {json.dumps({'status': 'connecting', 'message': 'Connecting to device...'})}\n\n"
                device_manager_bl = BroadlinkDeviceManager(ha_url, ha_token)
                connection_info = device_manager_bl.get_device_connection_info(
                    entity_id
                )

                if connection_info:
                    # Cache for future use
                    web_server.cache_connection_info(entity_id, connection_info)
            else:
                yield f"data: {json.dumps({'status': 'connecting', 'message': 'Using cached connection...'})}\n\n"

            if not connection_info:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Could not get connection info'})}\n\n"
                return

            # Create learner
            learner = BroadlinkLearner(
                host=connection_info["host"],
                mac=connection_info["mac_bytes"],
                device_type=connection_info["type"],
            )

            # Authenticate
            if not learner.authenticate():
                yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to authenticate'})}\n\n"
                return

            yield f"data: {json.dumps({'status': 'ready', 'message': f'Ready to learn {command_type.upper()} command'})}\n\n"

            # Learn command with progress
            if command_type == "rf":
                # Create a list to capture progress messages
                progress_messages = []

                def progress_handler(message, step):
                    progress_messages.append((message, step))

                # Start RF learning in a thread so we can yield progress
                import threading

                result_container = [None]

                def learn_thread():
                    result_container[0] = learner.learn_rf_command_with_progress(
                        timeout=30, progress_callback=progress_handler
                    )

                thread = threading.Thread(target=learn_thread)
                thread.start()

                # Poll for progress updates
                last_message_count = 0
                while thread.is_alive():
                    time.sleep(0.5)
                    if len(progress_messages) > last_message_count:
                        for msg, step in progress_messages[last_message_count:]:
                            yield f"data: {json.dumps({'status': 'learning', 'message': msg, 'step': step})}\n\n"
                        last_message_count = len(progress_messages)

                thread.join()
                result = result_container[0]

                if result:
                    base64_data, frequency = result
                    yield f"data: {json.dumps({'status': 'captured', 'message': f'RF command captured at {frequency} MHz', 'frequency': frequency})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Timeout - no RF signal detected'})}\n\n"
                    return
            else:
                yield f"data: {json.dumps({'status': 'learning', 'message': 'Waiting for IR signal...', 'step': 'capture'})}\n\n"
                result = learner.learn_ir_command(timeout=30)
                if result:
                    base64_data = result
                    frequency = None
                    yield f"data: {json.dumps({'status': 'captured', 'message': 'IR command captured'})}\n\n"
                else:
                    yield f"data: {json.dumps({'status': 'error', 'message': 'Timeout - no IR signal detected'})}\n\n"
                    return

            # Save command
            yield f"data: {json.dumps({'status': 'saving', 'message': 'Saving command...'})}\n\n"

            device_manager = DeviceManager(
                storage_path=str(web_server.broadlink_manager_path)
            )
            success = device_manager.add_learned_command(
                device_id=device_id,
                command_name=command_name,
                command_data=base64_data,
                command_type=command_type,
                frequency=frequency,
            )

            if not success:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Failed to save command'})}\n\n"
                return

            # Update connection info
            device_manager.update_device_connection_info(
                device_id,
                {
                    "host": connection_info["host"],
                    "mac": connection_info["mac"],
                    "type": connection_info["type"],
                    "type_hex": connection_info["type_hex"],
                    "model": connection_info["model"],
                },
            )

            yield f"data: {json.dumps({'status': 'complete', 'message': 'Command learned successfully!', 'command_name': command_name})}\n\n"

        except Exception as e:
            logger.error(f"Error in SSE learning: {e}", exc_info=True)
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")


@api_bp.route("/commands/learn/direct", methods=["POST"])
def learn_command_direct():
    """
    Learn a command directly from Broadlink device

    Request body:
    {
        "device_id": "living_room_tv",
        "entity_id": "remote.living_room_rm4_pro",
        "command_name": "power",
        "command_type": "ir"  // or "rf"
    }

    Returns:
    {
        "success": true,
        "command_name": "power",
        "command_type": "ir",
        "data": "scBIAdieBgALFgsXFwsXDAoXFwsXCwoXGAoL...",
        "data_length": 444,
        "frequency": 433.92  // RF only
    }
    """
    try:
        from broadlink_learner import BroadlinkLearner
        from broadlink_device_manager import BroadlinkDeviceManager
        from device_manager import DeviceManager

        data = request.get_json()
        device_id = data.get("device_id")
        entity_id = data.get("entity_id")
        command_name = data.get("command_name")
        command_type = data.get("command_type", "ir")

        if not all([device_id, entity_id, command_name]):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "Missing required fields: device_id, entity_id, command_name",
                    }
                ),
                400,
            )

        if command_type not in ["ir", "rf"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": 'Invalid command_type. Must be "ir" or "rf"',
                    }
                ),
                400,
            )

        # Get HA config
        web_server = get_web_server()
        ha_url = web_server.ha_url
        ha_token = web_server.ha_token

        # Get device connection info (try cache first)
        connection_info = web_server.get_cached_connection_info(entity_id)

        if not connection_info:
            device_manager_bl = BroadlinkDeviceManager(ha_url, ha_token)
            connection_info = device_manager_bl.get_device_connection_info(entity_id)

            if connection_info:
                # Cache for future use
                web_server.cache_connection_info(entity_id, connection_info)

        if not connection_info:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Could not get connection info for {entity_id}",
                    }
                ),
                404,
            )

        # Create learner
        learner = BroadlinkLearner(
            host=connection_info["host"],
            mac=connection_info["mac_bytes"],
            device_type=connection_info["type"],
        )

        # Authenticate
        if not learner.authenticate():
            return (
                jsonify(
                    {"success": False, "error": "Failed to authenticate with device"}
                ),
                500,
            )

        # Learn command
        logger.info(
            f"Learning {command_type} command '{command_name}' for device {device_id}"
        )

        if command_type == "ir":
            result = learner.learn_ir_command(timeout=30)
            if result:
                base64_data = result
                frequency = None
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Timeout - no IR signal detected within 30 seconds",
                        }
                    ),
                    408,
                )
        else:  # RF
            result = learner.learn_rf_command(timeout=30)
            if result:
                base64_data, frequency = result
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "Timeout - no RF signal detected within 30 seconds",
                        }
                    ),
                    408,
                )

        # Save to devices.json
        device_manager = DeviceManager(
            storage_path=str(web_server.broadlink_manager_path)
        )
        success = device_manager.add_learned_command(
            device_id=device_id,
            command_name=command_name,
            command_data=base64_data,
            command_type=command_type,
            frequency=frequency,
        )

        if not success:
            return (
                jsonify(
                    {"success": False, "error": "Failed to save command to storage"}
                ),
                500,
            )

        # Also update connection info in device
        device_manager.update_device_connection_info(
            device_id,
            {
                "host": connection_info["host"],
                "mac": connection_info["mac"],
                "type": connection_info["type"],
                "type_hex": connection_info["type_hex"],
                "model": connection_info["model"],
            },
        )

        response = {
            "success": True,
            "command_name": command_name,
            "command_type": command_type,
            "data": base64_data,
            "data_length": len(base64_data),
        }

        if frequency:
            response["frequency"] = frequency

        logger.info(
            f"Successfully learned command '{command_name}' ({len(base64_data)} chars)"
        )
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error learning command: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/test/direct", methods=["POST"])
def test_command_direct():
    """
    Test a command by sending it directly to the device

    Request body:
    {
        "device_id": "living_room_tv",
        "entity_id": "remote.living_room_rm4_pro",
        "command_name": "power"
    }

    Returns:
    {
        "success": true,
        "message": "Command sent successfully"
    }
    """
    try:
        from broadlink_learner import BroadlinkLearner
        from broadlink_device_manager import BroadlinkDeviceManager
        from device_manager import DeviceManager

        data = request.get_json()
        device_id = data.get("device_id")
        entity_id = data.get("entity_id")
        command_name = data.get("command_name")

        if not all([device_id, entity_id, command_name]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Get web server for storage path
        web_server = get_web_server()

        # Get command data and device info
        device_manager = DeviceManager(
            storage_path=str(web_server.broadlink_manager_path)
        )
        command_data = device_manager.get_command_data(device_id, command_name)

        if not command_data:
            return (
                jsonify(
                    {"success": False, "error": f"Command {command_name} not found"}
                ),
                404,
            )

        # Try cache first, then stored connection, then discovery
        connection_info = web_server.get_cached_connection_info(entity_id)

        if not connection_info:
            # Check if device has stored connection info
            device_info = device_manager.get_device(device_id)
            stored_connection = device_info.get("connection") if device_info else None

            if stored_connection and stored_connection.get("host"):
                # Use stored connection info
                logger.info(f"Using stored connection info for device {device_id}")
                connection_info = {
                    "host": stored_connection["host"],
                    "mac_bytes": bytes.fromhex(
                        stored_connection["mac"].replace(":", "")
                    ),
                    "type": stored_connection.get("type", 0x2712),  # Default RM type
                }
            else:
                # Fall back to discovery
                logger.info(f"No stored connection, discovering device for {entity_id}")
                device_manager_bl = BroadlinkDeviceManager(
                    web_server.ha_url, web_server.ha_token
                )
                connection_info = device_manager_bl.get_device_connection_info(
                    entity_id
                )

            if connection_info:
                # Cache for future use
                web_server.cache_connection_info(entity_id, connection_info)

        if not connection_info:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Could not get connection info for {entity_id}",
                    }
                ),
                404,
            )

        # Create learner and test
        learner = BroadlinkLearner(
            host=connection_info["host"],
            mac=connection_info["mac_bytes"],
            device_type=connection_info["type"],
        )

        if not learner.authenticate():
            return (
                jsonify(
                    {"success": False, "error": "Failed to authenticate with device"}
                ),
                500,
            )

        if learner.test_command(command_data):
            # Update test status
            device_manager.update_command_test_status(device_id, command_name, "direct")

            return jsonify(
                {
                    "success": True,
                    "message": "Command sent successfully via direct connection",
                }
            )
        else:
            return jsonify({"success": False, "error": "Failed to send command"}), 500

    except Exception as e:
        logger.error(f"Error testing command: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/commands/test/ha", methods=["POST"])
def test_command_ha():
    """
    Test a command via HA remote.send_command service

    Request body:
    {
        "device_id": "living_room_tv",
        "entity_id": "remote.living_room_rm4_pro",
        "command_name": "power"
    }

    Returns:
    {
        "success": true,
        "message": "Command sent successfully"
    }
    """
    try:
        from device_manager import DeviceManager
        import requests

        data = request.get_json()
        device_id = data.get("device_id")
        entity_id = data.get("entity_id")
        command_name = data.get("command_name")

        if not all([device_id, entity_id, command_name]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400

        # Get web server for storage path
        web_server = get_web_server()

        # Get command data
        device_manager = DeviceManager(
            storage_path=str(web_server.broadlink_manager_path)
        )
        command_data = device_manager.get_command_data(device_id, command_name)

        if not command_data:
            return (
                jsonify(
                    {"success": False, "error": f"Command {command_name} not found"}
                ),
                404,
            )

        # Send via HA
        web_server = get_web_server()
        ha_url = web_server.ha_url
        ha_token = web_server.ha_token

        headers = {
            "Authorization": f"Bearer {ha_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "entity_id": entity_id,
            "command": command_data,  # Raw base64, no prefix
        }

        response = requests.post(
            f"{ha_url}/api/services/remote/send_command",
            headers=headers,
            json=payload,
            timeout=10,
        )

        if response.status_code == 200:
            # Update test status
            device_manager.update_command_test_status(device_id, command_name, "ha")

            return jsonify(
                {
                    "success": True,
                    "message": "Command sent successfully via Home Assistant",
                }
            )
        else:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"HA API returned status {response.status_code}",
                    }
                ),
                response.status_code,
            )

    except Exception as e:
        logger.error(f"Error testing command via HA: {e}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
