"""
Unit tests for config_loader module
Tests configuration loading for both Supervisor and standalone modes
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.config_loader import ConfigLoader


class TestConfigLoaderInitialization:
    """Test ConfigLoader initialization and mode detection"""

    def test_init_supervisor_mode(self):
        """Test initialization in Supervisor mode"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            loader = ConfigLoader()
            assert loader.is_supervisor is True
            assert loader.mode == "supervisor"

    def test_init_standalone_mode(self):
        """Test initialization in standalone mode"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            assert loader.is_supervisor is False
            assert loader.mode == "standalone"

    def test_detect_supervisor_environment_with_token(self):
        """Test supervisor detection with SUPERVISOR_TOKEN"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            loader = ConfigLoader()
            assert loader._detect_supervisor_environment() is True

    def test_detect_supervisor_environment_without_token(self):
        """Test supervisor detection without SUPERVISOR_TOKEN"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            assert loader._detect_supervisor_environment() is False


class TestHAURLConfiguration:
    """Test Home Assistant URL configuration"""

    def test_get_ha_url_supervisor_mode(self):
        """Test HA URL in Supervisor mode"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            loader = ConfigLoader()
            url = loader.get_ha_url()
            assert url == "http://supervisor/core"

    def test_get_ha_url_standalone_default(self):
        """Test HA URL in standalone mode with default"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            url = loader.get_ha_url()
            assert url == "http://localhost:8123"

    def test_get_ha_url_standalone_custom(self):
        """Test HA URL in standalone mode with custom URL"""
        with patch.dict(os.environ, {'HA_URL': 'http://homeassistant.local:8123'}):
            loader = ConfigLoader()
            url = loader.get_ha_url()
            assert url == "http://homeassistant.local:8123"

    def test_get_ha_url_removes_trailing_slash(self):
        """Test that trailing slash is removed from HA URL"""
        with patch.dict(os.environ, {'HA_URL': 'http://homeassistant.local:8123/'}):
            loader = ConfigLoader()
            url = loader.get_ha_url()
            assert url == "http://homeassistant.local:8123"
            assert not url.endswith('/')


class TestHATokenConfiguration:
    """Test Home Assistant token configuration"""

    def test_get_ha_token_supervisor_mode(self):
        """Test HA token in Supervisor mode"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'supervisor_token_123'}):
            loader = ConfigLoader()
            token = loader.get_ha_token()
            assert token == "supervisor_token_123"

    def test_get_ha_token_standalone_mode(self):
        """Test HA token in standalone mode"""
        with patch.dict(os.environ, {'HA_TOKEN': 'standalone_token_456'}):
            loader = ConfigLoader()
            token = loader.get_ha_token()
            assert token == "standalone_token_456"

    def test_get_ha_token_missing_supervisor(self):
        """Test missing token in Supervisor mode"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test'}, clear=True):
            # Remove the token after initialization
            del os.environ['SUPERVISOR_TOKEN']
            loader = ConfigLoader()
            loader.is_supervisor = True
            token = loader.get_ha_token()
            assert token is None

    def test_get_ha_token_missing_standalone(self):
        """Test missing token in standalone mode"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            token = loader.get_ha_token()
            assert token is None


