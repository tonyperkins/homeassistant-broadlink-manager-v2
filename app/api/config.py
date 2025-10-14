"""
Configuration API endpoints
"""

import logging
import asyncio
from flask import jsonify, request, current_app
from . import api_bp

logger = logging.getLogger(__name__)

def get_web_server():
    """Get web server instance from Flask app context"""
    return current_app.config.get('web_server')

@api_bp.route('/config', methods=['GET'])
def get_config():
    """Get current configuration"""
    # TODO: Implement config fetching
    return jsonify({
        'config': {},
        'message': 'Get config - Coming soon'
    })

@api_bp.route('/config/reload', methods=['POST'])
def reload_config():
    """Reload Home Assistant configuration"""
    # TODO: Implement config reload
    return jsonify({
        'success': True,
        'message': 'Reload config - Coming soon'
    })

@api_bp.route('/config/generate-entities', methods=['POST'])
def generate_entities():
    """Generate Home Assistant entities"""
    # TODO: Implement entity generation
    return jsonify({
        'success': True,
        'message': 'Generate entities - Coming soon'
    })

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

