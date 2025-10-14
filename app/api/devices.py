"""
Device API endpoints
"""

import logging
import re
from flask import jsonify, request, current_app
from . import api_bp

logger = logging.getLogger(__name__)

def get_storage_manager():
    """Get storage manager from Flask app context"""
    return current_app.config.get('storage_manager')

def normalize_device_name(name):
    """
    Convert display name to storage-safe name
    Examples:
        "Living Room TV" -> "living_room_tv"
        "Tony's Office" -> "tonys_office"
        "Master Bedroom!" -> "master_bedroom"
    """
    # Remove or replace special characters (keep only alphanumeric and spaces)
    name = re.sub(r"[^\w\s]", "", name)
    # Replace spaces with underscores and convert to lowercase
    return name.strip().replace(' ', '_').lower()

@api_bp.route('/devices', methods=['GET'])
def get_devices():
    """Get all managed devices"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Get all entities from storage
        entities = storage.get_all_entities()
        
        # Convert entities to device format for frontend
        devices = []
        for entity_id, entity_data in entities.items():
            try:
                # Extract device name safely
                device_name = entity_data.get('device')
                if not device_name:
                    # Fallback: extract from entity_id
                    device_name = entity_id.split('.')[1] if '.' in entity_id else entity_id
                
                device = {
                    'id': entity_id,
                    'name': entity_data.get('name') or entity_data.get('friendly_name', entity_id),
                    'entity_type': entity_data.get('entity_type', 'switch'),
                    'area': entity_data.get('area', ''),
                    'icon': entity_data.get('icon', ''),
                    'broadlink_entity': entity_data.get('broadlink_entity', ''),
                    'device': device_name,  # Add device field for command learning
                    'commands': entity_data.get('commands', {}),
                    'enabled': entity_data.get('enabled', True)
                }
                devices.append(device)
            except Exception as e:
                logger.error(f"Error processing entity {entity_id}: {e}")
                continue
        
        return jsonify({'devices': devices})
    
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """Get a specific device"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({'error': 'Device not found'}), 404
        
        device = {
            'id': device_id,
            'name': entity_data.get('name') or entity_data.get('friendly_name', device_id),
            'entity_type': entity_data.get('entity_type', 'switch'),
            'area': entity_data.get('area', ''),
            'icon': entity_data.get('icon', ''),
            'broadlink_entity': entity_data.get('broadlink_entity', ''),
            'commands': entity_data.get('commands', {}),
            'enabled': entity_data.get('enabled', True)
        }
        
        return jsonify({'device': device})
    
    except Exception as e:
        logger.error(f"Error getting device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/devices', methods=['POST'])
def create_device():
    """Create a new managed device"""
    try:
        data = request.json
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Generate entity_id from name
        name = data.get('name', '')
        entity_type = data.get('entity_type', 'switch')
        
        # If device field is provided (e.g., from adoption), use it as-is
        # Otherwise, normalize the name for the device field
        device_name = data.get('device')
        if not device_name:
            device_name = normalize_device_name(name)
        
        # Generate entity_id from device name
        entity_id = f"{entity_type}.{device_name}"
        
        # Check if already exists
        if storage.get_entity(entity_id):
            return jsonify({'error': 'Device with this name already exists'}), 400
        
        # Create entity data
        entity_data = {
            'entity_type': entity_type,
            'device': device_name,  # Broadlink storage device name (must match .storage file)
            'broadlink_entity': data.get('broadlink_entity', ''),
            'area': data.get('area', ''),
            'friendly_name': name,  # Display name
            'name': name,  # Display name
            'icon': data.get('icon', ''),
            'commands': data.get('commands', {}),  # Include commands if provided
            'enabled': True
        }
        
        # Save to storage
        storage.save_entity(entity_id, entity_data)
        
        return jsonify({
            'success': True,
            'device': {
                'id': entity_id,
                **entity_data
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Error creating device: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/devices/<device_id>', methods=['PUT'])
def update_device(device_id):
    """Update an existing device"""
    try:
        data = request.json
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Get existing entity
        entity_data = storage.get_entity(device_id)
        if not entity_data:
            return jsonify({'error': 'Device not found'}), 404
        
        # Check if we need to rename the entity_id (only if no commands learned)
        new_entity_id = device_id
        if 'name' in data:
            # Check if commands exist in metadata (this includes optimistically added commands)
            # This is more reliable than checking storage files which update slowly in standalone mode
            current_commands = entity_data.get('commands', {})
            has_commands = current_commands and len(current_commands) > 0
            
            if has_commands:
                logger.info(f"Device '{device_id}' has {len(current_commands)} commands in metadata - rename blocked")
            
            if not has_commands:
                # No commands in metadata yet - safe to rename entity_id
                new_device_name = normalize_device_name(data['name'])
                entity_type = entity_data.get('entity_type', 'switch')
                new_entity_id = f"{entity_type}.{new_device_name}"
                
                # If entity_id is changing, we need to delete old and create new
                if new_entity_id != device_id:
                    logger.info(f"Renaming entity from '{device_id}' to '{new_entity_id}' (no commands learned yet)")
                    # Delete old entity
                    storage.delete_entity(device_id)
                    # Update device field
                    entity_data['device'] = new_device_name
        
        # Update fields
        if 'name' in data:
            entity_data['name'] = data['name']
            entity_data['friendly_name'] = data['name']
        if 'entity_type' in data:
            entity_data['entity_type'] = data['entity_type']
        if 'area' in data:
            entity_data['area'] = data['area']
        if 'icon' in data:
            entity_data['icon'] = data['icon']
        if 'broadlink_entity' in data:
            entity_data['broadlink_entity'] = data['broadlink_entity']
        if 'enabled' in data:
            entity_data['enabled'] = data['enabled']
        if 'commands' in data:
            entity_data['commands'] = data['commands']
        
        # Save entity (with new ID if renamed, or same ID if not)
        storage.save_entity(new_entity_id, entity_data)
        
        return jsonify({
            'success': True,
            'device': {
                'id': new_entity_id,
                **entity_data
            }
        })
    
    except Exception as e:
        logger.error(f"Error updating device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Delete a device"""
    try:
        storage = get_storage_manager()
        if not storage:
            return jsonify({'error': 'Storage manager not available'}), 500
        
        # Check if exists
        if not storage.get_entity(device_id):
            return jsonify({'error': 'Device not found'}), 404
        
        # Delete the device
        storage.delete_entity(device_id)
        
        return jsonify({
            'success': True,
            'message': f'Device {device_id} deleted'
        })
    
    except Exception as e:
        logger.error(f"Error deleting device {device_id}: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/devices/find-broadlink-owner', methods=['POST'])
def find_broadlink_owner():
    """Find which Broadlink device owns a specific device's commands"""
    try:
        import asyncio
        
        data = request.json
        device_name = data.get('device_name')
        
        if not device_name:
            return jsonify({'error': 'device_name is required'}), 400
        
        web_server = current_app.config.get('web_server')
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        # Use the existing method to find the Broadlink entity
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_entity = loop.run_until_complete(web_server._find_broadlink_entity_for_device(device_name))
        loop.close()
        
        return jsonify({
            'broadlink_entity': broadlink_entity,
            'device_name': device_name
        })
    
    except Exception as e:
        logger.error(f"Error finding Broadlink owner: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/devices/discover', methods=['GET'])
def discover_untracked_devices():
    """Discover devices that exist in Broadlink storage but are not tracked in metadata"""
    try:
        import asyncio
        
        web_server = current_app.config.get('web_server')
        storage = get_storage_manager()
        
        if not storage or not web_server:
            return jsonify({'error': 'Storage or web server not available'}), 500
        
        # Get all commands from Broadlink storage
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        broadlink_commands = loop.run_until_complete(web_server._get_all_broadlink_commands())
        loop.close()
        
        # Get all tracked devices from metadata
        entities = storage.get_all_entities()
        tracked_device_names = set()
        
        for entity_id, entity_data in entities.items():
            device_name = entity_data.get('device')
            if device_name:
                tracked_device_names.add(device_name)
        
        # Cleanup expired deletion cache entries
        web_server._cleanup_deletion_cache()
        
        # Find untracked devices (filter out devices where ALL commands are recently deleted)
        untracked_devices = []
        for device_name, commands in broadlink_commands.items():
            if device_name not in tracked_device_names:
                # Filter out recently deleted commands
                remaining_commands = [
                    cmd for cmd in commands.keys()
                    if not web_server._is_recently_deleted(device_name, cmd)
                ]
                
                # Only include device if it has commands that aren't recently deleted
                if remaining_commands:
                    untracked_devices.append({
                        'device_name': device_name,
                        'command_count': len(remaining_commands),
                        'commands': remaining_commands
                    })
        
        return jsonify({
            'untracked_devices': untracked_devices,
            'count': len(untracked_devices)
        })
    
    except Exception as e:
        logger.error(f"Error discovering untracked devices: {e}")
        return jsonify({'error': str(e)}), 500
