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
import aiofiles
import websockets

logger = logging.getLogger(__name__)

class BroadlinkWebServer:
    """Web server for Broadlink device management"""
    
    def __init__(self, port: int = 8099):
        self.port = port
        self.app = Flask(__name__, template_folder='templates')
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
            return render_template('index.html')
        
        @self.app.route('/api/areas')
        def get_areas():
            """Get Home Assistant areas from storage"""
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
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Get all detected Broadlink devices
                all_devices = loop.run_until_complete(self._get_broadlink_devices())
                
                # Get learned commands
                learned_commands = loop.run_until_complete(self._get_learned_commands())
                
                # Get areas
                areas = loop.run_until_complete(self._get_ha_areas())
                
                loop.close()
                
                return jsonify({
                    'detected_broadlink_devices': all_devices,
                    'learned_commands': learned_commands,
                    'areas': areas,
                    'summary': {
                        'total_detected_devices': len(all_devices),
                        'devices_with_commands': len(learned_commands),
                        'total_areas': len(areas)
                    }
                })
            except Exception as e:
                logger.error(f"Error getting debug data: {e}")
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
                        logger.error(f"POST API request failed with status {response.status}: {response_text}")
                        return None
    
    async def _get_ha_areas(self) -> List[Dict]:
        """Get Home Assistant areas from storage file"""
        try:
            areas_file = self.storage_path / "core.area_registry"
            
            if areas_file.exists():
                logger.info("Reading areas from storage file...")
                async with aiofiles.open(areas_file, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    areas = data.get('data', {}).get('areas', [])
                    logger.info(f"Found {len(areas)} areas from storage")
                    return areas
            else:
                logger.warning("Areas storage file not found")
                return []
            
        except Exception as e:
            logger.error(f"Error reading areas from storage: {e}")
            return []
    
    async def _get_broadlink_devices(self) -> List[Dict]:
        """Get Broadlink remote devices from storage files with area information"""
        try:
            # Read from storage files (primary method for add-on)
            logger.info("Reading Broadlink devices from storage files...")
            
            # Get area information first
            areas_data = await self._get_ha_areas()
            area_lookup = {area['id']: area['name'] for area in areas_data}
            
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
                            area_name = area_lookup.get(area_id, 'Unknown Area')
                            
                            logger.info(f"Found Broadlink device: {name} (ID: {device_id}, Area: {area_name})")
                            
                            # Find corresponding entities
                            for entity in entities:
                                if (entity.get('device_id') == device_id and 
                                    entity.get('entity_id', '').startswith('remote.')):
                                    
                                    broadlink_devices.append({
                                        'entity_id': entity.get('entity_id'),
                                        'name': device.get('name', entity.get('entity_id')),
                                        'device_id': device_id,
                                        'unique_id': entity.get('unique_id'),
                                        'area_id': area_id,
                                        'area_name': area_name
                                    })
                    except Exception as e:
                        logger.warning(f"Error processing device entry: {e}, device: {device}")
                        continue
                
                logger.info(f"Found {len(broadlink_devices)} Broadlink devices from storage")
                return broadlink_devices
            else:
                logger.warning("Device or entity registry storage files not found")
                return []

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
            area_lookup = {area['id']: area['name'] for area in areas_data}
            
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
            
            # First, let's check what services are available
            logger.info("Checking available services...")
            services_result = await self._make_ha_request('GET', 'services')
            if services_result:
                remote_services = services_result.get('remote', {})
                logger.info(f"Available remote services: {list(remote_services.keys()) if remote_services else 'None'}")
                
                # Check if learn_command exists
                if 'learn_command' in remote_services:
                    learn_service = remote_services['learn_command']
                    logger.info(f"learn_command service details: {learn_service}")
                else:
                    logger.warning("learn_command service not found in remote services!")
            
            # Also check the entity state and attributes
            entity_state = await self._make_ha_request('GET', f'states/{entity_id}')
            if entity_state:
                logger.info(f"Entity {entity_id} state: {entity_state.get('state')}")
                logger.info(f"Entity attributes: {entity_state.get('attributes', {})}")
            
            # Prepare the service call payload using the correct HA format
            # According to HA docs, the format should be:
            # target: { entity_id: ... }
            # data: { device: ..., command: ..., command_type: ... }
            service_payload = {
                'target': {
                    'entity_id': entity_id
                },
                'data': {
                    'device': device,
                    'command': command
                }
            }
            
            # Add command_type only for RF commands (IR is default)
            if command_type == 'rf':
                service_payload['data']['command_type'] = 'rf'
            
            logger.info(f"Calling learn_command service with payload: {service_payload}")
            
            # Use the correct HA service call format
            logger.info("Attempting service call to services/remote/learn_command with target/data format")
            result = await self._make_ha_request('POST', 'services/remote/learn_command', service_payload)
            logger.info(f"Learn command service result: {result}")
            
            # If that didn't work, try different service approaches
            if not result or result == []:
                logger.info("Empty result, trying alternative service calls...")
                
                # Try broadlink-specific service
                logger.info("Trying broadlink.learn service...")
                broadlink_result = await self._make_ha_request('POST', 'services/broadlink/learn', {
                    'host': entity_id.replace('remote.', '').replace('_', '.'),  # Convert entity_id to host format
                    'packet': f"{device}_{command}"
                })
                logger.info(f"Broadlink service result: {broadlink_result}")
                
                # Try the service without entity_id in the path
                logger.info("Trying service call without entity_id in path...")
                alt_result = await self._make_ha_request('POST', 'services/remote/learn_command', {
                    'entity_id': entity_id,
                    'device': device,
                    'command': command,
                    'command_type': command_type
                })
                logger.info(f"Alternative service result: {alt_result}")
                
                # Try calling it as a script or automation trigger
                logger.info("Trying to trigger learning via entity service call...")
                trigger_result = await self._make_ha_request('POST', f'services/remote/learn_command', {
                    'entity_id': entity_id,
                    'device': device,
                    'command': command,
                    'command_type': command_type
                })
                logger.info(f"Trigger result: {trigger_result}")
                
                # Check entity state after all attempts
                final_state = await self._make_ha_request('GET', f'states/{entity_id}')
                logger.info(f"Final entity state: {final_state}")
                
                result = broadlink_result or alt_result or trigger_result
            
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
    
    async def _send_command(self, data: Dict) -> Dict:
        """Send a learned command"""
        try:
            entity_id = data.get('entity_id')
            device = data.get('device')
            command = data.get('command')
            
            logger.info(f"SEND REQUEST DEBUG:")
            logger.info(f"  Raw data received: {data}")
            logger.info(f"  entity_id: '{entity_id}'")
            logger.info(f"  device: '{device}' (length: {len(device) if device else 'None'})")
            logger.info(f"  command: '{command}' (length: {len(command) if command else 'None'})")
            logger.info(f"Sending command: {device}_{command} to entity {entity_id}")
            
            # Use the correct HA service call format with target/data structure
            payload = {
                'target': {
                    'entity_id': entity_id
                },
                'data': {
                    'device': device,
                    'command': command
                }
            }
            
            result = await self._make_ha_request('POST', 'services/remote/send_command', payload)
            
            if result is not None:
                logger.info(f"Command sent successfully: {device}{command}")
                return {'success': True, 'message': f'Command {command} sent successfully'}
            else:
                logger.error(f"Failed to send command: {device}{command}")
                return {'success': False, 'error': 'Failed to send command'}
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _delete_command(self, data: Dict) -> Dict:
        """Delete a learned command"""
        try:
            entity_id = data.get('entity_id')
            device = data.get('device')
            command = data.get('command')
            
            logger.info(f"DELETE REQUEST DEBUG:")
            logger.info(f"  Raw data received: {data}")
            logger.info(f"  entity_id: '{entity_id}'")
            logger.info(f"  device: '{device}' (length: {len(device) if device else 'None'})")
            logger.info(f"  command: '{command}' (length: {len(command) if command else 'None'})")
            logger.info(f"Deleting command: {device}_{command} from entity {entity_id}")
            
            # Use the correct HA service call format with target/data structure
            service_payload = {
                'target': {
                    'entity_id': entity_id
                },
                'data': {
                    'device': device,
                    'command': command
                }
            }
            
            result = await self._make_ha_request('POST', 'services/remote/delete_command', service_payload)
            
            if result is not None:
                logger.info(f"Command deleted successfully: {device}{command}")
                return {'success': True, 'message': f'Command {command} deleted successfully'}
            else:
                logger.error(f"Failed to delete command: {device}{command}")
                return {'success': False, 'error': 'Failed to delete command'}
            
        except Exception as e:
            logger.error(f"Error deleting command: {e}")
            return {'success': False, 'error': str(e)}

    def run(self):
        """Run the Flask web server"""
        logger.info(f"Starting Broadlink Manager web server on port {self.port}")
        self.app.run(host='0.0.0.0', port=self.port, debug=False)


if __name__ == "__main__":
    server = BroadlinkWebServer()
    server.run()
