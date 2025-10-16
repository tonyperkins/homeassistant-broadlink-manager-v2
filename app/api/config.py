"""
Configuration API endpoints
"""

import logging
import asyncio
from flask import jsonify, request, current_app
from . import api_bp
from controller_detector import ControllerDetector

logger = logging.getLogger(__name__)

# Initialize controller detector
controller_detector = ControllerDetector()

def get_web_server():
    """Get web server instance from Flask app context"""
    return current_app.config.get('web_server')

@api_bp.route('/broadlink/devices', methods=['GET'])
def get_broadlink_devices():
    """Get available Broadlink devices from Home Assistant"""
    try:
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        # Call the existing async method synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        devices = loop.run_until_complete(web_server._get_broadlink_devices("GET /api/broadlink/devices"))
        loop.close()
        
        return jsonify({'devices': devices})
    
    except Exception as e:
        logger.error(f"Error getting Broadlink devices: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/remote/devices', methods=['GET'])
def get_all_remote_devices():
    """Get ALL remote entities from Home Assistant API (simplified approach)"""
    try:
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get all entities from HA API
        states = loop.run_until_complete(web_server._make_ha_request("GET", "states"))
        
        loop.close()
        
        if not states:
            return jsonify({'devices': []})
        
        remote_devices = []
        
        # Filter for remote.* entities
        for state in states:
            entity_id = state.get('entity_id', '')
            
            # Skip if not a remote entity
            if not entity_id.startswith('remote.'):
                continue
            
            # Get attributes
            attributes = state.get('attributes', {})
            
            # Skip Android TV, Roku, Apple TV, and similar media remotes
            # These are for controlling media players, not for sending IR/RF codes
            
            # Check the 'supported_features' attribute
            # Android TV remotes typically have supported_features = 4
            # Broadlink/IR remotes typically have supported_features = 3 or other values
            supported_features = attributes.get('supported_features', 0)
            
            # Media device remotes typically have activity_list attribute
            has_activity_list = 'activity_list' in attributes or 'current_activity' in attributes
            
            # Check entity ID for media device patterns (be specific to avoid false positives)
            skip_patterns = [
                'androidtv', 'android_tv', 'google_tv', 'chromecast',
                'roku', 'apple_tv', 'appletv', 'fire_tv', 'firetv'
            ]
            
            entity_lower = entity_id.lower()
            
            # Check if this is a media device remote (skip it)
            is_media_remote = (
                has_activity_list or  # Has media player activity tracking
                (supported_features == 4 and 'tv' in entity_lower) or  # Android TV pattern
                any(pattern in entity_lower for pattern in skip_patterns)
            )
            
            if is_media_remote:
                logger.info(f"Skipping media device remote: {entity_id} (supported_features={supported_features})")
                continue
            
            # Detect controller type
            controller_info = controller_detector.detect_controller_type(entity_id)
            
            # Build device info
            device_info = {
                'entity_id': entity_id,
                'name': attributes.get('friendly_name', entity_id),
                'state': state.get('state'),
                'controller_type': controller_info['type'],
                'controller_name': controller_info['name'],
                'supports_learning': controller_info['supports_learning'],
                'supports_deletion': controller_info['supports_deletion'],
                'icon': controller_info['icon'],
                'color': controller_info['color'],
                'confidence': controller_info['confidence'],
                # Optional: include any other useful attributes
                'supported_features': attributes.get('supported_features'),
            }
            
            remote_devices.append(device_info)
            logger.debug(f"Added remote device: {entity_id} ({controller_info['type']})")
        
        logger.info(f"Found {len(remote_devices)} remote devices from HA API")
        return jsonify({'devices': remote_devices})
    
    except Exception as e:
        logger.error(f"Error getting remote devices: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/controller/info/<path:entity_id>', methods=['GET'])
def get_controller_info(entity_id):
    """Get controller type and capabilities for a specific entity"""
    try:
        # Detect controller type
        controller_info = controller_detector.detect_controller_type(entity_id)
        
        return jsonify({
            'success': True,
            'entity_id': entity_id,
            **controller_info
        })
    
    except Exception as e:
        logger.error(f"Error detecting controller type for {entity_id}: {e}")
        return jsonify({'error': str(e)}), 500

