#!/usr/bin/env python3
"""
SmartIR API endpoints for Broadlink Manager Add-on
"""

import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

# Blueprint will be initialized by web_server.py
smartir_bp = Blueprint("smartir", __name__, url_prefix="/api/smartir")


def init_smartir_routes(smartir_detector):
    """Initialize SmartIR routes with detector instance"""

    @smartir_bp.route("/status", methods=["GET"])
    def get_status():
        """Get SmartIR installation status"""
        try:
            status = smartir_detector.get_status()
            return jsonify(status), 200
        except Exception as e:
            logger.error(f"Error getting SmartIR status: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms", methods=["GET"])
    def get_platforms():
        """Get available SmartIR platforms"""
        try:
            if not smartir_detector.is_installed():
                return jsonify({
                    "installed": False,
                    "platforms": [],
                    "message": "SmartIR not installed"
                }), 200

            platforms = smartir_detector.get_supported_platforms()
            return jsonify({
                "installed": True,
                "platforms": platforms
            }), 200
        except Exception as e:
            logger.error(f"Error getting platforms: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/codes", methods=["GET"])
    def get_platform_codes(platform):
        """Get device codes for a specific platform"""
        try:
            if not smartir_detector.is_installed():
                return jsonify({
                    "error": "SmartIR not installed"
                }), 404

            codes = smartir_detector.get_device_codes(platform)
            return jsonify({
                "platform": platform,
                "codes": codes,
                "count": len(codes)
            }), 200
        except Exception as e:
            logger.error(f"Error getting codes for {platform}: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/next-code", methods=["GET"])
    def get_next_code(platform):
        """Get next available custom code number for platform"""
        try:
            if not smartir_detector.is_installed():
                return jsonify({
                    "error": "SmartIR not installed"
                }), 404

            next_code = smartir_detector.find_next_custom_code(platform)
            return jsonify({
                "platform": platform,
                "next_code": next_code
            }), 200
        except Exception as e:
            logger.error(f"Error getting next code: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/validate-code", methods=["POST"])
    def validate_code():
        """Validate a SmartIR code file"""
        try:
            data = request.get_json()
            platform = data.get("platform")
            code_number = data.get("code")

            if not platform or not code_number:
                return jsonify({
                    "error": "Missing platform or code"
                }), 400

            result = smartir_detector.validate_code_file(platform, code_number)
            return jsonify(result), 200
        except Exception as e:
            logger.error(f"Error validating code: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/install-instructions", methods=["GET"])
    def get_install_instructions():
        """Get SmartIR installation instructions"""
        try:
            instructions = smartir_detector.get_install_instructions()
            return jsonify(instructions), 200
        except Exception as e:
            logger.error(f"Error getting install instructions: {e}")
            return jsonify({"error": str(e)}), 500

    return smartir_bp
