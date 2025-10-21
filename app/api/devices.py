"""
Device API endpoints
"""

import logging
import re
import json
import io
import zipfile
from flask import jsonify, request, current_app, send_file
from . import api_bp

logger = logging.getLogger(__name__)


def get_storage_manager():
    """Get storage manager from Flask app context"""
    return current_app.config.get("storage_manager")


def get_device_manager():
    """Get device manager from Flask app context"""
    return current_app.config.get("device_manager")


def normalize_device_name(name):
    """
    Convert display name to storage-safe name
    Examples:
        "Living Room TV" -> "living_room_tv"
        "Tony's Office" -> "tonys_office"
        "Master Bedroom!" -> "master_bedroom"
    """
    # Remove or replace special characters (keep only alphanumeric and spaces)
    name = re.sub(r"[^\w\s]", "", name)
    # Collapse multiple spaces into single space
    name = re.sub(r"\s+", " ", name)
    # Replace spaces with underscores and convert to lowercase
    return name.strip().replace(" ", "_").lower()


@api_bp.route("/devices", methods=["GET"])
def get_devices():
    """Get all managed devices"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({"error": "Storage manager not available"}), 500

        # Get all entities from storage (reload from disk to get latest data)
        entities = storage.get_all_entities(reload=True)

        # Convert entities to device format for frontend
        devices = []
        for entity_id, entity_data in entities.items():
            try:
                # Extract device name safely
                device_name = entity_data.get("device")
                if not device_name:
                    # Fallback: extract from entity_id
                    device_name = (
                        entity_id.split(".")[1] if "." in entity_id else entity_id
                    )

                device = {
                    "id": entity_id,
                    "name": entity_data.get("name")
                    or entity_data.get("friendly_name", entity_id),
                    "entity_type": entity_data.get("entity_type", "switch"),
                    "area": entity_data.get("area", ""),
                    "icon": entity_data.get("icon", ""),
                    "broadlink_entity": entity_data.get("broadlink_entity", ""),
                    "device": device_name,  # Add device field for command learning
                    "commands": entity_data.get("commands", {}),
                    "enabled": entity_data.get("enabled", True),
                }
                devices.append(device)
            except Exception as e:
                logger.error(f"Error processing entity {entity_id}: {e}")
                continue

        return jsonify({"devices": devices})

    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/<device_id>", methods=["GET"])
def get_device(device_id):
    """Get a specific device"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({"error": "Storage manager not available"}), 500

        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({"error": "Device not found"}), 404

        device = {
            "id": device_id,
            "name": entity_data.get("name")
            or entity_data.get("friendly_name", device_id),
            "entity_type": entity_data.get("entity_type", "switch"),
            "area": entity_data.get("area", ""),
            "icon": entity_data.get("icon", ""),
            "broadlink_entity": entity_data.get("broadlink_entity", ""),
            "commands": entity_data.get("commands", {}),
            "enabled": entity_data.get("enabled", True),
        }

        return jsonify({"device": device})

    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices", methods=["POST"])
def create_device():
    """Create a new managed device"""
    try:
        data = request.json
        storage = get_storage_manager()
        if not storage:
            return jsonify({"error": "Storage manager not available"}), 500

        # Generate entity_id from name
        name = data.get("name", "")
        entity_type = data.get("entity_type", "switch")

        # If device field is provided (e.g., from adoption), use it as-is
        # Otherwise, normalize the name for the device field
        device_name = data.get("device")
        if not device_name:
            device_name = normalize_device_name(name)

        # Use device_name as entity_id (without entity type prefix)
        # The entity generator will use this as the key in the YAML
        entity_id = device_name

        # Check if already exists
        if storage.get_entity(entity_id):
            return jsonify({"error": "Device with this name already exists"}), 400

        # Create entity data
        entity_data = {
            "entity_type": entity_type,
            "device": device_name,  # Broadlink storage device name (must match .storage file)
            "broadlink_entity": data.get("broadlink_entity", ""),
            "area": data.get("area", ""),
            "friendly_name": name,  # Display name
            "name": name,  # Display name
            "icon": data.get("icon", ""),
            "commands": data.get("commands", {}),  # Include commands if provided
            "enabled": True,
        }

        # Save to storage
        storage.save_entity(entity_id, entity_data)

        return (
            jsonify({"success": True, "device": {"id": entity_id, **entity_data}}),
            201,
        )

    except Exception as e:
        logger.error(f"Error creating device: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/<device_id>", methods=["PUT"])
