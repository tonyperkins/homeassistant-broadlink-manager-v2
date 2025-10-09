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

from storage_manager import StorageManager
from entity_detector import EntityDetector
from entity_generator import EntityGenerator
from area_manager import AreaManager

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
        
        # Initialize entity management components
        self.storage_manager = StorageManager()
        self.entity_detector = EntityDetector()
        self.area_manager = AreaManager(self.ha_url, self.ha_token)
        
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
        
        @self.app.route('/api/theme')
        def get_theme():
            """Get current Home Assistant theme information"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                theme_info = loop.run_until_complete(self._get_ha_theme())
                loop.close()
                return jsonify(theme_info)
            except Exception as e:
                logger.error(f"Error getting theme: {e}")
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
                        # Handle both string and list command codes
                        if isinstance(command_code, list):
                            # If it's a list, check the first element
                            command_type = 'rf' if (command_code and isinstance(command_code[0], str) and command_code[0].startswith('sc')) else 'ir'
                        elif isinstance(command_code, str):
                            command_type = 'rf' if command_code.startswith('sc') else 'ir'
                        else:
                            command_type = 'ir'  # Default to IR if unknown type
                        
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
        
        # Entity Management Routes
        
        @self.app.route('/api/entities')
        def get_entities():
            """Get all configured entities"""
            try:
                entities = self.storage_manager.get_all_entities()
                stats = self.storage_manager.get_stats()
                return jsonify({
                    'entities': entities,
                    'stats': stats
                })
            except Exception as e:
                logger.error(f"Error getting entities: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/<entity_id>')
        def get_entity(entity_id):
            """Get a specific entity"""
            try:
                entity = self.storage_manager.get_entity(entity_id)
                if entity:
                    return jsonify(entity)
                return jsonify({"error": "Entity not found"}), 404
            except Exception as e:
                logger.error(f"Error getting entity: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities', methods=['POST'])
        def save_entity():
            """Save or update an entity"""
            try:
                data = request.get_json()
                entity_id = data.get('entity_id')
                entity_data = data.get('entity_data')
                
                if not entity_id or not entity_data:
                    return jsonify({"error": "Missing entity_id or entity_data"}), 400
                
                self.storage_manager.save_entity(entity_id, entity_data)
                return jsonify({
                    'success': True,
                    'message': f'Entity {entity_id} saved successfully',
                    'entity_id': entity_id
                })
            except Exception as e:
                logger.error(f"Error saving entity: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/<entity_id>', methods=['DELETE'])
        def delete_entity(entity_id):
            """Delete an entity"""
            try:
                success = self.storage_manager.delete_entity(entity_id)
                if success:
                    return jsonify({
                        'success': True,
                        'message': f'Entity {entity_id} deleted successfully'
                    })
                return jsonify({"error": "Entity not found"}), 404
            except Exception as e:
                logger.error(f"Error deleting entity: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/detect', methods=['POST'])
        def detect_entities():
            """Auto-detect entities from commands"""
            try:
                data = request.get_json()
                device_name = data.get('device_name')
                commands = data.get('commands')
                area_name = data.get('area_name')
                
                if not device_name or not commands:
                    return jsonify({"error": "Missing device_name or commands"}), 400
                
                detected = self.entity_detector.group_commands_by_entity(device_name, commands, area_name)
                return jsonify({
                    'success': True,
                    'detected_entities': detected,
                    'count': len(detected)
                })
            except Exception as e:
                logger.error(f"Error detecting entities: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/generate', methods=['POST'])
        def generate_entities():
            """Generate YAML entity files"""
            try:
                data = request.get_json()
                device_id = data.get('device_id')
                
                if not device_id:
                    return jsonify({"error": "Missing device_id"}), 400
                
                # Get all Broadlink commands
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                broadlink_commands = loop.run_until_complete(self._get_all_broadlink_commands())
                loop.close()
                
                # Generate entities
                generator = EntityGenerator(self.storage_manager, device_id)
                result = generator.generate_all(broadlink_commands)
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Error generating entities: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/types')
        def get_entity_types():
            """Get supported entity types and their command roles"""
            try:
                types = self.entity_detector.get_entity_types()
                roles = {}
                for entity_type in types:
                    roles[entity_type] = self.entity_detector.get_command_roles_for_type(entity_type)
                
                return jsonify({
                    'types': types,
                    'roles': roles
                })
            except Exception as e:
                logger.error(f"Error getting entity types: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/reload-config', methods=['POST'])
        def reload_config():
            """Reload Home Assistant configuration to pick up new entities"""
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                success = loop.run_until_complete(self.area_manager.reload_config())
                loop.close()
                
                if success:
                    return jsonify({
                        "success": True,
                        "message": "Configuration reloaded successfully"
                    })
                else:
                    return jsonify({
                        "success": False,
                        "message": "Configuration reload may have failed"
                    })
                    
            except Exception as e:
                logger.error(f"Error reloading config: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/entities/assign-areas', methods=['POST'])
        def assign_areas():
            """Assign entities to areas automatically"""
            try:
                # Get all entities from metadata
                entities = self.storage_manager.get_all_entities()
                
                if not entities:
                    return jsonify({
                        "success": False,
                        "message": "No entities found to assign"
                    })
                
                # Assign areas asynchronously
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                results = loop.run_until_complete(self.area_manager.assign_entities_to_areas(entities))
                loop.close()
                
                return jsonify({
                    "success": True,
                    "message": f"Assigned {results['assigned']} entities to areas",
                    "results": results
                })
                
            except Exception as e:
                logger.error(f"Error assigning areas: {e}")
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
                                    
                                    entity_id = entity.get('entity_id')
                                    
                                    # Get device status
                                    status = await self._get_device_status(entity_id)
                                    
                                    broadlink_devices.append({
                                        'entity_id': entity_id,
                                        'name': device.get('name', entity_id),
                                        'device_id': device_id,
                                        'unique_id': entity.get('unique_id'),
                                        'area_id': area_id,
                                        'area_name': area_name,
                                        'status': status
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
    
    async def _get_device_status(self, entity_id: str) -> dict:
        """Determine the actual status of a Broadlink device"""
        try:
            # Get current entity state from Home Assistant
            entity_state = await self._make_ha_request('GET', f'states/{entity_id}')
            
            if not entity_state:
                return {
                    'status': 'unknown',
                    'label': 'Unknown',
                    'color': '#6b7280',  # Gray
                    'method': 'no_response'
                }
            
            state = entity_state.get('state', 'unknown')
            attributes = entity_state.get('attributes', {})
            
            # Primary: Check Home Assistant entity state
            if state == 'on':
                return {
                    'status': 'online',
                    'label': 'Online',
                    'color': '#10b981',  # Green
                    'method': 'entity_state'
                }
            elif state == 'off':
                return {
                    'status': 'idle',
                    'label': 'Idle', 
                    'color': '#f59e0b',  # Yellow/Orange
                    'method': 'entity_state'
                }
            elif state == 'unavailable':
                return {
                    'status': 'offline',
                    'label': 'Offline',
                    'color': '#ef4444',  # Red
                    'method': 'entity_unavailable'
                }
            else:
                return {
                    'status': 'unknown',
                    'label': 'Unknown',
                    'color': '#6b7280',  # Gray
                    'method': 'unknown_state'
                }
                
        except Exception as e:
            logger.error(f"Error determining device status for {entity_id}: {e}")
            return {
                'status': 'error',
                'label': 'Error',
                'color': '#ef4444',  # Red
                'method': 'error'
            }
    
    async def _get_ha_theme(self) -> dict:
        """Get current Home Assistant theme from storage files or API"""
        try:
            # First try to get theme from HA API
            try:
                url = f"{self.ha_url}/api/config"
                headers = {
                    'Authorization': f'Bearer {self.ha_token}',
                    'Content-Type': 'application/json'
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            config = await response.json()
                            theme_name = config.get('theme', 'default')
                            logger.info(f"Got theme from HA API config: {theme_name}")
                            
                            # Now try to get the actual theme colors from frontend API
                            # Try multiple endpoints to get theme data
                            theme_colors = None
                            
                            # Try /api/frontend/themes first
                            try:
                                frontend_themes_url = f"{self.ha_url}/api/frontend/themes"
                                logger.info(f"Trying frontend themes API: {frontend_themes_url}")
                                async with session.get(frontend_themes_url, headers=headers) as themes_response:
                                    logger.info(f"Frontend themes API response status: {themes_response.status}")
                                    if themes_response.status == 200:
                                        themes_data = await themes_response.json()
                                        logger.info(f"Frontend themes data keys: {list(themes_data.keys())}")
                                        
                                        # Check different possible structures
                                        if 'themes' in themes_data and theme_name in themes_data['themes']:
                                            theme_colors = themes_data['themes'][theme_name]
                                            logger.info(f"Found theme '{theme_name}' in frontend API")
                                        elif theme_name in themes_data:
                                            theme_colors = themes_data[theme_name]
                                            logger.info(f"Found theme '{theme_name}' directly in frontend API")
                            except Exception as e:
                                logger.warning(f"Frontend themes API failed: {e}")
                            
                            # Try /api/themes as fallback
                            if not theme_colors:
                                try:
                                    themes_url = f"{self.ha_url}/api/themes"
                                    logger.info(f"Trying themes API: {themes_url}")
                                    async with session.get(themes_url, headers=headers) as themes_response:
                                        logger.info(f"Themes API response status: {themes_response.status}")
                                        if themes_response.status == 200:
                                            themes_data = await themes_response.json()
                                            logger.info(f"Themes data keys: {list(themes_data.keys())}")
                                            logger.info(f"Available themes: {list(themes_data.get('themes', {}).keys())}")
                                            
                                            if 'themes' in themes_data and theme_name in themes_data['themes']:
                                                theme_colors = themes_data['themes'][theme_name]
                                                logger.info(f"Found theme '{theme_name}' in themes API")
                                except Exception as e:
                                    logger.warning(f"Themes API failed: {e}")
                            
                            # If we found theme colors, return them
                            if theme_colors:
                                logger.info(f"Theme colors keys: {list(theme_colors.keys())}")
                                logger.info(f"Sample colors: primary={theme_colors.get('primary-color')}, background={theme_colors.get('primary-background-color')}")
                                
                                # Determine if dark theme
                                is_dark = 'dark' in theme_name.lower() or \
                                         theme_colors.get('dark-primary-color') is not None or \
                                         (theme_colors.get('primary-background-color', '#ffffff').startswith('#') and \
                                          theme_colors.get('primary-background-color', '#ffffff')[1:3] in ['00', '01', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '1a', '1b', '1c', '1d', '1e', '1f', '20'])
                                
                                return {
                                    'theme_name': theme_name,
                                    'colors': {
                                        'primary': theme_colors.get('primary-color', '#03a9f4'),
                                        'accent': theme_colors.get('accent-color', '#ff9800'),
                                        'background': theme_colors.get('primary-background-color', '#111111'),
                                        'surface': theme_colors.get('card-background-color', theme_colors.get('primary-background-color', '#1c1c1c')),
                                        'text_primary': theme_colors.get('primary-text-color', '#ffffff'),
                                        'text_secondary': theme_colors.get('secondary-text-color', '#9ca3af'),
                                        'border': theme_colors.get('divider-color', '#2c2c2c'),
                                        'success': theme_colors.get('success-color', '#4caf50'),
                                        'warning': theme_colors.get('warning-color', '#ff9800'),
                                        'error': theme_colors.get('error-color', '#f44336'),
                                        'info': theme_colors.get('info-color', '#2196f3')
                                    },
                                    'is_dark': is_dark
                                }
                            else:
                                logger.warning(f"Could not find theme colors for '{theme_name}' in any API endpoint")
            except Exception as e:
                logger.warning(f"Could not get theme from HA API: {e}")
            
            # Fallback: Read frontend storage to get theme configuration
            frontend_file = self.storage_path / "frontend.user_data"
            
            theme_name = 'default'
            theme_mode = 'dark'
            
            logger.info(f"Checking for frontend storage at: {frontend_file}")
            logger.info(f"Frontend file exists: {frontend_file.exists()}")
            
            # Try to get user's theme preference from frontend storage
            if frontend_file.exists():
                try:
                    async with aiofiles.open(frontend_file, 'r') as f:
                        content = await f.read()
                        frontend_data = json.loads(content)
                        
                        # Look for theme settings in user data
                        data = frontend_data.get('data', {})
                        logger.info(f"Frontend data keys: {list(data.keys())}")
                        
                        for user_id, user_data in data.items():
                            if isinstance(user_data, dict):
                                logger.info(f"User {user_id} data keys: {list(user_data.keys())}")
                                # Get theme from user preferences
                                if 'selectedTheme' in user_data:
                                    theme_name = user_data['selectedTheme']
                                    logger.info(f"Found selectedTheme: {theme_name}")
                                if 'selectedDarkTheme' in user_data:
                                    theme_mode = 'dark'
                                    logger.info(f"Found selectedDarkTheme")
                                elif 'selectedLightTheme' in user_data:
                                    theme_mode = 'light'
                                    logger.info(f"Found selectedLightTheme")
                                break
                        
                        logger.info(f"Found theme from frontend storage: {theme_name} ({theme_mode})")
                except Exception as e:
                    logger.warning(f"Could not read frontend storage: {e}")
            else:
                logger.warning(f"Frontend storage file not found at {frontend_file}")
            
            # Try to read theme definitions from themes storage
            themes_file = self.storage_path / "frontend.themes"
            theme_data = {}
            
            logger.info(f"Checking for themes storage at: {themes_file}")
            logger.info(f"Themes file exists: {themes_file.exists()}")
            
            if themes_file.exists():
                try:
                    async with aiofiles.open(themes_file, 'r') as f:
                        content = await f.read()
                        themes_storage = json.loads(content)
                        
                        # Get theme data
                        themes = themes_storage.get('data', {}).get('themes', {})
                        logger.info(f"Available themes in storage: {list(themes.keys())}")
                        
                        if theme_name in themes:
                            theme_data = themes[theme_name]
                            logger.info(f"Loaded theme data for: {theme_name}")
                            logger.info(f"Theme data keys: {list(theme_data.keys())}")
                        elif theme_name != 'default':
                            logger.warning(f"Theme {theme_name} not found in storage, using default")
                except Exception as e:
                    logger.warning(f"Could not read themes storage: {e}")
            else:
                logger.warning(f"Themes storage file not found at {themes_file}")
            
            # Extract common theme colors with fallbacks
            result = {
                'theme_name': theme_name,
                'colors': {
                    'primary': theme_data.get('primary-color', '#03a9f4'),
                    'accent': theme_data.get('accent-color', '#ff9800'),
                    'background': theme_data.get('primary-background-color', '#111111'),
                    'surface': theme_data.get('card-background-color', '#1c1c1c'),
                    'text_primary': theme_data.get('primary-text-color', '#ffffff'),
                    'text_secondary': theme_data.get('secondary-text-color', '#9ca3af'),
                    'border': theme_data.get('divider-color', '#2c2c2c'),
                    'success': theme_data.get('success-color', '#4caf50'),
                    'warning': theme_data.get('warning-color', '#ff9800'),
                    'error': theme_data.get('error-color', '#f44336'),
                    'info': theme_data.get('info-color', '#2196f3')
                },
                'is_dark': theme_mode == 'dark' or 'dark' in theme_name.lower()
            }
            
            logger.info(f"Returning theme: {result['theme_name']} with colors: {result['colors']}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting HA theme: {e}", exc_info=True)
            return self._get_default_theme()
    
    def _get_default_theme(self) -> dict:
        """Get default dark theme colors matching current design"""
        return {
            'theme_name': 'default_dark',
            'colors': {
                'primary': '#03a9f4',
                'accent': '#ff9800', 
                'background': '#111111',
                'surface': '#1c1c1c',
                'text_primary': '#ffffff',
                'text_secondary': '#9ca3af',
                'border': '#2c2c2c',
                'success': '#10b981',
                'warning': '#f59e0b',
                'error': '#ef4444',
                'info': '#3b82f6'
            },
            'is_dark': True
        }
    
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
    
    async def _get_all_broadlink_commands(self) -> Dict[str, Dict[str, str]]:
        """Get all Broadlink commands in simple format for entity generator"""
        try:
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))
            all_commands = {}
            
            for storage_file in storage_files:
                try:
                    async with aiofiles.open(storage_file, 'r') as f:
                        content = await f.read()
                        data = json.loads(content)
                        
                        # Extract device commands
                        for device_name, commands in data.get('data', {}).items():
                            if isinstance(commands, dict):
                                all_commands[device_name] = commands
                
                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue
            
            return all_commands
            
        except Exception as e:
            logger.error(f"Error getting Broadlink commands: {e}")
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
                logger.info(f"Services result type: {type(services_result)}")
                
                # Handle both dict and list formats
                if isinstance(services_result, dict):
                    remote_services = services_result.get('remote', {})
                elif isinstance(services_result, list):
                    # Find remote services in the list
                    remote_services = {}
                    for service_domain in services_result:
                        if isinstance(service_domain, dict) and service_domain.get('domain') == 'remote':
                            remote_services = service_domain.get('services', {})
                            break
                else:
                    remote_services = {}
                
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
                state = entity_state.get('state')
                logger.info(f"Entity {entity_id} state: {state}")
                logger.info(f"Entity attributes: {entity_state.get('attributes', {})}")
                
                # Check if device is available
                if state == 'unavailable':
                    logger.warning(f"Device {entity_id} is unavailable - learning may not work")
                    return {
                        'success': False, 
                        'error': f'Broadlink device is unavailable. Please check that the device is powered on and connected to your network.'
                    }
            
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
            
            # Add a timeout to prevent getting stuck
            service_payload['data']['timeout'] = 30
            
            logger.info(f"Calling learn_command service with payload: {service_payload}")
            
            # Use the correct HA service call format
            logger.info("Attempting service call to services/remote/learn_command with target/data format")
            result = await self._make_ha_request('POST', 'services/remote/learn_command', service_payload)
            logger.info(f"Learn command service result: {result}")
            
            # Check if we got a 400 error, which might mean the format is wrong
            if result is None:
                logger.info("Got None result (likely 400 error), trying legacy format...")
                
                # Try the old format as fallback
                legacy_payload = {
                    'entity_id': entity_id,
                    'device': device,
                    'command': command,
                    'timeout': 30
                }
                if command_type == 'rf':
                    legacy_payload['command_type'] = 'rf'
                
                logger.info(f"Trying legacy format: {legacy_payload}")
                result = await self._make_ha_request('POST', 'services/remote/learn_command', legacy_payload)
                logger.info(f"Legacy format result: {result}")
            
            # Check if the legacy format worked (empty array is actually success for learn_command)
            if result == []:
                logger.info("Legacy format returned empty array - this is normal for learn_command")
                return {
                    'success': True, 
                    'message': 'Learning process started. Check Home Assistant notifications (🔔) for instructions.',
                    'result': result
                }
            elif result is not None:
                logger.info("Learn command service called successfully")
                return {
                    'success': True, 
                    'message': 'Learning process started. Check Home Assistant notifications (🔔) for instructions.',
                    'result': result
                }
            else:
                logger.error("Learn command service failed - all attempts returned None")
                return {'success': False, 'error': 'Failed to start learning process - check that the Broadlink device is online and accessible'}
                
        except Exception as e:
            logger.error(f"Error learning command: {e}")
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
            
            # If we got a 400 error, try the legacy format
            if result is None:
                logger.info("Got None result for send_command, trying legacy format...")
                legacy_payload = {
                    'entity_id': entity_id,
                    'device': device,
                    'command': command
                }
                logger.info(f"Trying legacy send format: {legacy_payload}")
                result = await self._make_ha_request('POST', 'services/remote/send_command', legacy_payload)
                logger.info(f"Legacy send result: {result}")
            
            if result is not None:
                logger.info(f"Command sent successfully: {device}_{command}")
                return {'success': True, 'message': f'Command {command} sent successfully'}
            else:
                logger.error(f"Failed to send command: {device}_{command}")
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
            
            # If we got a 400 error, try the legacy format
            if result is None:
                logger.info("Got None result for delete_command, trying legacy format...")
                legacy_payload = {
                    'entity_id': entity_id,
                    'device': device,
                    'command': command
                }
                logger.info(f"Trying legacy delete format: {legacy_payload}")
                result = await self._make_ha_request('POST', 'services/remote/delete_command', legacy_payload)
                logger.info(f"Legacy delete result: {result}")
            
            if result is not None:
                logger.info(f"Command deleted successfully: {device}_{command}")
                return {'success': True, 'message': f'Command {command} deleted successfully'}
            else:
                logger.error(f"Failed to delete command: {device}_{command}")
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
