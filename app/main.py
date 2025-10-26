#!/usr/bin/env python3
"""
Broadlink Manager Add-on for Home Assistant
Main application entry point
"""

import os
import sys
import json
import logging
import signal
import threading
import time
from typing import Dict, Any
from pathlib import Path

# Suppress Flask development server warning
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

# Load .env file if it exists (for development)
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from web_server import BroadlinkWebServer  # noqa: E402
from config_loader import ConfigLoader  # noqa: E402

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


class BroadlinkManager:
    """Main Broadlink Manager application class"""

    def __init__(self):
        self.running = True

        # Initialize configuration loader
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_options()

        # Validate configuration
        if not self.config_loader.validate_configuration():
            logger.error("Configuration validation failed")
            logger.error("Please check your configuration and try again")
            sys.exit(1)

        self.web_server = None
        self.web_thread = None

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        if self.web_server:
            # Note: Flask doesn't have a clean shutdown method in this context
            # The process will terminate when the main thread exits
            pass

    def _start_web_server(self):
        """Start the web server in a separate thread"""
        try:
            port = self.config.get("web_port", 8099)
            self.web_server = BroadlinkWebServer(
                port=port, config_loader=self.config_loader
            )
            logger.info(f"Starting web server on port {port}")
            self.web_server.run()
        except Exception as e:
            logger.error(f"Web server error: {e}")

    def start(self):
        """Start the Broadlink Manager application"""
        logger.info("Starting Broadlink Manager...")

        try:
            # Start the web server in a separate thread
            self.web_thread = threading.Thread(
                target=self._start_web_server, daemon=True
            )
            self.web_thread.start()

            logger.info("Broadlink Manager web interface started")
            logger.info(
                f"Access the web interface at http://localhost:{self.config.get('web_port', 8099)}"
            )

            # Main application loop - keep the main thread alive
            while self.running:
                # Check if web thread is still alive
                if self.web_thread and not self.web_thread.is_alive():
                    logger.error("Web server thread died, restarting...")
                    self.web_thread = threading.Thread(
                        target=self._start_web_server, daemon=True
                    )
                    self.web_thread.start()

                # Sleep for a bit to avoid busy waiting
                time.sleep(5)

        except Exception as e:
            logger.error(f"Application error: {e}")
            sys.exit(1)

        logger.info("Broadlink Manager stopped")

    def stop(self):
        """Stop the application"""
        self.running = False


def main():
    """Main entry point"""
    logger.info("Initializing Broadlink Manager")

    # Detect environment and log info
    config_loader = ConfigLoader()
    env_info = config_loader.get_environment_info()
    logger.info(f"Running in {env_info['mode']} mode")
    logger.info(f"Home Assistant URL: {env_info['ha_url']}")
    logger.info(f"Config path: {env_info['config_path']}")

    try:
        manager = BroadlinkManager()
        manager.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
