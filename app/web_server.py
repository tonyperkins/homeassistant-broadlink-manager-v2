#!/usr/bin/env python3
"""
Flask web server for Broadlink Manager Add-on
Provides a web interface for managing Broadlink devices
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import time

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import aiohttp
import aiofiles  # type: ignore
import websockets

from entity_detector import EntityDetector
from entity_generator import EntityGenerator
from area_manager import AreaManager
from config_loader import ConfigLoader
from device_manager import DeviceManager
from smartir_detector import SmartIRDetector
from smartir_code_service import SmartIRCodeService

# Import API blueprint for v2
from api import api_bp
from api.smartir import init_smartir_routes

logger = logging.getLogger(__name__)


class IngressMiddleware:
    """Middleware to handle Home Assistant ingress paths"""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # Get the ingress path from the header
        ingress_path = environ.get("HTTP_X_INGRESS_PATH", "")

        # Debug logging
        logger.debug(
            f"Ingress request - Path: {environ.get('PATH_INFO')}, Ingress Path: {ingress_path}"
        )

        if ingress_path:
            # Set SCRIPT_NAME to the ingress path
            environ["SCRIPT_NAME"] = ingress_path

            # Remove ingress path from PATH_INFO if present
            path_info = environ.get("PATH_INFO", "")
            if path_info.startswith(ingress_path):
                environ["PATH_INFO"] = path_info[len(ingress_path) :] or "/"
                logger.debug(f"Adjusted PATH_INFO to: {environ['PATH_INFO']}")

        return self.app(environ, start_response)


class BroadlinkWebServer:
    """Web server for Broadlink device management"""

    def __init__(self, port: int = 8099, config_loader: Optional[ConfigLoader] = None):
        self.port = port
        # Use relative static path to work with Home Assistant ingress
        self.app = Flask(__name__, template_folder="templates", static_folder="static")

        # Apply custom ingress middleware
        self.app.wsgi_app = IngressMiddleware(self.app.wsgi_app)

        CORS(self.app)

        # Load configuration using ConfigLoader
        self.config_loader = config_loader or ConfigLoader()

        # Home Assistant configuration (from ConfigLoader)
        self.ha_url = self.config_loader.get_ha_url()
        self.ha_token = self.config_loader.get_ha_token()
        self.storage_path = (
            self.config_loader.get_storage_path()
        )  # For HA storage files (.storage/)
        self.broadlink_manager_path = (
            self.config_loader.get_broadlink_manager_path()
        )  # For devices.json (broadlink_manager/)

        logger.info(f"Web server initialized in {self.config_loader.mode} mode")

        # WebSocket notifications cache
        self.ws_notifications: list[str] = []
        self.last_notification_check = 0

        # Cache for recently deleted commands to handle storage lag
        # Format: {device_name: {command_name: timestamp}}
        self.recently_deleted_commands: dict[str, dict[str, int]] = {}
        self.DELETION_CACHE_TTL = 30  # Keep deleted commands in cache for 30 seconds
        
        # Storage command cache to handle async file writes
        # This cache sits in front of _get_all_broadlink_commands()
        # Format: {device_name: {command_name: command_data}}
        # When we write to storage, we update this cache immediately
        # Reads return cached data until file is actually written
        self.storage_command_cache: dict[str, dict[str, str]] = {}
        self.storage_cache_timestamp: float = 0
        self.STORAGE_CACHE_TTL = 60  # Refresh cache every 60 seconds

        # Device connection info cache to speed up learning/testing
        # Format: {entity_id: {host, mac, type, type_hex, model, mac_bytes, cached_at}}
        self.device_connection_cache: dict[str, dict] = {}
        self.CONNECTION_CACHE_TTL = 300  # Cache for 5 minutes

        # Call tracking for logging context
        self._call_counter = 0
        self._call_lock = threading.Lock()

        # Background polling for pending commands
        # Format: [(device_id, device_name, command_name, poll_count, max_polls)]
        self.pending_command_polls: list[tuple[str, str, str, int, int]] = []
        self.poll_lock = threading.Lock()
        self.poll_thread = None
        self.poll_thread_running = False

        # Initialize entity management components
        self.entity_detector = EntityDetector()
        self.area_manager = AreaManager(self.ha_url or "", self.ha_token or "")
        self.device_manager = DeviceManager(
            str(self.config_loader.get_broadlink_manager_path())
        )
        self.smartir_detector = SmartIRDetector(
            str(self.config_loader.get_config_path())
        )
        self.smartir_code_service = SmartIRCodeService(
            str(self.config_loader.get_broadlink_manager_path() / "cache"),
            smartir_detector=self.smartir_detector,
        )

        # Make managers available to API endpoints
        self.app.config["device_manager"] = self.device_manager
        self.app.config["area_manager"] = self.area_manager
        self.app.config["web_server"] = self  # For command learning
        self.app.config["smartir_detector"] = self.smartir_detector
        self.app.config["smartir_code_service"] = self.smartir_code_service
        self.app.config["config_path"] = str(self.config_loader.get_config_path())

        # Register API blueprint for v2
        self.app.register_blueprint(api_bp)
        logger.info("Registered API blueprint at /api")

        # Register SmartIR API blueprint with code service
        smartir_bp = init_smartir_routes(
            self.smartir_detector, self.smartir_code_service
        )
        self.app.register_blueprint(smartir_bp)
        logger.info("Registered SmartIR API blueprint at /api/smartir")

        self._setup_routes()
        # Initialize WebSocket variables
        self.ws_connection = None
        self.ws_message_id = 0
        self.ws_notifications = []

        # Automatic migration disabled - user preference
        # self._schedule_migration_check()

    def _setup_routes(self):
        """Setup Flask routes"""

        @self.app.route("/")
        def index():
            """Serve the main web interface (Vue app if built, otherwise template)"""
            # Try to serve Vue app from static folder first
            vue_index = Path(self.app.static_folder) / "index.html"
            if vue_index.exists():
                return send_from_directory(self.app.static_folder, "index.html")
            # Fallback to template (v1 interface)
            return render_template("index.html")

        @self.app.route("/static/<path:filename>")
        def serve_static(filename):
            """Explicitly serve static files to work with ingress"""
            return send_from_directory(self.app.static_folder, filename)

        @self.app.route("/assets/<path:filename>")
        def serve_assets(filename):
            """Serve Vue app assets (CSS, JS) with correct MIME types"""
            assets_path = Path(self.app.static_folder) / "assets"
            return send_from_directory(assets_path, filename)

        @self.app.route("/api/areas")
        def get_areas():
            """Get Home Assistant areas from storage"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                areas = loop.run_until_complete(self._get_ha_areas("GET /api/areas"))
                loop.close()
                return jsonify(areas)
            except Exception as e:
                logger.error(f"Error getting areas: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/devices")
        def get_broadlink_devices():
            """Get Broadlink devices"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                devices = loop.run_until_complete(
                    self._get_broadlink_devices("GET /api/devices")
                )
                loop.close()
                return jsonify(devices)
            except Exception as e:
                logger.error(f"Error getting devices: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/commands/<device_id>")
        def get_commands(device_id):
            """Get learned commands for a device"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                commands = loop.run_until_complete(
                    self._get_learned_commands(device_id)
                )
                loop.close()
                return jsonify(commands)
            except Exception as e:
                logger.error(f"Error getting commands: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/learn", methods=["POST"])
        def learn_command():
            """Learn a new command"""
            try:
                data = request.get_json()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._learn_command(data))
                loop.close()
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error learning command: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/theme")
        def get_theme():
            """Get current Home Assistant theme information"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                theme_info = loop.run_until_complete(self._get_ha_theme())
                loop.close()
                return jsonify(theme_info)
            except Exception as e:
                logger.error(f"Error getting theme: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/send", methods=["POST"])
        def send_command():
            """Send a command"""
            try:
                data = request.get_json()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._send_command(data))
                loop.close()
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error sending command: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/debug/token")
        def get_token():
            """Get supervisor token for WebSocket authentication"""
            try:
                # For add-on context, we need to check if supervisor token works
                # If not, we'll need to use alternative authentication
                logger.info(f"Providing token for WebSocket: {self.ha_token[:20]}...")
                return jsonify(
                    {
                        "token": self.ha_token,
                    }
                )
            except Exception as e:
                logger.error(f"Error getting token: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/learned-devices")
        def get_learned_devices():
            """Get all learned devices with area and command information for filtering"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                commands_data = loop.run_until_complete(self._get_learned_commands())
                loop.close()

                # Transform data for filtering UI
                result = {"areas": {}, "devices": {}, "commands": []}

                for device_name, device_info in commands_data.items():
                    area_id = device_info.get("area_id")
                    area_name = device_info.get("area_name", "Unknown")
                    device_part = device_info.get("device_part", device_name)

                    # Add to areas
                    if area_id and area_id not in result["areas"]:
                        result["areas"][area_id] = area_name

                    # Add to devices
                    if device_name not in result["devices"]:
                        result["devices"][device_name] = {
                            "area_id": area_id,
                            "area_name": area_name,
                            "device_part": device_part,
                            "full_name": device_name,
                        }

                    # Add commands
                    command_data = device_info.get("command_data", {})
                    for command in device_info.get("commands", []):
                        command_code = command_data.get(command, "")
                        # Handle both string and list command codes
                        if isinstance(command_code, list):
                            # If it's a list, check the first element
                            command_type = (
                                "rf"
                                if (
                                    command_code
                                    and isinstance(command_code[0], str)
                                    and command_code[0].startswith("sc")
                                )
                                else "ir"
                            )
                        elif isinstance(command_code, str):
                            command_type = (
                                "rf" if command_code.startswith("sc") else "ir"
                            )
                        else:
                            command_type = "ir"  # Default to IR if unknown type

                        result["commands"].append(
                            {
                                "device_name": device_name,
                                "device_part": device_part,
                                "command": command,
                                "command_type": command_type,
                                "area_id": area_id,
                                "area_name": area_name,
                                "full_command_name": f"{device_name}_{command}",
                            }
                        )

                return jsonify(result)
            except Exception as e:
                logger.error(f"Error getting learned devices: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/debug/broadlink-full-data")
        def debug_broadlink_full_data():
            """Get all learned devices with area and command information for debugging"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Get all detected Broadlink devices
                all_devices = loop.run_until_complete(
                    self._get_broadlink_devices("GET /api/debug/broadlink-full-data")
                )

                # Get learned commands
                learned_commands = loop.run_until_complete(self._get_learned_commands())

                # Get areas
                areas = loop.run_until_complete(
                    self._get_ha_areas("GET /api/debug/broadlink-full-data")
                )

                loop.close()

                return jsonify(
                    {
                        "detected_broadlink_devices": all_devices,
                        "learned_commands": learned_commands,
                        "areas": areas,
                        "summary": {
                            "total_detected_devices": len(all_devices),
                            "devices_with_commands": len(learned_commands),
                            "total_areas": len(areas),
                        },
                    }
                )
            except Exception as e:
                logger.error(f"Error getting debug data: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/delete", methods=["POST"])
        def delete_command():
            """Delete a command"""
            try:
                data = request.get_json()
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._delete_command(data))
                loop.close()
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error deleting command: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/notifications")
        def get_notifications():
            """Get persistent notifications for learning status"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Try WebSocket method first, fallback to REST API
                try:
                    notifications = loop.run_until_complete(
                        self._get_ws_notifications()
                    )
                    if notifications:
                        loop.close()
                        return jsonify(notifications)
                except Exception as ws_error:
                    logger.warning(f"WebSocket notifications failed: {ws_error}")

                # Fallback to REST API
                notifications = loop.run_until_complete(self._get_notifications())
                loop.close()
                return jsonify(notifications)
            except Exception as e:
                logger.error(f"Error getting notifications: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/debug/all-notifications")
        def get_all_notifications():
            """Get all persistent notifications for debugging"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                states = loop.run_until_complete(self._make_ha_request("GET", "states"))
                loop.close()

                all_notifications = []
                if isinstance(states, list):
                    for entity in states:
                        entity_id = entity.get("entity_id", "")
                        if entity_id.startswith("persistent_notification."):
                            attributes = entity.get("attributes", {})
                            all_notifications.append(
                                {
                                    "id": entity_id,
                                    "title": attributes.get("title", ""),
                                    "message": attributes.get("message", ""),
                                    "created_at": entity.get("last_changed"),
                                }
                            )

                return jsonify(all_notifications)
            except Exception as e:
                logger.error(f"Error getting all notifications: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/debug/test-service", methods=["POST"])
        def test_service():
            """Test if we can call Broadlink services at all"""
            try:
                data = request.get_json()
                entity_id = data.get("entity_id", "remote.broadlink")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Try to call the Broadlink service info first
                logger.info(
                    f"Testing service call to remote.learn_command for entity: {entity_id}"
                )

                test_data = {
                    "entity_id": entity_id,
                    "device": "test_device",
                    "command": "test_command",
                    "command_type": "rf",
                }

                result = loop.run_until_complete(
                    self._make_ha_request(
                        "POST", "services/remote/learn_command", test_data
                    )
                )
                loop.close()

                return jsonify(
                    {
                        "success": True,
                        "message": "Service test completed",
                        "result": result,
                        "entity_id": entity_id,
                    }
                )
            except Exception as e:
                logger.error(f"Error testing service: {e}")
                return jsonify({"error": str(e)}), 500

        # Entity Management Routes

        @self.app.route("/api/entities")
        def get_entities():
            """Get all configured entities"""
            try:
                entities = self.storage_manager.get_all_entities()
                stats = self.storage_manager.get_stats()
                return jsonify({"entities": entities, "stats": stats})
            except Exception as e:
                logger.error(f"Error getting entities: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities/<entity_id>")
        def get_entity(entity_id):
            """Get a specific entity"""
            try:
                entity = self.storage_manager.get_entity(entity_id)
                if entity:
                    return jsonify(entity)
                return jsonify({"error": "Entity not found"}), 404
            except Exception as e:
                logger.error(f"Error getting entity: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities", methods=["POST"])
        def save_entity():
            """Save or update an entity"""
            try:
                data = request.get_json()
                entity_id = data.get("entity_id")
                entity_data = data.get("entity_data")

                if not entity_id or not entity_data:
                    return jsonify({"error": "Missing entity_id or entity_data"}), 400

                self.storage_manager.save_entity(entity_id, entity_data)
                return jsonify(
                    {
                        "success": True,
                        "message": f"Entity {entity_id} saved successfully",
                        "entity_id": entity_id,
                    }
                )
            except Exception as e:
                logger.error(f"Error saving entity: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities/<entity_id>", methods=["DELETE"])
        def delete_entity(entity_id):
            """Delete an entity"""
            try:
                success = self.storage_manager.delete_entity(entity_id)
                if success:
                    return jsonify(
                        {
                            "success": True,
                            "message": f"Entity {entity_id} deleted successfully",
                        }
                    )
                return jsonify({"error": "Entity not found"}), 404
            except Exception as e:
                logger.error(f"Error deleting entity: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities/detect", methods=["POST"])
        def detect_entities():
            """Auto-detect entities from commands"""
            try:
                data = request.get_json()
                device_name = data.get("device_name")
                commands = data.get("commands")
                area_name = data.get("area_name")
                broadlink_entity = data.get(
                    "broadlink_entity"
                )  # NEW: which Broadlink device sends these commands

                if not device_name or not commands:
                    return jsonify({"error": "Missing device_name or commands"}), 400

                detected = self.entity_detector.group_commands_by_entity(
                    device_name, commands, area_name, broadlink_entity
                )
                return jsonify(
                    {
                        "success": True,
                        "detected_entities": detected,
                        "count": len(detected),
                    }
                )
            except Exception as e:
                logger.error(f"Error detecting entities: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities/generate", methods=["POST"])
        def generate_entities():
            """Generate YAML entity files for both Broadlink and SmartIR devices"""
            try:
                data = request.get_json()
                device_id = data.get(
                    "device_id"
                )  # Optional: for backward compatibility

                logger.info("🔄 Manual entity generation triggered...")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Note: No longer need to sync to metadata - adapter handles conversion
                # self._sync_devices_to_metadata()

                # Separate devices by type
                all_devices = self.device_manager.get_all_devices()
                broadlink_devices = {
                    k: v
                    for k, v in all_devices.items()
                    if v.get("device_type", "broadlink") == "broadlink"
                }
                smartir_devices = {
                    k: v
                    for k, v in all_devices.items()
                    if v.get("device_type") == "smartir"
                }

                results = {
                    "success": True,
                    "broadlink_count": 0,
                    "smartir_count": 0,
                    "total_count": 0,
                    "errors": [],
                }

                # Generate Broadlink native entities
                if broadlink_devices:
                    logger.info(
                        f"📝 Generating {len(broadlink_devices)} Broadlink native entities..."
                    )

                    # Use device_manager directly - commands are now stored in devices.json
                    from entity_generator_v2 import EntityGeneratorV2

                    generator = EntityGeneratorV2(
                        device_manager=self.device_manager,
                        config_path=str(self.config_loader.get_config_path()),
                    )
                    broadlink_result = generator.generate_all_devices(broadlink_devices)

                    if broadlink_result.get("success"):
                        results["broadlink_count"] = broadlink_result.get(
                            "entities_count", 0
                        )
                        logger.info(
                            f"✅ Generated {results['broadlink_count']} Broadlink entities"
                        )
                    else:
                        results["errors"].append(
                            f"Broadlink: {broadlink_result.get('message', 'Unknown error')}"
                        )

                # Generate SmartIR entities
                if smartir_devices:
                    logger.info(
                        f"📝 Generating {len(smartir_devices)} SmartIR entities..."
                    )
                    from smartir_yaml_generator import SmartIRYAMLGenerator

                    smartir_generator = SmartIRYAMLGenerator(
                        str(self.config_loader.get_config_path())
                    )

                    # Get Broadlink device list for IP lookup
                    broadlink_device_list = loop.run_until_complete(
                        self._get_broadlink_devices()
                    )

                    smartir_success_count = 0
                    for device_id, device_data in smartir_devices.items():
                        smartir_result = smartir_generator.generate_device_config(
                            device_id, device_data, broadlink_device_list
                        )

                        if smartir_result.get("success"):
                            smartir_success_count += 1
                        else:
                            error_msg = smartir_result.get("error", "Unknown error")
                            results["errors"].append(
                                f"SmartIR {device_id}: {error_msg}"
                            )
                            logger.error(
                                f"Failed to generate SmartIR config for {device_id}: {error_msg}"
                            )

                    results["smartir_count"] = smartir_success_count
                    logger.info(
                        f"✅ Generated {smartir_success_count} SmartIR entities"
                    )

                # Calculate totals
                results["total_count"] = (
                    results["broadlink_count"] + results["smartir_count"]
                )
                results["entities_count"] = results[
                    "total_count"
                ]  # For backward compatibility

                # Build message
                messages = []
                if results["broadlink_count"] > 0:
                    messages.append(f"{results['broadlink_count']} Broadlink native")
                if results["smartir_count"] > 0:
                    messages.append(f"{results['smartir_count']} SmartIR")

                if results["total_count"] > 0:
                    results["message"] = (
                        f"Generated {' and '.join(messages)} entity configuration(s)"
                    )
                else:
                    results["success"] = False
                    results["message"] = "No entities configured"

                # Reload configurations if we generated anything
                if results["total_count"] > 0:
                    logger.info("🔄 Reloading Broadlink configuration...")
                    reload_success = loop.run_until_complete(
                        self._reload_broadlink_config()
                    )

                    logger.info("🔄 Reloading Home Assistant YAML configuration...")
                    yaml_reload_success = loop.run_until_complete(
                        self.area_manager.reload_config()
                    )

                    if reload_success and yaml_reload_success:
                        results["config_reloaded"] = True
                        results["message"] += " Configuration reloaded successfully."
                    else:
                        results["config_reloaded"] = False
                        results["message"] += " Warning: Configuration reload failed."

                loop.close()

                return jsonify(results)
            except Exception as e:
                logger.error(f"Error generating entities: {e}", exc_info=True)
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities/types")
        def get_entity_types():
            """Get supported entity types and their command roles"""
            try:
                types = self.entity_detector.get_entity_types()
                roles = {}
                for entity_type in types:
                    roles[entity_type] = (
                        self.entity_detector.get_command_roles_for_type(entity_type)
                    )

                return jsonify({"types": types, "roles": roles})
            except Exception as e:
                logger.error(f"Error getting entity types: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/entities/reload-config", methods=["POST"])
        def reload_config():
            """Reload Home Assistant configuration to pick up new entities"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(self.area_manager.reload_config())
                loop.close()

                if success:
                    return jsonify(
                        {
                            "success": True,
                            "message": "Configuration reloaded successfully",
                        }
                    )
                else:
                    return jsonify(
                        {
                            "success": False,
                            "message": "Configuration reload may have failed",
                        }
                    )

            except Exception as e:
                logger.error(f"Error reloading config: {e}")
                return jsonify({"error": str(e)}), 500

        # Migration Management Routes

        @self.app.route("/api/migration/status")
        def get_migration_status():
            """Get current migration status"""
            try:
                status = self.migration_manager.get_migration_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Error getting migration status: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/migration/check", methods=["POST"])
        def check_migration():
            """Check if migration is needed and perform it"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                devices = loop.run_until_complete(
                    self._get_broadlink_devices("POST /api/migration/check")
                )
                result = loop.run_until_complete(
                    self.migration_manager.check_and_migrate(devices)
                )

                loop.close()

                return jsonify(result)
            except Exception as e:
                logger.error(f"Error checking migration: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/migration/force", methods=["POST"])
        def force_migration():
            """Force migration even if metadata exists"""
            try:
                data = request.get_json() or {}
                overwrite = data.get("overwrite", False)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                devices = loop.run_until_complete(
                    self._get_broadlink_devices("POST /api/migration/force")
                )
                result = loop.run_until_complete(
                    self.migration_manager.force_migration(devices, overwrite)
                )

                loop.close()

                return jsonify(result)
            except Exception as e:
                logger.error(f"Error forcing migration: {e}")
                return jsonify({"error": str(e)}), 500

        # Device Management Endpoints
        @self.app.route("/api/devices/managed", methods=["GET"])
        def get_managed_devices():
            """Get all managed devices"""
            try:
                devices = self.device_manager.get_all_devices()
                return jsonify(devices)
            except Exception as e:
                logger.error(f"Error getting managed devices: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/devices/managed/<device_id>", methods=["GET"])
        def get_managed_device(device_id):
            """Get a specific managed device"""
            try:
                device = self.device_manager.get_device(device_id)
                if device:
                    return jsonify(device)
                return jsonify({"error": "Device not found"}), 404
            except Exception as e:
                logger.error(f"Error getting device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/devices/managed", methods=["POST"])
        def create_managed_device():
            """Create a new managed device"""
            print("=" * 80)
            print("🔵 POST /api/devices/managed endpoint hit!")
            print("=" * 80)
            logger.info("🔵 POST /api/devices/managed endpoint hit!")
            try:
                data = request.get_json()
                logger.info(f"📥 Received device creation request: {data}")

                device_name = data.get("device_name")
                storage_name = data.get("device")  # Storage name for adopted devices
                area_id = data.get("area_id", "")  # Allow empty area
                area_name = data.get("area_name", "")
                entity_type = data.get("entity_type")
                icon = data.get("icon")
                broadlink_entity = data.get("broadlink_entity")

                logger.info(
                    f"📥 Parsed fields - device_name: {device_name}, storage_name: {storage_name}, entity_type: {entity_type}, broadlink_entity: {broadlink_entity}"
                )

                # Validate required fields (area is optional)
                if not device_name:
                    logger.error(
                        f"❌ Validation failed: device_name is missing or empty"
                    )
                    return jsonify({"error": "Device name is required"}), 400
                if not entity_type:
                    return jsonify({"error": "Entity type is required"}), 400
                if not broadlink_entity:
                    return jsonify({"error": "Broadlink device is required"}), 400

                # Use storage name as device ID if provided (adopted device)
                # Otherwise generate new ID from area + device name
                if storage_name:
                    device_id = storage_name
                else:
                    device_id = self.device_manager.generate_device_id(
                        area_id, device_name
                    )

                # Create device data
                device_data = {
                    "name": device_name,
                    "full_name": (
                        f"{area_name} {device_name}" if area_name else device_name
                    ),
                    "area": area_name,
                    "area_id": area_id,
                    "entity_type": entity_type,
                    "icon": icon,
                    "broadlink_entity": broadlink_entity,
                }

                if self.device_manager.create_device(device_id, device_data):
                    return jsonify(
                        {
                            "success": True,
                            "device_id": device_id,
                            "device": self.device_manager.get_device(device_id),
                        }
                    )

                return jsonify({"error": "Failed to create device"}), 500

            except Exception as e:
                logger.error(f"Error creating device: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/devices/managed/<device_id>", methods=["PUT"])
        def update_managed_device(device_id):
            """Update a managed device"""
            try:
                data = request.get_json()

                if self.device_manager.update_device(device_id, data):
                    return jsonify(
                        {
                            "success": True,
                            "device": self.device_manager.get_device(device_id),
                        }
                    )

                return jsonify({"error": "Device not found"}), 404

            except Exception as e:
                logger.error(f"Error updating device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/devices/managed/<device_id>", methods=["DELETE"])
        def delete_managed_device(device_id):
            """Delete a managed device"""
            try:
                data = request.get_json() or {}
                delete_commands = data.get("delete_commands", False)

                # Get device info before deleting
                device = self.device_manager.get_device(device_id)
                if not device:
                    return jsonify({"error": "Device not found"}), 404

                # Delete the device from device manager
                if self.device_manager.delete_device(device_id):
                    logger.info(f"Deleted device: {device_id}")

                    # Note: Command deletion is now handled by the device manager API
                    # See app/api/devices.py delete_managed_device endpoint

                    return jsonify(
                        {"success": True, "deleted_commands": delete_commands}
                    )

                return jsonify({"error": "Failed to delete device"}), 500

            except Exception as e:
                logger.error(f"Error deleting device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/devices/managed/<device_id>/commands", methods=["POST"])
        def add_device_command(device_id):
            """Add a command to a device by learning it from Broadlink"""
            try:
                data = request.get_json()
                command_name = data.get("command_name")
                command_type = data.get("command_type", "rf")
                broadlink_entity = data.get("broadlink_entity")

                if not command_name:
                    return jsonify({"error": "Missing command_name"}), 400

                if not broadlink_entity:
                    return jsonify({"error": "Missing broadlink_entity"}), 400

                # Get the device to construct the full device name
                device = self.device_manager.get_device(device_id)
                if not device:
                    return jsonify({"error": "Device not found"}), 404

                # Learn the command using the existing learn endpoint logic
                logger.info(
                    f"Learning command '{command_name}' for device '{device_id}' using {broadlink_entity}"
                )

                # Prepare data for learning
                learn_data = {
                    "entity_id": broadlink_entity,
                    "device": device_id,  # Use device_id as the device name
                    "command": command_name,
                    "command_type": command_type,
                }

                # Call the async learn_command method
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self._learn_command(learn_data))
                loop.close()

                if result.get("success"):
                    # Add the command to the device metadata
                    command_data = {
                        "command_type": command_type,
                        "learned_at": result.get("learned_at"),
                    }
                    self.device_manager.add_command(
                        device_id, command_name, command_data
                    )

                    return jsonify(
                        {
                            "success": True,
                            "device": self.device_manager.get_device(device_id),
                        }
                    )
                else:
                    return (
                        jsonify(
                            {
                                "success": False,
                                "error": result.get("error", "Failed to learn command"),
                            }
                        ),
                        400,
                    )

            except Exception as e:
                logger.error(f"Error adding command to device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route(
            "/api/devices/managed/<device_id>/import-commands", methods=["POST"]
        )
        def import_device_commands(device_id):
            """Import existing commands to a device without re-learning"""
            try:
                data = request.get_json()
                commands = data.get("commands", [])

                if not commands:
                    return jsonify({"error": "No commands provided"}), 400

                device = self.device_manager.get_device(device_id)
                if not device:
                    return jsonify({"error": "Device not found"}), 404

                logger.info(f"Importing {len(commands)} commands to device {device_id}")

                # Add each command to the device metadata
                for cmd in commands:
                    command_name = cmd.get("command_name")
                    command_type = cmd.get("command_type", "rf")

                    if command_name:
                        command_data = {"command_type": command_type, "imported": True}
                        self.device_manager.add_command(
                            device_id, command_name, command_data
                        )
                        logger.info(
                            f"Imported command: {command_name} ({command_type})"
                        )

                return jsonify(
                    {
                        "success": True,
                        "imported_count": len(commands),
                        "device": self.device_manager.get_device(device_id),
                    }
                )

            except Exception as e:
                logger.error(f"Error importing commands to device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route(
            "/api/devices/managed/<device_id>/commands/<command_name>",
            methods=["DELETE"],
        )
        def delete_device_command(device_id, command_name):
            """Delete a command from a device"""
            try:
                if self.device_manager.delete_command(device_id, command_name):
                    return jsonify({"success": True})

                return jsonify({"error": "Device or command not found"}), 404

            except Exception as e:
                logger.error(f"Error deleting command from device {device_id}: {e}")
                return jsonify({"error": str(e)}), 500

        # Auto-assign areas endpoint removed - areas are now explicitly selected during command learning

    async def _make_ha_request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        """Make a request to Home Assistant API"""
        url = f"{self.ha_url}/api/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.ha_token}",
            "Content-Type": "application/json",
        }

        logger.info(f"Making {method} request to: {url}")

        async with aiohttp.ClientSession() as session:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    # Color-coded status logging
                    status = response.status
                    if status == 200:
                        logger.info(f"✅ Response status: {status}")
                    elif 400 <= status < 500:
                        logger.warning(f"⚠️  Response status: {status} (Client Error)")
                    elif status >= 500:
                        logger.error(f"❌ Response status: {status} (Server Error)")
                    else:
                        logger.info(f"ℹ️  Response status: {status}")

                    if response.status == 200:
                        result = await response.json()
                        logger.info(
                            f"Response data type: {type(result)}, length: {len(result) if isinstance(result, (list, dict)) else 'N/A'}"
                        )
                        return result
                    else:
                        logger.error(
                            f"API request failed with status {response.status}: {await response.text()}"
                        )
                        return {}
            elif method.upper() == "POST":
                async with session.post(url, headers=headers, json=data) as response:
                    # Color-coded status logging
                    status = response.status
                    if status == 200:
                        logger.info(f"✅ POST Response status: {status}")
                    elif 400 <= status < 500:
                        logger.warning(
                            f"⚠️  POST Response status: {status} (Client Error)"
                        )
                    elif status >= 500:
                        logger.error(
                            f"❌ POST Response status: {status} (Server Error)"
                        )
                    else:
                        logger.info(f"ℹ️  POST Response status: {status}")

                    response_text = await response.text()
                    logger.info(f"POST Response body: {response_text}")
                    if response.status == 200:
                        try:
                            return await response.json() if response_text else {}
                        except:
                            logger.info(
                                "POST response was successful but not JSON, returning empty dict"
                            )
                            return {}
                    else:
                        logger.error(
                            f"POST API request failed with status {response.status}: {response_text}"
                        )
                        return None

    def _get_call_id(self) -> str:
        """Generate a unique call ID for tracking concurrent requests"""
        with self._call_lock:
            self._call_counter += 1
            return f"#{self._call_counter}"

    async def _get_ha_areas(self, call_context: str = "unknown") -> List[Dict]:
        """Get Home Assistant areas from storage file

        Args:
            call_context: Context identifier for logging (e.g., 'GET /api/areas', 'device_discovery')
        """
        try:
            areas_file = self.storage_path / "core.area_registry"

            if areas_file.exists():
                logger.info(f"[{call_context}] Reading areas from storage file...")
                async with aiofiles.open(areas_file, "r") as f:
                    content = await f.read()
                    data = json.loads(content)
                    areas = data.get("data", {}).get("areas", [])
                    logger.info(
                        f"[{call_context}] Found {len(areas)} areas from storage"
                    )
                    return areas
            else:
                logger.warning(f"[{call_context}] Areas storage file not found")
                return []

        except Exception as e:
            logger.error(f"[{call_context}] Error reading areas from storage: {e}")
            return []

    async def _get_broadlink_devices(self, call_context: str = "unknown") -> List[Dict]:
        """Get Broadlink remote devices from storage files with area information

        Args:
            call_context: Context identifier for logging (e.g., 'GET /api/broadlink/devices', 'migration')
        """
        try:
            # Read from storage files (primary method for add-on)
            logger.info(
                f"[{call_context}] Reading Broadlink devices from storage files..."
            )

            # Get area information first
            areas_data = await self._get_ha_areas(call_context)
            area_lookup = {area["id"]: area["name"] for area in areas_data}

            # Get device registry
            device_registry_file = self.storage_path / "core.device_registry"
            entity_registry_file = self.storage_path / "core.entity_registry"

            broadlink_devices = []

            if device_registry_file.exists() and entity_registry_file.exists():
                # Read device registry
                async with aiofiles.open(device_registry_file, "r") as f:
                    device_content = await f.read()
                    device_data = json.loads(device_content)
                    devices = device_data.get("data", {}).get("devices", [])

                # Read entity registry
                async with aiofiles.open(entity_registry_file, "r") as f:
                    entity_content = await f.read()
                    entity_data = json.loads(entity_content)
                    entities = entity_data.get("data", {}).get("entities", [])

                # Find Broadlink devices
                for device in devices:
                    try:
                        manufacturer = (device.get("manufacturer") or "").lower()
                        name = (device.get("name") or "").lower()
                        identifiers = device.get("identifiers", [])

                        # Check if this is a Broadlink device
                        if (
                            manufacturer == "broadlink"
                            or "broadlink" in name
                            or any(
                                "broadlink" in str(identifier).lower()
                                for identifier in identifiers
                            )
                        ):

                            device_id = device.get("id")
                            area_id = device.get("area_id")
                            area_name = area_lookup.get(area_id, "Unknown Area")

                            logger.info(
                                f"[{call_context}] Found Broadlink device: {name} (ID: {device_id}, Area: {area_name})"
                            )

                            # Find corresponding entities
                            for entity in entities:
                                if entity.get("device_id") == device_id and entity.get(
                                    "entity_id", ""
                                ).startswith("remote."):

                                    entity_id = entity.get("entity_id")

                                    # Get device status and attributes (including IP)
                                    status = await self._get_device_status(entity_id)

                                    # Get entity state to extract IP address
                                    entity_state = await self._make_ha_request(
                                        "GET", f"states/{entity_id}"
                                    )
                                    host = None
                                    if entity_state:
                                        attributes = entity_state.get("attributes", {})
                                        host = attributes.get("host") or attributes.get(
                                            "friendly_name"
                                        )

                                    broadlink_devices.append(
                                        {
                                            "entity_id": entity_id,
                                            "name": device.get("name", entity_id),
                                            "device_id": device_id,
                                            "unique_id": entity.get("unique_id"),
                                            "area_id": area_id,
                                            "area_name": area_name,
                                            "status": status,
                                            "host": host,
                                            "ip": host,  # Alias for compatibility
                                        }
                                    )
                    except Exception as e:
                        logger.warning(
                            f"Error processing device entry: {e}, device: {device}"
                        )
                        continue

                logger.info(
                    f"[{call_context}] Found {len(broadlink_devices)} Broadlink devices from storage"
                )
                return broadlink_devices
            else:
                logger.warning("Device or entity registry storage files not found")
                return []

        except Exception as e:
            logger.error(f"Error getting Broadlink devices: {e}")
            return []

    async def _get_device_status(self, entity_id: str) -> dict:
        """Determine the actual status of a Broadlink device"""
        try:
            # Get current entity state from Home Assistant
            entity_state = await self._make_ha_request("GET", f"states/{entity_id}")

            if not entity_state:
                return {
                    "status": "unknown",
                    "label": "Unknown",
                    "color": "#6b7280",  # Gray
                    "method": "no_response",
                }

            state = entity_state.get("state", "unknown")
            attributes = entity_state.get("attributes", {})

            # Primary: Check Home Assistant entity state
            if state == "on":
                return {
                    "status": "online",
                    "label": "Online",
                    "color": "#10b981",  # Green
                    "method": "entity_state",
                }
            elif state == "off":
                return {
                    "status": "idle",
                    "label": "Idle",
                    "color": "#f59e0b",  # Yellow/Orange
                    "method": "entity_state",
                }
            elif state == "unavailable":
                return {
                    "status": "offline",
                    "label": "Offline",
                    "color": "#ef4444",  # Red
                    "method": "entity_unavailable",
                }
            else:
                return {
                    "status": "unknown",
                    "label": "Unknown",
                    "color": "#6b7280",  # Gray
                    "method": "unknown_state",
                }

        except Exception as e:
            logger.error(f"Error determining device status for {entity_id}: {e}")
            return {
                "status": "error",
                "label": "Error",
                "color": "#ef4444",  # Red
                "method": "error",
            }

    async def _get_ha_theme(self) -> dict:
        """Get current Home Assistant theme from storage files or API"""
        try:
            # First try to get theme from HA API
            try:
                url = f"{self.ha_url}/api/config"
                headers = {
                    "Authorization": f"Bearer {self.ha_token}",
                    "Content-Type": "application/json",
                }

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            config = await response.json()
                            theme_name = config.get("theme", "default")
                            logger.info(f"Got theme from HA API config: {theme_name}")

                            # Now try to get the actual theme colors from frontend API
                            # Try multiple endpoints to get theme data
                            theme_colors = None

                            # Try /api/frontend/themes first
                            try:
                                frontend_themes_url = (
                                    f"{self.ha_url}/api/frontend/themes"
                                )
                                logger.info(
                                    f"Trying frontend themes API: {frontend_themes_url}"
                                )
                                async with session.get(
                                    frontend_themes_url, headers=headers
                                ) as themes_response:
                                    logger.info(
                                        f"Frontend themes API response status: {themes_response.status}"
                                    )
                                    if themes_response.status == 200:
                                        themes_data = await themes_response.json()
                                        logger.info(
                                            f"Frontend themes data keys: {list(themes_data.keys())}"
                                        )

                                        # Check different possible structures
                                        if (
                                            "themes" in themes_data
                                            and theme_name in themes_data["themes"]
                                        ):
                                            theme_colors = themes_data["themes"][
                                                theme_name
                                            ]
                                            logger.info(
                                                f"Found theme '{theme_name}' in frontend API"
                                            )
                                        elif theme_name in themes_data:
                                            theme_colors = themes_data[theme_name]
                                            logger.info(
                                                f"Found theme '{theme_name}' directly in frontend API"
                                            )
                            except Exception as e:
                                logger.warning(f"Frontend themes API failed: {e}")

                            # Try /api/themes as fallback
                            if not theme_colors:
                                try:
                                    themes_url = f"{self.ha_url}/api/themes"
                                    logger.info(f"Trying themes API: {themes_url}")
                                    async with session.get(
                                        themes_url, headers=headers
                                    ) as themes_response:
                                        logger.info(
                                            f"Themes API response status: {themes_response.status}"
                                        )
                                        if themes_response.status == 200:
                                            themes_data = await themes_response.json()
                                            logger.info(
                                                f"Themes data keys: {list(themes_data.keys())}"
                                            )
                                            logger.info(
                                                f"Available themes: {list(themes_data.get('themes', {}).keys())}"
                                            )

                                            if (
                                                "themes" in themes_data
                                                and theme_name in themes_data["themes"]
                                            ):
                                                theme_colors = themes_data["themes"][
                                                    theme_name
                                                ]
                                                logger.info(
                                                    f"Found theme '{theme_name}' in themes API"
                                                )
                                except Exception as e:
                                    logger.warning(f"Themes API failed: {e}")

                            # If we found theme colors, return them
                            if theme_colors:
                                logger.info(
                                    f"Theme colors keys: {list(theme_colors.keys())}"
                                )
                                logger.info(
                                    f"Sample colors: primary={theme_colors.get('primary-color')}, background={theme_colors.get('primary-background-color')}"
                                )

                                # Determine if dark theme
                                is_dark = (
                                    "dark" in theme_name.lower()
                                    or theme_colors.get("dark-primary-color")
                                    is not None
                                    or (
                                        theme_colors.get(
                                            "primary-background-color", "#ffffff"
                                        ).startswith("#")
                                        and theme_colors.get(
                                            "primary-background-color", "#ffffff"
                                        )[1:3]
                                        in [
                                            "00",
                                            "01",
                                            "10",
                                            "11",
                                            "12",
                                            "13",
                                            "14",
                                            "15",
                                            "16",
                                            "17",
                                            "18",
                                            "19",
                                            "1a",
                                            "1b",
                                            "1c",
                                            "1d",
                                            "1e",
                                            "1f",
                                            "20",
                                        ]
                                    )
                                )

                                return {
                                    "theme_name": theme_name,
                                    "colors": {
                                        "primary": theme_colors.get(
                                            "primary-color", "#03a9f4"
                                        ),
                                        "accent": theme_colors.get(
                                            "accent-color", "#ff9800"
                                        ),
                                        "background": theme_colors.get(
                                            "primary-background-color", "#111111"
                                        ),
                                        "surface": theme_colors.get(
                                            "card-background-color",
                                            theme_colors.get(
                                                "primary-background-color", "#1c1c1c"
                                            ),
                                        ),
                                        "text_primary": theme_colors.get(
                                            "primary-text-color", "#ffffff"
                                        ),
                                        "text_secondary": theme_colors.get(
                                            "secondary-text-color", "#9ca3af"
                                        ),
                                        "border": theme_colors.get(
                                            "divider-color", "#2c2c2c"
                                        ),
                                        "success": theme_colors.get(
                                            "success-color", "#4caf50"
                                        ),
                                        "warning": theme_colors.get(
                                            "warning-color", "#ff9800"
                                        ),
                                        "error": theme_colors.get(
                                            "error-color", "#f44336"
                                        ),
                                        "info": theme_colors.get(
                                            "info-color", "#2196f3"
                                        ),
                                    },
                                    "is_dark": is_dark,
                                }
                            else:
                                logger.warning(
                                    f"Could not find theme colors for '{theme_name}' in any API endpoint"
                                )
            except Exception as e:
                logger.warning(f"Could not get theme from HA API: {e}")

            # Fallback: Read frontend storage to get theme configuration
            frontend_file = self.storage_path / "frontend.user_data"

            theme_name = "default"
            theme_mode = "dark"

            logger.info(f"Checking for frontend storage at: {frontend_file}")
            logger.info(f"Frontend file exists: {frontend_file.exists()}")

            # Try to get user's theme preference from frontend storage
            if frontend_file.exists():
                try:
                    async with aiofiles.open(frontend_file, "r") as f:
                        content = await f.read()
                        frontend_data = json.loads(content)

                        # Look for theme settings in user data
                        data = frontend_data.get("data", {})
                        logger.info(f"Frontend data keys: {list(data.keys())}")

                        for user_id, user_data in data.items():
                            if isinstance(user_data, dict):
                                logger.info(
                                    f"User {user_id} data keys: {list(user_data.keys())}"
                                )
                                # Get theme from user preferences
                                if "selectedTheme" in user_data:
                                    theme_name = user_data["selectedTheme"]
                                    logger.info(f"Found selectedTheme: {theme_name}")
                                if "selectedDarkTheme" in user_data:
                                    theme_mode = "dark"
                                    logger.info(f"Found selectedDarkTheme")
                                elif "selectedLightTheme" in user_data:
                                    theme_mode = "light"
                                    logger.info(f"Found selectedLightTheme")
                                break

                        logger.info(
                            f"Found theme from frontend storage: {theme_name} ({theme_mode})"
                        )
                except Exception as e:
                    logger.warning(f"Could not read frontend storage: {e}")
            else:
                logger.warning(f"Frontend storage file not found at {frontend_file}")

            # Try to read theme definitions from themes storage
            themes_file = self.storage_path / "frontend.themes"
            theme_data = {}

            logger.info(f"Checking for themes storage at: {themes_file}")
            logger.info(f"Themes file exists: {themes_file.exists()}")

            if themes_file.exists():
                try:
                    async with aiofiles.open(themes_file, "r") as f:
                        content = await f.read()
                        themes_storage = json.loads(content)

                        # Get theme data
                        themes = themes_storage.get("data", {}).get("themes", {})
                        logger.info(
                            f"Available themes in storage: {list(themes.keys())}"
                        )

                        if theme_name in themes:
                            theme_data = themes[theme_name]
                            logger.info(f"Loaded theme data for: {theme_name}")
                            logger.info(f"Theme data keys: {list(theme_data.keys())}")
                        elif theme_name != "default":
                            logger.warning(
                                f"Theme {theme_name} not found in storage, using default"
                            )
                except Exception as e:
                    logger.warning(f"Could not read themes storage: {e}")
            else:
                logger.warning(f"Themes storage file not found at {themes_file}")

            # Extract common theme colors with fallbacks
            result = {
                "theme_name": theme_name,
                "colors": {
                    "primary": theme_data.get("primary-color", "#03a9f4"),
                    "accent": theme_data.get("accent-color", "#ff9800"),
                    "background": theme_data.get("primary-background-color", "#111111"),
                    "surface": theme_data.get("card-background-color", "#1c1c1c"),
                    "text_primary": theme_data.get("primary-text-color", "#ffffff"),
                    "text_secondary": theme_data.get("secondary-text-color", "#9ca3af"),
                    "border": theme_data.get("divider-color", "#2c2c2c"),
                    "success": theme_data.get("success-color", "#4caf50"),
                    "warning": theme_data.get("warning-color", "#ff9800"),
                    "error": theme_data.get("error-color", "#f44336"),
                    "info": theme_data.get("info-color", "#2196f3"),
                },
                "is_dark": theme_mode == "dark" or "dark" in theme_name.lower(),
            }

            logger.info(
                f"Returning theme: {result['theme_name']} with colors: {result['colors']}"
            )
            return result

        except Exception as e:
            logger.error(f"Error getting HA theme: {e}", exc_info=True)
            return self._get_default_theme()

    def _get_default_theme(self) -> dict:
        """Get default dark theme colors matching current design"""
        return {
            "theme_name": "default_dark",
            "colors": {
                "primary": "#03a9f4",
                "accent": "#ff9800",
                "background": "#111111",
                "surface": "#1c1c1c",
                "text_primary": "#ffffff",
                "text_secondary": "#9ca3af",
                "border": "#2c2c2c",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "info": "#3b82f6",
            },
            "is_dark": True,
        }

    async def _get_learned_commands(self, device_id: Optional[str] = None) -> Dict:
        """Get learned commands from storage files with filtering and area information"""
        try:
            # Find the storage files for Broadlink commands
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))

            all_commands = {}

            # Get area information and Broadlink devices
            areas_data = await self._get_ha_areas("_get_learned_commands")
            area_lookup = {area["id"]: area["name"] for area in areas_data}

            # Get all Broadlink devices to map storage files to device areas
            broadlink_devices = await self._get_broadlink_devices(
                "_get_learned_commands"
            )

            # Create a mapping from storage file to device area
            # Storage files are named like: broadlink_remote_<unique_id>_codes
            storage_to_device = {}
            for device in broadlink_devices:
                unique_id = device.get("unique_id", "")
                if unique_id:
                    # Match storage file pattern
                    storage_pattern = f"broadlink_remote_{unique_id}_codes"
                    storage_to_device[storage_pattern] = {
                        "area_id": device.get("area_id"),
                        "area_name": device.get("area_name", "Unknown"),
                        "entity_id": device.get("entity_id"),
                    }

            for storage_file in storage_files:
                try:
                    async with aiofiles.open(storage_file, "r") as f:
                        content = await f.read()
                        data = json.loads(content)

                        # Get the device info for this storage file
                        storage_filename = storage_file.name
                        device_info = storage_to_device.get(storage_filename, {})
                        file_area_id = device_info.get("area_id")
                        file_area_name = device_info.get("area_name", "Unknown")

                        # The data structure contains device names as keys
                        for device_name, commands in data.get("data", {}).items():
                            if isinstance(commands, dict):
                                # Use the area from the Broadlink device that owns this storage file
                                # This ensures commands are always associated with the current device area
                                all_commands[device_name] = {
                                    "commands": list(commands.keys()),
                                    "command_data": commands,  # Include actual command codes
                                    "area_id": file_area_id,
                                    "area_name": file_area_name,
                                    "device_part": device_name,
                                    "full_name": device_name,
                                    "storage_file": storage_filename,
                                }

                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue

            logger.info(f"Found {len(all_commands)} learned devices with commands")
            return all_commands

        except Exception as e:
            logger.error(f"Error getting learned commands: {e}")
            return {}

    async def _get_all_broadlink_commands(self) -> Dict[str, Dict[str, str]]:
        """
        Get all Broadlink commands with cache layer.
        
        This method sits behind a cache that handles async file writes:
        - On read: Returns cached data merged with file data
        - Cache is refreshed periodically (STORAGE_CACHE_TTL)
        - Recently deleted commands are filtered out
        """
        try:
            current_time = time.time()
            
            # Read from storage files
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))
            file_commands = {}

            for storage_file in storage_files:
                try:
                    async with aiofiles.open(storage_file, "r") as f:
                        content = await f.read()
                        data = json.loads(content)

                        # Extract device commands
                        for device_name, commands in data.get("data", {}).items():
                            if isinstance(commands, dict):
                                file_commands[device_name] = commands

                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue

            # Merge with cache: cache takes precedence for devices that have cached data
            all_commands = {}
            
            # Start with file data
            for device_name, commands in file_commands.items():
                all_commands[device_name] = commands.copy()
            
            # Apply cache updates (additions/modifications)
            for device_name, cached_commands in self.storage_command_cache.items():
                if device_name not in all_commands:
                    all_commands[device_name] = {}
                all_commands[device_name].update(cached_commands)
            
            # Filter out recently deleted commands
            for device_name in list(all_commands.keys()):
                if device_name in self.recently_deleted_commands:
                    for cmd_name in list(all_commands[device_name].keys()):
                        if self._is_recently_deleted(device_name, cmd_name):
                            logger.debug(f"Filtering out recently deleted: {device_name}/{cmd_name}")
                            del all_commands[device_name][cmd_name]
                    
                    # Clean up empty devices
                    if not all_commands[device_name]:
                        del all_commands[device_name]
            
            # Clean up expired deletion cache entries
            self._cleanup_deletion_cache()

            return all_commands

        except Exception as e:
            logger.error(f"Error getting Broadlink commands: {e}")
            return {}

    def _add_to_deletion_cache(self, device_name: str, command_name: str):
        """Add a command to the recently deleted cache"""
        if device_name not in self.recently_deleted_commands:
            self.recently_deleted_commands[device_name] = {}
        self.recently_deleted_commands[device_name][command_name] = time.time()
        logger.info(f"Added to deletion cache: {device_name}/{command_name}")

    def _is_recently_deleted(self, device_name: str, command_name: str) -> bool:
        """Check if a command was recently deleted (within TTL)"""
        if device_name not in self.recently_deleted_commands:
            return False

        if command_name not in self.recently_deleted_commands[device_name]:
            return False

        deletion_time = self.recently_deleted_commands[device_name][command_name]
        age = time.time() - deletion_time

        if age > self.DELETION_CACHE_TTL:
            # Expired, remove from cache
            del self.recently_deleted_commands[device_name][command_name]
            if not self.recently_deleted_commands[device_name]:
                del self.recently_deleted_commands[device_name]
            return False

        return True

    def _cleanup_deletion_cache(self):
        """Remove expired entries from deletion cache"""
        current_time = time.time()
        devices_to_remove = []

        for device_name, commands in self.recently_deleted_commands.items():
            commands_to_remove = []
            for command_name, deletion_time in commands.items():
                if current_time - deletion_time > self.DELETION_CACHE_TTL:
                    commands_to_remove.append(command_name)

            for command_name in commands_to_remove:
                del commands[command_name]
            
            # Mark device for removal if no commands left
            if not commands:
                devices_to_remove.append(device_name)
        
        # Remove empty devices
        for device_name in devices_to_remove:
            del self.recently_deleted_commands[device_name]
    
    def _add_to_storage_cache(self, device_name: str, command_name: str, command_data: str):
        """
        Add a command to the storage cache.
        This is called immediately when learning/importing a command.
        The cache will return this data until the file is actually written.
        """
        if device_name not in self.storage_command_cache:
            self.storage_command_cache[device_name] = {}
        self.storage_command_cache[device_name][command_name] = command_data
        logger.info(f"✅ Added to storage cache: {device_name}/{command_name}")
    
    def _remove_from_storage_cache(self, device_name: str, command_name: str):
        """
        Remove a command from the storage cache.
        This is called immediately when deleting a command.
        """
        if device_name in self.storage_command_cache:
            if command_name in self.storage_command_cache[device_name]:
                del self.storage_command_cache[device_name][command_name]
                logger.info(f"🗑️ Removed from storage cache: {device_name}/{command_name}")
                
                # Clean up empty device entries
                if not self.storage_command_cache[device_name]:
                    del self.storage_command_cache[device_name]
    
    def _clear_storage_cache(self, device_name: Optional[str] = None):
        """
        Clear storage cache for a device or all devices.
        Called after file operations complete to sync with actual file state.
        """
        if device_name:
            if device_name in self.storage_command_cache:
                del self.storage_command_cache[device_name]
                logger.debug(f"Cleared storage cache for device: {device_name}")
        else:
            self.storage_command_cache.clear()
            logger.debug("Cleared all storage cache")

    def schedule_command_poll(self, device_id: str, device_name: str, command_name: str):
        """Schedule background polling for a pending command"""
        with self.poll_lock:
            # Add to poll list (device_id, device_name, command_name, poll_count, max_polls)
            self.pending_command_polls.append((device_id, device_name, command_name, 0, 10))
            logger.info(f"📋 Scheduled poll for {device_name}/{command_name}")
            
            # Start poll thread if not running
            if not self.poll_thread_running:
                self.poll_thread_running = True
                self.poll_thread = threading.Thread(target=self._poll_pending_commands, daemon=True)
                self.poll_thread.start()
                logger.info("🔄 Started background polling thread")
    
    def _poll_pending_commands(self):
        """Background thread that polls for pending commands"""
        logger.info("🔄 Background polling thread started")
        
        while True:
            try:
                time.sleep(3)  # Poll every 3 seconds
                
                with self.poll_lock:
                    if not self.pending_command_polls:
                        # No more pending commands, stop thread
                        self.poll_thread_running = False
                        logger.info("✅ No more pending commands, stopping poll thread")
                        break
                    
                    # Process each pending command
                    still_pending = []
                    for device_id, device_name, command_name, poll_count, max_polls in self.pending_command_polls:
                        poll_count += 1
                        
                        # Try to fetch the code
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            all_commands = loop.run_until_complete(self._get_all_broadlink_commands())
                            device_commands = all_commands.get(device_name, {})
                            learned_code = device_commands.get(command_name)
                            
                            if learned_code and learned_code != "pending":
                                # Got the code! Update devices.json
                                logger.info(f"✅ Poll #{poll_count}: Found code for {device_name}/{command_name} (length: {len(learned_code)} chars)")
                                
                                # Update devices.json
                                device = self.device_manager.get_device(device_id)
                                if device:
                                    if "commands" not in device:
                                        device["commands"] = {}
                                    
                                    # Update with actual code
                                    if command_name in device["commands"]:
                                        device["commands"][command_name]["data"] = learned_code
                                        self.device_manager.update_device(device_id, device)
                                        logger.info(f"✅ Updated devices.json with actual code for {device_name}/{command_name}")
                                    else:
                                        logger.warning(f"⚠️ Command {command_name} not found in devices.json")
                                else:
                                    logger.warning(f"⚠️ Device {device_id} not found in device_manager")
                                
                                # Don't re-add to pending list (success!)
                            elif poll_count >= max_polls:
                                # Max polls reached, give up
                                logger.warning(f"⚠️ Gave up polling for {device_name}/{command_name} after {poll_count} attempts")
                            else:
                                # Still pending, try again
                                logger.debug(f"⏳ Poll #{poll_count}: Code still pending for {device_name}/{command_name}")
                                still_pending.append((device_id, device_name, command_name, poll_count, max_polls))
                        finally:
                            loop.close()
                    
                    # Update pending list
                    self.pending_command_polls = still_pending
                    
            except Exception as e:
                logger.error(f"Error in polling thread: {e}")
                time.sleep(5)  # Wait a bit before retrying on error

    async def _find_broadlink_entity_for_device(self, device_name: str) -> str:
        """Find which Broadlink entity owns the commands for a given device name"""
        try:
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))
            broadlink_devices = await self._get_broadlink_devices(
                "_find_broadlink_entity_for_device"
            )

            # Create mapping from storage file to entity_id
            storage_to_entity = {}
            for device in broadlink_devices:
                unique_id = device.get("unique_id", "")
                if unique_id:
                    storage_filename = f"broadlink_remote_{unique_id}_codes"
                    storage_to_entity[storage_filename] = device.get("entity_id")

            # Search storage files for the device
            for storage_file in storage_files:
                try:
                    async with aiofiles.open(storage_file, "r") as f:
                        content = await f.read()
                        data = json.loads(content)

                        # Check if this device exists in this storage file
                        if device_name in data.get("data", {}):
                            # Found it! Return the corresponding entity_id
                            entity_id = storage_to_entity.get(storage_file.name)
                            if entity_id:
                                logger.info(
                                    f"Found device '{device_name}' in storage file '{storage_file.name}' -> entity '{entity_id}'"
                                )
                                return entity_id

                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue

            logger.warning(
                f"Could not find Broadlink entity for device '{device_name}'"
            )
            return None

        except Exception as e:
            logger.error(f"Error finding Broadlink entity: {e}")
            return None

    async def _learn_command(self, data: Dict) -> Dict:
        """Learn a new command with 2-step process monitoring"""
        try:
            entity_id = data.get("entity_id")
            device = data.get("device")
            command = data.get("command")
            command_type = data.get("command_type", "ir")
            entity_type_hint = data.get("entity_type_hint")
            area_name = data.get("area_name")

            log_msg = f"Starting learning process for command: {command}"
            if entity_type_hint:
                log_msg += f" (entity type hint: {entity_type_hint})"
            if area_name:
                log_msg += f" in area: {area_name}"
            logger.info(log_msg)

            # First, let's check what services are available
            logger.info("Checking available services...")
            services_result = await self._make_ha_request("GET", "services")
            if services_result:
                logger.info(f"Services result type: {type(services_result)}")

                # Handle both dict and list formats
                if isinstance(services_result, dict):
                    remote_services = services_result.get("remote", {})
                elif isinstance(services_result, list):
                    # Find remote services in the list
                    remote_services = {}
                    for service_domain in services_result:
                        if (
                            isinstance(service_domain, dict)
                            and service_domain.get("domain") == "remote"
                        ):
                            remote_services = service_domain.get("services", {})
                            break
                else:
                    remote_services = {}

                logger.info(
                    f"Available remote services: {list(remote_services.keys()) if remote_services else 'None'}"
                )

                # Check if learn_command exists
                if "learn_command" in remote_services:
                    learn_service = remote_services["learn_command"]
                    logger.info(f"learn_command service details: {learn_service}")
                else:
                    logger.warning(
                        "learn_command service not found in remote services!"
                    )

            # Also check the entity state and attributes
            entity_state = await self._make_ha_request("GET", f"states/{entity_id}")
            if entity_state:
                state = entity_state.get("state")
                logger.info(f"Entity {entity_id} state: {state}")
                logger.info(f"Entity attributes: {entity_state.get('attributes', {})}")

                # Check if device is available
                if state == "unavailable":
                    logger.warning(
                        f"Device {entity_id} is unavailable - learning may not work"
                    )
                    return {
                        "success": False,
                        "error": f"Broadlink device is unavailable. Please check that the device is powered on and connected to your network.",
                    }

            # Prepare the service call payload using the correct HA format
            # According to HA docs, the format should be:
            # target: { entity_id: ... }
            # data: { device: ..., command: ..., command_type: ... }
            service_payload = {
                "target": {"entity_id": entity_id},
                "data": {"device": device, "command": command},
            }

            # Add command_type only for RF commands (IR is default)
            if command_type == "rf":
                service_payload["data"]["command_type"] = "rf"

            # Add a timeout to prevent getting stuck
            service_payload["data"]["timeout"] = 30

            logger.info(
                f"Calling learn_command service with payload: {service_payload}"
            )

            # Use the correct HA service call format
            logger.info(
                "Attempting service call to services/remote/learn_command with target/data format"
            )
            result = await self._make_ha_request(
                "POST", "services/remote/learn_command", service_payload
            )
            logger.info(f"Learn command service result: {result}")

            # Check if we got a 400 error, which might mean the format is wrong
            if result is None:
                logger.info(
                    "Got None result (likely 400 error), trying legacy format..."
                )

                # Try the old format as fallback
                legacy_payload = {
                    "entity_id": entity_id,
                    "device": device,
                    "command": command,
                    "timeout": 30,
                }
                if command_type == "rf":
                    legacy_payload["command_type"] = "rf"

                logger.info(f"Trying legacy format: {legacy_payload}")
                result = await self._make_ha_request(
                    "POST", "services/remote/learn_command", legacy_payload
                )
                logger.info(f"Legacy format result: {result}")

            # Check if the service call succeeded
            if result == [] or result is not None:
                logger.info("Learn command service called successfully")
                return {
                    "success": True,
                    "message": "⚠️ Learning request sent to device. Check Home Assistant notifications (🔔) for instructions. Note: If the device is offline or times out, you will see a notification but this dialog will still show success.",
                    "result": result,
                }
            else:
                logger.error(
                    "Learn command service failed - all attempts returned None"
                )
                return {
                    "success": False,
                    "error": "Failed to start learning process - check that the Broadlink device is online and accessible",
                }

        except Exception as e:
            logger.error(f"Error learning command: {e}")
            return {"success": False, "error": str(e)}

    async def _get_notifications_http(self) -> List[Dict]:
        """Get persistent notifications via HTTP (fallback when WebSocket fails)"""
        try:
            # Get all states and filter for persistent notifications
            states = await self._make_ha_request("GET", "states")
            if not isinstance(states, list):
                logger.warning("States API returned non-list response")
                return []

            notifications = []
            for entity in states:
                entity_id = entity.get("entity_id", "")
                if entity_id.startswith("persistent_notification."):
                    attributes = entity.get("attributes", {})
                    title = attributes.get("title", "")
                    message = attributes.get("message", "")

                    # Log ALL persistent notifications for debugging
                    logger.info(
                        f"HTTP: Found notification - Title: '{title}', Message: '{message[:50]}...'"
                    )

                    # Look for Broadlink learning notifications
                    if any(
                        keyword in title.lower()
                        for keyword in ["sweep frequency", "learn command"]
                    ) or any(
                        keyword in message.lower()
                        for keyword in [
                            "broadlink",
                            "sweep",
                            "learning",
                            "press and hold",
                            "press the button",
                            "remote",
                        ]
                    ):
                        notifications.append(
                            {
                                "title": title,
                                "message": message,
                                "notification_id": entity_id,
                                "created_at": entity.get("last_changed", ""),
                            }
                        )
                        logger.info(
                            f"★ HTTP MATCHED Broadlink notification: '{title}' - '{message[:100]}'"
                        )

            logger.info(
                f"HTTP notifications: Found {len([e for e in states if e.get('entity_id', '').startswith('persistent_notification.')])} total, {len(notifications)} Broadlink"
            )
            return notifications

        except Exception as e:
            logger.error(f"Error getting HTTP notifications: {e}")
            return []

    async def _get_notifications(self) -> List[Dict]:
        """Get persistent notifications from Home Assistant - using correct API endpoint"""
        try:
            current_time = time.time()

            # Try the direct persistent notification API endpoint first
            logger.info("Trying direct persistent notification API endpoint...")
            pn_notifications = await self._make_ha_request(
                "GET", "persistent_notification"
            )

            if isinstance(pn_notifications, list) and len(pn_notifications) > 0:
                logger.info(
                    f"Found {len(pn_notifications)} notifications via persistent_notification API"
                )

                notifications = []
                for notification in pn_notifications:
                    title = notification.get("title", "")
                    message = notification.get("message", "")
                    notification_id = notification.get("notification_id", "")

                    # Debug: Log ALL persistent notifications
                    logger.info(
                        f"DEBUG: Persistent notification - ID: '{notification_id}', Title: '{title}', Message: '{message[:100]}...'"
                    )

                    # Look for Broadlink learning notifications
                    full_search_text = f"{title} {message}".lower()

                    if any(
                        keyword in full_search_text
                        for keyword in [
                            "sweep frequency",
                            "learn command",
                            "broadlink",
                            "sweep",
                            "learning",
                            "press and hold",
                            "press the button",
                            "remote",
                            "rf",
                            "ir",
                        ]
                    ):
                        notifications.append(
                            {
                                "id": notification_id,
                                "title": title,
                                "message": message,
                                "created_at": notification.get("created_at", ""),
                                "notification": notification,
                            }
                        )
                        logger.info(
                            f"★ MATCHED Broadlink notification: '{title}' - '{message[:100]}'"
                        )

                # Cache the results
                self.cached_notifications = notifications
                self.last_notification_check = current_time

                logger.info(
                    f"Total persistent notifications found: {len(pn_notifications)}"
                )
                logger.info(
                    f"Matched Broadlink learning notifications: {len(notifications)}"
                )
                return notifications

            # Fallback to states API if persistent_notification endpoint doesn't work
            logger.info(
                "Persistent notification API returned empty, trying states API..."
            )
            states = await self._make_ha_request("GET", "states")
            if not isinstance(states, list):
                logger.warning("States API returned non-list response")
                return []

            notifications = []
            for entity in states:
                entity_id = entity.get("entity_id", "")
                if entity_id.startswith("persistent_notification."):
                    attributes = entity.get("attributes", {})
                    title = attributes.get("title", "")
                    message = attributes.get("message", "")

                    # Debug: Log ALL persistent notifications to see what we have
                    logger.info(
                        f"DEBUG: Found persistent notification via states - ID: '{entity_id}', Title: '{title}', Message: '{message[:100]}...', State: '{entity.get('state', 'N/A')}'"
                    )

                    # Look for Broadlink learning notifications - much broader search
                    # Check title, message, and entity attributes for any Broadlink-related content
                    entity_attrs = entity.get("attributes", {})
                    full_search_text = f"{title} {message} {entity_attrs}".lower()

                    if any(
                        keyword in full_search_text
                        for keyword in [
                            "sweep frequency",
                            "learn command",
                            "broadlink",
                            "sweep",
                            "learning",
                            "press and hold",
                            "press the button",
                            "remote",
                            "rf",
                            "ir",
                        ]
                    ):
                        notifications.append(
                            {
                                "id": entity_id,
                                "title": title,
                                "message": message,
                                "created_at": entity.get("last_changed", ""),
                                "state": entity.get("state", ""),
                                "attributes": entity_attrs,
                            }
                        )
                        logger.info(
                            f"★ MATCHED Broadlink notification: '{title}' - '{message[:100]}'"
                        )

            # Cache the results
            self.cached_notifications = notifications
            self.last_notification_check = current_time

            persistent_count = len(
                [
                    e
                    for e in states
                    if e.get("entity_id", "").startswith("persistent_notification.")
                ]
            )
            logger.info(
                f"Total persistent notifications found via states: {persistent_count}"
            )
            logger.info(
                f"Matched Broadlink learning notifications: {len(notifications)}"
            )
            return notifications

        except Exception as e:
            logger.error(f"Error getting notifications: {e}")
            return []

    def _start_websocket_client(self):
        """Start WebSocket client in a separate thread"""

        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._websocket_client())
            except Exception as e:
                logger.error(f"WebSocket client error: {e}")
            finally:
                loop.close()

        self.ws_thread = threading.Thread(target=run_websocket, daemon=True)
        self.ws_thread.start()
        logger.info("Started WebSocket client thread")

    async def _websocket_client(self):
        """WebSocket client to connect to Home Assistant"""
        ws_url = "ws://supervisor/core/api/websocket"

        while True:
            try:
                logger.info(f"Connecting to WebSocket: {ws_url}")
                async with websockets.connect(ws_url) as websocket:
                    self.ws_connection = websocket

                    # Authenticate
                    auth_msg = {"type": "auth", "access_token": self.ha_token}
                    await websocket.send(json.dumps(auth_msg))

                    # Wait for auth response
                    auth_response = await websocket.recv()
                    auth_data = json.loads(auth_response)

                    if auth_data.get("type") == "auth_ok":
                        logger.info("WebSocket authenticated successfully")

                        # Listen for messages
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                await self._handle_websocket_message(data)
                            except Exception as e:
                                logger.error(f"Error handling WebSocket message: {e}")
                    else:
                        logger.error(f"WebSocket authentication failed: {auth_data}")

            except Exception as e:
                logger.error(f"WebSocket connection error: {e}")
                await asyncio.sleep(5)  # Wait before reconnecting

    async def _handle_websocket_message(self, data: Dict):
        """Handle incoming WebSocket messages"""
        if data.get("type") == "result" and data.get("success") and "result" in data:
            result = data["result"]
            if isinstance(result, list):
                # This could be persistent notifications
                self.ws_notifications = result
                logger.info(f"Updated WebSocket notifications: {len(result)} items")

    async def _get_ws_notifications(self) -> List[Dict]:
        """Get notifications from WebSocket cache"""
        try:
            if self.ws_connection:
                # Request fresh notifications
                self.ws_message_id += 1
                request_msg = {
                    "id": self.ws_message_id,
                    "type": "persistent_notification/get",
                }
                await self.ws_connection.send(json.dumps(request_msg))

                # Wait a bit for response
                await asyncio.sleep(0.5)

            # Filter for learning-related notifications
            learning_notifications = []
            for notification in self.ws_notifications:
                title = notification.get("title", "").lower()
                message = notification.get("message", "").lower()
                if (
                    "sweep" in title
                    or "learn" in title
                    or "command" in title
                    or "broadlink" in message
                ):
                    learning_notifications.append(notification)
                    logger.info(
                        f"Found WebSocket notification: {notification.get('title')} - {notification.get('message', '')[:100]}"
                    )

            return learning_notifications

        except Exception as e:
            logger.error(f"Error getting WebSocket notifications: {e}")
            return []

    async def _send_command(self, data: Dict) -> Dict:
        """Send a learned command"""
        try:
            entity_id = data.get("entity_id")
            device = data.get("device")
            command = data.get("command")

            logger.info(f"SEND REQUEST DEBUG:")
            logger.info(f"  Raw data received: {data}")
            logger.info(f"  entity_id: '{entity_id}'")
            logger.info(
                f"  device: '{device}' (length: {len(device) if device else 'None'})"
            )
            logger.info(
                f"  command: '{command}' (length: {len(command) if command else 'None'})"
            )
            logger.info(f"Sending command: {device}_{command} to entity {entity_id}")

            # Broadlink integration expects command as an array
            command_list = [command] if isinstance(command, str) else command

            # Try the working format first: flat structure with command as array
            # This is what the Broadlink integration actually expects
            payload = {
                "entity_id": entity_id,
                "device": device,
                "command": command_list,
            }

            logger.info(f"Sending command with payload: {payload}")
            result = await self._make_ha_request(
                "POST", "services/remote/send_command", payload
            )

            if result is not None:
                logger.info(f"✅ Command sent successfully: {device}_{command}")
                return {
                    "success": True,
                    "message": f"Command {command} sent successfully",
                }

            # Fallback: Try modern format with target/data structure (for newer HA versions)
            logger.info("Trying modern format with target/data structure...")
            modern_payload = {
                "target": {"entity_id": entity_id},
                "data": {"device": device, "command": command_list},
            }
            result = await self._make_ha_request(
                "POST", "services/remote/send_command", modern_payload
            )

            if result is not None:
                logger.info(
                    f"✅ Command sent successfully with modern format: {device}_{command}"
                )
                return {
                    "success": True,
                    "message": f"Command {command} sent successfully",
                }

            # Last resort: Try with command as string (very old format)
            logger.info("Trying string command format...")
            string_payload = {
                "entity_id": entity_id,
                "device": device,
                "command": command,
            }
            result = await self._make_ha_request(
                "POST", "services/remote/send_command", string_payload
            )

            if result is not None:
                logger.info(
                    f"✅ Command sent successfully with string format: {device}_{command}"
                )
                return {
                    "success": True,
                    "message": f"Command {command} sent successfully",
                }
            else:
                logger.error(
                    f"❌ FAILED: All formats failed for command: {device}_{command}"
                )
                return {
                    "success": False,
                    "error": "Failed to send command - all formats rejected by Home Assistant",
                }

        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return {"success": False, "error": str(e)}

    def _sync_devices_to_metadata(self):
        """Convert devices.json format to metadata.json format for entity generator"""
        try:
            devices = self.device_manager.get_all_devices()

            for device_id, device_data in devices.items():
                # Map device commands to entity commands
                entity_commands = self._map_device_commands_to_entity_commands(
                    device_data.get("commands", {}), device_data.get("entity_type")
                )

                if not entity_commands:
                    logger.warning(
                        f"Device {device_id} has no mappable commands, skipping"
                    )
                    continue

                # Create entity metadata
                entity_metadata = {
                    "device": device_id,
                    "name": device_data.get("full_name", device_data.get("name")),
                    "friendly_name": device_data.get(
                        "full_name", device_data.get("name")
                    ),
                    "entity_type": device_data.get("entity_type"),
                    "commands": entity_commands,
                    "broadlink_entity": device_data.get("broadlink_entity"),
                    "icon": device_data.get("icon"),
                    "enabled": True,
                }

                # Save to metadata
                self.storage_manager.save_entity(device_id, entity_metadata)

            logger.info(f"Synced {len(devices)} devices to metadata")

        except Exception as e:
            logger.error(f"Error syncing devices to metadata: {e}")

    def _map_device_commands_to_entity_commands(
        self, device_commands: dict, entity_type: str
    ) -> dict:
        """Map device command names to standardized entity command names"""
        entity_commands = {}

        # Command name mappings
        on_commands = ["power_on", "turn_on", "on", "light_on"]
        off_commands = ["power_off", "turn_off", "off", "light_off"]
        toggle_commands = ["toggle", "power_toggle", "light_toggle"]

        # For climate and cover entities, pass through all commands as-is
        # since they have specific command patterns (temperature_*, hvac_mode_*, position_*, etc.)
        if entity_type in ["climate", "cover"]:
            for cmd_name in device_commands.keys():
                cmd_lower = cmd_name.lower()

                # Still map common on/off commands
                if cmd_lower in on_commands:
                    entity_commands["turn_on"] = cmd_name
                elif cmd_lower in off_commands:
                    entity_commands["turn_off"] = cmd_name
                elif cmd_lower == "open":
                    entity_commands["open"] = cmd_name
                elif cmd_lower == "close":
                    entity_commands["close"] = cmd_name
                elif cmd_lower == "stop":
                    entity_commands["stop"] = cmd_name
                else:
                    # Pass through all other commands as-is (temperature_*, hvac_mode_*, etc.)
                    entity_commands[cmd_name] = cmd_name
        else:
            # For other entity types, use standard mapping
            for cmd_name in device_commands.keys():
                cmd_lower = cmd_name.lower()

                if cmd_lower in on_commands:
                    entity_commands["turn_on"] = cmd_name
                elif cmd_lower in off_commands:
                    entity_commands["turn_off"] = cmd_name
                elif cmd_lower in toggle_commands:
                    entity_commands["toggle"] = cmd_name
                elif cmd_name.startswith("speed_") or cmd_name.startswith("fan_speed_"):
                    # Fan speed commands
                    entity_commands[cmd_name] = cmd_name
                elif cmd_name.startswith("fan_"):
                    # Other fan-specific commands (fan_off, fan_reverse, etc.)
                    entity_commands[cmd_name] = cmd_name
                elif cmd_lower in ["reverse", "direction"]:
                    # Direction/reverse commands for fans
                    entity_commands[cmd_name] = cmd_name

        return entity_commands

    async def _reload_broadlink_config(self) -> bool:
        """Reload Broadlink integration configuration without restarting HA"""
        try:
            logger.info("🔄 Reloading Broadlink configuration...")

            # Call the homeassistant.reload_config_entry service for Broadlink
            # First, we need to find the Broadlink config entry ID
            result = await self._make_ha_request("GET", "config/config_entries/entry")

            if result:
                # Find Broadlink entries
                broadlink_entries = [
                    entry for entry in result if entry.get("domain") == "broadlink"
                ]

                for entry in broadlink_entries:
                    entry_id = entry.get("entry_id")
                    if entry_id:
                        logger.info(f"Reloading Broadlink config entry: {entry_id}")
                        reload_result = await self._make_ha_request(
                            "POST", f"config/config_entries/entry/{entry_id}/reload"
                        )
                        if reload_result is not None:
                            logger.info(
                                f"✅ Broadlink configuration reloaded successfully"
                            )
                            return True

            logger.warning("Could not reload Broadlink config - no entries found")
            return False

        except Exception as e:
            logger.error(f"Error reloading Broadlink config: {e}")
            return False

    async def _delete_command(self, data: Dict) -> Dict:
        """Delete a learned command"""
        try:
            entity_id = data.get("entity_id")
            device = data.get("device")
            command = data.get("command")

            logger.info(f"DELETE REQUEST DEBUG:")
            logger.info(f"  Raw data received: {data}")
            logger.info(f"  entity_id: '{entity_id}'")
            logger.info(
                f"  device: '{device}' (length: {len(device) if device else 'None'})"
            )
            logger.info(
                f"  command: '{command}' (length: {len(command) if command else 'None'})"
            )
            logger.info(f"Deleting command: {device}_{command} from entity {entity_id}")

            # Use the same format as V1 - flat structure with entity_id
            service_data = {
                "entity_id": entity_id,
                "device": device,
                "command": command,
            }

            logger.info(f"Deleting command with payload: {service_data}")
            result = await self._make_ha_request(
                "POST", "services/remote/delete_command", service_data
            )

            if result is not None:
                logger.info(f"✅ Command deleted successfully: {device}_{command}")
                return {
                    "success": True,
                    "message": f"Command {command} deleted successfully",
                }
            else:
                logger.error(f"❌ FAILED to delete command: {device}_{command}")
                return {
                    "success": False,
                    "error": "Failed to delete command from Broadlink storage",
                }

        except Exception as e:
            logger.error(f"Error deleting command: {e}")
            return {"success": False, "error": str(e)}

    def _schedule_migration_check(self):
        """Schedule automatic migration check on startup"""

        def run_migration_check():
            try:
                logger.info("=" * 60)
                logger.info("🔍 Broadlink Manager - Checking installation type...")
                logger.info("=" * 60)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Get Broadlink devices
                devices = loop.run_until_complete(
                    self._get_broadlink_devices("startup_migration")
                )
                logger.info(f"Found {len(devices)} Broadlink device(s)")

                # Check and perform migration if needed
                result = loop.run_until_complete(
                    self.migration_manager.check_and_migrate(devices)
                )

                loop.close()

                # Log results based on scenario
                scenario = result.get("scenario", "unknown")

                if scenario == "existing_broadlink_user" and result.get("success"):
                    logger.info("=" * 60)
                    logger.info("✅ AUTOMATIC MIGRATION COMPLETED")
                    logger.info("=" * 60)
                    logger.info(
                        f"📊 Migrated: {result.get('migrated_entities', 0)} entities"
                    )
                    logger.info(f"📁 From: {len(result.get('entities', []))} devices")
                    if result.get("skipped_devices"):
                        logger.info(
                            f"⚠️  Skipped: {len(result.get('skipped_devices', []))} devices (no valid entities)"
                        )
                    logger.info("🎯 Next steps:")
                    logger.info("   1. Review entities in the web interface")
                    logger.info("   2. Adjust areas if needed")
                    logger.info("   3. Generate YAML entities")
                    logger.info("   4. Restart Home Assistant")
                    logger.info("=" * 60)

                elif scenario == "existing_bl_manager_user":
                    logger.info("=" * 60)
                    logger.info("📋 EXISTING INSTALLATION DETECTED")
                    logger.info("=" * 60)
                    logger.info(
                        f"Found {result.get('existing_entities', 0)} existing entities"
                    )
                    logger.info("No migration needed - your configuration is preserved")
                    logger.info("=" * 60)

                elif scenario == "first_time_user":
                    logger.info("=" * 60)
                    logger.info("👋 WELCOME TO BROADLINK MANAGER!")
                    logger.info("=" * 60)
                    logger.info("No learned commands found yet")
                    logger.info("🎯 Get started:")
                    logger.info("   1. Open the web interface")
                    logger.info("   2. Select a Broadlink device")
                    logger.info("   3. Learn IR/RF commands")
                    logger.info("   4. Auto-generate entities")
                    logger.info("=" * 60)

                elif result.get("error"):
                    logger.error("=" * 60)
                    logger.error("❌ MIGRATION CHECK ERROR")
                    logger.error("=" * 60)
                    logger.error(f"Error: {result.get('error')}")
                    logger.error(
                        "The add-on will continue to run, but automatic migration failed"
                    )
                    logger.error("=" * 60)

            except Exception as e:
                logger.error("=" * 60)
                logger.error("❌ MIGRATION CHECK FAILED")
                logger.error("=" * 60)
                logger.error(
                    f"Error during automatic migration check: {e}", exc_info=True
                )
                logger.error("The add-on will continue to run")
                logger.error("=" * 60)

        # Run in background thread to not block startup
        import threading

        migration_thread = threading.Thread(target=run_migration_check, daemon=True)
        migration_thread.start()

    def get_cached_connection_info(self, entity_id: str):
        """Get cached device connection info if available and not expired"""
        import time
        
        if entity_id not in self.device_connection_cache:
            return None
        
        cached = self.device_connection_cache[entity_id]
        cached_at = cached.get("cached_at", 0)
        
        # Check if cache is expired
        if time.time() - cached_at > self.CONNECTION_CACHE_TTL:
            logger.debug(f"Cache expired for {entity_id}")
            del self.device_connection_cache[entity_id]
            return None
        
        logger.debug(f"Using cached connection info for {entity_id}")
        return cached
    
    def cache_connection_info(self, entity_id: str, connection_info: dict):
        """Cache device connection info"""
        import time
        
        if connection_info:
            connection_info["cached_at"] = time.time()
            self.device_connection_cache[entity_id] = connection_info
            logger.debug(f"Cached connection info for {entity_id}")
    
    def invalidate_connection_cache(self, entity_id: str = None):
        """Invalidate connection cache for specific device or all devices"""
        if entity_id:
            if entity_id in self.device_connection_cache:
                del self.device_connection_cache[entity_id]
                logger.debug(f"Invalidated cache for {entity_id}")
        else:
            self.device_connection_cache.clear()
            logger.debug("Cleared all connection cache")

    def run(self):
        """Run the Flask web server"""
        logger.info(f"Starting Broadlink Manager web server on port {self.port}")
        self.app.run(host="0.0.0.0", port=self.port, debug=False)


if __name__ == "__main__":
    server = BroadlinkWebServer()
    server.run()