def update_device(device_id):
    """Update an existing device"""
    try:
        data = request.json
        storage = get_storage_manager()
        if not storage:
            return jsonify({"error": "Storage manager not available"}), 500

        # Get existing entity
        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({"error": "Device not found"}), 404

        # Check if we need to rename the entity_id (only if no commands learned)
        new_entity_id = device_id
        if "name" in data:
            # Check if commands exist in metadata (this includes optimistically added commands)
            # This is more reliable than checking storage files which update slowly in standalone mode
            current_commands = entity_data.get("commands", {})
            has_commands = current_commands and len(current_commands) > 0

            if has_commands:
                logger.info(
                    f"Device '{device_id}' has {len(current_commands)} commands in metadata - rename blocked"
                )

            if not has_commands:
                # No commands in metadata yet - safe to rename entity_id
                new_device_name = normalize_device_name(data["name"])
                # Use device_name as entity_id (without entity type prefix)
                new_entity_id = new_device_name

                # If entity_id is changing, we need to delete old and create new
                if new_entity_id != device_id:
                    logger.info(
                        f"Renaming entity from '{device_id}' to '{new_entity_id}' (no commands learned yet)"
                    )
                    # Delete old entity
                    storage.delete_entity(device_id)
                    # Update device field
                    entity_data["device"] = new_device_name

        # Update fields
        if "name" in data:
            entity_data["name"] = data["name"]
            entity_data["friendly_name"] = data["name"]
        if "entity_type" in data:
            entity_data["entity_type"] = data["entity_type"]
        if "area" in data:
            entity_data["area"] = data["area"]
        if "icon" in data:
            entity_data["icon"] = data["icon"]
        if "broadlink_entity" in data:
            entity_data["broadlink_entity"] = data["broadlink_entity"]
        if "enabled" in data:
            entity_data["enabled"] = data["enabled"]
        if "commands" in data:
            entity_data["commands"] = data["commands"]

        # Update SmartIR-specific fields
        device_type = entity_data.get("device_type", "broadlink")
        if device_type == "smartir":
            # Support both direct fields and smartir_config object
            smartir_config = data.get("smartir_config", {})

            if "manufacturer" in data or "manufacturer" in smartir_config:
                entity_data["manufacturer"] = data.get(
                    "manufacturer"
                ) or smartir_config.get("manufacturer", "")
            if "model" in data or "model" in smartir_config:
                entity_data["model"] = data.get("model") or smartir_config.get(
                    "model", ""
                )
            if "device_code" in data or "code_id" in smartir_config:
                entity_data["device_code"] = data.get(
                    "device_code"
                ) or smartir_config.get("code_id", "")
            if "controller_device" in data or "controller_device" in smartir_config:
                entity_data["controller_device"] = data.get(
                    "controller_device"
                ) or smartir_config.get("controller_device", "")

            # Optional climate-specific fields
            if "temperature_sensor" in data:
                entity_data["temperature_sensor"] = data["temperature_sensor"]
            if "humidity_sensor" in data:
                entity_data["humidity_sensor"] = data["humidity_sensor"]
            if "power_sensor" in data:
                entity_data["power_sensor"] = data["power_sensor"]

        # Save entity (with new ID if renamed, or same ID if not)
        storage.save_entity(new_entity_id, entity_data)

        return jsonify(
            {"success": True, "device": {"id": new_entity_id, **entity_data}}
        )

    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/<device_id>", methods=["DELETE"])
