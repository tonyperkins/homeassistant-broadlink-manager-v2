"""
Diagnostics module for Broadlink Manager
Generates diagnostic reports for troubleshooting
"""

import json
import logging
import platform
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import re

logger = logging.getLogger(__name__)


class DiagnosticsCollector:
    """Collect diagnostic information for troubleshooting"""

    def __init__(self, storage_path: str, device_manager=None, storage_manager=None):
        """
        Initialize diagnostics collector

        Args:
            storage_path: Path to storage directory
            device_manager: Optional DeviceManager instance
            storage_manager: Optional StorageManager instance
        """
        self.storage_path = Path(storage_path)
        self.device_manager = device_manager
        self.storage_manager = storage_manager

    def collect_all(self) -> Dict[str, Any]:
        """
        Collect all diagnostic information

        Returns:
            Dictionary containing all diagnostic data
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self._collect_system_info(),
            "configuration": self._collect_configuration(),
            "devices": self._collect_device_info(),
            "integrations": self._collect_integration_status(),
            "storage": self._collect_storage_info(),
            "command_structure": self._collect_command_structure(),
            "errors": self._collect_recent_errors(),
        }

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information"""
        try:
            return {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "platform_release": platform.release(),
                "python_version": sys.version,
                "python_executable": sys.executable,
                "architecture": platform.machine(),
            }
        except Exception as e:
            logger.error(f"Error collecting system info: {e}")
            return {"error": str(e)}

    def _collect_configuration(self) -> Dict[str, Any]:
        """Collect configuration (sanitized)"""
        try:
            import os

            config = {
                "storage_path": str(self.storage_path),
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
            else:
                config["config_file_exists"] = False

            return config
        except Exception as e:
            logger.error(f"Error collecting configuration: {e}")
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
                    info["devices_by_type"][device_type] = info["devices_by_type"].get(device_type, 0) + 1

                    # Count by entity type
                    entity_type = device_data.get("entity_type", "unknown")
                    info["devices_by_entity_type"][entity_type] = info["devices_by_entity_type"].get(entity_type, 0) + 1

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
            status = {"smartir": {"installed": False, "version": None}, "broadlink_devices": {"detected": False, "count": 0}}

            # Check for SmartIR (would need to be passed in or detected)
            # This is a placeholder - actual implementation depends on how you detect SmartIR

            return status
        except Exception as e:
            logger.error(f"Error collecting integration status: {e}")
            return {"error": str(e)}

    def _collect_storage_info(self) -> Dict[str, Any]:
        """Collect storage information"""
        try:
            info = {"storage_path_exists": self.storage_path.exists(), "files": {}, "command_files": {}}

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
                            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
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
                            "modified": datetime.fromtimestamp(cmd_file.stat().st_mtime).isoformat(),
                        }
                else:
                    info["command_files"]["directory_exists"] = False

            return info
        except Exception as e:
            logger.error(f"Error collecting storage info: {e}")
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
                        structure[device_id] = {"source": "device_manager", "command_count": len(commands), "commands": {}}

                        for cmd_name, cmd_data in commands.items():
                            if isinstance(cmd_data, dict):
                                structure[device_id]["commands"][cmd_name] = {
                                    "type": cmd_data.get("command_type", "unknown"),
                                    "imported": cmd_data.get("imported", False),
                                    "learned_at": cmd_data.get("learned_at") is not None,
                                }
                            else:
                                # Handle simple string values
                                structure[device_id]["commands"][cmd_name] = {"type": "unknown", "value": str(cmd_data)}

            # Get commands from storage_manager (metadata.json)
            if self.storage_manager:
                entities = self.storage_manager.get_all_entities()
                for entity_id, entity_data in entities.items():
                    commands = entity_data.get("commands", {})
                    if commands:
                        structure[entity_id] = {"source": "storage_manager", "command_count": len(commands), "commands": {}}

                        for cmd_name, cmd_data in commands.items():
                            if isinstance(cmd_data, dict):
                                structure[entity_id]["commands"][cmd_name] = {
                                    "type": cmd_data.get("command_type", "unknown"),
                                    "imported": cmd_data.get("imported", False),
                                    "learned_at": cmd_data.get("learned_at") is not None,
                                }
                            else:
                                # Handle simple string values (command references)
                                structure[entity_id]["commands"][cmd_name] = {"type": "reference", "value": str(cmd_data)}

            if not structure:
                return {"note": "No commands found in devices or metadata"}

            return structure
        except Exception as e:
            logger.error(f"Error collecting command structure: {e}")
            return {"error": str(e)}

    def _collect_recent_errors(self) -> Dict[str, Any]:
        """Collect recent errors from logs"""
        try:
            # This is a simplified version - you'd want to read from actual log file
            # or maintain an in-memory error buffer
            return {"note": "Log collection not yet implemented", "errors": [], "warnings": []}
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
            "",
            "## System Information",
            f"- **Platform:** {data['system'].get('platform', 'Unknown')}",
            f"- **Python Version:** {data['system'].get('python_version', 'Unknown').split()[0]}",
            "",
            "## Configuration",
            f"- **Storage Path:** `{data['configuration'].get('storage_path', 'Unknown')}`",
            f"- **Log Level:** {data['configuration'].get('log_level', 'Unknown')}",
            f"- **HA URL Configured:** {'✅' if data['configuration'].get('ha_url_configured') else '❌'}",
            f"- **HA Token Configured:** {'✅' if data['configuration'].get('ha_token_configured') else '❌'}",
            "",
            "## Devices",
            f"- **Total Devices:** {data['devices'].get('total_devices', 0)}",
            f"- **Broadlink Entities:** {data['devices'].get('broadlink_entities', 0)}",
            f"- **SmartIR Devices:** {data['devices'].get('smartir_devices', 0)}",
            "",
        ]

        # Device breakdown
        if data["devices"].get("devices_by_entity_type"):
            lines.append("### Devices by Type")
            for entity_type, count in data["devices"]["devices_by_entity_type"].items():
                lines.append(f"- **{entity_type}:** {count}")
            lines.append("")

        # Storage info
        lines.extend(
            ["## Storage", f"- **Storage Path Exists:** {'✅' if data['storage'].get('storage_path_exists') else '❌'}", ""]
        )

        if data["storage"].get("files"):
            lines.append("### Files")
            for filename, file_info in data["storage"]["files"].items():
                if file_info.get("exists"):
                    lines.append(f"- **{filename}:** {file_info.get('size', 0)} bytes")
                else:
                    lines.append(f"- **{filename}:** ❌ Missing")
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

        return "\n".join(lines)
