"""
Command API endpoints
"""

import logging
import asyncio
import json
from pathlib import Path
from flask import jsonify, request, current_app
from . import api_bp

logger = logging.getLogger(__name__)

def get_storage_manager():
    """Get storage manager from Flask app context"""
    return current_app.config.get('storage_manager')

def get_web_server():
    """Get web server instance from Flask app context"""
    return current_app.config.get('web_server')

async def verify_command_in_storage(web_server, device_name: str, command_name: str, max_retries: int = 10, delay: float = 1.0) -> bool:
    """
    Verify that a command exists in Broadlink storage by polling.
    
    Args:
        web_server: BroadlinkWebServer instance
        device_name: Device name (storage key)
        command_name: Command name to verify
        max_retries: Maximum number of retry attempts (default: 10)
        delay: Delay in seconds between retries (default: 1.0)
    """
    import asyncio
    
    try:
        for attempt in range(max_retries):
            # Get all Broadlink commands from storage
            all_commands = await web_server._get_all_broadlink_commands()
            
            # Check if the device has commands
            device_commands = all_commands.get(device_name, {})
            
            # Check if the specific command exists
            if command_name in device_commands:
                if attempt > 0:
                    logger.info(f"✅ Verified command '{command_name}' exists for device '{device_name}' (after {attempt + 1} attempts)")
                else:
                    logger.info(f"✅ Verified command '{command_name}' exists for device '{device_name}'")
                return True
            
            # Command not found yet, wait and retry
            if attempt < max_retries - 1:
                logger.debug(f"Command '{command_name}' not found yet, retrying in {delay}s... (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
        
        # All retries exhausted
        logger.warning(f"⚠️ Command '{command_name}' not found in storage for device '{device_name}' after {max_retries} attempts")
        return False
        
    except Exception as e:
        logger.error(f"Error verifying command: {e}")
        return False

@api_bp.route('/commands/learn', methods=['POST'])
def learn_command():
    """Start learning a new command (synchronous call to HA)"""
    try:
        data = request.json
        logger.info(f"Learn command request data: {data}")
        
        entity_id = data.get('entity_id')
        device = data.get('device')
        command = data.get('command')
        command_type = data.get('command_type', 'ir')
        device_id = data.get('device_id')  # For managed devices
        
        logger.info(f"Parsed: entity_id={entity_id}, device={device}, command={command}, type={command_type}, device_id={device_id}")
        
        # If device is not provided, try to derive it from device_id
        if not device and device_id:
            # For managed devices, use the device_id as the device name
            # Remove entity_type prefix if present (e.g., "switch.office_lamp" -> "office_lamp")
            device = device_id.split('.')[-1] if '.' in device_id else device_id
            logger.info(f"Derived device name from device_id: {device}")
        
        if not all([entity_id, device, command]):
            missing = []
            if not entity_id: missing.append('entity_id')
            if not device: missing.append('device (or device_id)')
            if not command: missing.append('command')
            
            error_msg = f'Missing required fields: {", ".join(missing)}'
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400
        
        # Update data with derived device name if it was derived
        if device and not data.get('device'):
            data['device'] = device
            logger.info(f"Updated data with derived device: {device}")
        
        # Get web server instance to use its _learn_command method
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        # Call the existing async learn_command method synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(web_server._learn_command(data))
        loop.close()
        
        # If HA API returned success, trust it - command will appear in storage eventually
        if result.get('success'):
            logger.info(f"✅ Learn command API call succeeded for '{command}' on device '{device}'")
            logger.info(f"ℹ️  Command will appear in storage after HA writes (may take 10-30 seconds)")
            result['message'] = f"✅ Command '{command}' learned successfully! (May take a moment to appear)"
            # Add placeholder code field for frontend compatibility
            # The actual code will be in storage after HA writes
            result['code'] = 'pending'  # Placeholder to satisfy frontend validation
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"Error learning command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/commands/test', methods=['POST'])
def test_command():
    """Test a learned command by sending it"""
    try:
        data = request.json
        logger.info(f"Test command request data: {data}")
        
        entity_id = data.get('entity_id')
        device = data.get('device')
        command = data.get('command')
        device_id = data.get('device_id')  # Entity ID to look up command mapping
        
        logger.info(f"Parsed - entity_id: {entity_id}, device: {device}, command: {command}, device_id: {device_id}")
        
        # If device is not provided, try to derive it from device_id
        if not device and device_id:
            # For managed devices, use the device_id as the device name
            # Remove entity_type prefix if present (e.g., "switch.office_lamp" -> "office_lamp")
            device = device_id.split('.')[-1] if '.' in device_id else device_id
            logger.info(f"Derived device name from device_id: {device}")
        
        if not all([entity_id, device, command]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: entity_id, device (or device_id), command'
            }), 400
        
        # Get storage to look up command mapping and device type
        storage = get_storage_manager()
        is_smartir = False
        if storage and device_id:
            # Try to get entity data - device_id might be with or without entity type prefix
            entity_data = storage.get_entity(device_id)
            
            # If not found and device_id doesn't have a dot, try to find it in all entities
            if not entity_data and '.' not in device_id:
                logger.info(f"Device ID '{device_id}' not found, searching all entities...")
                all_entities = storage.get_all_entities()
                for entity_id, data in all_entities.items():
                    if entity_id.endswith(f'.{device_id}') or entity_id == device_id:
                        entity_data = data
                        logger.info(f"Found entity: {entity_id}")
                        break
            
            if entity_data:
                is_smartir = entity_data.get('device_type') == 'smartir'
                logger.info(f"Device type detected: {'SmartIR' if is_smartir else 'Broadlink'}")
                commands_mapping = entity_data.get('commands', {})
                # Look up the actual Broadlink command name from the mapping
                actual_command = commands_mapping.get(command, command)
                logger.info(f"Command mapping: '{command}' -> '{actual_command}'")
                command = actual_command
            else:
                logger.warning(f"Entity data not found for device_id: {device_id}")
        
        # Get web server instance
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        # Call HA service to send the command
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Command as an array
        command_list = [command] if isinstance(command, str) else command
        
        # SmartIR uses standard remote.send_command format (no device parameter)
        # Broadlink uses custom format with device parameter
        if is_smartir:
            service_payload = {
                "entity_id": entity_id,
                "command": command_list
            }
            logger.info(f"Sending SmartIR payload to HA: {service_payload}")
        else:
            service_payload = {
                "entity_id": entity_id,
                "device": device,
                "command": command_list
            }
            logger.info(f"Sending Broadlink payload to HA: {service_payload}")
        
        result = loop.run_until_complete(
            web_server._make_ha_request("POST", "services/remote/send_command", service_payload)
        )
        loop.close()
        
        if result is not None or result == []:
            return jsonify({
                'success': True,
                'message': 'Command sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to send command'
            }), 400
    
    except Exception as e:
        logger.error(f"Error testing command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/commands/<device_id>/<command_name>', methods=['DELETE'])
def delete_command(device_id, command_name):
    """Delete a command from a device via HA API"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Get device entity
        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({'error': 'Device not found'}), 404
        
        # Check command exists
        commands = entity_data.get('commands', {})
        if command_name not in commands:
            return jsonify({'error': 'Command not found'}), 404
        
        # Get the actual Broadlink command name (might be mapped)
        # commands is like {"turn_off": "living_room_stereo_turn_off"}
        broadlink_command_name = commands[command_name]
        
        # Get the broadlink entity and device name
        broadlink_entity = entity_data.get('broadlink_entity', '')
        device_name = entity_data.get('device')
        if not device_name:
            # Fallback: extract from device_id
            device_name = device_id.split('.')[1] if '.' in device_id else device_id
        
        logger.info(f"Delete command request:")
        logger.info(f"  device_id: {device_id}")
        logger.info(f"  command_name (key): {command_name}")
        logger.info(f"  broadlink_command_name (value): {broadlink_command_name}")
        logger.info(f"  device_name: {device_name}")
        logger.info(f"  broadlink_entity: '{broadlink_entity}'")
        logger.info(f"  entity_data keys: {list(entity_data.keys())}")
        
        # If no broadlink_entity specified, find which Broadlink device owns this device's commands
        if not broadlink_entity:
            web_server = get_web_server()
            if web_server:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Use the new method to find the correct Broadlink entity
                broadlink_entity = loop.run_until_complete(web_server._find_broadlink_entity_for_device(device_name))
                loop.close()
                
                if broadlink_entity:
                    logger.info(f"Found Broadlink entity for device '{device_name}': {broadlink_entity}")
        
        if not broadlink_entity:
            logger.error(f"No broadlink_entity configured and could not auto-detect for device {device_id}")
            return jsonify({
                'success': False,
                'error': 'No Broadlink device configured for this device. Please edit the device and select a Broadlink device.'
            }), 400
        
        logger.info(f"Deleting command '{broadlink_command_name}' from device '{device_name}' using Broadlink entity '{broadlink_entity}'")
        
        # Call HA API to delete the command from Broadlink storage
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        delete_data = {
            'entity_id': broadlink_entity,
            'device': device_name,
            'command': broadlink_command_name  # Use the actual Broadlink command name
        }
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(web_server._delete_command(delete_data))
        loop.close()
        
        if result.get('success'):
            # Add to deletion cache to handle storage lag
            web_server._add_to_deletion_cache(device_name, broadlink_command_name)
            
            # Remove from metadata (trust that HA deleted it from Broadlink storage)
            del commands[command_name]
            entity_data['commands'] = commands
            storage.save_entity(device_id, entity_data)
            logger.info(f"✅ Command '{command_name}' deleted from metadata")
            
            return jsonify({
                'success': True,
                'message': f"Command '{command_name}' deleted successfully"
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to delete command')
            }), 400
    
    except Exception as e:
        logger.error(f"Error deleting command: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/commands/<device_id>', methods=['GET'])
def get_device_commands(device_id):
    """Get all commands for a device"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Get device entity
        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({'error': 'Device not found'}), 404
        
        commands = entity_data.get('commands', {})
        
        return jsonify({
            'commands': commands,
            'device_id': device_id
        })
    
    except Exception as e:
        logger.error(f"Error getting commands: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/commands/broadlink/<device_name>', methods=['GET'])
def get_broadlink_commands(device_name):
    """Get learned commands from Broadlink storage files"""
    try:
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        # Get all Broadlink commands
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        all_commands = loop.run_until_complete(web_server._get_all_broadlink_commands())
        loop.close()
        
        # Get commands for specific device
        device_commands = all_commands.get(device_name, {})
        
        return jsonify({
            'commands': device_commands,
            'device_name': device_name
        })
    
    except Exception as e:
        logger.error(f"Error getting Broadlink commands: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/commands/untracked', methods=['GET'])
def get_untracked_commands():
    """Get commands that exist in Broadlink storage but not in metadata"""
    try:
        storage = get_storage_manager()
        web_server = get_web_server()
        
        if not storage or not web_server:
            return jsonify({'error': 'Storage or web server not available'}), 500
        
        # Get all commands from Broadlink storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(web_server._get_all_broadlink_commands())
        loop.close()
        
        # Get all tracked commands from metadata
        entities = storage.get_all_entities()
        tracked_commands = {}
        
        # Build a map of device_name -> tracked Broadlink command names (the values, not keys)
        for entity_id, entity_data in entities.items():
            device_name = entity_data.get('device')
            if device_name:
                # Commands is a dict like {"turn_off": "living_room_stereo_turn_off"}
                # We need to track the VALUES (actual Broadlink command names)
                commands_dict = entity_data.get('commands', {})
                tracked_commands[device_name] = set(commands_dict.values())
        
        # Cleanup expired deletion cache entries
        web_server._cleanup_deletion_cache()
        
        # Find untracked commands (excluding recently deleted ones)
        untracked = {}
        for device_name, commands in broadlink_commands.items():
            tracked = tracked_commands.get(device_name, set())
            untracked_for_device = {
                cmd: data for cmd, data in commands.items() 
                if cmd not in tracked and not web_server._is_recently_deleted(device_name, cmd)
            }
            
            if untracked_for_device:
                untracked[device_name] = {
                    'commands': untracked_for_device,
                    'count': len(untracked_for_device)
                }
        
        return jsonify({
            'untracked': untracked,
            'total_count': sum(d['count'] for d in untracked.values())
        })
    
    except Exception as e:
        logger.error(f"Error getting untracked commands: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/commands/import', methods=['POST'])
def import_commands():
    """Import untracked commands into a device's metadata"""
    try:
        data = request.json
        device_id = data.get('device_id')  # Target device to import into
        source_device = data.get('source_device')  # Broadlink device name
        commands = data.get('commands', [])  # List of command names to import
        
        if not all([device_id, source_device, commands]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: device_id, source_device, commands'
            }), 400
        
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Get target device
        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({'error': 'Device not found'}), 404
        
        # Add commands to device metadata
        device_commands = entity_data.get('commands', {})
        for cmd in commands:
            device_commands[cmd] = cmd  # Simple mapping
        
        entity_data['commands'] = device_commands
        storage.save_entity(device_id, entity_data)
        
        logger.info(f"Imported {len(commands)} commands from '{source_device}' to device '{device_id}'")
        
        return jsonify({
            'success': True,
            'message': f'Imported {len(commands)} commands successfully',
            'imported_count': len(commands)
        })
    
    except Exception as e:
        logger.error(f"Error importing commands: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