def delete_device(device_id):
    """Delete a device"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({"error": "Storage manager not available"}), 500

        # Check if exists
        if not storage.get_entity(device_id):
            return jsonify({"error": "Device not found"}), 404

        # Delete the device
        storage.delete_entity(device_id)

        return jsonify({"success": True, "message": f"Device {device_id} deleted"})

    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/find-broadlink-owner", methods=["POST"])
def find_broadlink_owner():
    """Find which Broadlink device owns a specific device's commands"""
    try:
        import asyncio

        data = request.json
        device_name = data.get("device_name")

        if not device_name:
            return jsonify({"error": "device_name is required"}), 400

        web_server = current_app.config.get("web_server")
        if not web_server:
            return jsonify({"error": "Web server not available"}), 500

        # Use the existing method to find the Broadlink entity
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_entity = loop.run_until_complete(
            web_server._find_broadlink_entity_for_device(device_name)
        )
        loop.close()

        return jsonify(
            {"broadlink_entity": broadlink_entity, "device_name": device_name}
        )

    except Exception as e:
        logger.error(f"Error finding Broadlink owner: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/discover", methods=["GET"])
def discover_untracked_devices():
    """Discover devices that exist in Broadlink storage but are not tracked in metadata"""
    try:
        import asyncio

        web_server = current_app.config.get("web_server")
        storage = get_storage_manager()

        if not storage or not web_server:
            return jsonify({"error": "Storage or web server not available"}), 500

        # Get all commands from Broadlink storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(
            web_server._get_all_broadlink_commands()
        )
        loop.close()

        # Get all tracked devices from device manager AND old metadata
        device_manager = get_device_manager()
        tracked_device_names = set()

        # Get devices from new device manager
        if device_manager:
            devices = device_manager.get_all_devices()
            for device_id, device_data in devices.items():
                # For Broadlink devices, the device_id IS the storage name (e.g., "samsung_model1")
                # For devices with area prefix, we need to extract just the device part
                if device_data.get("device_type") == "broadlink":
                    tracked_device_names.add(device_id)

        # Also check old metadata for backward compatibility
        entities = storage.get_all_entities()
        for entity_id, entity_data in entities.items():
            device_name = entity_data.get("device")
            if device_name:
                tracked_device_names.add(device_name)

        # Cleanup expired deletion cache entries
        web_server._cleanup_deletion_cache()

        # Find untracked devices (filter out devices where ALL commands are recently deleted)
        untracked_devices = []
        for device_name, commands in broadlink_commands.items():
            if device_name not in tracked_device_names:
                # Filter out recently deleted commands
                remaining_commands = [
                    cmd
                    for cmd in commands.keys()
                    if not web_server._is_recently_deleted(device_name, cmd)
                ]

                # Only include device if it has commands that aren't recently deleted
                if remaining_commands:
                    untracked_devices.append(
                        {
                            "device_name": device_name,
                            "command_count": len(remaining_commands),
                            "commands": remaining_commands,
                        }
                    )

        return jsonify(
            {"untracked_devices": untracked_devices, "count": len(untracked_devices)}
        )

    except Exception as e:
        logger.error(f"Error discovering untracked devices: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/untracked/<device_name>", methods=["DELETE"])
def delete_untracked_device(device_name):
    """Delete all commands for an untracked device from Broadlink storage"""
    try:
        import asyncio

        web_server = current_app.config.get("web_server")

        if not web_server:
            return jsonify({"error": "Web server not available"}), 500

        # Get the device's commands from Broadlink storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(
            web_server._get_all_broadlink_commands()
        )

        # Check if device exists
        if device_name not in broadlink_commands:
            loop.close()
            return jsonify({"error": f"Device {device_name} not found"}), 404

        commands = broadlink_commands[device_name]

        # Find which Broadlink entity owns these commands
        broadlink_entity = loop.run_until_complete(
            web_server._find_broadlink_entity_for_device(device_name)
        )

        if not broadlink_entity:
            loop.close()
            return (
                jsonify(
                    {
                        "error": f"Could not determine Broadlink entity for device {device_name}"
                    }
                ),
                400,
            )

        # Delete all commands
        deleted_count = 0
        failed_commands = []

        for command_name in commands.keys():
            delete_data = {
                "entity_id": broadlink_entity,
                "device": device_name,
                "command": command_name,
            }

            result = loop.run_until_complete(web_server._delete_command(delete_data))

            if result.get("success"):
                deleted_count += 1
            else:
                failed_commands.append(command_name)

        loop.close()

        if failed_commands:
            return (
                jsonify(
                    {
                        "success": False,
                        "deleted_count": deleted_count,
                        "failed_commands": failed_commands,
                        "error": f"Failed to delete {len(failed_commands)} command(s)",
                    }
                ),
                207,
            )  # Multi-Status

        return jsonify(
            {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"Successfully deleted {deleted_count} command(s) from device {device_name}",
            }
        )

    except Exception as e:
        logger.error(f"Error deleting untracked device: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/managed", methods=["POST"])
