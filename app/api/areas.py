"""
Area API endpoints
"""

import logging
import asyncio
from flask import jsonify, request, current_app
from . import api_bp

logger = logging.getLogger(__name__)

def get_web_server():
    """Get web server instance from Flask app context"""
    return current_app.config.get('web_server')

@api_bp.route('/areas', methods=['GET'])
def get_areas():
    """Get available areas from Home Assistant"""
    try:
        web_server = get_web_server()
        if not web_server:
            return jsonify({'error': 'Web server not available'}), 500
        
        # Call the existing async method synchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        areas = loop.run_until_complete(web_server._get_ha_areas())
        loop.close()
        
        # Return just the area names
        area_names = [area['name'] for area in areas]
        
        return jsonify({'areas': area_names})
    
    except Exception as e:
        logger.error(f"Error getting areas: {e}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/areas/<area_id>', methods=['GET'])
def get_area(area_id):
    """Get a specific area"""
    # TODO: Implement single area fetch
    return jsonify({
        'area': None,
        'message': f'Get area {area_id} - Coming soon'
    })
