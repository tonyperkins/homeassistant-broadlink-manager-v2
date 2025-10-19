#!/usr/bin/env python3
"""
SmartIR API endpoints for Broadlink Manager Add-on
"""

import logging
import json
from pathlib import Path
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

# Blueprint will be initialized by web_server.py
smartir_bp = Blueprint("smartir", __name__, url_prefix="/api/smartir")


def _count_commands(commands_obj):
    """
    Recursively count all command codes in a SmartIR commands structure.

    SmartIR commands can be:
    - Flat: {"power": "JgBQAAA...", "volumeUp": "JgBQAAA..."}
    - Nested (climate): {"cool": {"16": {"auto": "JgBQAAA..."}}}

    Args:
        commands_obj: The commands object from SmartIR profile

    Returns:
        int: Total number of command codes
    """
    if not isinstance(commands_obj, dict):
        return 0

    count = 0
    for value in commands_obj.values():
        if isinstance(value, str):
            # This is an actual command code (base64 string)
            count += 1
        elif isinstance(value, dict):
            # This is a nested structure, recurse
            count += _count_commands(value)

    return count


def _extract_command_names(commands_obj, prefix=""):
    """
    Extract all command names from a SmartIR commands structure.

    Args:
        commands_obj: The commands object from SmartIR profile
        prefix: Prefix for nested command names

    Returns:
        list: List of command names
    """
    if not isinstance(commands_obj, dict):
        return []

    names = []
    for key, value in commands_obj.items():
        if isinstance(value, str):
            # This is an actual command - add the full path as name
            name = f"{prefix}{key}" if prefix else key
            names.append(name)
        elif isinstance(value, dict):
            # Nested structure - recurse with prefix
            new_prefix = f"{prefix}{key}_" if prefix else f"{key}_"
            names.extend(_extract_command_names(value, new_prefix))

    return names