def create_managed_device():
    """Create a new managed device (supports both Broadlink and SmartIR types)"""
    try:
        data = request.json
        logger.info(f"Received device creation request: {data}")
        device_manager = get_device_manager()

        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        # Extract device data - support both 'name' and 'device_name' for compatibility
        name = data.get("device_name") or data.get("name", "")
        storage_name = data.get("device")  # Storage name for adopted devices
        entity_type = data.get("entity_type", "switch")
        device_type = data.get("device_type", "broadlink")
        area = data.get("area_name") or data.get("area", "")
        area_id = data.get("area_id", "")
        icon = data.get("icon", "")

        if not name:
            return jsonify({"error": "Device name is required"}), 400

        # Use storage name as device ID if provided (adopted device)
        # Otherwise generate new ID from area + device name
        if storage_name:
            device_id = storage_name
        else:
            # Generate device_id (includes area to allow same device name in different areas)
            area_id_for_gen = area_id or (
                area.lower().replace(" ", "_") if area else ""
            )
            device_id = device_manager.generate_device_id(area_id_for_gen, name)

        # Check if device already exists
        existing_device = device_manager.get_device(device_id)
        if existing_device:
            # Provide helpful error message
            area_name = area if area else "No Area"
            return (
                jsonify(
                    {
                        "error": (
                            f'A device named "{name}" already exists in {area_name}. '
                            "Please use a different name or choose a different area."
                        ),
                        "existing_device_id": device_id,
                        "suggestion": 'Try adding a room identifier to the name (e.g., "Stereo - Living Room")',
                    }
                ),
                409,
            )  # 409 Conflict is more appropriate than 400

        # Build device data based on type
        device_data = {
            "name": name,
            "entity_type": entity_type,
            "device_type": device_type,
            "area": area,
            "icon": icon,
        }

        if device_type == "smartir":
            # SmartIR device - validate and add SmartIR-specific fields
            # Support both direct fields and smartir_config object
            smartir_config = data.get("smartir_config", {})
            device_data.update(
                {
                    "manufacturer": data.get("manufacturer")
                    or smartir_config.get("manufacturer", ""),
                    "model": data.get("model") or smartir_config.get("model", ""),
                    "device_code": data.get("device_code")
                    or smartir_config.get("code_id", ""),
                    "controller_device": data.get("controller_device")
                    or smartir_config.get("controller_device", ""),
                }
            )

            # Optional fields for climate entities
            if entity_type == "climate":
                if data.get("temperature_sensor"):
                    device_data["temperature_sensor"] = data["temperature_sensor"]
                if data.get("humidity_sensor"):
                    device_data["humidity_sensor"] = data["humidity_sensor"]

            # Validate SmartIR device data
            is_valid, error_msg = device_manager.validate_smartir_device(device_data)
            if not is_valid:
                return jsonify({"error": error_msg}), 400

        else:
            # Broadlink device - add Broadlink-specific fields
            broadlink_entity = data.get("broadlink_entity", "")
            if not broadlink_entity:
                return (
                    jsonify(
                        {"error": "broadlink_entity is required for Broadlink devices"}
                    ),
                    400,
                )

            device_data["broadlink_entity"] = broadlink_entity

            # Include commands if provided (for adopted devices)
            commands = data.get("commands", {})
            if commands:
                device_data["commands"] = commands

        # Create the device
        if device_manager.create_device(device_id, device_data):
            return (
                jsonify({"success": True, "device": {"id": device_id, **device_data}}),
                201,
            )
        else:
            return jsonify({"error": "Failed to create device"}), 500

    except Exception as e:
        logger.error(f"Error creating managed device: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/managed", methods=["GET"])
