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
from typing import Dict, Any
from pathlib import Path

from web_server import BroadlinkWebServer

# Configure logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'info').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class BroadlinkManager:
    """Main Broadlink Manager application class"""
    
    def __init__(self):
        self.running = True
        self.config = self._load_config()
        self.web_server = None
        self.web_thread = None
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from add-on options"""
        config = {
            'log_level': os.getenv('LOG_LEVEL', 'info'),
            'web_port': 8099,
            'auto_discover': True
        }
        
        # Try to load from options.json (Supervisor add-on configuration)
        options_file = Path('/data/options.json')
        if options_file.exists():
            try:
                with open(options_file, 'r') as f:
                    options = json.load(f)
                    config.update(options)
                    logger.info("Loaded configuration from options.json")
            except Exception as e:
                logger.warning(f"Could not load options.json: {e}")
        
        logger.info(f"Configuration: {config}")
        return config
    
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
            port = self.config.get('web_port', 8099)
            self.web_server = BroadlinkWebServer(port=port)
            logger.info(f"Starting web server on port {port}")
            self.web_server.run()
        except Exception as e:
            logger.error(f"Web server error: {e}")
    
    def start(self):
        """Start the Broadlink Manager application"""
        logger.info("Starting Broadlink Manager...")
        
        try:
            # Start the web server in a separate thread
            self.web_thread = threading.Thread(target=self._start_web_server, daemon=True)
            self.web_thread.start()
            
            logger.info("Broadlink Manager web interface started")
            logger.info(f"Access the web interface at http://localhost:{self.config.get('web_port', 8099)}")
            
            # Main application loop - keep the main thread alive
            while self.running:
                # Check if web thread is still alive
                if self.web_thread and not self.web_thread.is_alive():
                    logger.error("Web server thread died, restarting...")
                    self.web_thread = threading.Thread(target=self._start_web_server, daemon=True)
                    self.web_thread.start()
                
                # Sleep for a bit to avoid busy waiting
                import time
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
    logger.info("Initializing Broadlink Manager Add-on")
    
    # Verify we have the required environment
    if not os.environ.get('SUPERVISOR_TOKEN'):
        logger.warning("SUPERVISOR_TOKEN not found - some features may not work")
    
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