class TestPathConfiguration:
    """Test path configuration"""

    def test_get_config_path_default(self):
        """Test default config path"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            path = loader.get_config_path()
            assert path == Path("/config")

    def test_get_config_path_ha_config_path(self):
        """Test config path with HA_CONFIG_PATH env var"""
        with patch.dict(os.environ, {'HA_CONFIG_PATH': '/custom/config'}):
            loader = ConfigLoader()
            path = loader.get_config_path()
            assert path == Path("/custom/config")

    def test_get_config_path_config_path(self):
        """Test config path with CONFIG_PATH env var"""
        with patch.dict(os.environ, {'CONFIG_PATH': '/another/config'}):
            loader = ConfigLoader()
            path = loader.get_config_path()
            assert path == Path("/another/config")

    def test_get_config_path_priority(self):
        """Test that HA_CONFIG_PATH takes priority over CONFIG_PATH"""
        with patch.dict(os.environ, {
            'HA_CONFIG_PATH': '/priority/config',
            'CONFIG_PATH': '/secondary/config'
        }):
            loader = ConfigLoader()
            path = loader.get_config_path()
            assert path == Path("/priority/config")

    def test_get_storage_path(self):
        """Test storage path"""
        with patch.dict(os.environ, {'HA_CONFIG_PATH': '/test/config'}):
            loader = ConfigLoader()
            path = loader.get_storage_path()
            assert path == Path("/test/config/.storage")

    def test_get_broadlink_manager_path(self):
        """Test Broadlink Manager path"""
        with patch.dict(os.environ, {'HA_CONFIG_PATH': '/test/config'}):
            loader = ConfigLoader()
            path = loader.get_broadlink_manager_path()
            assert path == Path("/test/config/broadlink_manager")


class TestLoadOptions:
    """Test configuration options loading"""

    def test_load_options_default(self):
        """Test loading default options"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            options = loader.load_options()
            
            assert options["log_level"] == "info"
            assert options["web_port"] == 8099
            assert options["auto_discover"] is True

    def test_load_options_supervisor_mode(self):
        """Test loading options in Supervisor mode"""
        supervisor_options = {
            "log_level": "debug",
            "web_port": 8080,
            "auto_discover": False
        }
        
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(supervisor_options))):
                    loader = ConfigLoader()
                    options = loader.load_options()
                    
                    assert options["log_level"] == "debug"
                    assert options["web_port"] == 8080
                    assert options["auto_discover"] is False

    def test_load_options_standalone_mode(self):
        """Test loading options in standalone mode"""
        with patch.dict(os.environ, {
            'LOG_LEVEL': 'DEBUG',
            'WEB_PORT': '9000',
            'AUTO_DISCOVER': 'false'
        }):
            loader = ConfigLoader()
            options = loader.load_options()
            
            assert options["log_level"] == "debug"
            assert options["web_port"] == 9000
            assert options["auto_discover"] is False


class TestLoadSupervisorOptions:
    """Test Supervisor options loading"""

    def test_load_supervisor_options_file_exists(self):
        """Test loading Supervisor options when file exists"""
        supervisor_options = {
            "log_level": "trace",
            "web_port": 7000,
            "custom_option": "value"
        }
        
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data=json.dumps(supervisor_options))):
                    loader = ConfigLoader()
                    options = loader._load_supervisor_options()
                    
                    assert options["log_level"] == "trace"
                    assert options["web_port"] == 7000
                    assert options["custom_option"] == "value"

    def test_load_supervisor_options_file_missing(self):
        """Test loading Supervisor options when file is missing"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            with patch('pathlib.Path.exists', return_value=False):
                loader = ConfigLoader()
                options = loader._load_supervisor_options()
                assert options == {}

    def test_load_supervisor_options_json_error(self):
        """Test loading Supervisor options with JSON parse error"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            with patch('pathlib.Path.exists', return_value=True):
                with patch('builtins.open', mock_open(read_data='invalid json')):
                    loader = ConfigLoader()
                    options = loader._load_supervisor_options()
                    assert options == {}