def get_managed_devices():
    """Get all managed devices from device manager"""
    try:
        device_manager = get_device_manager()

        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        # Get all devices
        devices = device_manager.get_all_devices()

        # Convert to list format for frontend
        device_list = []
        for device_id, device_data in devices.items():
            device_list.append({"id": device_id, **device_data})

        return jsonify(
            {"success": True, "devices": device_list, "count": len(device_list)}
        )

    except Exception as e:
        logger.error(f"Error getting managed devices: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/managed/<device_id>", methods=["GET"])
def get_managed_device(device_id):
    """Get a specific managed device"""
    try:
        device_manager = get_device_manager()

        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        device = device_manager.get_device(device_id)

        if not device:
            return jsonify({"error": "Device not found"}), 404

        return jsonify({"success": True, "device": {"id": device_id, **device}})

    except Exception as e:
        logger.error(f"Error getting managed device: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/managed/<device_id>", methods=["PUT"])
def update_managed_device(device_id):
    """Update a managed device"""
    try:
        device_manager = get_device_manager()

        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get existing device
        existing_device = device_manager.get_device(device_id)
        if not existing_device:
            return jsonify({"error": f"Device {device_id} not found"}), 404

        # Update device data (preserve device_type - it cannot be changed)
        updated_data = {
            **existing_device,
            **data,
            "device_type": existing_device.get(
                "device_type", "broadlink"
            ),  # Preserve device_type
        }

        # Handle SmartIR config if present
        if "smartir_config" in data and existing_device.get("device_type") == "smartir":
            smartir_config = data["smartir_config"]
            # Extract SmartIR fields from nested config to top level
            if "manufacturer" in smartir_config:
                updated_data["manufacturer"] = smartir_config["manufacturer"]
            if "model" in smartir_config:
                updated_data["model"] = smartir_config["model"]
            if "code_id" in smartir_config:
                updated_data["device_code"] = smartir_config["code_id"]
            if "controller_device" in smartir_config:
                updated_data["controller_device"] = smartir_config["controller_device"]
            # Remove the nested config object
            del updated_data["smartir_config"]

        # Update the device
        if device_manager.update_device(device_id, updated_data):
            return jsonify(
                {
                    "success": True,
                    "message": f"Device {device_id} updated",
                    "device": device_manager.get_device(device_id),
                }
            )
        else:
            return jsonify({"error": "Failed to update device"}), 500

    except Exception as e:
        logger.error(f"Error updating managed device: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/managed/<device_id>", methods=["DELETE"])
def delete_managed_device(device_id):
    """Delete a managed device and optionally its commands from Broadlink storage"""
    try:
        import asyncio
        import time

        device_manager = get_device_manager()
        web_server = current_app.config.get("web_server")

        if not device_manager:
            return jsonify({"error": "Device manager not available"}), 500

        # Check if we should also delete commands from Broadlink storage
        data = request.get_json() or {}
        delete_commands = data.get("delete_commands", False)

        # Get device info before deleting (to know which commands to delete)
        device = device_manager.get_device(device_id)
        if not device:
            return jsonify({"error": "Device not found"}), 404

        # Delete the device from metadata
        if not device_manager.delete_device(device_id):
            return jsonify({"error": "Failed to delete device"}), 500

        # If requested, also delete commands from Broadlink storage
        if delete_commands and device.get("device_type") == "broadlink" and web_server:
            commands = device.get("commands", {})
            broadlink_entity = device.get("broadlink_entity")

            if commands and broadlink_entity:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                for command_name in commands.keys():
                    try:
                        loop.run_until_complete(
                            web_server._delete_command(
                                {
                                    "entity_id": broadlink_entity,
                                    "device": device_id,
                                    "command": command_name,
                                }
                            )
                        )
                        logger.info(
                            f"Deleted command '{command_name}' from Broadlink storage"
                        )

                        # Mark command as recently deleted to filter from discovery
                        web_server._add_to_deletion_cache(device_id, command_name)
                    except Exception as cmd_error:
                        logger.warning(
                            f"Failed to delete command '{command_name}': {cmd_error}"
                        )

                loop.close()

                # Small delay to allow HA storage to sync (reduce race condition)
                time.sleep(0.5)

        return jsonify(
            {
                "success": True,
                "message": f"Device {device_id} deleted",
                "commands_deleted": delete_commands,
            }
        )

    except Exception as e:
        logger.error(f"Error deleting managed device: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/devices/<device_id>/sync-area", methods=["POST"])