def init_smartir_routes(smartir_detector, smartir_code_service=None):
    """Initialize SmartIR routes with detector instance and code service"""

    # Check if routes are already registered (for testing)
    if len(smartir_bp.deferred_functions) > 0:
        # Routes already registered, just return the blueprint
        return smartir_bp

    @smartir_bp.route("/status", methods=["GET"])
    def get_status():
        """Get SmartIR installation status"""
        try:
            status = smartir_detector.get_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Error getting SmartIR status: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms", methods=["GET"])
    def get_platforms():
        """Get available SmartIR platforms"""
        try:
            if not smartir_detector.is_installed():
                return jsonify({"installed": False, "platforms": [], "message": "SmartIR not installed"}), 200

            platforms = smartir_detector.get_supported_platforms()
            return jsonify({"installed": True, "platforms": platforms}), 200
        except Exception as e:
            logger.error(f"Error getting platforms: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/codes", methods=["GET"])
    def get_platform_codes(platform):
        """Get device codes for a specific platform"""
        try:
            if not smartir_detector.is_installed():
                return jsonify({"error": "SmartIR not installed"}), 404

            codes = smartir_detector.get_device_codes(platform)
            return jsonify({"platform": platform, "codes": codes, "count": len(codes)}), 200
        except Exception as e:
            logger.error(f"Error getting codes for {platform}: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/next-code", methods=["GET"])
    def get_next_code(platform):
        """Get next available custom code number for platform"""
        try:
            if not smartir_detector.is_installed():
                return jsonify({"error": "SmartIR not installed"}), 404

            next_code = smartir_detector.find_next_custom_code(platform)
            return jsonify({"platform": platform, "next_code": next_code}), 200
        except Exception as e:
            logger.error(f"Error getting next code: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/validate-code", methods=["POST"])
    def validate_code():
        """Validate a SmartIR code file"""
        try:
            data = request.get_json()
            platform = data.get("platform")
            code_number = data.get("code")

            if not platform or not code_number:
                return jsonify({"error": "Missing platform or code"}), 400

            result = smartir_detector.validate_code_file(platform, code_number)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Error validating code: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/install-instructions", methods=["GET"])
    def get_install_instructions():
        """Get SmartIR installation instructions"""
        try:
            instructions = smartir_detector.get_install_instructions()
            return jsonify(instructions), 200
        except Exception as e:
            logger.error(f"Error getting install instructions: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/refresh-index", methods=["POST"])
    def refresh_index():
        """Refresh the SmartIR device index from GitHub"""
        try:
            if smartir_code_service:
                result = smartir_code_service.refresh_device_index()
                return jsonify(result), 200 if result.get("success") else 500
            else:
                return jsonify({"success": False, "error": "SmartIR code service not available"}), 503
        except Exception as e:
            logger.error(f"Error refreshing device index: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @smartir_bp.route("/profiles", methods=["POST"])
    def save_profile():
        """Save a SmartIR device profile"""
        try:
            data = request.get_json()

            # Extract profile data
            platform = data.get("platform")
            profile_json = data.get("json")
            code_number = data.get("code_number")

            if not all([platform, profile_json, code_number]):
                return jsonify({"success": False, "error": "Missing required fields: platform, json, or code_number"}), 400

            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({"success": False, "error": "SmartIR is not installed"}), 404

            # Get SmartIR codes directory
            smartir_path = smartir_detector.smartir_path
            codes_dir = smartir_path / "codes" / platform

            # Create codes directory if it doesn't exist
            codes_dir.mkdir(parents=True, exist_ok=True)

            # Save the JSON file
            filename = f"{code_number}.json"
            file_path = codes_dir / filename

            # Check if file already exists
            if file_path.exists():
                logger.warning(f"Profile file {filename} already exists, overwriting")

            # Write JSON file with proper formatting
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(profile_json, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Saved SmartIR profile: {file_path}")

            return (
                jsonify(
                    {
                        "success": True,
                        "message": f"Profile saved successfully as {filename}",
                        "path": str(file_path),
                        "filename": filename,
                        "code_number": code_number,
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @smartir_bp.route("/config/check", methods=["GET"])
    def check_config():
        """Check SmartIR configuration setup status"""
        try:
            from flask import current_app

            config_path = current_app.config.get("config_path", "/config")

            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            configuration_yaml = config_path / "configuration.yaml"

            result = {"smartir_dir_exists": smartir_dir.exists(), "platforms": {}}

            # Check each platform file
            for platform in ["climate", "media_player", "fan", "light"]:
                platform_file = smartir_dir / f"{platform}.yaml"
                result["platforms"][platform] = {"file_exists": platform_file.exists(), "file_path": str(platform_file)}

            # Check if configuration.yaml has platform entries
            if configuration_yaml.exists():
                try:
                    with open(configuration_yaml, "r", encoding="utf-8") as f:
                        config_content = f.read()

                    # Simple detection - look for platform entries
                    result["configuration_warnings"] = []

                    for platform in ["climate", "media_player", "fan", "light"]:
                        # Check if platform is defined directly (not as include)
                        if f"\n{platform}:" in config_content or f"\n{platform} :" in config_content:
                            # Check if it's NOT an include
                            if f"!include smartir/{platform}.yaml" not in config_content:
                                result["configuration_warnings"].append(
                                    {
                                        "platform": platform,
                                        "message": (
                                            f"Found '{platform}:' in configuration.yaml. "
                                            f"You may need to migrate entries to smartir/{platform}.yaml"
                                        ),
                                    }
                                )
                except Exception as e:
                    logger.warning(f"Could not read configuration.yaml: {e}")

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Error checking config: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/profiles", methods=["GET"])
    def list_platform_profiles(platform):
        """List all profiles for a platform"""
        try:
            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({"success": False, "error": "SmartIR is not installed"}), 404

            # Get SmartIR codes directory
            smartir_path = smartir_detector.smartir_path
            codes_dir = smartir_path / "codes" / platform

            if not codes_dir.exists():
                return jsonify({"success": True, "profiles": []}), 200

            # Load YAML config to get controller data
            from flask import current_app
            import yaml

            config_path = current_app.config.get("config_path", "/config")
            config_path = Path(config_path)
            platform_file = config_path / "smartir" / f"{platform}.yaml"

            # Build a map of code -> controller_data
            controller_map = {}
            if platform_file.exists():
                try:
                    with open(platform_file, "r", encoding="utf-8") as f:
                        yaml_config = yaml.safe_load(f) or []

                    for device in yaml_config:
                        device_code = str(device.get("device_code", ""))
                        controller_data = device.get("controller_data", "")
                        if device_code and controller_data:
                            controller_map[device_code] = controller_data
                except Exception as e:
                    logger.warning(f"Could not read {platform_file}: {e}")

            # Get Broadlink storage path to check for learned commands
            config_path = current_app.config.get("config_path", "/config")
            storage_path = Path(config_path) / ".storage"

            # Read all JSON files in the directory
            profiles = []
            for file_path in codes_dir.glob("*.json"):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    code = file_path.stem
                    controller = controller_map.get(code, None)

                    # Count commands in the profile
                    command_count = _count_commands(data.get("commands", {}))

                    # Count learned commands if controller is set
                    learned_count = 0
                    if controller and storage_path.exists():
                        try:
                            # Extract command names from SmartIR profile
                            profile_commands = set(_extract_command_names(data.get("commands", {})))

                            # Generate expected device name from manufacturer and model
                            import re

                            manufacturer = re.sub(r"[^a-z0-9]+", "_", data.get("manufacturer", "").lower())
                            model = (
                                re.sub(r"[^a-z0-9]+", "_", data.get("supportedModels", [""])[0].lower())
                                if data.get("supportedModels")
                                else ""
                            )
                            expected_device_name = f"{manufacturer}_{model}" if manufacturer and model else None

                            logger.debug(f"Looking for learned commands in device: {expected_device_name}")

                            # Find Broadlink storage files
                            for storage_file in storage_path.glob("broadlink_remote_*_codes"):
                                try:
                                    with open(storage_file, "r", encoding="utf-8") as sf:
                                        storage_data = json.load(sf)

                                    # Only check the specific device for this profile
                                    if expected_device_name:
                                        device_data = storage_data.get("data", {}).get(expected_device_name, {})
                                        if device_data:
                                            learned_commands = set(device_data.keys())
                                            # Count matching commands (case-insensitive)
                                            profile_lower = {cmd.lower() for cmd in profile_commands}
                                            learned_lower = {cmd.lower() for cmd in learned_commands}
                                            matches = profile_lower.intersection(learned_lower)
                                            learned_count = len(matches)
                                            logger.debug(f"Found {learned_count} learned commands for {expected_device_name}")
                                            break  # Found the device, stop searching
                                except Exception as e:
                                    logger.debug(f"Error reading storage file {storage_file}: {e}")
                        except Exception as e:
                            logger.debug(f"Error checking learned commands for {code}: {e}")

                    # Extract controller brand from entity ID (e.g., "remote.master_bedroom_rm4_pro" -> "Broadlink")
                    controller_brand = "Not Set"
                    if controller:
                        # Default to "Broadlink" if the entity contains common Broadlink patterns
                        if any(x in controller.lower() for x in ["rm4", "rm3", "rm_pro", "broadlink"]):
                            controller_brand = "Broadlink"
                        elif "xiaomi" in controller.lower():
                            controller_brand = "Xiaomi"
                        elif "harmony" in controller.lower():
                            controller_brand = "Harmony Hub"
                        else:
                            controller_brand = "IR Remote"

                    profiles.append(
                        {
                            "code": code,
                            "manufacturer": data.get("manufacturer", "Unknown"),
                            "model": data.get("supportedModels", ["Unknown"])[0] if data.get("supportedModels") else "Unknown",
                            "file_name": file_path.name,
                            "controller": controller,
                            "controllerBrand": controller_brand,
                            "commandCount": command_count,
                            "learnedCount": learned_count,
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not read profile {file_path}: {e}")

            # Sort by code number
            profiles.sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)

            return jsonify({"success": True, "profiles": profiles}), 200

        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/profiles/<code>", methods=["GET"])
    def get_profile(platform, code):
        """Get a specific profile"""
        try:
            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({"success": False, "error": "SmartIR is not installed"}), 404

            # Get file path
            smartir_path = smartir_detector.smartir_path
            file_path = smartir_path / "codes" / platform / f"{code}.json"

            if not file_path.exists():
                return jsonify({"success": False, "error": f"Profile {code} not found"}), 404

            # Read the profile
            with open(file_path, "r", encoding="utf-8") as f:
                profile_data = json.load(f)

            return jsonify({"success": True, "profile": profile_data}), 200

        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @smartir_bp.route("/profiles/<code>", methods=["DELETE"])
    def delete_profile(code):
        """Delete a SmartIR profile"""
        try:
            data = request.get_json() or {}
            platform = data.get("platform")

            if not platform:
                return jsonify({"success": False, "error": "Missing platform parameter"}), 400

            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({"success": False, "error": "SmartIR is not installed"}), 404

            # Get file path
            smartir_path = smartir_detector.smartir_path
            file_path = smartir_path / "codes" / platform / f"{code}.json"

            if not file_path.exists():
                return jsonify({"success": False, "error": f"Profile {code} not found"}), 404

            # Check if profile is in use by any managed devices
            from flask import current_app

            storage_manager = current_app.config.get("storage_manager")
            if storage_manager:
                # Get all entities from metadata (includes SmartIR devices)
                entities = storage_manager.get_all_entities()
                devices_using_profile = []

                for entity_id, entity_data in entities.items():
                    # Check if this entity has a device_code matching the profile
                    if "device_code" in entity_data and str(entity_data.get("device_code")) == str(code):
                        devices_using_profile.append(entity_data.get("friendly_name", entity_data.get("name", entity_id)))

                if devices_using_profile:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": f"Cannot delete profile {code}: it is currently in use by {len(devices_using_profile)} device(s)",
                                "devices": devices_using_profile,
                            }
                        ),
                        400,
                    )

            # Read the profile to get manufacturer/model for Broadlink storage cleanup
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    import json

                    profile_data = json.load(f)
                    manufacturer = profile_data.get("manufacturer", "")
                    model = profile_data.get("supportedModels", [""])[0]

                    # Delete from Broadlink storage
                    if manufacturer and model:
                        import re

                        device_name = f"{manufacturer.lower()}_{model.lower()}"
                        device_name = re.sub(r"[^a-z0-9]+", "_", device_name)

                        # Find and update Broadlink storage files
                        from flask import current_app

                        config_path = current_app.config.get("config_path", "/config")
                        storage_path = Path(config_path) / ".storage"

                        if storage_path.exists():
                            deleted = False
                            for storage_file in storage_path.glob("broadlink_remote_*_codes"):
                                try:
                                    with open(storage_file, "r", encoding="utf-8") as sf:
                                        storage_data = json.load(sf)

                                    # Check if this device exists in storage
                                    if device_name in storage_data.get("data", {}):
                                        # Remove the device
                                        del storage_data["data"][device_name]

                                        # Write back
                                        with open(storage_file, "w", encoding="utf-8") as sf:
                                            json.dump(storage_data, sf, indent=2)

                                        logger.info(
                                            f"✅ Deleted Broadlink storage for device: {device_name} from {storage_file.name}"
                                        )
                                        deleted = True
                                        break
                                except Exception as e:
                                    logger.debug(f"Error checking storage file {storage_file}: {e}")

                            if not deleted:
                                logger.debug(f"No Broadlink storage found for device: {device_name}")
            except Exception as e:
                logger.warning(f"Could not clean up Broadlink storage: {e}")

            # Delete the file
            file_path.unlink()
            logger.info(f"✅ Deleted SmartIR profile: {file_path}")

            # Remove from smartir/{platform}.yaml config file
            from flask import current_app

            config_path = current_app.config.get("config_path", "/config")
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            platform_file = smartir_dir / f"{platform}.yaml"

            if platform_file.exists():
                try:
                    with open(platform_file, "r", encoding="utf-8") as f:
                        content = f.read()

                    # Parse YAML to find and remove the device with this code
                    import yaml

                    try:
                        config = yaml.safe_load(content) or []
                    except Exception:
                        config = []

                    # Filter out devices with matching device_code
                    original_count = len(config)
                    config = [device for device in config if device.get("device_code") != int(code)]
                    removed_count = original_count - len(config)

                    if removed_count > 0:
                        # Write back the updated config
                        with open(platform_file, "w", encoding="utf-8") as f:
                            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                        logger.info(f"✅ Removed {removed_count} device(s) with code {code} from {platform_file}")
                    else:
                        logger.warning(f"No devices with code {code} found in {platform_file}")

                except Exception as e:
                    logger.warning(f"Could not update {platform_file}: {e}")

            return jsonify({"success": True, "message": f"Profile {code} deleted successfully"}), 200

        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @smartir_bp.route("/config/get-device", methods=["GET"])
    def get_device_from_config():
        """Get device configuration from YAML file"""
        try:
            from flask import current_app

            platform = request.args.get("platform")
            code = request.args.get("code")

            if not all([platform, code]):
                return jsonify({"success": False, "error": "Missing platform or code parameter"}), 400

            config_path = current_app.config.get("config_path", "/config")
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            platform_file = smartir_dir / f"{platform}.yaml"

            if not platform_file.exists():
                return jsonify({"success": False, "error": f"Config file {platform}.yaml not found"}), 404

            # Read and parse YAML
            with open(platform_file, "r", encoding="utf-8") as f:
                content = f.read()

            import yaml

            try:
                config = yaml.safe_load(content) or []
            except Exception:
                config = []

            # Find device with matching code
            device = next((d for d in config if d.get("device_code") == int(code)), None)

            if not device:
                return jsonify({"success": False, "error": f"Device with code {code} not found in config"}), 404

            return (
                jsonify(
                    {
                        "success": True,
                        "controller_data": device.get("controller_data", ""),
                        "name": device.get("name", ""),
                        "unique_id": device.get("unique_id", ""),
                    }
                ),
                200,
            )

        except Exception as e:
            logger.error(f"Error getting device from config: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    @smartir_bp.route("/config/add-device", methods=["POST"])
    def add_device_to_config():
        """Add a SmartIR device to the platform YAML file"""
        try:
            from flask import current_app

            data = request.get_json()

            platform = data.get("platform")
            device_config = data.get("device_config")

            if not all([platform, device_config]):
                return jsonify({"success": False, "error": "Missing platform or device_config"}), 400

            config_path = current_app.config.get("config_path", "/config")
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"

            # Create smartir directory if needed
            smartir_dir.mkdir(exist_ok=True)

            platform_file = smartir_dir / f"{platform}.yaml"

            # Read existing content or start fresh
            existing_content = ""
            if platform_file.exists():
                with open(platform_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()
            else:
                # Add header comment for new file
                existing_content = f"# SmartIR {platform.title()} Devices\n# Managed by Broadlink Manager\n\n"

            # Append new device config
            new_entry = f"\n- platform: smartir\n"
            for key, value in device_config.items():
                if isinstance(value, str):
                    new_entry += f'  {key}: "{value}"\n'
                else:
                    new_entry += f"  {key}: {value}\n"

            updated_content = existing_content + new_entry

            # Write updated file
            with open(platform_file, "w", encoding="utf-8") as f:
                f.write(updated_content)

            logger.info(f"✅ Added device to {platform_file}")

            return (
                jsonify({"success": True, "message": f"Device added to {platform}.yaml", "file_path": str(platform_file)}),
                200,
            )

        except Exception as e:
            logger.error(f"Error adding device to config: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

    # ========== SmartIR Code Service Endpoints (GitHub Repository) ==========

    if smartir_code_service:

        @smartir_bp.route("/codes/manufacturers", methods=["GET"])
        def get_code_manufacturers():
            """Get list of manufacturers from GitHub repository"""
            try:
                entity_type = request.args.get("entity_type", "climate")

                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({"error": "Invalid entity_type. Must be: climate, fan, media_player, or light"}), 400

                manufacturers = smartir_code_service.get_manufacturers(entity_type)

                return (
                    jsonify(
                        {
                            "success": True,
                            "entity_type": entity_type,
                            "manufacturers": manufacturers,
                            "count": len(manufacturers),
                        }
                    ),
                    200,
                )

            except Exception as e:
                logger.error(f"Error getting manufacturers: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/models", methods=["GET"])
        def get_code_models():
            """Get list of models for a manufacturer"""
            try:
                entity_type = request.args.get("entity_type", "climate")
                manufacturer = request.args.get("manufacturer")

                if not manufacturer:
                    return jsonify({"error": "Missing manufacturer parameter"}), 400

                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({"error": "Invalid entity_type. Must be: climate, fan, media_player, or light"}), 400

                models = smartir_code_service.get_models(entity_type, manufacturer)

                return (
                    jsonify(
                        {
                            "success": True,
                            "entity_type": entity_type,
                            "manufacturer": manufacturer,
                            "models": models,
                            "count": len(models),
                        }
                    ),
                    200,
                )

            except Exception as e:
                logger.error(f"Error getting models: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/code", methods=["GET"])
        def get_code_by_params():
            """Get code details using query parameters"""
            try:
                entity_type = request.args.get("entity_type")
                code_id = request.args.get("code_id")

                if not entity_type or not code_id:
                    return jsonify({"success": False, "error": "entity_type and code_id are required"}), 400

                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return (
                        jsonify(
                            {"success": False, "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"}
                        ),
                        400,
                    )

                # Check if this is a custom code (10000+) - load from local file
                try:
                    code_num = int(code_id)
                    if code_num >= 10000 and smartir_detector.is_installed():
                        # Load from local SmartIR installation
                        smartir_path = smartir_detector.smartir_path
                        file_path = smartir_path / "codes" / entity_type / f"{code_id}.json"

                        if file_path.exists():
                            with open(file_path, "r", encoding="utf-8") as f:
                                full_code = json.load(f)

                            logger.debug(f"Loaded custom profile {code_id} from local file")
                            return jsonify({"success": True, "code": full_code, "custom": True}), 200
                except (ValueError, TypeError):
                    pass  # Not a numeric code, continue to GitHub fetch

                # Fetch full code from GitHub (for repository codes)
                full_code = smartir_code_service.fetch_full_code(entity_type, code_id)
                if full_code:
                    return jsonify({"success": True, "code": full_code}), 200
                else:
                    return jsonify({"success": False, "error": f"Code {code_id} not found"}), 404

            except Exception as e:
                logger.error(f"Error getting code: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/<entity_type>/<code_id>", methods=["GET"])
        def get_code_details(entity_type, code_id):
            """Get full code details from GitHub"""
            try:
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({"error": "Invalid entity_type. Must be: climate, fan, media_player, or light"}), 400

                # Try to get from cache first
                code_info = smartir_code_service.get_code_info(entity_type, code_id)

                # Fetch full code if requested
                fetch_full = request.args.get("full", "false").lower() == "true"
                if fetch_full:
                    full_code = smartir_code_service.fetch_full_code(entity_type, code_id)
                    if full_code:
                        return jsonify({"success": True, "code": full_code}), 200
                    else:
                        return jsonify({"success": False, "error": f"Code {code_id} not found"}), 404

                # Return cached info
                if code_info:
                    return jsonify({"success": True, "code": code_info}), 200
                else:
                    return jsonify({"success": False, "error": f"Code {code_id} not found in cache"}), 404

            except Exception as e:
                logger.error(f"Error getting code details: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/search", methods=["GET"])
        def search_codes():
            """Search codes by manufacturer or model"""
            try:
                entity_type = request.args.get("entity_type", "climate")
                query = request.args.get("query", "")

                if not query:
                    return jsonify({"error": "Missing query parameter"}), 400

                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({"error": "Invalid entity_type. Must be: climate, fan, media_player, or light"}), 400

                results = smartir_code_service.search_codes(entity_type, query)

                return (
                    jsonify(
                        {
                            "success": True,
                            "entity_type": entity_type,
                            "query": query,
                            "results": results,
                            "count": len(results),
                        }
                    ),
                    200,
                )

            except Exception as e:
                logger.error(f"Error searching codes: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/refresh", methods=["POST"])
        def refresh_codes():
            """Refresh code cache from GitHub"""
            try:
                data = request.get_json() or {}
                entity_type = data.get("entity_type", "climate")
                force = data.get("force", False)

                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({"error": "Invalid entity_type. Must be: climate, fan, media_player, or light"}), 400

                success = smartir_code_service.refresh_codes(entity_type, force=force)

                if success:
                    return jsonify({"success": True, "message": f"Cache refreshed for {entity_type}"}), 200
                else:
                    return jsonify({"success": False, "error": "Failed to refresh cache"}), 500

            except Exception as e:
                logger.error(f"Error refreshing codes: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/cache-status", methods=["GET"])
        def get_cache_status():
            """Get cache status"""
            try:
                status = smartir_code_service.get_cache_status()
                return jsonify({"success": True, "cache": status}), 200
            except Exception as e:
                logger.error(f"Error getting cache status: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/codes/clear-cache", methods=["POST"])
        def clear_cache():
            """Clear code cache"""
            try:
                success = smartir_code_service.clear_cache()

                if success:
                    return jsonify({"success": True, "message": "Cache cleared successfully"}), 200
                else:
                    return jsonify({"success": False, "error": "Failed to clear cache"}), 500

            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/profiles/browse", methods=["GET"])
        def browse_profiles():
            """Browse all profiles with filtering and pagination"""
            try:
                # Get query parameters
                platform = request.args.get("platform", "climate")
                manufacturer = request.args.get("manufacturer", "")
                model = request.args.get("model", "")
                source = request.args.get("source", "all")  # all, index, custom
                page = int(request.args.get("page", 1))
                limit = int(request.args.get("limit", 50))
                sort_by = request.args.get("sort_by", "code")  # code, manufacturer, model

                if platform not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({"success": False, "error": "Invalid platform"}), 400

                all_profiles = []

                # Get index profiles
                if source in ["all", "index"]:
                    index_data = smartir_code_service._device_index.get("platforms", {}).get(platform, {})
                    manufacturers_data = index_data.get("manufacturers", {})

                    for mfr, mfr_data in manufacturers_data.items():
                        # Filter by manufacturer if specified
                        if manufacturer and mfr.lower() != manufacturer.lower():
                            continue

                        for model_info in mfr_data.get("models", []):
                            # Filter by model if specified
                            if model:
                                model_names = [m.lower() for m in model_info.get("models", [])]
                                if not any(model.lower() in m for m in model_names):
                                    continue

                            all_profiles.append(
                                {
                                    "code": model_info.get("code"),
                                    "manufacturer": mfr,
                                    "model": (
                                        model_info.get("models", ["Unknown"])[0] if model_info.get("models") else "Unknown"
                                    ),
                                    "models": model_info.get("models", []),
                                    "platform": platform,
                                    "source": "index",
                                    "url": model_info.get("url"),
                                    "controller_brand": "Broadlink",
                                    "command_count": 0,  # Not loaded yet
                                    "learned_count": 0,
                                    "is_custom": False,
                                }
                            )

                # Get custom profiles
                if source in ["all", "custom"] and smartir_detector.is_installed():
                    smartir_path = smartir_detector.smartir_path
                    codes_dir = smartir_path / "codes" / platform

                    if codes_dir.exists():
                        for file_path in codes_dir.glob("*.json"):
                            try:
                                code = file_path.stem
                                code_num = int(code)

                                # Only include custom codes (10000+)
                                if code_num < 10000:
                                    continue

                                with open(file_path, "r", encoding="utf-8") as f:
                                    data = json.load(f)

                                mfr = data.get("manufacturer", "Unknown")
                                models = data.get("supportedModels", ["Unknown"])

                                # Filter by manufacturer if specified
                                if manufacturer and mfr.lower() != manufacturer.lower():
                                    continue

                                # Filter by model if specified
                                if model:
                                    model_names = [m.lower() for m in models]
                                    if not any(model.lower() in m for m in model_names):
                                        continue

                                command_count = _count_commands(data.get("commands", {}))

                                all_profiles.append(
                                    {
                                        "code": code,
                                        "manufacturer": mfr,
                                        "model": models[0] if models else "Unknown",
                                        "models": models,
                                        "platform": platform,
                                        "source": "custom",
                                        "controller_brand": "Broadlink",
                                        "command_count": command_count,
                                        "learned_count": 0,
                                        "is_custom": True,
                                        "created_date": file_path.stat().st_ctime,
                                        "modified_date": file_path.stat().st_mtime,
                                    }
                                )
                            except Exception as e:
                                logger.debug(f"Error reading custom profile {file_path}: {e}")

                # Sort profiles
                if sort_by == "manufacturer":
                    all_profiles.sort(key=lambda x: (x["manufacturer"].lower(), int(x["code"]) if x["code"].isdigit() else 0))
                elif sort_by == "model":
                    all_profiles.sort(key=lambda x: (x["model"].lower(), int(x["code"]) if x["code"].isdigit() else 0))
                else:  # sort by code
                    all_profiles.sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)

                # Paginate
                total_count = len(all_profiles)
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_profiles = all_profiles[start_idx:end_idx]

                return (
                    jsonify(
                        {
                            "success": True,
                            "platform": platform,
                            "profiles": paginated_profiles,
                            "pagination": {
                                "page": page,
                                "limit": limit,
                                "total": total_count,
                                "total_pages": (total_count + limit - 1) // limit,
                            },
                            "filters": {"manufacturer": manufacturer, "model": model, "source": source},
                        }
                    ),
                    200,
                )

            except Exception as e:
                logger.error(f"Error browsing profiles: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @smartir_bp.route("/profiles/search", methods=["GET"])
        def search_profiles():
            """Search profiles across all platforms"""
            try:
                query = request.args.get("query", "").strip()
                platform = request.args.get("platform", "all")
                source = request.args.get("source", "all")
                limit = int(request.args.get("limit", 100))

                if not query:
                    return jsonify({"success": False, "error": "Query parameter is required"}), 400

                platforms_to_search = ["climate", "fan", "media_player", "light"] if platform == "all" else [platform]
                all_results = []

                for plt in platforms_to_search:
                    # Search index profiles
                    if source in ["all", "index"]:
                        index_data = smartir_code_service._device_index.get("platforms", {}).get(plt, {})
                        manufacturers_data = index_data.get("manufacturers", {})

                        for mfr, mfr_data in manufacturers_data.items():
                            if query.lower() in mfr.lower():
                                for model_info in mfr_data.get("models", []):
                                    all_results.append(
                                        {
                                            "code": model_info.get("code"),
                                            "manufacturer": mfr,
                                            "model": (
                                                model_info.get("models", ["Unknown"])[0]
                                                if model_info.get("models")
                                                else "Unknown"
                                            ),
                                            "models": model_info.get("models", []),
                                            "platform": plt,
                                            "source": "index",
                                            "match_type": "manufacturer",
                                        }
                                    )
                            else:
                                for model_info in mfr_data.get("models", []):
                                    model_names = model_info.get("models", [])
                                    if any(query.lower() in m.lower() for m in model_names):
                                        all_results.append(
                                            {
                                                "code": model_info.get("code"),
                                                "manufacturer": mfr,
                                                "model": model_names[0] if model_names else "Unknown",
                                                "models": model_names,
                                                "platform": plt,
                                                "source": "index",
                                                "match_type": "model",
                                            }
                                        )

                    # Search custom profiles
                    if source in ["all", "custom"] and smartir_detector.is_installed():
                        smartir_path = smartir_detector.smartir_path
                        codes_dir = smartir_path / "codes" / plt

                        if codes_dir.exists():
                            for file_path in codes_dir.glob("*.json"):
                                try:
                                    code = file_path.stem
                                    code_num = int(code)
                                    if code_num < 10000:
                                        continue

                                    with open(file_path, "r", encoding="utf-8") as f:
                                        data = json.load(f)

                                    mfr = data.get("manufacturer", "Unknown")
                                    models = data.get("supportedModels", ["Unknown"])

                                    match_type = None
                                    if query.lower() in mfr.lower():
                                        match_type = "manufacturer"
                                    elif any(query.lower() in m.lower() for m in models):
                                        match_type = "model"

                                    if match_type:
                                        all_results.append(
                                            {
                                                "code": code,
                                                "manufacturer": mfr,
                                                "model": models[0] if models else "Unknown",
                                                "models": models,
                                                "platform": plt,
                                                "source": "custom",
                                                "match_type": match_type,
                                            }
                                        )
                                except Exception as e:
                                    logger.debug(f"Error searching custom profile {file_path}: {e}")

                # Limit results
                all_results = all_results[:limit]

                return jsonify({"success": True, "query": query, "results": all_results, "count": len(all_results)}), 200

            except Exception as e:
                logger.error(f"Error searching profiles: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

    return smartir_bp