class TestLoadEnvOptions:
    """Test environment variable options loading"""

    def test_load_env_options_log_level(self):
        """Test loading log level from environment"""
        with patch.dict(os.environ, {'LOG_LEVEL': 'WARNING'}):
            loader = ConfigLoader()
            options = loader._load_env_options()
            assert options["log_level"] == "warning"

    def test_load_env_options_web_port_valid(self):
        """Test loading valid web port from environment"""
        with patch.dict(os.environ, {'WEB_PORT': '8888'}):
            loader = ConfigLoader()
            options = loader._load_env_options()
            assert options["web_port"] == 8888

    def test_load_env_options_web_port_invalid(self):
        """Test loading invalid web port from environment"""
        with patch.dict(os.environ, {'WEB_PORT': 'invalid'}):
            loader = ConfigLoader()
            options = loader._load_env_options()
            assert "web_port" not in options

    def test_load_env_options_auto_discover_true(self):
        """Test loading auto_discover=true from environment"""
        test_cases = ['true', 'TRUE', '1', 'yes', 'YES', 'on', 'ON']
        
        for value in test_cases:
            with patch.dict(os.environ, {'AUTO_DISCOVER': value}):
                loader = ConfigLoader()
                options = loader._load_env_options()
                assert options["auto_discover"] is True, f"Failed for value: {value}"

    def test_load_env_options_auto_discover_false(self):
        """Test loading auto_discover=false from environment"""
        test_cases = ['false', 'FALSE', '0', 'no', 'NO', 'off', 'OFF']
        
        for value in test_cases:
            with patch.dict(os.environ, {'AUTO_DISCOVER': value}):
                loader = ConfigLoader()
                options = loader._load_env_options()
                assert options["auto_discover"] is False, f"Failed for value: {value}"

    def test_load_env_options_empty(self):
        """Test loading options with no environment variables"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            options = loader._load_env_options()
            assert options == {}


class TestConfigSanitization:
    """Test configuration sanitization"""

    def test_sanitize_config_for_log(self):
        """Test config sanitization for logging"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            config = {
                "log_level": "info",
                "web_port": 8099,
                "auto_discover": True
            }
            
            sanitized = loader._sanitize_config_for_log(config)
            
            # Currently just returns a copy, but verifies structure
            assert sanitized["log_level"] == "info"
            assert sanitized["web_port"] == 8099
            assert sanitized["auto_discover"] is True

    def test_sanitize_config_does_not_modify_original(self):
        """Test that sanitization doesn't modify original config"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            original = {"key": "value"}
            sanitized = loader._sanitize_config_for_log(original)
            
            # Modify sanitized
            sanitized["key"] = "modified"
            
            # Original should be unchanged
            assert original["key"] == "value"


class TestConfigValidation:
    """Test configuration validation"""

    def test_validate_configuration_valid_supervisor(self):
        """Test validation with valid Supervisor configuration"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch.dict(os.environ, {'CONFIG_PATH': tmpdir}):
                    loader = ConfigLoader()
                    is_valid = loader.validate_configuration()
                    assert is_valid is True

    def test_validate_configuration_valid_standalone(self):
        """Test validation with valid standalone configuration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {
                'HA_TOKEN': 'test_token',
                'CONFIG_PATH': tmpdir
            }):
                loader = ConfigLoader()
                is_valid = loader.validate_configuration()
                assert is_valid is True

    def test_validate_configuration_missing_token_supervisor(self):
        """Test validation with missing Supervisor token"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test'}, clear=True):
            del os.environ['SUPERVISOR_TOKEN']
            with tempfile.TemporaryDirectory() as tmpdir:
                with patch.dict(os.environ, {'CONFIG_PATH': tmpdir}):
                    loader = ConfigLoader()
                    loader.is_supervisor = True
                    is_valid = loader.validate_configuration()
                    assert is_valid is False

    def test_validate_configuration_missing_token_standalone(self):
        """Test validation with missing standalone token"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {'CONFIG_PATH': tmpdir}, clear=True):
                loader = ConfigLoader()
                is_valid = loader.validate_configuration()
                assert is_valid is False

    def test_validate_configuration_missing_config_path(self):
        """Test validation with missing config path"""
        with patch.dict(os.environ, {
            'HA_TOKEN': 'test_token',
            'CONFIG_PATH': '/nonexistent/path'
        }):
            loader = ConfigLoader()
            is_valid = loader.validate_configuration()
            assert is_valid is False

    def test_validate_configuration_all_invalid(self):
        """Test validation with all invalid configuration"""
        with patch.dict(os.environ, {'CONFIG_PATH': '/nonexistent'}, clear=True):
            loader = ConfigLoader()
            is_valid = loader.validate_configuration()
            assert is_valid is False


class TestEnvironmentInfo:
    """Test environment information retrieval"""

    def test_get_environment_info_supervisor(self):
        """Test environment info in Supervisor mode"""
        with patch.dict(os.environ, {'SUPERVISOR_TOKEN': 'test_token'}):
            loader = ConfigLoader()
            info = loader.get_environment_info()
            
            assert info["mode"] == "supervisor"
            assert info["is_supervisor"] is True
            assert info["ha_url"] == "http://supervisor/core"
            assert "config_path" in info
            assert "storage_path" in info
            assert info["has_token"] is True

    def test_get_environment_info_standalone(self):
        """Test environment info in standalone mode"""
        with patch.dict(os.environ, {
            'HA_TOKEN': 'test_token',
            'HA_URL': 'http://homeassistant.local:8123'
        }):
            loader = ConfigLoader()
            info = loader.get_environment_info()
            
            assert info["mode"] == "standalone"
            assert info["is_supervisor"] is False
            assert info["ha_url"] == "http://homeassistant.local:8123"
            assert "config_path" in info
            assert "storage_path" in info
            assert info["has_token"] is True

    def test_get_environment_info_no_token(self):
        """Test environment info without token"""
        with patch.dict(os.environ, {}, clear=True):
            loader = ConfigLoader()
            info = loader.get_environment_info()
            
            assert info["has_token"] is False

    def test_get_environment_info_custom_paths(self):
        """Test environment info with custom paths"""
        with patch.dict(os.environ, {'HA_CONFIG_PATH': '/custom/config'}):
            loader = ConfigLoader()
            info = loader.get_environment_info()
            
            # Use Path for cross-platform compatibility
            assert Path(info["config_path"]) == Path("/custom/config")
            assert Path(info["storage_path"]) == Path("/custom/config/.storage")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