def sync_device_area(device_id):
    """Sync area from Home Assistant entity registry"""
    import asyncio

    try:
        device_manager = get_device_manager()
        storage_manager = get_storage_manager()
        area_manager = current_app.config.get("area_manager")

        if not area_manager:
            return jsonify({"error": "Area manager not available"}), 500

        # Try to find device in device_manager first (SmartIR devices)
        device_data = None
        use_device_manager = False

        try:
            if device_manager:
                device_data = device_manager.get_device(device_id)
                if device_data:
                    use_device_manager = True
                    logger.info(f"Found device '{device_id}' in device_manager")
        except Exception as e:
            logger.warning(f"Error checking device_manager: {e}")

        # If not found, try storage_manager (Broadlink devices)
        try:
            if not device_data and storage_manager:
                device_data = storage_manager.get_entity(device_id)
                if device_data:
                    use_device_manager = False
                    logger.info(f"Found device '{device_id}' in storage_manager")
        except Exception as e:
            logger.warning(f"Error checking storage_manager: {e}")

        if not device_data:
            logger.warning(f"Device '{device_id}' not found in either manager")
            return jsonify({"error": "Device not found"}), 404

        # Build full entity_id
        entity_type = device_data.get("entity_type", "switch")
        full_entity_id = f"{entity_type}.{device_id}"

        logger.info(f"Syncing area for entity: {full_entity_id}")

        # Get entity details from HA (includes area_id)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            entity_details = loop.run_until_complete(
                area_manager.get_entity_details(full_entity_id)
            )

            if not entity_details:
                loop.close()
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": (
                                "Entity not found in HA registry. "
                                "Make sure entities are generated and HA has been restarted."
                            ),
                            "area": None,
                        }
                    ),
                    404,
                )

            area_id = entity_details.get("area_id")

            if area_id:
                # Get area name from area_id
                areas = loop.run_until_complete(
                    area_manager._send_ws_command("config/area_registry/list")
                )

                area_name = next(
                    (a["name"] for a in areas if a["area_id"] == area_id), None
                )

                # Update device data using appropriate manager
                device_data["area"] = area_name
                device_data["area_id"] = area_id

                if use_device_manager:
                    # Only pass the fields we want to update
                    updates = {"area": area_name, "area_id": area_id}
                    result = device_manager.update_device(device_id, updates)
                    logger.info(f"Device manager update result: {result}")
                else:
                    storage_manager.save_entity(device_id, device_data)

                manager_type = (
                    "device_manager" if use_device_manager else "storage_manager"
                )
                logger.info(
                    f"Synced area '{area_name}' for device '{device_id}' (using {manager_type})"
                )

                return jsonify(
                    {
                        "success": True,
                        "area": area_name,
                        "area_id": area_id,
                        "message": f"Area synced: {area_name}",
                    }
                )
            else:
                # No area assigned in HA
                device_data["area"] = ""
                device_data["area_id"] = None

                if use_device_manager:
                    # Only pass the fields we want to update
                    updates = {"area": "", "area_id": None}
                    result = device_manager.update_device(device_id, updates)
                    logger.info(f"Device manager update result: {result}")
                else:
                    storage_manager.save_entity(device_id, device_data)

                manager_type = (
                    "device_manager" if use_device_manager else "storage_manager"
                )
                logger.info(
                    f"No area assigned for device '{device_id}' in HA (using {manager_type})"
                )

                return jsonify(
                    {
                        "success": True,
                        "area": None,
                        "message": "No area assigned in Home Assistant",
                    }
                )
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Error syncing area for device {device_id}: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/diagnostics", methods=["GET"])
def get_diagnostics():
    """Get diagnostic information as JSON"""
    try:
        from diagnostics import DiagnosticsCollector

        device_manager = get_device_manager()
        storage_manager = get_storage_manager()
        area_manager = current_app.config.get("area_manager")
        web_server = current_app.config.get("web_server")
        storage_path = current_app.config.get(
            "storage_path", "/config/broadlink_manager"
        )

        collector = DiagnosticsCollector(
            storage_path, device_manager, storage_manager, area_manager, web_server
        )
        data = collector.collect_all()
        sanitized = collector.sanitize_data(data)

        return jsonify({"success": True, "diagnostics": sanitized})

    except Exception as e:
        logger.error(f"Error collecting diagnostics: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/diagnostics/markdown", methods=["GET"])
