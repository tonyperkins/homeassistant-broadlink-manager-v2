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

from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_cors import CORS
import aiohttp
import aiofiles

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
        
        self._setup_routes()
    
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
        """Learn a new command"""
        try:
            entity_id = data.get('entity_id')
            device = data.get('device')
            command = data.get('command')
            command_type = data.get('command_type', 'ir')
            
            payload = {
                'entity_id': entity_id,
                'device': device,
                'command': command,
                'command_type': command_type
            }
            
            result = await self._make_ha_request('POST', 'services/remote/learn_command', payload)
            return {'success': True, 'result': result}
            
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
            
            payload = {
                'entity_id': entity_id,
                'device': device,
                'command': command
            }
            
            result = await self._make_ha_request('POST', 'services/remote/delete_command', payload)
            return {'success': True, 'result': result}
            
        except Exception as e:
            logger.error(f"Error deleting command: {e}")
            return {'success': False, 'error': str(e)}
    
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

        async function learnCommand(index) {
            const command = commands[index];
            const deviceEntityId = document.getElementById('broadlinkDevice').value;
            const commandType = document.getElementById('commandType').value;
            
            if (!deviceEntityId) {
                showAlert('Please select a Broadlink device', 'error');
                return;
            }
            
            command.status = 'learning';
            updateCommandList();
            
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
                    command.status = 'learned';
                    log(`Successfully learned: ${command.name}`);
                    showAlert(`Command "${command.name}" learned successfully!`, 'success');
                } else {
                    command.status = 'failed';
                    log(`Failed to learn: ${command.name} - ${result.error}`, 'error');
                    showAlert(`Failed to learn command: ${result.error}`, 'error');
                }
            } catch (error) {
                command.status = 'failed';
                log(`Error learning command: ${error.message}`, 'error');
                showAlert(`Error learning command: ${error.message}`, 'error');
            }
            
            updateCommandList();
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

        document.getElementById('deviceName').addEventListener('change', function() {
            currentDeviceName = this.value;
        });
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
