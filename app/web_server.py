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

from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import aiohttp
import aiofiles
import websockets

logger = logging.getLogger(__name__)


class BroadlinkWebServer:
    """Web server for Broadlink device management"""
    
    def __init__(self, port: int = 8099):
        self.port = port
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Home Assistant configuration
        self.ha_url = "http://supervisor/core"
        self.ha_token = os.environ.get('SUPERVISOR_TOKEN')
        self.storage_path = Path("/config/.storage")
        
        # Simple notification cache
        self.cached_notifications = []
        self.last_notification_check = 0
        
        self._setup_routes()
        # Initialize WebSocket variables
        self.ws_connection = None
        self.ws_message_id = 0
        self.ws_notifications = []
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Serve the main web interface"""
            return render_template_string(self._get_html_template())
        
        @self.app.route('/api/areas')
        def get_areas():
            """Get Home Assistant areas"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                areas = loop.run_until_complete(self._get_ha_areas())
                loop.close()
                return jsonify(areas)
            except Exception as e:
                logger.error(f"Error getting areas: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/devices')
        def get_broadlink_devices():
            """Get Broadlink devices"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                devices = loop.run_until_complete(self._get_broadlink_devices())
                loop.close()
                return jsonify(devices)
            except Exception as e:
                logger.error(f"Error getting devices: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/commands/<device_id>')
        def get_commands(device_id):
            """Get learned commands for a device"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                commands = loop.run_until_complete(self._get_learned_commands(device_id))
                loop.close()
                return jsonify(commands)
            except Exception as e:
                logger.error(f"Error getting commands: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/learn', methods=['POST'])
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
        
        @self.app.route('/api/send', methods=['POST'])
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
        
        @self.app.route('/api/delete', methods=['POST'])
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
        
        @self.app.route('/api/notifications')
        def get_notifications():
            """Get persistent notifications for learning status"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Try WebSocket method first, fallback to REST API
                try:
                    notifications = loop.run_until_complete(self._get_ws_notifications())
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
        
        @self.app.route('/api/debug/all-notifications')
        def get_all_notifications():
            """Get all persistent notifications for debugging"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                states = loop.run_until_complete(self._make_ha_request('GET', 'states'))
                loop.close()
                
                all_notifications = []
                if isinstance(states, list):
                    for entity in states:
                        entity_id = entity.get('entity_id', '')
                        if entity_id.startswith('persistent_notification.'):
                            attributes = entity.get('attributes', {})
                            all_notifications.append({
                                'id': entity_id,
                                'title': attributes.get('title', ''),
                                'message': attributes.get('message', ''),
                                'created_at': entity.get('last_changed')
                            })
                
                return jsonify(all_notifications)
            except Exception as e:
                logger.error(f"Error getting all notifications: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/debug/token')
        def get_token():
            """Get supervisor token for WebSocket authentication"""
            try:
                return jsonify({"token": self.ha_token})
            except Exception as e:
                logger.error(f"Error getting token: {e}")
                return jsonify({"error": str(e)}), 500
    
    async def _make_ha_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make a request to Home Assistant API"""
        url = f"{self.ha_url}/api/{endpoint}"
        headers = {
            'Authorization': f'Bearer {self.ha_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"Making {method} request to: {url}")
        
        async with aiohttp.ClientSession() as session:
            if method.upper() == 'GET':
                async with session.get(url, headers=headers) as response:
                    logger.info(f"Response status: {response.status}")
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Response data type: {type(result)}, length: {len(result) if isinstance(result, (list, dict)) else 'N/A'}")
                        return result
                    else:
                        logger.error(f"API request failed with status {response.status}: {await response.text()}")
                        return {}
            elif method.upper() == 'POST':
                async with session.post(url, headers=headers, json=data) as response:
                    logger.info(f"Response status: {response.status}")
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"API request failed with status {response.status}: {await response.text()}")
                        return {}
    
    async def _get_ha_areas(self) -> List[Dict]:
        """Get Home Assistant areas"""
        try:
            # First try API call (more reliable)
            logger.info("Attempting to get areas via Home Assistant API...")
            areas_response = await self._make_ha_request('GET', 'config/area_registry')
            
            if areas_response and isinstance(areas_response, list):
                logger.info(f"Found {len(areas_response)} areas via API")
                return [{'area_id': area.get('area_id', area.get('id', '')), 'name': area.get('name', '')} for area in areas_response if area.get('name')]
            
            # Fallback to storage file
            logger.info("API call failed, trying storage file...")
            registry_file = self.storage_path / "core.area_registry"
            if registry_file.exists():
                async with aiofiles.open(registry_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    areas = data.get('data', {}).get('areas', [])
                    logger.info(f"Found {len(areas)} areas in storage file")
                    
                    # Handle different storage formats
                    result_areas = []
                    for area in areas:
                        try:
                            area_id = area.get('area_id') or area.get('id', '')
                            name = area.get('name', '')
                            if area_id and name:
                                result_areas.append({'area_id': area_id, 'name': name})
                        except Exception as e:
                            logger.warning(f"Skipping malformed area entry: {area}, error: {e}")
                    
                    logger.info(f"Successfully processed {len(result_areas)} areas from storage")
                    return result_areas
            
            # If no areas found, return empty list (don't force a default)
            logger.warning("No areas found via API or storage file")
            return []
            
        except Exception as e:
            logger.error(f"Error getting areas: {e}")
            # Try alternative API endpoint - this returns all entities, need to filter
            try:
                logger.info("Trying to get areas from states API...")
                states_response = await self._make_ha_request('GET', 'states')
                if states_response and isinstance(states_response, list):
                    # Extract unique area names from entity attributes
                    areas_set = set()
                    for entity in states_response:
                        attributes = entity.get('attributes', {})
                        area_id = attributes.get('area_id')
                        if area_id:
                            # Try to get area name from device registry or use area_id
                            area_name = area_id.replace('_', ' ').title()
                            areas_set.add((area_id, area_name))
                    
                    areas_list = [{'area_id': area_id, 'name': name} for area_id, name in areas_set]
                    logger.info(f"Extracted {len(areas_list)} unique areas from states")
                    return areas_list
            except Exception as e2:
                logger.error(f"States API also failed: {e2}")
            
            # Return empty list instead of default
            return []
    
    async def _get_broadlink_devices(self) -> List[Dict]:
        """Get Broadlink remote devices"""
        try:
            states = await self._make_ha_request('GET', 'states')
            broadlink_devices = []
            
            for entity in states:
                entity_id = entity.get('entity_id', '')
                if entity_id.startswith('remote.') and 'broadlink' in entity_id.lower():
                    attributes = entity.get('attributes', {})
                    broadlink_devices.append({
                        'entity_id': entity_id,
                        'name': attributes.get('friendly_name', entity_id),
                        'state': entity.get('state')
                    })
            
            return broadlink_devices
        except Exception as e:
            logger.error(f"Error getting Broadlink devices: {e}")
            return []
    
    async def _get_learned_commands(self, device_id: str) -> Dict:
        """Get learned commands for a specific device by reading storage files"""
        try:
            # Find the storage file for this device
            # Broadlink storage files are named like: broadlink_remote_{unique_id}_codes
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))
            
            all_commands = {}
            
            for storage_file in storage_files:
                try:
                    async with aiofiles.open(storage_file, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        # The data structure contains device names as keys
                        for device_name, commands in data.get('data', {}).items():
                            if isinstance(commands, dict):
                                all_commands[device_name] = list(commands.keys())
                
                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue
            
            return all_commands
            
        except Exception as e:
            logger.error(f"Error getting learned commands: {e}")
            return {}
    
    async def _learn_command(self, data: Dict) -> Dict:
        """Learn a new command with 2-step process monitoring"""
        try:
            entity_id = data.get('entity_id')
            device = data.get('device')
            command = data.get('command')
            command_type = data.get('command_type', 'ir')
            
            logger.info(f"Starting learning process for command: {command}")
            
            # Prepare the service call payload
            service_data = {
                'entity_id': entity_id,
                'device': device,
                'command': command,
                'command_type': command_type
            }
            
            # Start the learning process
            logger.info(f"Calling learn_command service with data: {service_data}")
            result = await self._make_ha_request('POST', 'services/remote/learn_command', service_data)
            
            if result:
                logger.info("Learn command service called successfully")
                return {
                    'success': True, 
                    'message': 'Learning process started. Follow the instructions in Home Assistant notifications.',
                    'result': result
                }
            else:
                return {'success': False, 'error': 'Failed to start learning process'}
            
        except Exception as e:
            logger.error(f"Error learning command: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _send_command(self, data: Dict) -> Dict:
        """Send a command"""
        try:
            entity_id = data.get('entity_id')
            device = data.get('device')
            command = data.get('command')
            
            payload = {
                'entity_id': entity_id,
                'device': device,
                'command': command
            }
            
            result = await self._make_ha_request('POST', 'services/remote/send_command', payload)
            return {'success': True, 'result': result}
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _delete_command(self, data: Dict) -> Dict:
        """Delete a command"""
        try:
            entity_id = data.get('entity_id')
            device = data.get('device')
            command = data.get('command')
            
            service_data = {
                'entity_id': entity_id,
                'device': device,
                'command': command
            }
            
            result = await self._make_ha_request('POST', 'services/remote/delete_command', service_data)
            return {'success': True, 'result': result}
            
        except Exception as e:
            logger.error(f"Error deleting command: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _get_notifications(self) -> List[Dict]:
        """Get persistent notifications from Home Assistant - simplified approach"""
        try:
            current_time = time.time()
            
            # Check states for persistent_notification entities
            states = await self._make_ha_request('GET', 'states')
            if not isinstance(states, list):
                logger.warning("States API returned non-list response")
                return []
            
            notifications = []
            for entity in states:
                entity_id = entity.get('entity_id', '')
                if entity_id.startswith('persistent_notification.'):
                    attributes = entity.get('attributes', {})
                    title = attributes.get('title', '')
                    message = attributes.get('message', '')
                    
                    # Debug: Log all notification titles to see what we're getting
                    if title:
                        logger.info(f"DEBUG: Found notification - Title: '{title}', Message: '{message[:50]}...'")

                    # Look for Broadlink learning notifications (broader search)
                    if ('sweep frequency' in title.lower() or 'learn command' in title.lower() or 
                        'broadlink' in title.lower() or 'sweep' in title.lower() or 
                        'learn' in title.lower()):
                        notifications.append({
                            'id': entity_id,
                            'title': title,
                            'message': message,
                            'created_at': entity.get('last_changed', ''),
                            'state': entity.get('state', '')
                        })
                        logger.info(f"Found potential Broadlink notification: '{title}' - '{message[:100]}'")
            
            # Cache the results
            self.cached_notifications = notifications
            self.last_notification_check = current_time
            
            logger.info(f"Total notifications found: {len([e for e in states if e.get('entity_id', '').startswith('persistent_notification.')])}")
            logger.info(f"Found {len(notifications)} potential Broadlink learning notifications")
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
                    "type": "persistent_notification/get"
                }
                await self.ws_connection.send(json.dumps(request_msg))
                
                # Wait a bit for response
                await asyncio.sleep(0.5)
            
            # Filter for learning-related notifications
            learning_notifications = []
            for notification in self.ws_notifications:
                title = notification.get('title', '').lower()
                message = notification.get('message', '').lower()
                if ('sweep' in title or 'learn' in title or 
                    'command' in title or 'broadlink' in message):
                    learning_notifications.append(notification)
                    logger.info(f"Found WebSocket notification: {notification.get('title')} - {notification.get('message', '')[:100]}")
            
            return learning_notifications
            
        except Exception as e:
            logger.error(f"Error getting WebSocket notifications: {e}")
            return []
    
    def _get_html_template(self) -> str:
        """Get the HTML template for the web interface"""
        # This will be a simplified version of the reference HTML
        # We'll remove the HA URL/token fields since we're running inside HA
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Broadlink Manager</title>
    <style>
        :root {
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --secondary: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --background: #0f172a;
            --surface: #1e293b;
            --surface-light: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --text-muted: #94a3b8;
            --border: #334155;
            --border-light: #475569;
            --radius: 12px;
            --radius-sm: 8px;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--background);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
        }

        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 16px;
        }

        .header {
            text-align: center;
            margin-bottom: 24px;
            padding: 24px 0;
        }

        .header h1 {
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--primary), #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .config-section {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: var(--shadow);
        }

        .config-section h2 {
            color: var(--text-primary);
            margin-bottom: 16px;
            font-size: 1.1rem;
            font-weight: 600;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        label {
            font-weight: 500;
            font-size: 0.875rem;
            color: var(--text-secondary);
        }

        input, select {
            padding: 10px 12px;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            font-size: 14px;
            background: var(--surface-light);
            color: var(--text-primary);
            transition: all 0.2s ease;
        }

        input:focus, select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }

        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: var(--radius-sm);
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.875rem;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-primary {
            background: var(--primary);
            color: white;
        }

        .btn-primary:hover {
            background: var(--primary-hover);
        }

        .btn-success {
            background: var(--success);
            color: white;
        }

        .btn-warning {
            background: var(--warning);
            color: white;
        }

        .btn-danger {
            background: var(--danger);
            color: white;
        }

        .btn-small {
            padding: 6px 10px;
            font-size: 0.75rem;
        }

        .command-list {
            max-height: 350px;
            overflow-y: auto;
            border: 1px solid var(--border);
            border-radius: var(--radius-sm);
            background: var(--surface-light);
        }

        .command-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
        }

        .command-item:last-child {
            border-bottom: none;
        }

        .command-name {
            font-weight: 500;
            color: var(--text-primary);
            font-size: 0.9rem;
        }

        .command-actions {
            display: flex;
            gap: 8px;
        }

        .log-area {
            background: #0a0a0a;
            color: #22c55e;
            font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
            padding: 16px;
            border-radius: var(--radius-sm);
            height: 180px;
            overflow-y: auto;
            margin-top: 16px;
            border: 1px solid var(--border);
            font-size: 0.8rem;
        }

        .alert {
            padding: 12px 16px;
            border-radius: var(--radius-sm);
            margin-bottom: 16px;
            font-size: 0.875rem;
            border-left: 4px solid;
        }

        .alert-success {
            background: rgba(16, 185, 129, 0.1);
            color: #6ee7b7;
            border-left-color: var(--success);
        }

        .alert-error {
            background: rgba(239, 68, 68, 0.1);
            color: #fca5a5;
            border-left-color: var(--danger);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏠 Broadlink Manager</h1>
            <p>Manage your Broadlink devices from Home Assistant</p>
        </div>

        <!-- Device Selection -->
        <div class="config-section">
            <h2>🔗 Device Selection</h2>
            <div class="form-grid">
                <div class="form-group">
                    <label for="broadlinkDevice">Broadlink Device</label>
                    <select id="broadlinkDevice">
                        <option value="">Loading devices...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="roomName">Room</label>
                    <select id="roomName">
                        <option value="">Loading areas...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="deviceName">Device Name</label>
                    <input type="text" id="deviceName" placeholder="fan" value="fan">
                </div>
                <div class="form-group">
                    <label for="commandType">Type</label>
                    <select id="commandType">
                        <option value="rf">RF</option>
                        <option value="ir">IR</option>
                    </select>
                </div>
            </div>
        </div>

        <!-- Command Management -->
        <div class="config-section">
            <h2>🎮 Commands</h2>
            <div style="display: flex; gap: 12px; align-items: end; margin-bottom: 16px;">
                <div class="form-group" style="flex: 1;">
                    <label for="newCommand">Add Command</label>
                    <input type="text" id="newCommand" placeholder="command_name">
                </div>
                <button class="btn btn-primary" onclick="addCommand()">Add</button>
                <button class="btn btn-success" onclick="loadCommands()">Refresh</button>
                <button class="btn btn-warning" onclick="testNotifications()">Test Notifications</button>
            </div>
            
            <div class="command-list" id="commandList">
                <!-- Commands will be populated here -->
            </div>
        </div>

        <!-- Activity Log -->
        <div class="config-section">
            <h2>📊 Activity Log</h2>
            <div class="log-area" id="logArea">
                <div>🚀 Broadlink Manager initialized...</div>
            </div>
        </div>
    </div>

    <script>
        let commands = [];
        let currentDevice = '';
        let currentRoom = '';
        let currentDeviceName = '';

        // Initialize the application
        document.addEventListener('DOMContentLoaded', function() {
            loadAreas();
            loadBroadlinkDevices();
            // Enable WebSocket for proper notification handling
            connectWebSocket();
            log('Application initialized');
        });

        async function loadAreas() {
            try {
                const response = await fetch('/api/areas');
                const areas = await response.json();
                
                const select = document.getElementById('roomName');
                select.innerHTML = '<option value="">Select a room...</option>';
                
                areas.forEach(area => {
                    const option = document.createElement('option');
                    option.value = area.area_id || area.name.toLowerCase().replace(/\\s+/g, '_');
                    option.textContent = area.name;
                    select.appendChild(option);
                });
                
                log(`Loaded ${areas.length} areas`);
            } catch (error) {
                log(`Error loading areas: ${error.message}`, 'error');
            }
        }

        async function loadBroadlinkDevices() {
            try {
                const response = await fetch('/api/devices');
                const devices = await response.json();
                
                const select = document.getElementById('broadlinkDevice');
                select.innerHTML = '<option value="">Select a device...</option>';
                
                devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.entity_id;
                    option.textContent = device.name;
                    select.appendChild(option);
                });
                
                if (devices.length > 0) {
                    select.value = devices[0].entity_id;
                    currentDevice = devices[0].entity_id;
                }
                
                log(`Loaded ${devices.length} Broadlink devices`);
            } catch (error) {
                log(`Error loading devices: ${error.message}`, 'error');
            }
        }

        async function loadCommands() {
            if (!currentDevice) {
                log('No device selected', 'error');
                return;
            }
            
            try {
                const response = await fetch(`/api/commands/${encodeURIComponent(currentDevice)}`);
                const commandData = await response.json();
                
                commands = [];
                for (const [deviceName, commandList] of Object.entries(commandData)) {
                    commandList.forEach(cmd => {
                        commands.push({
                            name: cmd,
                            device: deviceName,
                            status: 'learned'
                        });
                    });
                }
                
                updateCommandList();
                log(`Loaded ${commands.length} commands`);
            } catch (error) {
                log(`Error loading commands: ${error.message}`, 'error');
            }
        }

        function addCommand() {
            const commandName = document.getElementById('newCommand').value.trim();
            if (!commandName) {
                showAlert('Please enter a command name', 'error');
                return;
            }
            
            commands.push({
                name: commandName,
                device: getDeviceKey(),
                status: 'pending'
            });
            
            updateCommandList();
            document.getElementById('newCommand').value = '';
            log(`Added command: ${commandName}`);
        }

        function getDeviceKey() {
            const room = document.getElementById('roomName').value;
            const device = document.getElementById('deviceName').value;
            return `${room}_${device}`;
        }

        // Learning state variables
        let isLearning = false;
        let learningCommand = '';
        let pollingInterval = null;
        
        // WebSocket variables (like reference HTML)
        let wsConnection = null;
        let wsMessageId = 0;
        let currentlyLearningIndex = -1;

        async function learnCommand(index) {
            const command = commands[index];
            const deviceEntityId = document.getElementById('broadlinkDevice').value;
            const commandType = document.getElementById('commandType').value;
            
            if (!deviceEntityId) {
                showAlert('Please select a Broadlink device', 'error');
                return;
            }

            if (isLearning) {
                showAlert('Already learning a command. Please wait.', 'warning');
                return;
            }
            
            isLearning = true;
            learningCommand = command.name;
            command.status = 'learning';
            updateCommandList();
            
            // Start polling for notifications
            startLearningPolling(index);
            
            try {
                const response = await fetch('/api/learn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity_id: deviceEntityId,
                        device: command.device,
                        command: command.name,
                        command_type: commandType
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    log(`Learning started: ${command.name}`);
                    showAlert(result.message || 'Learning process started. Watch for Home Assistant notifications.', 'info');
                } else {
                    command.status = 'failed';
                    log(`Failed to start learning: ${command.name} - ${result.error}`, 'error');
                    showAlert(`Failed to start learning: ${result.error}`, 'error');
                    stopLearningPolling();
                }
            } catch (error) {
                command.status = 'failed';
                log(`Error starting learning: ${error.message}`, 'error');
                showAlert(`Error starting learning: ${error.message}`, 'error');
                stopLearningPolling();
            }
            
            updateCommandList();
        }

        // Learning phase tracking
        let learningPhase = 'idle'; // 'idle', 'sweeping', 'learning', 'completed'
        let lastInstruction = '';

        // Start polling for learning notifications (WebSocket + HTTP fallback)
        function startLearningPolling(commandIndex) {
            if (pollingInterval) {
                clearInterval(pollingInterval);
            }
            
            learningPhase = 'sweeping';
            lastInstruction = '';
            currentlyLearningIndex = commandIndex;
            
            const pollStartTime = Date.now();
            const TIMEOUT = 45000; // 45 seconds
            
            pollingInterval = setInterval(async () => {
                if (Date.now() - pollStartTime > TIMEOUT) {
                    log('Learning process timed out', 'error');
                    commands[commandIndex].status = 'failed';
                    showAlert('⏰ Learning process timed out', 'warning');
                    stopLearningPolling();
                    updateCommandList();
                    return;
                }
                
                try {
                    // Try WebSocket first if available
                    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
                        wsConnection.send(JSON.stringify({ 
                            id: ++wsMessageId, 
                            type: 'persistent_notification/get' 
                        }));
                    } else {
                        // Fallback to HTTP API
                        const response = await fetch('/api/notifications');
                        const notifications = await response.json();
                        
                        if (notifications && notifications.length > 0) {
                            handleNotificationPoll(notifications, commandIndex);
                        }
                    }
                } catch (error) {
                    // Polling errors are normal during WebSocket, don't show them
                    console.log('Polling error (normal):', error);
                }
            }, 1000); // Poll every 1 second like reference
            
            log(`Started polling for command: ${commands[commandIndex]?.name || commandIndex}`);
        }

        // Handle notification polling results - enhanced to match reference HTML logic
        function handleNotificationPoll(notifications, commandIndex) {
            if (currentlyLearningIndex === -1 || !isLearning) return;

            const command = commands[commandIndex];
            const deviceFullName = getDeviceKey(); // Using our device key function
            const commandName = command.name;
            const fullCommandName = `${deviceFullName}_${commandName}`;
            
            log(`Poll result: Found ${notifications.length} notifications for ${fullCommandName}`);
            
            // Create matchers for the command name (like reference HTML)
            const nameMatchers = [
                `'${commandName}'`,
                commandName,
                `'${fullCommandName}'`,
                fullCommandName,
                `'${command.device}_${commandName}'`,
                `${command.device}_${commandName}`
            ];

            if (learningPhase === 'sweeping') {
                // Look for "Sweep frequency" notification
                const sweepNotification = notifications.find(n => {
                    if (n.title !== 'Sweep frequency') return false;
                    const msg = n.message || '';
                    return nameMatchers.some(k => msg.includes(k));
                });
                
                if (sweepNotification) {
                    const instruction = "Press and hold the remote button...";
                    if (lastInstruction !== instruction) {
                        lastInstruction = instruction;
                        showAlert(`🔄 Step 1: ${instruction}`, 'info');
                        log(`Learning instruction: ${instruction}`);
                    }
                } else if (lastInstruction.startsWith('Press and hold') && 
                          !notifications.some(n => n.title === 'Sweep frequency')) {
                    // Transition from sweeping to learning phase
                    const instruction = "Release the button. Now prepare to press it briefly.";
                    showAlert(`🔄 Transition: ${instruction}`, 'info');
                    log(`Learning instruction: ${instruction}`);
                    learningPhase = 'learning';
                    lastInstruction = instruction;
                }
            } else if (learningPhase === 'learning') {
                // Look for "Learn command" notification
                const learnNotification = notifications.find(n => {
                    if (n.title !== 'Learn command') return false;
                    const msg = n.message || '';
                    return nameMatchers.some(k => msg.includes(k));
                });
                
                if (learnNotification) {
                    const instruction = "Press the button briefly.";
                    if (lastInstruction !== instruction) {
                        lastInstruction = instruction;
                        showAlert(`🔄 Step 2: ${instruction}`, 'info');
                        log(`Learning instruction: ${instruction}`);
                    }
                } else if (lastInstruction.startsWith('Press the button')) {
                    // Learning completed
                    learningPhase = 'completed';
                    lastInstruction = '';
                    commands[commandIndex].status = 'learned';
                    showAlert(`✅ Successfully learned ${learningCommand}!`, 'success');
                    log(`Learning completed for ${learningCommand}`);
                    stopLearningPolling();
                    updateCommandList();
                }
            }
        }

        // Stop polling for learning notifications
        function stopLearningPolling() {
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
            isLearning = false;
            learningCommand = '';
            learningPhase = 'idle';
            lastInstruction = '';
            currentlyLearningIndex = -1;
            log('Stopped polling.');
        }

        // Test notifications function for debugging
        async function testNotifications() {
            try {
                log('Testing notification detection...');
                
                // Test regular notifications endpoint
                const response = await fetch('/api/notifications');
                const notifications = await response.json();
                log(`Regular notifications: ${JSON.stringify(notifications, null, 2)}`);
                
                // Test debug endpoint
                const debugResponse = await fetch('/api/debug/all-notifications');
                const allNotifications = await debugResponse.json();
                log(`All notifications: ${JSON.stringify(allNotifications, null, 2)}`);
                
                showAlert(`Found ${notifications.length} learning notifications, ${allNotifications.length} total. Check logs for details.`, 'info');
            } catch (error) {
                log(`Error testing notifications: ${error.message}`, 'error');
                showAlert(`Error testing notifications: ${error.message}`, 'error');
            }
        }

        async function testCommand(index) {
            const command = commands[index];
            const deviceEntityId = document.getElementById('broadlinkDevice').value;
            
            if (command.status !== 'learned') {
                showAlert('Command must be learned before testing', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/send', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity_id: deviceEntityId,
                        device: command.device,
                        command: command.name
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    log(`Successfully sent: ${command.name}`);
                    showAlert(`Command "${command.name}" sent successfully!`, 'success');
                } else {
                    log(`Failed to send: ${command.name} - ${result.error}`, 'error');
                    showAlert(`Failed to send command: ${result.error}`, 'error');
                }
            } catch (error) {
                log(`Error sending command: ${error.message}`, 'error');
                showAlert(`Error sending command: ${error.message}`, 'error');
            }
        }

        function removeCommand(index) {
            const command = commands[index];
            commands.splice(index, 1);
            updateCommandList();
            log(`Removed command: ${command.name}`);
        }

        function updateCommandList() {
            const container = document.getElementById('commandList');
            container.innerHTML = '';
            
            commands.forEach((command, index) => {
                const item = document.createElement('div');
                item.className = 'command-item';
                
                const statusColor = {
                    'pending': '#f59e0b',
                    'learning': '#6366f1',
                    'learned': '#10b981',
                    'failed': '#ef4444'
                }[command.status] || '#64748b';
                
                item.innerHTML = `
                    <div>
                        <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${statusColor}; margin-right: 8px;"></span>
                        <span class="command-name">${command.device}_${command.name}</span>
                    </div>
                    <div class="command-actions">
                        <button class="btn btn-primary btn-small" onclick="learnCommand(${index})" ${command.status === 'learning' ? 'disabled' : ''}>
                            ${command.status === 'learning' ? 'Learning...' : 'Learn'}
                        </button>
                        <button class="btn btn-warning btn-small" onclick="testCommand(${index})" ${command.status !== 'learned' ? 'disabled' : ''}>Test</button>
                        <button class="btn btn-danger btn-small" onclick="removeCommand(${index})">Remove</button>
                    </div>
                `;
                container.appendChild(item);
            });
        }

        function showAlert(message, type = 'error') {
            const container = document.querySelector('.container');
            const alertEl = document.createElement('div');
            alertEl.className = `alert alert-${type}`;
            alertEl.textContent = message;
            
            container.insertBefore(alertEl, container.children[1]);
            
            setTimeout(() => {
                alertEl.style.transition = 'opacity 0.5s ease';
                alertEl.style.opacity = '0';
                setTimeout(() => alertEl.remove(), 500);
            }, 5000);
        }

        function log(message, level = 'info') {
            const logArea = document.getElementById('logArea');
            const timestamp = new Date().toLocaleTimeString();
            const logEntry = document.createElement('div');
            logEntry.textContent = `[${timestamp}] ${message}`;
            if (level === 'error') logEntry.style.color = '#ff4d4d';
            logArea.appendChild(logEntry);
            logArea.scrollTop = logArea.scrollHeight;
        }

        // Event listeners
        document.getElementById('broadlinkDevice').addEventListener('change', function() {
            currentDevice = this.value;
            loadCommands();
        });

        document.getElementById('roomName').addEventListener('change', function() {
            currentRoom = this.value;
        });
                
        const result = await response.json();
                    getTokenAndAuth();
                };
                
                wsConnection.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === "auth_ok") {
                        log('WebSocket authenticated successfully');
                    } else if (data.type === "result" && data.success) {
                        // Handle persistent notification results
                        if (Array.isArray(data.result)) {
                            handleNotificationPoll(data.result, currentlyLearningIndex);
                        }
                    } else if (data.type === "result" && !data.success) {
                        log(`WS Error: ${data.error?.message || 'Unknown error'}`, 'error');
                    }
                };
                
                wsConnection.onerror = (error) => log(`WebSocket error: ${error}`, 'error');
                wsConnection.onclose = () => {
                    log('WebSocket disconnected');
                    wsConnection = null;
                    if (pollingInterval && currentlyLearningIndex !== -1) {
                        log('WebSocket closed during learning - continuing with HTTP fallback');
                    }
                };
            } catch (error) {
                log(`WebSocket connection failed: ${error.message}`, 'error');
            }
        }

        async function getTokenAndAuth() {
            try {
                // Get the supervisor token from our backend
                const response = await fetch('/api/debug/token');
                const tokenData = await response.json();
                
                if (tokenData.token) {
                    wsConnection.send(JSON.stringify({ type: "auth", access_token: tokenData.token }));
                } else {
                    log('Failed to get authentication token', 'error');
                }
            } catch (error) {
                log(`Failed to authenticate WebSocket: ${error.message}`, 'error');
            }
        }
    </script>
</body>
</html>
        '''
    
    def run(self):
        """Run the Flask web server"""
        logger.info(f"Starting Broadlink Manager web server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)


if __name__ == "__main__":
    server = BroadlinkWebServer()
    server.run()