def get_diagnostics_markdown():
    """Get diagnostic information as markdown"""
    try:
        from diagnostics import DiagnosticsCollector

        device_manager = get_device_manager()
        storage_manager = get_storage_manager()
        area_manager = current_app.config.get("area_manager")
        web_server = current_app.config.get("web_server")
        storage_path = current_app.config.get(
            "storage_path", "/config/broadlink_manager"
        )

        collector = DiagnosticsCollector(
            storage_path, device_manager, storage_manager, area_manager, web_server
        )
        data = collector.collect_all()
        sanitized = collector.sanitize_data(data)
        markdown = collector.generate_markdown_report(sanitized)

        return jsonify({"success": True, "markdown": markdown})

    except Exception as e:
        logger.error(f"Error generating markdown diagnostics: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/diagnostics/download", methods=["GET"])
def download_diagnostics():
    """Download diagnostic bundle as ZIP file"""
    try:
        from diagnostics import DiagnosticsCollector
        from datetime import datetime

        device_manager = get_device_manager()
        storage_manager = get_storage_manager()
        area_manager = current_app.config.get("area_manager")
        web_server = current_app.config.get("web_server")
        storage_path = current_app.config.get(
            "storage_path", "/config/broadlink_manager"
        )

        collector = DiagnosticsCollector(
            storage_path, device_manager, storage_manager, area_manager, web_server
        )
        data = collector.collect_all()
        sanitized = collector.sanitize_data(data)
        markdown = collector.generate_markdown_report(sanitized)

        # Create ZIP file in memory
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add diagnostics JSON
            zf.writestr("diagnostics.json", json.dumps(sanitized, indent=2))

            # Add markdown report
            zf.writestr("README.md", markdown)

            # Add sanitized device data if available
            if device_manager:
                devices = device_manager.get_all_devices()
                # Remove sensitive command data
                sanitized_devices = {}
                for device_id, device_data in devices.items():
                    sanitized_device = device_data.copy()
                    if "commands" in sanitized_device:
                        sanitized_device["commands"] = {
                            cmd_name: {"type": cmd_data.get("command_type", "unknown")}
                            for cmd_name, cmd_data in sanitized_device[
                                "commands"
                            ].items()
                        }
                    sanitized_devices[device_id] = sanitized_device

                zf.writestr(
                    "devices_sanitized.json", json.dumps(sanitized_devices, indent=2)
                )

            # Add command structure (names only, no codes)
            if sanitized.get("command_structure"):
                zf.writestr(
                    "command_structure.json",
                    json.dumps(sanitized["command_structure"], indent=2),
                )

            # Add log entries if available
            if sanitized.get("errors") and (
                sanitized["errors"].get("errors") or sanitized["errors"].get("warnings")
            ):
                log_content = "# Recent Log Entries\n\n"
                if sanitized["errors"].get("errors"):
                    log_content += "## Errors\n\n"
                    for error in sanitized["errors"]["errors"]:
                        log_content += f"{error}\n"
                    log_content += "\n"
                if sanitized["errors"].get("warnings"):
                    log_content += "## Warnings\n\n"
                    for warning in sanitized["errors"]["warnings"]:
                        log_content += f"{warning}\n"
                zf.writestr("recent_logs.txt", log_content)

        memory_file.seek(0)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"broadlink_manager_diagnostics_{timestamp}.zip"

        return send_file(
            memory_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        logger.error(f"Error creating diagnostic bundle: {e}")
        return jsonify({"error": str(e)}), 500
