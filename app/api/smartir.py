#!/usr/bin/env python3
"""
SmartIR API endpoints for Broadlink Manager Add-on
"""

import logging
import json
from pathlib import Path
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

# Blueprint will be initialized by web_server.py
smartir_bp = Blueprint("smartir", __name__, url_prefix="/api/smartir")


def init_smartir_routes(smartir_detector, smartir_code_service=None):
    """Initialize SmartIR routes with detector instance and code service"""

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

    @smartir_bp.route("/profiles", methods=["POST"])
    def save_profile():
        """Save a SmartIR device profile"""
        try:
            data = request.get_json()
            
            # Extract profile data
            platform = data.get("platform")
            profile_json = data.get("json")
            code_number = data.get("code_number")
            
            if not all([platform, profile_json, code_number]):
                return jsonify({
                    "success": False,
                    "error": "Missing required fields: platform, json, or code_number"
                }), 400
            
            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({
                    "success": False,
                    "error": "SmartIR is not installed"
                }), 404
            
            # Get SmartIR codes directory
            smartir_path = smartir_detector.smartir_path
            codes_dir = smartir_path / "codes" / platform
            
            # Create codes directory if it doesn't exist
            codes_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the JSON file
            filename = f"{code_number}.json"
            file_path = codes_dir / filename
            
            # Check if file already exists
            if file_path.exists():
                logger.warning(f"Profile file {filename} already exists, overwriting")
            
            # Write JSON file with proper formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(profile_json, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Saved SmartIR profile: {file_path}")
            
            return jsonify({
                "success": True,
                "message": f"Profile saved successfully as {filename}",
                "path": str(file_path),
                "filename": filename,
                "code_number": code_number
            }), 200
            
        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @smartir_bp.route("/config/check", methods=["GET"])
    def check_config():
        """Check SmartIR configuration setup status"""
        try:
            from flask import current_app
            config_path = current_app.config.get('config_path', '/config')
            
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            configuration_yaml = config_path / "configuration.yaml"
            
            result = {
                "smartir_dir_exists": smartir_dir.exists(),
                "platforms": {}
            }
            
            # Check each platform file
            for platform in ["climate", "media_player", "fan", "light"]:
                platform_file = smartir_dir / f"{platform}.yaml"
                result["platforms"][platform] = {
                    "file_exists": platform_file.exists(),
                    "file_path": str(platform_file)
                }
            
            # Check if configuration.yaml has platform entries
            if configuration_yaml.exists():
                try:
                    with open(configuration_yaml, 'r', encoding='utf-8') as f:
                        config_content = f.read()
                    
                    # Simple detection - look for platform entries
                    result["configuration_warnings"] = []
                    
                    for platform in ["climate", "media_player", "fan", "light"]:
                        # Check if platform is defined directly (not as include)
                        if f"\n{platform}:" in config_content or f"\n{platform} :" in config_content:
                            # Check if it's NOT an include
                            if f"!include smartir/{platform}.yaml" not in config_content:
                                result["configuration_warnings"].append({
                                    "platform": platform,
                                    "message": f"Found '{platform}:' in configuration.yaml. You may need to migrate entries to smartir/{platform}.yaml"
                                })
                except Exception as e:
                    logger.warning(f"Could not read configuration.yaml: {e}")
            
            return jsonify(result), 200
            
        except Exception as e:
            logger.error(f"Error checking config: {e}")
            return jsonify({"error": str(e)}), 500

    @smartir_bp.route("/platforms/<platform>/profiles", methods=["GET"])
    def list_platform_profiles(platform):
        """List all profiles for a platform"""
        try:
            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({
                    "success": False,
                    "error": "SmartIR is not installed"
                }), 404
            
            # Get SmartIR codes directory
            smartir_path = smartir_detector.smartir_path
            codes_dir = smartir_path / "codes" / platform
            
            if not codes_dir.exists():
                return jsonify({
                    "success": True,
                    "profiles": []
                }), 200
            
            # Read all JSON files in the directory
            profiles = []
            for file_path in codes_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    profiles.append({
                        "code": file_path.stem,
                        "manufacturer": data.get("manufacturer", "Unknown"),
                        "model": data.get("supportedModels", ["Unknown"])[0] if data.get("supportedModels") else "Unknown",
                        "file_name": file_path.name
                    })
                except Exception as e:
                    logger.warning(f"Could not read profile {file_path}: {e}")
            
            # Sort by code number
            profiles.sort(key=lambda x: int(x["code"]) if x["code"].isdigit() else 0)
            
            return jsonify({
                "success": True,
                "profiles": profiles
            }), 200
            
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @smartir_bp.route("/platforms/<platform>/profiles/<code>", methods=["GET"])
    def get_profile(platform, code):
        """Get a specific profile"""
        try:
            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({
                    "success": False,
                    "error": "SmartIR is not installed"
                }), 404
            
            # Get file path
            smartir_path = smartir_detector.smartir_path
            file_path = smartir_path / "codes" / platform / f"{code}.json"
            
            if not file_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Profile {code} not found"
                }), 404
            
            # Read the profile
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            return jsonify({
                "success": True,
                "profile": profile_data
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @smartir_bp.route("/profiles/<code>", methods=["DELETE"])
    def delete_profile(code):
        """Delete a SmartIR profile"""
        try:
            data = request.get_json() or {}
            platform = data.get("platform")
            
            if not platform:
                return jsonify({
                    "success": False,
                    "error": "Missing platform parameter"
                }), 400
            
            # Validate SmartIR is installed
            if not smartir_detector.is_installed():
                return jsonify({
                    "success": False,
                    "error": "SmartIR is not installed"
                }), 404
            
            # Get file path
            smartir_path = smartir_detector.smartir_path
            file_path = smartir_path / "codes" / platform / f"{code}.json"
            
            if not file_path.exists():
                return jsonify({
                    "success": False,
                    "error": f"Profile {code} not found"
                }), 404
            
            # Delete the file
            file_path.unlink()
            logger.info(f"✅ Deleted SmartIR profile: {file_path}")
            
            # Remove from smartir/{platform}.yaml config file
            from flask import current_app
            config_path = current_app.config.get('config_path', '/config')
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            platform_file = smartir_dir / f"{platform}.yaml"
            
            if platform_file.exists():
                try:
                    with open(platform_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse YAML to find and remove the device with this code
                    import yaml
                    try:
                        config = yaml.safe_load(content) or []
                    except:
                        config = []
                    
                    # Filter out devices with matching device_code
                    original_count = len(config)
                    config = [device for device in config if device.get('device_code') != int(code)]
                    removed_count = original_count - len(config)
                    
                    if removed_count > 0:
                        # Write back the updated config
                        with open(platform_file, 'w', encoding='utf-8') as f:
                            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                        logger.info(f"✅ Removed {removed_count} device(s) with code {code} from {platform_file}")
                    else:
                        logger.warning(f"No devices with code {code} found in {platform_file}")
                        
                except Exception as e:
                    logger.warning(f"Could not update {platform_file}: {e}")
            
            return jsonify({
                "success": True,
                "message": f"Profile {code} deleted successfully"
            }), 200
            
        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @smartir_bp.route("/config/get-device", methods=["GET"])
    def get_device_from_config():
        """Get device configuration from YAML file"""
        try:
            from flask import current_app
            platform = request.args.get("platform")
            code = request.args.get("code")
            
            if not all([platform, code]):
                return jsonify({
                    "success": False,
                    "error": "Missing platform or code parameter"
                }), 400
            
            config_path = current_app.config.get('config_path', '/config')
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            platform_file = smartir_dir / f"{platform}.yaml"
            
            if not platform_file.exists():
                return jsonify({
                    "success": False,
                    "error": f"Config file {platform}.yaml not found"
                }), 404
            
            # Read and parse YAML
            with open(platform_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import yaml
            try:
                config = yaml.safe_load(content) or []
            except:
                config = []
            
            # Find device with matching code
            device = next((d for d in config if d.get('device_code') == int(code)), None)
            
            if not device:
                return jsonify({
                    "success": False,
                    "error": f"Device with code {code} not found in config"
                }), 404
            
            return jsonify({
                "success": True,
                "controller_data": device.get('controller_data', ''),
                "name": device.get('name', ''),
                "unique_id": device.get('unique_id', '')
            }), 200
            
        except Exception as e:
            logger.error(f"Error getting device from config: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @smartir_bp.route("/config/add-device", methods=["POST"])
    def add_device_to_config():
        """Add a SmartIR device to the platform YAML file"""
        try:
            from flask import current_app
            data = request.get_json()
            
            platform = data.get("platform")
            device_config = data.get("device_config")
            
            if not all([platform, device_config]):
                return jsonify({
                    "success": False,
                    "error": "Missing platform or device_config"
                }), 400
            
            config_path = current_app.config.get('config_path', '/config')
            config_path = Path(config_path)
            smartir_dir = config_path / "smartir"
            
            # Create smartir directory if needed
            smartir_dir.mkdir(exist_ok=True)
            
            platform_file = smartir_dir / f"{platform}.yaml"
            
            # Read existing content or start fresh
            existing_content = ""
            if platform_file.exists():
                with open(platform_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
            else:
                # Add header comment for new file
                existing_content = f"# SmartIR {platform.title()} Devices\n# Managed by Broadlink Manager\n\n"
            
            # Append new device config
            new_entry = f"\n- platform: smartir\n"
            for key, value in device_config.items():
                if isinstance(value, str):
                    new_entry += f"  {key}: \"{value}\"\n"
                else:
                    new_entry += f"  {key}: {value}\n"
            
            updated_content = existing_content + new_entry
            
            # Write updated file
            with open(platform_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            logger.info(f"✅ Added device to {platform_file}")
            
            return jsonify({
                "success": True,
                "message": f"Device added to {platform}.yaml",
                "file_path": str(platform_file)
            }), 200
            
        except Exception as e:
            logger.error(f"Error adding device to config: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    # ========== SmartIR Code Service Endpoints (GitHub Repository) ==========
    
    if smartir_code_service:
        
        @smartir_bp.route("/codes/manufacturers", methods=["GET"])
        def get_code_manufacturers():
            """Get list of manufacturers from GitHub repository"""
            try:
                entity_type = request.args.get("entity_type", "climate")
                
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({
                        "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"
                    }), 400
                
                manufacturers = smartir_code_service.get_manufacturers(entity_type)
                
                return jsonify({
                    "success": True,
                    "entity_type": entity_type,
                    "manufacturers": manufacturers,
                    "count": len(manufacturers)
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting manufacturers: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/models", methods=["GET"])
        def get_code_models():
            """Get list of models for a manufacturer"""
            try:
                entity_type = request.args.get("entity_type", "climate")
                manufacturer = request.args.get("manufacturer")
                
                if not manufacturer:
                    return jsonify({
                        "error": "Missing manufacturer parameter"
                    }), 400
                
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({
                        "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"
                    }), 400
                
                models = smartir_code_service.get_models(entity_type, manufacturer)
                
                return jsonify({
                    "success": True,
                    "entity_type": entity_type,
                    "manufacturer": manufacturer,
                    "models": models,
                    "count": len(models)
                }), 200
                
            except Exception as e:
                logger.error(f"Error getting models: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/code", methods=["GET"])
        def get_code_by_params():
            """Get code details using query parameters"""
            try:
                entity_type = request.args.get("entity_type")
                code_id = request.args.get("code_id")
                
                if not entity_type or not code_id:
                    return jsonify({
                        "success": False,
                        "error": "entity_type and code_id are required"
                    }), 400
                
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({
                        "success": False,
                        "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"
                    }), 400
                
                # Fetch full code from GitHub
                full_code = smartir_code_service.fetch_full_code(entity_type, code_id)
                if full_code:
                    return jsonify({
                        "success": True,
                        "code": full_code
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Code {code_id} not found"
                    }), 404
                
            except Exception as e:
                logger.error(f"Error getting code: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/<entity_type>/<code_id>", methods=["GET"])
        def get_code_details(entity_type, code_id):
            """Get full code details from GitHub"""
            try:
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({
                        "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"
                    }), 400
                
                # Try to get from cache first
                code_info = smartir_code_service.get_code_info(entity_type, code_id)
                
                # Fetch full code if requested
                fetch_full = request.args.get("full", "false").lower() == "true"
                if fetch_full:
                    full_code = smartir_code_service.fetch_full_code(entity_type, code_id)
                    if full_code:
                        return jsonify({
                            "success": True,
                            "code": full_code
                        }), 200
                    else:
                        return jsonify({
                            "success": False,
                            "error": f"Code {code_id} not found"
                        }), 404
                
                # Return cached info
                if code_info:
                    return jsonify({
                        "success": True,
                        "code": code_info
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": f"Code {code_id} not found in cache"
                    }), 404
                
            except Exception as e:
                logger.error(f"Error getting code details: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/search", methods=["GET"])
        def search_codes():
            """Search codes by manufacturer or model"""
            try:
                entity_type = request.args.get("entity_type", "climate")
                query = request.args.get("query", "")
                
                if not query:
                    return jsonify({
                        "error": "Missing query parameter"
                    }), 400
                
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({
                        "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"
                    }), 400
                
                results = smartir_code_service.search_codes(entity_type, query)
                
                return jsonify({
                    "success": True,
                    "entity_type": entity_type,
                    "query": query,
                    "results": results,
                    "count": len(results)
                }), 200
                
            except Exception as e:
                logger.error(f"Error searching codes: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/refresh", methods=["POST"])
        def refresh_codes():
            """Refresh code cache from GitHub"""
            try:
                data = request.get_json() or {}
                entity_type = data.get("entity_type", "climate")
                force = data.get("force", False)
                
                if entity_type not in ["climate", "fan", "media_player", "light"]:
                    return jsonify({
                        "error": "Invalid entity_type. Must be: climate, fan, media_player, or light"
                    }), 400
                
                success = smartir_code_service.refresh_codes(entity_type, force=force)
                
                if success:
                    return jsonify({
                        "success": True,
                        "message": f"Cache refreshed for {entity_type}"
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to refresh cache"
                    }), 500
                
            except Exception as e:
                logger.error(f"Error refreshing codes: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/cache-status", methods=["GET"])
        def get_cache_status():
            """Get cache status"""
            try:
                status = smartir_code_service.get_cache_status()
                return jsonify({
                    "success": True,
                    "cache": status
                }), 200
            except Exception as e:
                logger.error(f"Error getting cache status: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500
        
        @smartir_bp.route("/codes/clear-cache", methods=["POST"])
        def clear_cache():
            """Clear code cache"""
            try:
                success = smartir_code_service.clear_cache()
                
                if success:
                    return jsonify({
                        "success": True,
                        "message": "Cache cleared successfully"
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to clear cache"
                    }), 500
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                return jsonify({
                    "success": False,
                    "error": str(e)
                }), 500

    return smartir_bp
