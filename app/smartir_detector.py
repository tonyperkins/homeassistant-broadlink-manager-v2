#!/usr/bin/env python3
"""
SmartIR Detector for Broadlink Manager Add-on
Detects SmartIR installation and provides integration helpers
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class SmartIRDetector:
    """Detect and interact with SmartIR installation"""

    def __init__(self, config_path: str = "/config"):
        self.config_path = Path(config_path)
        self.smartir_path = self.config_path / "custom_components" / "smartir"
        self.codes_path = self.smartir_path / "codes"

    def is_installed(self) -> bool:
        """Check if SmartIR is installed"""
        return self.smartir_path.exists() and (self.smartir_path / "manifest.json").exists()

    def get_version(self) -> Optional[str]:
        """Get SmartIR version if installed"""
        manifest_file = self.smartir_path / "manifest.json"
        if not manifest_file.exists():
            return None

        try:
            with open(manifest_file, "r") as f:
                manifest = json.load(f)
                return manifest.get("version")
        except Exception as e:
            logger.warning(f"Could not read SmartIR manifest: {e}")
            return None

    def get_supported_platforms(self) -> List[str]:
        """Get list of SmartIR platforms that have code directories"""
        if not self.codes_path.exists():
            return []

        platforms = []
        for platform_dir in self.codes_path.iterdir():
            if platform_dir.is_dir():
                platforms.append(platform_dir.name)

        return sorted(platforms)

    def get_device_codes(self, platform: str) -> List[Dict[str, Any]]:
        """Get list of available device codes for a platform"""
        platform_path = self.codes_path / platform
        if not platform_path.exists():
            return []

        codes = []
        for code_file in platform_path.glob("*.json"):
            try:
                code_number = int(code_file.stem)
                with open(code_file, "r") as f:
                    data = json.load(f)
                    codes.append(
                        {
                            "code": code_number,
                            "manufacturer": data.get("manufacturer", "Unknown"),
                            "models": data.get("supportedModels", []),
                            "file": str(code_file),
                        }
                    )
            except (ValueError, json.JSONDecodeError) as e:
                logger.debug(f"Skipping invalid code file {code_file}: {e}")
                continue

        return sorted(codes, key=lambda x: x["code"])

    def find_next_custom_code(self, platform: str) -> int:
        """Find next available custom device code (10000+)"""
        platform_path = self.codes_path / platform
        if not platform_path.exists():
            return 10000

        custom_codes = []
        for code_file in platform_path.glob("*.json"):
            try:
                code_number = int(code_file.stem)
                if code_number >= 10000:
                    custom_codes.append(code_number)
            except ValueError:
                continue

        if not custom_codes:
            return 10000

        return max(custom_codes) + 1

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive SmartIR status"""
        installed = self.is_installed()

        status = {
            "installed": installed,
            "version": None,
            "path": str(self.smartir_path),
            "platforms": [],
            "device_counts": {},
            "recommendation": None,
        }

        if not installed:
            status["recommendation"] = {
                "message": "SmartIR not detected. Install it to unlock climate device support!",
                "action": "install_smartir",
                "url": "https://github.com/smartHomeHub/SmartIR",
                "benefits": [
                    "Full climate entity support (AC, heaters)",
                    "120+ pre-configured device profiles",
                    "Temperature and humidity sensor integration",
                    "HVAC mode control (heat, cool, auto, dry, fan)",
                ],
            }
            return status

        # SmartIR is installed
        status["version"] = self.get_version()
        status["platforms"] = self.get_supported_platforms()

        # Count devices per platform
        for platform in status["platforms"]:
            codes = self.get_device_codes(platform)
            status["device_counts"][platform] = len(codes)

        status["recommendation"] = {
            "message": "SmartIR detected! You can now create climate device profiles.",
            "action": "create_profile",
            "next_steps": [
                "Use 'Create SmartIR Profile' to build device profiles",
                "Learn IR codes for your climate devices",
                "Generate SmartIR-compatible JSON files",
                "Get ready-to-use YAML configuration",
            ],
        }

        return status

    def validate_code_file(self, platform: str, code_number: int) -> Dict[str, Any]:
        """Validate a SmartIR code file exists and is valid"""
        code_file = self.codes_path / platform / f"{code_number}.json"

        result = {"valid": False, "exists": False, "error": None, "data": None}

        if not code_file.exists():
            result["error"] = f"Code file not found: {code_number}"
            return result

        result["exists"] = True

        try:
            with open(code_file, "r") as f:
                data = json.load(f)

            # Basic validation
            required_fields = ["manufacturer", "supportedController", "commandsEncoding", "commands"]
            missing = [field for field in required_fields if field not in data]

            if missing:
                result["error"] = f"Missing required fields: {', '.join(missing)}"
                return result

            result["valid"] = True
            result["data"] = {
                "manufacturer": data.get("manufacturer"),
                "models": data.get("supportedModels", []),
                "controller": data.get("supportedController"),
                "encoding": data.get("commandsEncoding"),
            }

        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON: {e}"
        except Exception as e:
            result["error"] = f"Validation error: {e}"

        return result

    def write_code_file(self, platform: str, code_number: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write a SmartIR code file"""
        platform_path = self.codes_path / platform

        result = {"success": False, "file": None, "error": None}

        # Ensure platform directory exists
        try:
            platform_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            result["error"] = f"Could not create platform directory: {e}"
            return result

        code_file = platform_path / f"{code_number}.json"

        # Check if file already exists
        if code_file.exists():
            result["error"] = f"Code file already exists: {code_number}"
            return result

        # Write file
        try:
            with open(code_file, "w") as f:
                json.dump(data, f, indent=2)

            result["success"] = True
            result["file"] = str(code_file)
            logger.info(f"Created SmartIR code file: {code_file}")

        except Exception as e:
            result["error"] = f"Could not write code file: {e}"
            logger.error(f"Failed to write SmartIR code file: {e}")

        return result

    def get_install_instructions(self) -> Dict[str, Any]:
        """Get installation instructions for SmartIR"""
        return {
            "title": "Install SmartIR",
            "description": "SmartIR enables full climate device support with temperature control, HVAC modes, and more.",
            "methods": [
                {
                    "name": "HACS (Recommended)",
                    "steps": [
                        "Open HACS in Home Assistant",
                        "Go to Integrations",
                        "Click the 3 dots menu → Custom repositories",
                        "Add: https://github.com/smartHomeHub/SmartIR",
                        "Category: Integration",
                        "Click 'Install'",
                        "Restart Home Assistant",
                    ],
                },
                {
                    "name": "Manual Installation",
                    "steps": [
                        "Download from: https://github.com/smartHomeHub/SmartIR",
                        "Extract the 'smartir' folder",
                        "Copy to /config/custom_components/smartir",
                        "Restart Home Assistant",
                    ],
                },
            ],
            "verification": "After installation, refresh this page to enable SmartIR features.",
            "links": {
                "github": "https://github.com/smartHomeHub/SmartIR",
                "documentation": "https://github.com/smartHomeHub/SmartIR#readme",
                "community": (
                    "https://community.home-assistant.io/t/"
                    "smartir-control-your-climate-tv-and-fan-devices-via-ir-rf-controllers/100798"
                ),
            },
        }
