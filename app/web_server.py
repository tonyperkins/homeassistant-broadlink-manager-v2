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
        
        @self.app.route('/api/debug/token')
        def get_token():
            """Get supervisor token for WebSocket authentication"""
            try:
                # For add-on context, we need to check if supervisor token works
                # If not, we'll need to use alternative authentication
                logger.info(f"Providing token for WebSocket: {self.ha_token[:20]}...")
                return jsonify({
                    "token": self.ha_token,
                })
            except Exception as e:
                logger.error(f"Error getting token: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/learned-devices')
        def get_learned_devices():
            """Get all learned devices with area and command information for filtering"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                commands_data = loop.run_until_complete(self._get_learned_commands())
                loop.close()
                
                # Transform data for filtering UI
                result = {
                    'areas': {},
                    'devices': {},
                    'commands': []
                }
                
                for device_name, device_info in commands_data.items():
                    area_id = device_info.get('area_id')
                    area_name = device_info.get('area_name', 'Unknown')
                    device_part = device_info.get('device_part', device_name)
                    
                    # Add to areas
                    if area_id and area_id not in result['areas']:
                        result['areas'][area_id] = area_name
                    
                    # Add to devices
                    if device_name not in result['devices']:
                        result['devices'][device_name] = {
                            'area_id': area_id,
                            'area_name': area_name,
                            'device_part': device_part,
                            'full_name': device_name
                        }
                    
                    # Add commands
                    command_data = device_info.get('command_data', {})
                    for command in device_info.get('commands', []):
                        command_code = command_data.get(command, '')
                        command_type = 'rf' if command_code.startswith('sc') else 'ir'
                        result['commands'].append({
                            'device_name': device_name,
                            'device_part': device_part,
                            'command': command,
                            'command_type': command_type,
                            'area_id': area_id,
                            'area_name': area_name,
                            'full_command_name': f"{device_name}_{command}"
                        })
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error getting learned devices: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/api/debug/broadlink-full-data')
        def debug_broadlink_full_data():
            """Get all learned devices with area and command information for debugging"""
        
        
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

        @self.app.route('/api/debug/test-service', methods=['POST'])
        def test_service():
            """Test if we can call Broadlink services at all"""
            try:
                data = request.get_json()
                entity_id = data.get('entity_id', 'remote.broadlink')
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Try to call the Broadlink service info first
                logger.info(f"Testing service call to remote.learn_command for entity: {entity_id}")
                
                test_data = {
                    'entity_id': entity_id,
                    'device': 'test_device',
                    'command': 'test_command',
                    'command_type': 'rf'
                }
                
                result = loop.run_until_complete(self._make_ha_request('POST', 'services/remote/learn_command', test_data))
                loop.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Service test completed',
                    'result': result,
                    'entity_id': entity_id
                })
            except Exception as e:
                logger.error(f"Error testing service: {e}")
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
                    logger.info(f"POST Response status: {response.status}")
                    response_text = await response.text()
                    logger.info(f"POST Response body: {response_text}")
                    if response.status == 200:
                        try:
                            return await response.json() if response_text else {}
                        except:
                            logger.info("POST response was successful but not JSON, returning empty dict")
                            return {}
                    else:
                        logger.error(f"POST API request failed with status {response.status}: {response_text}")
                        return None
    
    async def _get_ha_areas(self) -> List[Dict]:
        """Get Home Assistant areas from storage files"""
        try:
            # Read directly from storage file (primary method for add-on)
            logger.info("Reading areas from storage file...")
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
            
            # Fallback to API call if storage file doesn't exist
            logger.info("Storage file not found, trying API call...")
            areas_response = await self._make_ha_request('GET', 'config/area_registry')
            
            if areas_response and isinstance(areas_response, list):
                logger.info(f"Found {len(areas_response)} areas via API")
                return [{'area_id': area.get('area_id', area.get('id', '')), 'name': area.get('name', '')} for area in areas_response if area.get('name')]
            
            # If no areas found, return empty list
            logger.warning("No areas found via storage or API")
            return []
            
        except Exception as e:
            logger.error(f"Error getting areas: {e}")
            return []
    
    async def _get_broadlink_devices(self) -> List[Dict]:
        """Get Broadlink remote devices from storage files"""
        try:
            # Read from storage files (primary method for add-on)
            logger.info("Reading Broadlink devices from storage files...")
            
            # Get device registry
            device_registry_file = self.storage_path / "core.device_registry"
            entity_registry_file = self.storage_path / "core.entity_registry"
            
            broadlink_devices = []
            
            if device_registry_file.exists() and entity_registry_file.exists():
                # Read device registry
                async with aiofiles.open(device_registry_file, 'r') as f:
                    device_content = await f.read()
                    device_data = json.loads(device_content)
                    devices = device_data.get('data', {}).get('devices', [])
                
                # Read entity registry
                async with aiofiles.open(entity_registry_file, 'r') as f:
                    entity_content = await f.read()
                    entity_data = json.loads(entity_content)
                    entities = entity_data.get('data', {}).get('entities', [])
                
                # Find Broadlink devices
                for device in devices:
                    try:
                        manufacturer = (device.get('manufacturer') or '').lower()
                        name = (device.get('name') or '').lower()
                        identifiers = device.get('identifiers', [])
                        
                        # Check if this is a Broadlink device
                        if (manufacturer == 'broadlink' or
                            'broadlink' in name or
                            any('broadlink' in str(identifier).lower() for identifier in identifiers)):
                            
                            device_id = device.get('id')
                            area_id = device.get('area_id')
                            
                            logger.info(f"Found Broadlink device: {name} (ID: {device_id}, Manufacturer: {manufacturer})")
                            
                            # Find corresponding entities
                            for entity in entities:
                                if (entity.get('device_id') == device_id and 
                                    entity.get('entity_id', '').startswith('remote.')):
                                    
                                    broadlink_devices.append({
                                        'entity_id': entity.get('entity_id'),
                                        'name': device.get('name', entity.get('entity_id')),
                                        'device_id': device_id,
                                        'unique_id': entity.get('unique_id'),
                                        'area_id': area_id
                                    })
                    except Exception as e:
                        logger.warning(f"Error processing device entry: {e}, device: {device}")
                        continue
                
                logger.info(f"Found {len(broadlink_devices)} Broadlink devices from storage")
                return broadlink_devices
            
            # Fallback to API calls if storage files don't exist
            logger.info("Storage files not found, trying API calls...")
            device_registry = await self._make_ha_request('GET', 'config/device_registry')
            entity_registry = await self._make_ha_request('GET', 'config/entity_registry')
            
            if isinstance(device_registry, list) and isinstance(entity_registry, list):
                for device in device_registry:
                    manufacturer = (device.get('manufacturer') or '').lower()
                    name = (device.get('name') or '').lower()
                    identifiers = device.get('identifiers', [])
                    
                    if (manufacturer == 'broadlink' or
                        'broadlink' in name or
                        any('broadlink' in str(identifier).lower() for identifier in identifiers)):
                        
                        device_id = device.get('id')
                        
                        for entity in entity_registry:
                            if (entity.get('device_id') == device_id and 
                                entity.get('entity_id', '').startswith('remote.')):
                                
                                broadlink_devices.append({
                                    'entity_id': entity.get('entity_id'),
                                    'name': device.get('name', entity.get('entity_id')),
                                    'device_id': device_id,
                                    'unique_id': entity.get('unique_id'),
                                    'area_id': device.get('area_id')
                                })
            
            logger.info(f"Returning {len(broadlink_devices)} Broadlink remote devices")
            return broadlink_devices

        except Exception as e:
            logger.error(f"Error getting Broadlink devices: {e}")
            return []
    
    async def _get_learned_commands(self, device_id: str = None) -> Dict:
        """Get learned commands from storage files with filtering and area information"""
        try:
            # Find the storage files for Broadlink commands
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))
            
            all_commands = {}
            
            # Also get area information for filtering
            areas_data = await self._get_ha_areas()
            area_lookup = {area['area_id']: area['name'] for area in areas_data}
            
            for storage_file in storage_files:
                try:
                    async with aiofiles.open(storage_file, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        # The data structure contains device names as keys
                        for device_name, commands in data.get('data', {}).items():
                            if isinstance(commands, dict):
                                # Parse the device name to extract area and device info
                                # Format: {area}_{device} e.g., "tony_s_office_ceiling_fan"
                                parts = device_name.split('_')
                                if len(parts) >= 2:
                                    # Try to match area from the beginning of the device name
                                    area_id = None
                                    device_part = device_name
                                    
                                    # Check if device name starts with a known area
                                    for aid, aname in area_lookup.items():
                                        if device_name.startswith(aid + '_'):
                                            area_id = aid
                                            device_part = device_name[len(aid) + 1:]
                                            break
                                    
                                    all_commands[device_name] = {
                                        'commands': list(commands.keys()),
                                        'command_data': commands,  # Include actual command codes
                                        'area_id': area_id,
                                        'area_name': area_lookup.get(area_id, 'Unknown'),
                                        'device_part': device_part,
                                        'full_name': device_name
                                    }
                                else:
                                    all_commands[device_name] = {
                                        'commands': list(commands.keys()),
                                        'command_data': commands,  # Include actual command codes
                                        'area_id': None,
                                        'area_name': 'Unknown',
                                        'device_part': device_name,
                                        'full_name': device_name
                                    }
                
                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue
            
            logger.info(f"Found {len(all_commands)} learned devices with commands")
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
            
            logger.info(f"Learn command service result: {result}")
            
            if result is not None:
                logger.info("Learn command service called successfully")
                return {
                    'success': True, 
                    'message': 'Learning process started. Please follow the learning instructions in Home Assistant\'s notification area (bell icon).',
                    'result': result
                }
            else:
                logger.error("Learn command service returned None")
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
    
    async def _get_notifications_http(self) -> List[Dict]:
        """Get persistent notifications via HTTP (fallback when WebSocket fails)"""
        try:
            # Get all states and filter for persistent notifications
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
                    
                    # Log ALL persistent notifications for debugging
                    logger.info(f"HTTP: Found notification - Title: '{title}', Message: '{message[:50]}...'")
                    
                    # Look for Broadlink learning notifications
                    if (any(keyword in title.lower() for keyword in ['sweep frequency', 'learn command']) or
                        any(keyword in message.lower() for keyword in ['broadlink', 'sweep', 'learning', 'press and hold', 'press the button', 'remote'])):
                        notifications.append({
                            'title': title,
                            'message': message,
                            'notification_id': entity_id,
                            'created_at': entity.get('last_changed', ''),
                        })
                        logger.info(f"★ HTTP MATCHED Broadlink notification: '{title}' - '{message[:100]}'")
            
            logger.info(f"HTTP notifications: Found {len([e for e in states if e.get('entity_id', '').startswith('persistent_notification.')])} total, {len(notifications)} Broadlink")
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting HTTP notifications: {e}")
            return []
    
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
        """Get persistent notifications from Home Assistant - using correct API endpoint"""
        try:
            current_time = time.time()
            
            # Try the direct persistent notification API endpoint first
            logger.info("Trying direct persistent notification API endpoint...")
            pn_notifications = await self._make_ha_request('GET', 'persistent_notification')
            
            if isinstance(pn_notifications, list) and len(pn_notifications) > 0:
                logger.info(f"Found {len(pn_notifications)} notifications via persistent_notification API")
                
                notifications = []
                for notification in pn_notifications:
                    title = notification.get('title', '')
                    message = notification.get('message', '')
                    notification_id = notification.get('notification_id', '')
                    
                    # Debug: Log ALL persistent notifications
                    logger.info(f"DEBUG: Persistent notification - ID: '{notification_id}', Title: '{title}', Message: '{message[:100]}...'")
                    
                    # Look for Broadlink learning notifications
                    full_search_text = f"{title} {message}".lower()
                    
                    if (any(keyword in full_search_text for keyword in [
                        'sweep frequency', 'learn command', 'broadlink', 'sweep', 'learning', 
                        'press and hold', 'press the button', 'remote', 'rf', 'ir'
                    ])):
                        notifications.append({
                            'id': notification_id,
                            'title': title,
                            'message': message,
                            'created_at': notification.get('created_at', ''),
                            'notification': notification
                        })
                        logger.info(f"★ MATCHED Broadlink notification: '{title}' - '{message[:100]}'")
                
                # Cache the results
                self.cached_notifications = notifications
                self.last_notification_check = current_time
                
                logger.info(f"Total persistent notifications found: {len(pn_notifications)}")
                logger.info(f"Matched Broadlink learning notifications: {len(notifications)}")
                return notifications
            
            # Fallback to states API if persistent_notification endpoint doesn't work
            logger.info("Persistent notification API returned empty, trying states API...")
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
                    
                    # Debug: Log ALL persistent notifications to see what we have
                    logger.info(f"DEBUG: Found persistent notification via states - ID: '{entity_id}', Title: '{title}', Message: '{message[:100]}...', State: '{entity.get('state', 'N/A')}'")

                    # Look for Broadlink learning notifications - much broader search
                    # Check title, message, and entity attributes for any Broadlink-related content
                    entity_attrs = entity.get('attributes', {})
                    full_search_text = f"{title} {message} {entity_attrs}".lower()
                    
                    if (any(keyword in full_search_text for keyword in [
                        'sweep frequency', 'learn command', 'broadlink', 'sweep', 'learning', 
                        'press and hold', 'press the button', 'remote', 'rf', 'ir'
                    ])):
                        notifications.append({
                            'id': entity_id,
                            'title': title,
                            'message': message,
                            'created_at': entity.get('last_changed', ''),
                            'state': entity.get('state', ''),
                            'attributes': entity_attrs
                        })
                        logger.info(f"★ MATCHED Broadlink notification: '{title}' - '{message[:100]}'")
            
            # Cache the results
            self.cached_notifications = notifications
            self.last_notification_check = current_time
            
            persistent_count = len([e for e in states if e.get('entity_id', '').startswith('persistent_notification.')])
            logger.info(f"Total persistent notifications found via states: {persistent_count}")
            logger.info(f"Matched Broadlink learning notifications: {len(notifications)}")
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
            font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0f1419;
            color: #e1e5e9;
            margin: 0;
            padding: 0;
            line-height: 1.6;
            min-height: 100vh;
        }

        .header {
            background: #111827;
            border-bottom: 1px solid #374151;
            padding: 16px 24px;
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

        .btn-secondary {
            background: var(--secondary);
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

        /* Device Cards - Match mock.html exactly */
        .device-card {
            background: #1f2937;
            border: 1px solid #374151;
            border-radius: 12px;
            margin-bottom: 16px;
            overflow: hidden;
        }

        .device-header {
            padding: 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }

        .device-header:hover {
            background: #252f3f;
        }

        .device-icon {
            width: 56px;
            height: 56px;
            background: #374151;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            flex-shrink: 0;
        }

        .device-info {
            flex: 1;
            min-width: 0;
        }

        .device-name {
            font-size: 20px;
            font-weight: 500;
            color: #e1e5e9;
            margin-bottom: 6px;
        }

        .device-meta {
            font-size: 14px;
            color: #9ca3af;
        }

        .device-status {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            margin-right: 12px;
        }

        .device-chevron {
            color: var(--text-secondary);
            transition: transform 0.2s ease;
        }

        .device-chevron.expanded {
            transform: rotate(90deg);
        }

        /* Command Groups */
        .command-groups {
            display: none;
            background: #111827;
            border-top: 1px solid #374151;
        }

        .device-card.expanded .command-groups {
            display: block;
        }

        .command-group {
            border-bottom: 1px solid #1f2937;
        }

        .command-group:last-child {
            border-bottom: none;
        }

        .group-header {
            padding: 20px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            cursor: pointer;
            transition: background-color 0.2s ease;
        }

        .group-header:hover {
            background: #1f2937;
        }

        .group-chevron {
            margin-right: 8px;
            color: var(--text-secondary);
            transition: transform 0.2s ease;
        }

        .group-chevron.expanded {
            transform: rotate(90deg);
        }

        .group-name {
            font-weight: 500;
            color: var(--text-primary);
        }

        .group-count {
            margin-left: auto;
            background: var(--surface-light);
            color: var(--text-secondary);
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
        }

        /* Commands */
        .commands-list {
            display: none;
            background: #0d1117;
            padding: 16px 0;
        }

        .command-group.expanded .commands-list {
            display: block;
        }

        .command-item {
            padding: 16px 24px 16px 80px;
            display: flex;
            align-items: center;
            gap: 16px;
            transition: background-color 0.2s ease;
            min-height: 56px;
        }

        .command-item:hover {
            background: #1f2937;
        }

        .command-item:hover .command-actions {
            opacity: 1;
        }

        .command-info {
            flex: 1;
            display: flex;
            align-items: center;
        }

        .command-name {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            color: #e1e5e9;
            flex: 1;
        }

        .command-type {
            background: #374151;
            color: #9ca3af;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 11px;
            text-transform: uppercase;
            font-weight: 500;
        }

        .command-type.rf {
            background: #3b82f6;
            color: white;
        }

        .command-type.ir {
            background: #f59e0b;
            color: white;
        }

        .command-actions {
            display: flex;
            gap: 8px;
            opacity: 0;
            transition: opacity 0.2s ease;
        }

        .action-btn {
            padding: 4px 8px;
            border: none;
            border-radius: 4px;
            font-size: 0.75rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .action-btn.test {
            background: #3b82f6;
            color: white;
        }

        .action-btn.relearn {
            background: var(--warning);
            color: white;
        }

        .action-btn.delete {
            background: var(--danger);
            color: white;
        }

        .action-btn:hover {
            transform: translateY(-1px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            <div class="log-area" id="logArea">
                <div>🚀 Broadlink Manager initialized...</div>
            </div>
        </div>
    </div>

    <script>
        let commands = [];
        let learnedData = {};
        let currentMode = 'filter';
        let currentDevice = '';
        let currentArea = '';
        let currentDeviceName = '';

        // Helper function to get correct API URL for both direct and ingress access
        function getApiUrl(endpoint) {
            const baseUrl = window.location.pathname.endsWith('/') ? 
                window.location.pathname.slice(0, -1) : window.location.pathname;
            return baseUrl.includes('/api/hassio_ingress/') ? 
                `${baseUrl}${endpoint}` : endpoint;
        }

        // Initialize the application  
        document.addEventListener('DOMContentLoaded', function() {
            loadAreas();
            loadBroadlinkDevices();
            loadLearnedData();
            setMode('filter'); // Start in filter mode
            log('Application initialized - Filter mode active');
        });

        function setMode(mode) {
            currentMode = mode;
            
            const filterBtn = document.getElementById('filterModeBtn');
            const addBtn = document.getElementById('addModeBtn');
            const modeDesc = document.getElementById('modeDescription');
            const addModeFields = document.getElementById('addModeFields');
            const filterModeControls = document.getElementById('filterModeControls');
            const addModeControls = document.getElementById('addModeControls');
            
            if (mode === 'filter') {
                filterBtn.className = 'btn btn-primary';
                addBtn.className = 'btn btn-secondary';
                modeDesc.textContent = 'Filter existing commands by area and device';
                addModeFields.style.display = 'none';
                filterModeControls.style.display = 'flex';
                addModeControls.style.display = 'none';
                
                // Reset dropdowns to show all
                document.getElementById('areaName').value = '';
                document.getElementById('deviceName').value = '';
                
                // Load and display all commands
                loadCommands();
            } else {
                filterBtn.className = 'btn btn-secondary';
                addBtn.className = 'btn btn-primary';
                modeDesc.textContent = 'Add new commands by selecting area, device, and command details';
                addModeFields.style.display = 'block';
                filterModeControls.style.display = 'none';
                addModeControls.style.display = 'flex';
                
                // Clear command list in add mode
                document.getElementById('commandList').innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-secondary);">Select area, device, and command details above, then click Learn Command</div>';
            }
            
            log(`Switched to ${mode} mode`);
        }

        async function loadAreas() {
            try {
                const response = await fetch(getApiUrl('/api/areas'));
                const areas = await response.json();
                
                const select = document.getElementById('areaName');
                select.innerHTML = '<option value="">All Areas</option>';
                
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

        async function loadLearnedData() {
            try {
                const response = await fetch(getApiUrl('/api/learned-devices'));
                learnedData = await response.json();
                
                console.log('Loaded learned data:', learnedData);
                log(`Loaded learned data: ${learnedData.commands.length} commands from ${Object.keys(learnedData.devices).length} devices`);
                
                // Update the device count in header
                updateHeaderStats();
                
                // Render the new hierarchical view
                renderBroadlinkDevices();
                
            } catch (error) {
                console.error('Error loading learned data:', error);
                log(`Error loading learned data: ${error.message}`, 'error');
            }
        }

        function updateHeaderStats() {
            try {
                const deviceCount = Object.keys(learnedData.devices || {}).length;
                const commandCount = (learnedData.commands || []).length;
                const headerStats = document.querySelector('.container > div:first-child p');
                if (headerStats) {
                    headerStats.textContent = `${deviceCount} devices • ${commandCount} entities`;
                } else {
                    console.warn('Header stats element not found');
                }
            } catch (error) {
                console.error('Error updating header stats:', error);
            }
        }

        function updateAreaDropdown() {
            const select = document.getElementById('areaName');
            const currentValue = select.value;
            
            if (currentMode === 'filter') {
                // In filter mode, only show areas with learned commands
                select.innerHTML = '<option value="">All Areas</option>';
                
                Object.values(learnedData.areas).forEach(areaName => {
                    const areaId = Object.keys(learnedData.areas).find(key => learnedData.areas[key] === areaName);
                    const option = document.createElement('option');
                    option.value = areaId;
                    option.textContent = areaName;
                    select.appendChild(option);
                });
            } else {
                // In add mode, show all available areas
                loadAreas();
            }
            
            // Restore selection if still valid
            if (currentValue && [...select.options].some(opt => opt.value === currentValue)) {
                select.value = currentValue;
            }
        }

        async function loadBroadlinkDevices() {
            try {
                const response = await fetch(getApiUrl('/api/devices'));
                const devices = await response.json();
                
                const select = document.getElementById('broadlinkDevice');
                select.innerHTML = '<option value="">Select a device...</option>';
                
                devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.entity_id;
                    option.textContent = device.name;
                    select.appendChild(option);
                });
                
                log(`Loaded ${devices.length} Broadlink devices`);
            } catch (error) {
                log(`Error loading devices: ${error.message}`, 'error');
            }
        }

        function updateDeviceDropdown() {
            const areaSelect = document.getElementById('areaName');
            const deviceSelect = document.getElementById('deviceName');
            const broadlinkSelect = document.getElementById('broadlinkDevice');
            const selectedArea = areaSelect.value;
            
            if (currentMode === 'filter') {
                deviceSelect.innerHTML = '<option value="">All Devices</option>';
                
                // Only show devices if area or broadlink device is selected
                if (selectedArea || broadlinkSelect.value) {
                    // Filter devices based on selected area
                    const relevantDevices = Object.values(learnedData.devices).filter(device => 
                        !selectedArea || device.area_id === selectedArea
                    );
                    
                    relevantDevices.forEach(device => {
                        const option = document.createElement('option');
                        option.value = device.full_name;
                        option.textContent = device.device_part;
                        deviceSelect.appendChild(option);
                    });
                }
            } else {
                // In add mode, require area and broadlink device selection
                if (!selectedArea || !broadlinkSelect.value) {
                    deviceSelect.innerHTML = '<option value="">Select area and Broadlink device first</option>';
                    deviceSelect.disabled = true;
                } else {
                    deviceSelect.innerHTML = '<option value="">Select or enter device name</option>';
                    deviceSelect.disabled = false;
                }
            }
        }

        async function loadCommands() {
            if (currentMode !== 'filter') return;
            
            const areaFilter = document.getElementById('areaName').value;
            const deviceFilter = document.getElementById('deviceName').value;
            
            // Filter commands based on selections
            let filteredCommands = learnedData.commands;
            
            if (areaFilter) {
                filteredCommands = filteredCommands.filter(cmd => cmd.area_id === areaFilter);
            }
            
            if (deviceFilter) {
                filteredCommands = filteredCommands.filter(cmd => cmd.device_name === deviceFilter);
            }
            
            updateCommandList(filteredCommands);
            log(`Showing ${filteredCommands.length} commands (filtered from ${learnedData.commands.length} total)`);
        }

        function renderBroadlinkDevices() {
            const container = document.getElementById('broadlinkDevices');
            
            if (!container) {
                console.error('broadlinkDevices container not found');
                return;
            }
            
            if (!learnedData || !learnedData.commands || learnedData.commands.length === 0) {
                container.innerHTML = '<div style="padding: 40px; text-align: center; color: var(--text-secondary);">No learned commands found</div>';
                return;
            }
            
            // Group commands by Broadlink device (area) and then by device type
            const broadlinkDevices = {};
            
            learnedData.commands.forEach(command => {
                const areaName = command.area_name || 'Unknown Area';
                const devicePart = command.device_part;
                
                // Create Broadlink device entry if it doesn't exist
                if (!broadlinkDevices[areaName]) {
                    broadlinkDevices[areaName] = {
                        deviceGroups: {},
                        totalCommands: 0
                    };
                }
                
                // Group by device type within the Broadlink device
                if (!broadlinkDevices[areaName].deviceGroups[devicePart]) {
                    broadlinkDevices[areaName].deviceGroups[devicePart] = [];
                }
                
                broadlinkDevices[areaName].deviceGroups[devicePart].push(command);
                broadlinkDevices[areaName].totalCommands++;
            });
            
            container.innerHTML = '';
            
            // Create device cards for each Broadlink device
            Object.keys(broadlinkDevices).forEach(areaName => {
                const deviceData = broadlinkDevices[areaName];
                const deviceCard = document.createElement('div');
                deviceCard.className = 'device-card';
                
                const deviceCount = Object.keys(deviceData.deviceGroups).length;
                const safeAreaName = areaName.replace(/[^a-zA-Z0-9]/g, '_');
                
                deviceCard.innerHTML = `
                    <div class="device-header" onclick="toggleDevice(this.closest('.device-card'))">
                        <div class="device-icon">📡</div>
                        <div class="device-info">
                            <div class="device-name">${areaName} RM4 Pro</div>
                            <div class="device-meta">Broadlink • ${areaName} • ${deviceCount} entities</div>
                        </div>
                        <div class="device-status">
                            <div style="width: 10px; height: 10px; border-radius: 50%; background: #10b981;"></div>
                        </div>
                        <div class="expand-icon">▶</div>
                    </div>
                    <div class="command-groups" id="groups-${safeAreaName}" style="display: none;">
                        ${Object.keys(deviceData.deviceGroups).map(devicePart => {
                            const commands = deviceData.deviceGroups[devicePart];
                            const safeDevicePart = devicePart.replace(/[^a-zA-Z0-9]/g, '_');
                            return `
                                <div class="command-group">
                                    <div class="group-header" onclick="toggleGroup('${safeAreaName}', '${safeDevicePart}')">
                                        <div class="group-chevron" id="group-chevron-${safeAreaName}-${safeDevicePart}">▶</div>
                                        <div class="group-name">${devicePart}</div>
                                        <div class="group-count">${commands.length}</div>
                                    </div>
                                    <div class="commands-list" id="commands-${safeAreaName}-${safeDevicePart}" style="display: none;">
                                        ${commands.map(command => `
                                            <div class="command-item">
                                                <div class="command-name">${command.command}</div>
                                                <div class="command-type ${command.command_type}">${command.command_type.toUpperCase()}</div>
                                                <div class="command-actions">
                                                    <button class="btn btn-primary" onclick="testCommand('${command.device_name}', '${command.command}')">▶ Test</button>
                                                    <button class="btn btn-secondary">🔄 Re-learn</button>
                                                    <button class="btn btn-danger">🗑️</button>
                                                </div>
                                            </div>
                                        `).join('')}
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                `;
                
                container.appendChild(deviceCard);
            });
        }

        function toggleDevice(deviceElement) {
            deviceElement.classList.toggle('expanded');
            const deviceName = deviceElement.querySelector('.device-name').textContent;
            console.log(`Device ${deviceElement.classList.contains('expanded') ? 'expanded' : 'collapsed'}: ${deviceName}`);
        }

        function toggleGroup(safeAreaName, safeDevicePart) {
            const commands = document.getElementById(`commands-${safeAreaName}-${safeDevicePart}`);
            const chevron = document.getElementById(`group-chevron-${safeAreaName}-${safeDevicePart}`);
            
            if (commands && chevron) {
                if (commands.style.display === 'none') {
                    commands.style.display = 'block';
                    chevron.classList.add('expanded');
                } else {
                    commands.style.display = 'none';
                    chevron.classList.remove('expanded');
                }
            }
        }

        async function learnNewCommand() {
            const deviceEntityId = document.getElementById('broadlinkDevice').value;
            const areaId = document.getElementById('areaName').value;
            const newDeviceName = document.getElementById('newDeviceName').value.trim();
            const newCommandName = document.getElementById('newCommandName').value.trim();
            const commandType = document.getElementById('commandType').value;
            
            if (!deviceEntityId) {
                showAlert('Please select a Broadlink device', 'error');
                return;
            }
            
            if (!areaId) {
                showAlert('Please select an area', 'error');
                return;
            }
            
            if (!newDeviceName) {
                showAlert('Please enter a device name', 'error');
                return;
            }
            
            if (!newCommandName) {
                showAlert('Please enter a command name', 'error');
                return;
            }
            
            // Create the full device name in the format: {area}_{device}
            const fullDeviceName = `${areaId}_${newDeviceName}`;
            
            try {
                const response = await fetch(getApiUrl('/api/learn'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity_id: deviceEntityId,
                        device: fullDeviceName,
                        command: newCommandName,
                        command_type: commandType
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    log(`Learning started: ${fullDeviceName}_${newCommandName}`);
                    showAlert('✅ Learning started! Check Home Assistant notifications (🔔) for instructions.', 'success');
                    
                    // Clear the input fields
                    document.getElementById('newDeviceName').value = '';
                    document.getElementById('newCommandName').value = '';
                } else {
                    log(`Failed to start learning: ${result.error}`, 'error');
                    showAlert(`Failed to start learning: ${result.error}`, 'error');
                }
            } catch (error) {
                log(`Error starting learning: ${error.message}`, 'error');
                showAlert(`Error starting learning: ${error.message}`, 'error');
            }
        }

        async function testCommand(deviceName, commandName) {
            const deviceEntityId = document.getElementById('broadlinkDevice').value;
            
            if (!deviceEntityId) {
                showAlert('Please select a Broadlink device', 'error');
                return;
            }
            
            try {
                const response = await fetch(getApiUrl('/api/send'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity_id: deviceEntityId,
                        device: deviceName,
                        command: commandName
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    log(`Successfully sent: ${deviceName}_${commandName}`);
                    showAlert(`Command "${commandName}" sent successfully!`, 'success');
                } else {
                    log(`Failed to send: ${deviceName}_${commandName} - ${result.error}`, 'error');
                    showAlert(`Failed to send command: ${result.error}`, 'error');
                }
            } catch (error) {
                log(`Error sending command: ${error.message}`, 'error');
                showAlert(`Error sending command: ${error.message}`, 'error');
            }
        }

        async function deleteCommand(deviceName, commandName) {
            if (!confirm(`Are you sure you want to delete the command "${commandName}" from device "${deviceName}"?`)) {
                return;
            }
            
            const deviceEntityId = document.getElementById('broadlinkDevice').value;
            
            if (!deviceEntityId) {
                showAlert('Please select a Broadlink device', 'error');
                return;
            }
            
            try {
                const response = await fetch(getApiUrl('/api/delete'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity_id: deviceEntityId,
                        device: deviceName,
                        command: commandName
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    log(`Successfully deleted: ${deviceName}_${commandName}`);
                    showAlert(`Command "${commandName}" deleted successfully!`, 'success');
                    
                    // Reload learned data and refresh the command list
                    await loadLearnedData();
                } else {
                    log(`Failed to delete: ${deviceName}_${commandName} - ${result.error}`, 'error');
                    showAlert(`Failed to delete command: ${result.error}`, 'error');
                }
            } catch (error) {
                log(`Error deleting command: ${error.message}`, 'error');
                showAlert(`Error deleting command: ${error.message}`, 'error');
            }
        }

        // Event listeners for filtering
        document.getElementById('areaName').addEventListener('change', function() {
            currentArea = this.value;
            updateDeviceDropdown();
            loadCommands();
        });

        document.getElementById('deviceName').addEventListener('change', function() {
            currentDeviceName = this.value;
            loadCommands();
        });

        document.getElementById('broadlinkDevice').addEventListener('change', function() {
            currentDevice = this.value;
            updateDeviceDropdown();
        });

        async function refreshData() {
            log('Refreshing data...');
            await loadLearnedData();
            log('Data refreshed');
        }

        function detectCommandType(commandCode) {
            // If command starts with "sc", it's RF, otherwise IR
            return commandCode && commandCode.startsWith('sc') ? 'rf' : 'ir';
        }

        async function relearnCommand(deviceName, commandName) {
            if (!confirm(`Re-learn the command "${commandName}" from device "${deviceName}"?`)) {
                return;
            }
            
            // First delete the existing command
            try {
                const deleteResponse = await fetch(getApiUrl('/api/delete'), {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        entity_id: currentDevice || document.getElementById('broadlinkDevice').value,
                        device: deviceName,
                        command: commandName
                    })
                });
                
                if (deleteResponse.ok) {
                    // Then start learning the new command
                    const learnResponse = await fetch(getApiUrl('/api/learn'), {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            entity_id: currentDevice || document.getElementById('broadlinkDevice').value,
                            device: deviceName,
                            command: commandName,
                            command_type: 'ir' // Default to IR, will be detected after learning
                        })
                    });
                    
                    const result = await learnResponse.json();
                    
                    if (result.success) {
                        log(`Re-learning started: ${deviceName}_${commandName}`);
                        showAlert('✅ Re-learning started! Check Home Assistant notifications (🔔) for instructions.', 'success');
                        await loadLearnedData();
                    } else {
                        log(`Failed to start re-learning: ${result.error}`, 'error');
                        showAlert(`Failed to start re-learning: ${result.error}`, 'error');
                    }
                }
            } catch (error) {
                log(`Error re-learning command: ${error.message}`, 'error');
                showAlert(`Error re-learning command: ${error.message}`, 'error');
            }
        }

        function showAddDialog() {
            // TODO: Implement add dialog
            showAlert('Add dialog coming soon!', 'info');
        }

        function renderTestData() {
            const container = document.getElementById('broadlinkDevices');
            if (!container) return;
            
            // Test data matching your mockup
            container.innerHTML = `
                <div class="device-card">
                    <div class="device-header" onclick="toggleDevice('tonys_office')">
                        <div class="device-icon">📡</div>
                        <div class="device-info">
                            <div class="device-name">Tony's Office RM4 Pro</div>
                            <div class="device-details">Broadlink • Tony's Office • 9 entities</div>
                        </div>
                        <div class="device-status"></div>
                        <div class="device-chevron" id="chevron-tonys_office">▶</div>
                    </div>
                    <div class="command-groups" id="groups-tonys_office" style="display: none;">
                        <div class="command-group">
                            <div class="group-header" onclick="toggleGroup('tonys_office', 'ceiling_fan')">
                                <div class="group-chevron" id="group-chevron-tonys_office-ceiling_fan">▶</div>
                                <div class="group-name">ceiling_fan</div>
                                <div class="group-count">5</div>
                            </div>
                            <div class="commands-list" id="commands-tonys_office-ceiling_fan" style="display: none;">
                                <div class="command-row">
                                    <div class="command-info">
                                        <span class="command-name">fan_off</span>
                                        <span class="command-type-badge command-type-rf">RF</span>
                                    </div>
                                    <div class="command-actions">
                                        <button class="action-btn test">▶ Test</button>
                                        <button class="action-btn relearn">🔄 Re-learn</button>
                                        <button class="action-btn delete">🗑</button>
                                    </div>
                                </div>
                                <div class="command-row">
                                    <div class="command-info">
                                        <span class="command-name">fan_speed_1</span>
                                        <span class="command-type-badge command-type-rf">RF</span>
                                    </div>
                                    <div class="command-actions">
                                        <button class="action-btn test">▶ Test</button>
                                        <button class="action-btn relearn">🔄 Re-learn</button>
                                        <button class="action-btn delete">🗑</button>
                                    </div>
                                </div>
                                <div class="command-row">
                                    <div class="command-info">
                                        <span class="command-name">light_on</span>
                                        <span class="command-type-badge command-type-ir">IR</span>
                                    </div>
                                    <div class="command-actions">
                                        <button class="action-btn test">▶ Test</button>
                                        <button class="action-btn relearn">🔄 Re-learn</button>
                                        <button class="action-btn delete">🗑</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="command-group">
                            <div class="group-header" onclick="toggleGroup('tonys_office', 'workbench_lamp')">
                                <div class="group-chevron" id="group-chevron-tonys_office-workbench_lamp">▶</div>
                                <div class="group-name">workbench_lamp</div>
                                <div class="group-count">1</div>
                            </div>
                            <div class="commands-list" id="commands-tonys_office-workbench_lamp" style="display: none;">
                                <div class="command-row">
                                    <div class="command-info">
                                        <span class="command-name">toggle</span>
                                        <span class="command-type-badge command-type-ir">IR</span>
                                    </div>
                                    <div class="command-actions">
                                        <button class="action-btn test">▶ Test</button>
                                        <button class="action-btn relearn">🔄 Re-learn</button>
                                        <button class="action-btn delete">🗑</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="device-card">
                    <div class="device-header" onclick="toggleDevice('master_bedroom')">
                        <div class="device-icon">📡</div>
                        <div class="device-info">
                            <div class="device-name">Master Bedroom RM4 Pro</div>
                            <div class="device-details">Broadlink • Master Bedroom • 6 entities</div>
                        </div>
                        <div class="device-status"></div>
                        <div class="device-chevron" id="chevron-master_bedroom">▶</div>
                    </div>
                    <div class="command-groups" id="groups-master_bedroom" style="display: none;">
                        <!-- Master bedroom commands would go here -->
                    </div>
                </div>
            `;
            
            log('🎨 Test UI rendered - try clicking on device headers to expand');
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

        // Initialize the application
        document.addEventListener('DOMContentLoaded', async function() {
            log('🚀 Broadlink Manager initialized...');
            
            // Test if container exists
            const container = document.getElementById('broadlinkDevices');
            if (container) {
                log('✅ broadlinkDevices container found');
            } else {
                log('❌ broadlinkDevices container NOT found', 'error');
            }
            
            try {
                await loadLearnedData();
                log('✅ Initial data loaded successfully');
            } catch (error) {
                log(`❌ Failed to load initial data: ${error.message}`, 'error');
                
                // Fallback: render with test data to show UI structure
                log('🔧 Rendering with test data for debugging');
                renderTestData();
            }
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
