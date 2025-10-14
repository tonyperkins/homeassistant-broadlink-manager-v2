#!/usr/bin/env python3
"""
Configuration Loader for Broadlink Manager
Supports both Home Assistant Supervisor add-on and standalone Docker modes
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Load configuration from either Supervisor add-on or standalone environment.

    Automatically detects the environment and loads configuration accordingly:
    - Supervisor mode: Uses SUPERVISOR_TOKEN, /data/options.json, http://supervisor/core
    - Standalone mode: Uses environment variables (HA_TOKEN, HA_URL, etc.)
    """

    def __init__(self):
        self.is_supervisor = self._detect_supervisor_environment()
        self.mode = "supervisor" if self.is_supervisor else "standalone"
        logger.info(f"Running in {self.mode} mode")

    def _detect_supervisor_environment(self) -> bool:
        """
        Detect if running in Home Assistant Supervisor environment.

        Returns:
            True if running as a Supervisor add-on, False if standalone
        """
        return os.environ.get("SUPERVISOR_TOKEN") is not None

    def get_ha_url(self) -> str:
        """
        Get Home Assistant API URL.

        Returns:
            - Supervisor mode: http://supervisor/core
            - Standalone mode: Value from HA_URL env var or http://localhost:8123
        """
        if self.is_supervisor:
            return "http://supervisor/core"

        url = os.environ.get("HA_URL", "http://localhost:8123")
        # Remove trailing slash if present
        return url.rstrip("/")

    def get_ha_token(self) -> Optional[str]:
        """
        Get Home Assistant authentication token.

        Returns:
            - Supervisor mode: SUPERVISOR_TOKEN
            - Standalone mode: HA_TOKEN (long-lived access token)
        """
        if self.is_supervisor:
            token = os.environ.get("SUPERVISOR_TOKEN")
        else:
            token = os.environ.get("HA_TOKEN")

        if not token:
            logger.warning(f"No authentication token found for {self.mode} mode")

        return token

    def get_config_path(self) -> Path:
        """
        Get Home Assistant config directory path.

        Returns:
            Path to /config directory (same for both modes, just mounted differently)
        """
        # Check HA_CONFIG_PATH first (for standalone mode), then CONFIG_PATH (for Docker/add-on)
        config_path = os.environ.get("HA_CONFIG_PATH") or os.environ.get("CONFIG_PATH", "/config")
        return Path(config_path)

    def get_storage_path(self) -> Path:
        """
        Get Home Assistant storage directory path.

        Returns:
            Path to .storage directory inside config
        """
        return self.get_config_path() / ".storage"

    def get_broadlink_manager_path(self) -> Path:
        """
        Get Broadlink Manager data directory path.

        Returns:
            Path to broadlink_manager directory inside config
        """
        return self.get_config_path() / "broadlink_manager"

    def load_options(self) -> Dict[str, Any]:
        """
        Load application configuration options.

        Returns:
            Dictionary with configuration options
        """
        # Default configuration
        config = {"log_level": "info", "web_port": 8099, "auto_discover": True}

        if self.is_supervisor:
            # Try to load from Supervisor options.json
            config.update(self._load_supervisor_options())
        else:
            # Load from environment variables
            config.update(self._load_env_options())

        logger.info(f"Loaded configuration: {self._sanitize_config_for_log(config)}")
        return config

    def _load_supervisor_options(self) -> Dict[str, Any]:
        """
        Load configuration from Supervisor's options.json file.

        Returns:
            Dictionary with options from Supervisor
        """
        options_file = Path("/data/options.json")

        if not options_file.exists():
            logger.warning("Supervisor options.json not found, using defaults")
            return {}

        try:
            with open(options_file, "r") as f:
                options = json.load(f)
                logger.info("Loaded configuration from Supervisor options.json")
                return options
        except Exception as e:
            logger.error(f"Error loading Supervisor options.json: {e}")
            return {}

    def _load_env_options(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables (standalone mode).

        Environment variables:
            - LOG_LEVEL: Logging level (trace|debug|info|warning|error|fatal)
            - WEB_PORT: Web interface port (default: 8099)
            - AUTO_DISCOVER: Enable auto-discovery (true|false)

        Returns:
            Dictionary with options from environment
        """
        options = {}

        # Log level
        if "LOG_LEVEL" in os.environ:
            options["log_level"] = os.environ["LOG_LEVEL"].lower()

        # Web port
        if "WEB_PORT" in os.environ:
            try:
                options["web_port"] = int(os.environ["WEB_PORT"])
            except ValueError:
                logger.warning(f"Invalid WEB_PORT value: {os.environ['WEB_PORT']}")

        # Auto discover
        if "AUTO_DISCOVER" in os.environ:
            auto_discover = os.environ["AUTO_DISCOVER"].lower()
            options["auto_discover"] = auto_discover in ("true", "1", "yes", "on")

        logger.info("Loaded configuration from environment variables")
        return options

    def _sanitize_config_for_log(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove sensitive information from config before logging.

        Args:
            config: Configuration dictionary

        Returns:
            Sanitized configuration safe for logging
        """
        sanitized = config.copy()
        # No sensitive data in current config, but good practice for future
        return sanitized

    def validate_configuration(self) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            True if configuration is valid, False otherwise
        """
        valid = True

        # Check for HA token
        if not self.get_ha_token():
            logger.error(f"Missing authentication token in {self.mode} mode")
            if self.is_supervisor:
                logger.error("SUPERVISOR_TOKEN not found")
            else:
                logger.error("HA_TOKEN environment variable not set")
                logger.error(
                    "Please create a long-lived access token in Home Assistant"
                )
            valid = False

        # Check config path exists (in standalone mode, user must mount it)
        config_path = self.get_config_path()
        if not config_path.exists():
            logger.error(f"Config path does not exist: {config_path}")
            if not self.is_supervisor:
                logger.error("Please mount Home Assistant config directory to /config")
            valid = False

        return valid

    def get_environment_info(self) -> Dict[str, Any]:
        """
        Get information about the current environment.

        Returns:
            Dictionary with environment information
        """
        return {
            "mode": self.mode,
            "is_supervisor": self.is_supervisor,
            "ha_url": self.get_ha_url(),
            "config_path": str(self.get_config_path()),
            "storage_path": str(self.get_storage_path()),
            "has_token": self.get_ha_token() is not None,
        }
