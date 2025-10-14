"""
API module for Broadlink Manager v2
Provides RESTful API endpoints for the Vue frontend
"""

from flask import Blueprint

# Create API blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes (will be created next)
from . import devices, commands, config, areas

__all__ = ['api_bp']
