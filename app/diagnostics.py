"""
Diagnostics module for Broadlink Manager
Generates diagnostic reports for troubleshooting
"""

import json
import logging
import platform
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import re
from importlib.metadata import version, PackageNotFoundError
import yaml

logger = logging.getLogger(__name__)


class DiagnosticsCollector:
    """Collect diagnostic information for troubleshooting"""

    def __init__(
        self,
        storage_path: str,
        device_manager=None,
        storage_manager=None,
        area_manager=None,
        web_server=None,
    ):
        """
        Initialize diagnostics collector

        Args:
            storage_path: Path to storage directory
            device_manager: Optional DeviceManager instance
            storage_manager: Optional StorageManager instance
            area_manager: Optional AreaManager instance
            web_server: Optional WebServer instance
        """
        self.storage_path = Path(storage_path)
        self.device_manager = device_manager
        self.storage_manager = storage_manager
        self.area_manager = area_manager
        self.web_server = web_server
        self.app_version = self._get_app_version()

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all diagnostic information

        Returns:
            Dictionary containing all diagnostic data
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self._collect_system_info(),
            "dependencies": self._collect_dependencies(),
            "configuration": self._collect_configuration(),
            "environment": self._collect_environment(),
            "devices": self._collect_device_info(),
            "integrations": self._collect_integration_status(),
            "ha_connection": self._collect_ha_connection(),
            "broadlink_devices": self._collect_broadlink_devices(),
            "storage": self._collect_storage_info(),
            "backups": self._collect_backup_status(),
            "permissions": self._collect_permissions(),
            "command_structure": self._collect_command_structure(),
            "smartir_profiles": self._collect_smartir_profiles(),
            "errors": self._collect_recent_errors(),
        }

    def _get_app_version(self) -> str:
        """Get app version from config.yaml"""
        try:
            config_file = Path("config.yaml")
            if config_file.exists():
                with open(config_file, "r") as f:
                    config = yaml.safe_load(f)
                    return config.get("version", "unknown")
        except Exception as e:
            logger.debug(f"Could not read app version from config.yaml: {e}")
        return "unknown"

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        try:
            return {
                "app_version": self.app_version,
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "python_version": sys.version.split()[0],
                "python_full_version": sys.version,
                "python_executable": sys.executable,
                "architecture": platform.machine(),
                "hostname": platform.node(),
            }
        except Exception as e:
            logger.error(f"Error collecting system info: {e}")
            return {"error": str(e)}

    def _collect_dependencies(self) -> Dict[str, Any]:
        """Collect Python package versions"""
        try:
            # Key dependencies to track
            key_deps = [
                "broadlink",
                "flask",
                "flask-cors",
                "aiohttp",
                "aiofiles",
                "requests",
                "pyyaml",
                "websockets",
                "zeroconf",
                "colorlog",
                "python-dateutil",
                "python-dotenv",
            ]

            dependencies = {}
            for dep in key_deps:
                try:
                    dependencies[dep] = version(dep)
                except PackageNotFoundError:
                    dependencies[dep] = "not installed"

            return dependencies
        except Exception as e:
            logger.error(f"Error collecting dependencies: {e}")
            return {"error": str(e)}

    def _collect_configuration(self) -> Dict[str, Any]:
        """Collect configuration (sanitized)"""
        try:
            config = {
                "storage_path": str(self.storage_path),
                "storage_path_exists": self.storage_path.exists(),
                "log_level": os.environ.get("LOG_LEVEL", "info"),
                "web_port": os.environ.get("WEB_PORT", "8099"),
                "auto_discover": os.environ.get("AUTO_DISCOVER", "true"),
                "ha_url_configured": bool(os.environ.get("HA_URL")),
                "ha_token_configured": bool(os.environ.get("HA_TOKEN")),
            }

            # Check if config.yaml exists
            config_file = Path("config.yaml")
            if config_file.exists():
                config["config_file_exists"] = True
                config["config_file_size"] = config_file.stat().st_size
                config["config_file_modified"] = datetime.fromtimestamp(
                    config_file.stat().st_mtime
                ).isoformat()
            else:
                config["config_file_exists"] = False

            return config
        except Exception as e:
            logger.error(f"Error collecting configuration: {e}")
            return {"error": str(e)}

    def _collect_environment(self) -> Dict[str, Any]:
        """Collect environment variables (sanitized)"""
        try:
            # Safe environment variables to include (no secrets)
            safe_vars = [
                "LOG_LEVEL",
                "WEB_PORT",
                "AUTO_DISCOVER",
                "STORAGE_PATH",
                "PYTHONPATH",
                "PATH",
                "HOME",
                "USER",
            ]

            env = {}
            for var in safe_vars:
                value = os.environ.get(var)
                if value:
                    # Truncate very long values (like PATH)
                    if len(value) > 200:
                        env[var] = value[:200] + "..."
                    else:
                        env[var] = value

            return env
        except Exception as e:
            logger.error(f"Error collecting environment: {e}")
            return {"error": str(e)}

    def _collect_device_info(self) -> Dict[str, Any]:
        """Collect device information (sanitized)"""
        try:
            info = {
                "total_devices": 0,
                "devices_by_type": {},
                "devices_by_entity_type": {},
                "broadlink_entities": 0,
                "smartir_devices": 0,
            }

            # Get devices from device_manager
            if self.device_manager:
                devices = self.device_manager.get_all_devices()
                info["total_devices"] = len(devices)

                for device_id, device_data in devices.items():
                    # Count by device type
                    device_type = device_data.get("device_type", "broadlink")
                    info["devices_by_type"][device_type] = (
                        info["devices_by_type"].get(device_type, 0) + 1
                    )

                    # Count by entity type
                    entity_type = device_data.get("entity_type", "unknown")
                    info["devices_by_entity_type"][entity_type] = (
                        info["devices_by_entity_type"].get(entity_type, 0) + 1
                    )

                    # Count SmartIR devices
                    if device_type == "smartir":
                        info["smartir_devices"] += 1

            # Get entities from storage_manager
            if self.storage_manager:
                entities = self.storage_manager.get_all_entities()
                info["broadlink_entities"] = len(entities)

            return info
        except Exception as e:
            logger.error(f"Error collecting device info: {e}")
            return {"error": str(e)}

    def _collect_integration_status(self) -> Dict[str, Any]:
        """Collect integration status"""
        try:
            status = {
                "smartir": {
                    "enabled": os.environ.get("SMARTIR_ENABLED", "true").lower()
                    == "true",
                    "installed": False,
                    "version": None,
                },
                "broadlink_integration": {"detected": False},
            }

            # Check if SmartIR custom_components exists
            smartir_path = Path("/config/custom_components/smartir")
            if smartir_path.exists():
                status["smartir"]["installed"] = True
                manifest_file = smartir_path / "manifest.json"
                if manifest_file.exists():
                    try:
                        with open(manifest_file) as f:
                            manifest = json.load(f)
                            status["smartir"]["version"] = manifest.get("version")
                    except Exception:
                        pass

            return status
        except Exception as e:
            logger.error(f"Error collecting integration status: {e}")
            return {"error": str(e)}

    def _collect_ha_connection(self) -> Dict[str, Any]:
        """Collect Home Assistant connection details"""
        try:
            import asyncio

            connection = {
                "configured": bool(
                    os.environ.get("HA_URL") and os.environ.get("HA_TOKEN")
                ),
                "ha_url": os.environ.get("HA_URL", "not configured"),
                "connection_test": "not tested",
                "ha_version": None,
                "websocket_connected": False,
            }

            # Test connection if area_manager is available
            if self.area_manager and connection["configured"]:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    # Try to get HA config (includes version)
                    config = loop.run_until_complete(
                        self.area_manager._send_ws_command("get_config")
                    )
                    if config:
                        connection["connection_test"] = "success"
                        connection["ha_version"] = config.get("version")
                        connection["websocket_connected"] = True
                    else:
                        connection["connection_test"] = "failed"

                    loop.close()
                except Exception as e:
                    connection["connection_test"] = f"failed: {str(e)}"
                    logger.debug(f"HA connection test failed: {e}")

            return connection
        except Exception as e:
            logger.error(f"Error collecting HA connection info: {e}")
            return {"error": str(e)}

    def _collect_broadlink_devices(self) -> Dict[str, Any]:
        """Collect Broadlink device information"""
        try:
            devices_info = {"discovered_count": 0, "devices": []}

            # Get Broadlink devices from storage if available
            if self.storage_manager:
                entities = self.storage_manager.get_all_entities()
                broadlink_entities = [
                    e for e in entities.values() if e.get("broadlink_entity")
                ]

                devices_info["discovered_count"] = len(
                    set(e.get("broadlink_entity") for e in broadlink_entities)
                )

                # Collect unique Broadlink entities
                seen_entities = set()
                for entity in broadlink_entities:
                    broadlink_entity = entity.get("broadlink_entity")
                    if broadlink_entity and broadlink_entity not in seen_entities:
                        seen_entities.add(broadlink_entity)
                        # Extract device type from entity_id (e.g., remote.bedroom_rm4 -> RM4)
                        device_type = "Unknown"
                        if "rm4" in broadlink_entity.lower():
                            device_type = "RM4 Pro"
                        elif "rm3" in broadlink_entity.lower():
                            device_type = "RM3 Mini"
                        elif "rm" in broadlink_entity.lower():
                            device_type = "RM Device"

                        devices_info["devices"].append(
                            {
                                "entity_id": broadlink_entity,
                                "type": device_type,
                                "commands_count": len(
                                    [
                                        e
                                        for e in broadlink_entities
                                        if e.get("broadlink_entity") == broadlink_entity
                                    ]
                                ),
                            }
                        )

            return devices_info
        except Exception as e:
            logger.error(f"Error collecting Broadlink devices: {e}")
            return {"error": str(e)}

    def _collect_storage_info(self) -> Dict[str, Any]:
        """Collect storage information"""
        try:
            info = {
                "storage_path_exists": self.storage_path.exists(),
                "files": {},
                "command_files": {},
            }

            if self.storage_path.exists():
                # Check key files
                files_to_check = [
                    "devices.json",
                    "devices.json.backup",
                    "metadata.json",
                    "metadata.json.backup",
                    "entities.yaml",
                    "helpers.yaml",
                ]

                for filename in files_to_check:
                    file_path = self.storage_path / filename
                    if file_path.exists():
                        info["files"][filename] = {
                            "exists": True,
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                        }
                    else:
                        info["files"][filename] = {"exists": False}

                # Check commands directory
                commands_dir = self.storage_path / "commands"
                if commands_dir.exists() and commands_dir.is_dir():
                    info["command_files"]["directory_exists"] = True
                    info["command_files"]["total_files"] = 0
                    info["command_files"]["files_by_type"] = {}

                    # Count command files by type
                    for cmd_file in commands_dir.glob("*.json"):
                        info["command_files"]["total_files"] += 1
                        # Extract device ID from filename
                        device_id = cmd_file.stem
                        info["command_files"]["files_by_type"][device_id] = {
                            "size": cmd_file.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                cmd_file.stat().st_mtime
                            ).isoformat(),
                        }
                else:
                    info["command_files"]["directory_exists"] = False

            return info
        except Exception as e:
            logger.error(f"Error collecting storage info: {e}")
            return {"error": str(e)}

    def _collect_backup_status(self) -> Dict[str, Any]:
        """Collect backup file status"""
        try:
            backups = {}

            backup_files = ["devices.json.backup", "metadata.json.backup"]

            for backup_file in backup_files:
                backup_path = self.storage_path / backup_file
                if backup_path.exists():
                    stat = backup_path.stat()
                    modified = datetime.fromtimestamp(stat.st_mtime)
                    age = datetime.now() - modified

                    backups[backup_file] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": modified.isoformat(),
                        "age_hours": round(age.total_seconds() / 3600, 2),
                    }
                else:
                    backups[backup_file] = {"exists": False}

            return backups
        except Exception as e:
            logger.error(f"Error collecting backup status: {e}")
            return {"error": str(e)}

    def _collect_permissions(self) -> Dict[str, Any]:
        """Check file system permissions"""
        try:
            permissions = {}

            # Check storage path
            if self.storage_path.exists():
                permissions["storage_path_readable"] = os.access(
                    self.storage_path, os.R_OK
                )
                permissions["storage_path_writable"] = os.access(
                    self.storage_path, os.W_OK
                )
            else:
                permissions["storage_path_readable"] = False
                permissions["storage_path_writable"] = False

            # Check config path
            config_path = Path("/config")
            if config_path.exists():
                permissions["config_path_readable"] = os.access(config_path, os.R_OK)
                permissions["config_path_writable"] = os.access(config_path, os.W_OK)

            # Check HA storage path
            ha_storage_path = Path("/config/.storage")
            if ha_storage_path.exists():
                permissions["ha_storage_readable"] = os.access(ha_storage_path, os.R_OK)

            return permissions
        except Exception as e:
            logger.error(f"Error collecting permissions: {e}")
            return {"error": str(e)}

    def _collect_command_structure(self) -> Dict[str, Any]:
        """Collect command structure from devices (names only, no actual codes)"""
        try:
            structure = {}

            # Get commands from device_manager (devices.json)
            if self.device_manager:
                devices = self.device_manager.get_all_devices()
                for device_id, device_data in devices.items():
                    commands = device_data.get("commands", {})
                    if commands:
                        structure[device_id] = {
                            "source": "device_manager",
                            "command_count": len(commands),
                            "commands": {},
                        }

                        for cmd_name, cmd_data in commands.items():
                            if isinstance(cmd_data, dict):
                                structure[device_id]["commands"][cmd_name] = {
                                    "type": cmd_data.get("command_type", "unknown"),
                                    "imported": cmd_data.get("imported", False),
                                    "learned_at": cmd_data.get("learned_at")
                                    is not None,
                                }
                            else:
                                # Handle simple string values
                                structure[device_id]["commands"][cmd_name] = {
                                    "type": "unknown",
                                    "value": str(cmd_data),
                                }

            # Get commands from storage_manager (metadata.json)
            if self.storage_manager:
                entities = self.storage_manager.get_all_entities()
                for entity_id, entity_data in entities.items():
                    commands = entity_data.get("commands", {})
                    if commands:
                        structure[entity_id] = {
                            "source": "storage_manager",
                            "command_count": len(commands),
                            "commands": {},
                        }

                        for cmd_name, cmd_data in commands.items():
                            if isinstance(cmd_data, dict):
                                structure[entity_id]["commands"][cmd_name] = {
                                    "type": cmd_data.get("command_type", "unknown"),
                                    "imported": cmd_data.get("imported", False),
                                    "learned_at": cmd_data.get("learned_at")
                                    is not None,
                                }
                            else:
                                # Handle simple string values (command references)
                                structure[entity_id]["commands"][cmd_name] = {
                                    "type": "reference",
                                    "value": str(cmd_data),
                                }

            if not structure:
                return {"note": "No commands found in devices or metadata"}

            return structure
        except Exception as e:
            logger.error(f"Error collecting command structure: {e}")
            return {"error": str(e)}

    def _collect_smartir_profiles(self) -> Dict[str, Any]:
        """Collect SmartIR profile statistics"""
        try:
            profiles = {
                "total_custom_profiles": 0,
                "profiles_by_platform": {},
                "index_file_exists": False,
                "index_last_updated": None,
            }

            # Check for custom profiles directory
            custom_profiles_path = self.storage_path / "smartir_profiles"
            if custom_profiles_path.exists():
                for platform_dir in custom_profiles_path.iterdir():
                    if platform_dir.is_dir():
                        profile_count = len(list(platform_dir.glob("*.json")))
                        if profile_count > 0:
                            profiles["profiles_by_platform"][
                                platform_dir.name
                            ] = profile_count
                            profiles["total_custom_profiles"] += profile_count

            # Check device index
            index_file = Path("smartir_device_index.json")
            if index_file.exists():
                profiles["index_file_exists"] = True
                stat = index_file.stat()
                profiles["index_last_updated"] = datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()
                profiles["index_size"] = stat.st_size

            return profiles
        except Exception as e:
            logger.error(f"Error collecting SmartIR profiles: {e}")
            return {"error": str(e)}

    def _collect_recent_errors(self) -> Dict[str, Any]:
        """Collect recent errors from logs"""
        try:
            log_data = {"errors": [], "warnings": [], "log_file_found": False}

            # Try to find log file in common locations
            log_locations = [
                Path("/config/broadlink_manager.log"),
                Path("/var/log/broadlink_manager.log"),
                Path("broadlink_manager.log"),
            ]

            log_file = None
            for location in log_locations:
                if location.exists():
                    log_file = location
                    log_data["log_file_found"] = True
                    log_data["log_file_path"] = str(location)
                    break

            if log_file:
                try:
                    # Read last 100 lines
                    with open(log_file, "r") as f:
                        lines = f.readlines()[-100:]

                    # Extract errors and warnings
                    for line in lines:
                        if "ERROR" in line:
                            log_data["errors"].append(line.strip())
                        elif "WARNING" in line:
                            log_data["warnings"].append(line.strip())

                    # Limit to last 20 of each
                    log_data["errors"] = log_data["errors"][-20:]
                    log_data["warnings"] = log_data["warnings"][-20:]

                except Exception as read_error:
                    log_data["read_error"] = str(read_error)
            else:
                log_data["note"] = "Log file not found in common locations"

            return log_data
        except Exception as e:
            logger.error(f"Error collecting recent errors: {e}")
            return {"error": str(e)}

    def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize diagnostic data to remove sensitive information

        Args:
            data: Raw diagnostic data

        Returns:
            Sanitized data
        """
        sanitized = data.copy()

        # Remove sensitive patterns
        sensitive_patterns = [
            r'token["\']?\s*[:=]\s*["\']?[\w-]+',
            r'password["\']?\s*[:=]\s*["\']?[\w-]+',
            r'api_key["\']?\s*[:=]\s*["\']?[\w-]+',
            r'secret["\']?\s*[:=]\s*["\']?[\w-]+',
        ]

        # Convert to JSON string, sanitize, convert back
        json_str = json.dumps(sanitized)
        for pattern in sensitive_patterns:
            json_str = re.sub(pattern, "REDACTED", json_str, flags=re.IGNORECASE)

        return json.loads(json_str)

    def generate_markdown_report(self, data: Dict[str, Any]) -> str:
        """
        Generate a markdown-formatted diagnostic report

        Args:
            data: Diagnostic data

        Returns:
            Markdown-formatted report
        """
        lines = [
            "# Broadlink Manager Diagnostics",
            "",
            f"**Generated:** {data['timestamp']}",
            f"**App Version:** {data['system'].get('app_version', 'Unknown')}",
            "",
            "## System Information",
            f"- **Platform:** {data['system'].get('platform', 'Unknown')}",
            f"- **Python Version:** {data['system'].get('python_version', 'Unknown')}",
            f"- **Architecture:** {data['system'].get('architecture', 'Unknown')}",
            "",
            "## Key Dependencies",
        ]

        # Dependencies
        if data.get("dependencies") and not data["dependencies"].get("error"):
            deps = data["dependencies"]
            for dep in ["broadlink", "flask", "aiohttp", "pyyaml"]:
                version = deps.get(dep, "not installed")
                lines.append(f"- **{dep}:** {version}")
            lines.append(f"- **Total Packages:** {deps.get('total_packages', 0)}")
        lines.append("")

        # Configuration
        lines.extend(
            [
                "## Configuration",
                f"- **Storage Path:** `{data['configuration'].get('storage_path', 'Unknown')}`",
                f"- **Storage Exists:** {'✅' if data['configuration'].get('storage_path_exists') else '❌'}",
                f"- **Log Level:** {data['configuration'].get('log_level', 'Unknown')}",
                f"- **Web Port:** {data['configuration'].get('web_port', 'Unknown')}",
                "",
            ]
        )

        # Home Assistant Connection
        lines.append("## Home Assistant Connection")
        if data.get("ha_connection"):
            ha_conn = data["ha_connection"]
            lines.append(
                f"- **Configured:** {'✅' if ha_conn.get('configured') else '❌'}"
            )
            if ha_conn.get("configured"):
                lines.append(
                    f"- **Connection Test:** {ha_conn.get('connection_test', 'not tested')}"
                )
                if ha_conn.get("ha_version"):
                    lines.append(f"- **HA Version:** {ha_conn['ha_version']}")
                lines.append(
                    f"- **WebSocket:** {'✅ Connected' if ha_conn.get('websocket_connected') else '❌ Not connected'}"
                )
        lines.append("")

        # Devices
        lines.extend(
            [
                "## Devices",
                f"- **Total Devices:** {data['devices'].get('total_devices', 0)}",
                f"- **Broadlink Entities:** {data['devices'].get('broadlink_entities', 0)}",
                f"- **SmartIR Devices:** {data['devices'].get('smartir_devices', 0)}",
                "",
            ]
        )

        # Device breakdown
        if data["devices"].get("devices_by_entity_type"):
            lines.append("### Devices by Type")
            for entity_type, count in data["devices"]["devices_by_entity_type"].items():
                lines.append(f"- **{entity_type}:** {count}")
            lines.append("")

        # Broadlink Devices
        if data.get("broadlink_devices") and data["broadlink_devices"].get("devices"):
            lines.append("## Broadlink Devices")
            lines.append(
                f"- **Discovered:** {data['broadlink_devices'].get('discovered_count', 0)}"
            )
            for device in data["broadlink_devices"]["devices"]:
                lines.append(
                    f"- **{device['entity_id']}:** {device['type']} ({device['commands_count']} commands)"
                )
            lines.append("")

        # SmartIR Profiles
        if data.get("smartir_profiles"):
            profiles = data["smartir_profiles"]
            if profiles.get("total_custom_profiles", 0) > 0 or profiles.get(
                "index_file_exists"
            ):
                lines.append("## SmartIR Profiles")
                lines.append(
                    f"- **Custom Profiles:** {profiles.get('total_custom_profiles', 0)}"
                )
                if profiles.get("profiles_by_platform"):
                    for plat, count in profiles["profiles_by_platform"].items():
                        lines.append(f"  - **{plat}:** {count}")
                lines.append(
                    f"- **Device Index:** {'✅ Present' if profiles.get('index_file_exists') else '❌ Missing'}"
                )
                lines.append("")

        # Storage info
        lines.extend(
            [
                "## Storage",
                f"- **Storage Path Exists:** {'✅' if data['storage'].get('storage_path_exists') else '❌'}",
                "",
            ]
        )

        if data["storage"].get("files"):
            lines.append("### Files")
            for filename, file_info in data["storage"]["files"].items():
                if file_info.get("exists"):
                    lines.append(f"- **{filename}:** {file_info.get('size', 0)} bytes")
                else:
                    lines.append(f"- **{filename}:** ❌ Missing")
            lines.append("")

        # Backups
        if data.get("backups"):
            lines.append("### Backups")
            for backup_name, backup_info in data["backups"].items():
                if backup_info.get("exists"):
                    age = backup_info.get("age_hours", 0)
                    lines.append(f"- **{backup_name}:** ✅ ({age:.1f} hours old)")
                else:
                    lines.append(f"- **{backup_name}:** ❌ Missing")
            lines.append("")

        # Permissions
        if data.get("permissions"):
            perms = data["permissions"]
            lines.append("### Permissions")
            lines.append(
                f"- **Storage Readable:** {'✅' if perms.get('storage_path_readable') else '❌'}"
            )
            lines.append(
                f"- **Storage Writable:** {'✅' if perms.get('storage_path_writable') else '❌'}"
            )
            if "config_path_writable" in perms:
                lines.append(
                    f"- **Config Writable:** {'✅' if perms.get('config_path_writable') else '❌'}"
                )
            lines.append("")

        # Command structure
        if data.get("command_structure") and not data["command_structure"].get("note"):
            lines.append("## Command Files")
            total_commands = 0
            for device_id, cmd_info in data["command_structure"].items():
                if "error" not in cmd_info:
                    count = cmd_info.get("command_count", 0)
                    total_commands += count
                    lines.append(f"- **{device_id}:** {count} commands")
            lines.append(f"\n**Total Commands:** {total_commands}")
            lines.append("")

        # Errors and Warnings
        if data.get("errors"):
            errors = data["errors"]
            if errors.get("errors") or errors.get("warnings"):
                lines.append("## Recent Log Entries")
                if errors.get("errors"):
                    lines.append(f"- **Errors:** {len(errors['errors'])}")
                if errors.get("warnings"):
                    lines.append(f"- **Warnings:** {len(errors['warnings'])}")
                lines.append("")

        return "\n".join(lines)
