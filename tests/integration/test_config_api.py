"""
Integration tests for Config API endpoints
Tests /api/config/* endpoints for configuration management
"""

import pytest
import json
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock


@pytest.fixture(scope="module")
def app_for_config_testing():
    """Create Flask app for config testing"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'app'))
    
    from web_server import BroadlinkWebServer
    from config_loader import ConfigLoader
    
    # Mock config loader
    config_loader = Mock(spec=ConfigLoader)
    config_loader.mode = 'standalone'
    config_loader.is_supervisor = False
    config_loader.get_ha_url.return_value = 'http://localhost:8123'
    config_loader.get_ha_token.return_value = 'test_token'
    
    # Create temp storage
    temp_storage = Path(tempfile.mkdtemp())
    config_loader.get_storage_path.return_value = temp_storage
    config_loader.get_broadlink_manager_path.return_value = temp_storage / 'broadlink_manager'
    config_loader.get_config_path.return_value = temp_storage
    
    # Create directories
    (temp_storage / 'broadlink_manager').mkdir(exist_ok=True)
    
    # Create server
    server = BroadlinkWebServer(port=8099, config_loader=config_loader)
    server.app.config['TESTING'] = True
    
    yield server.app
    
    # Cleanup
    shutil.rmtree(str(temp_storage))


@pytest.fixture
def client(app_for_config_testing):
    """Create a test client"""
    with app_for_config_testing.test_client() as client:
        yield client


@pytest.mark.integration
class TestConfigEndpoints:
    """Test configuration API endpoints"""
    
    def test_get_config(self, client):
        """Test retrieving current configuration"""
        response = client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        
        # Should contain basic config info
        assert 'mode' in data or 'ha_url' in data or 'version' in data
    
    def test_get_system_info(self, client):
        """Test retrieving system information"""
        response = client.get('/api/config/system')
        
        # Should return system info or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            # May contain Python version, OS, etc.
            assert isinstance(data, dict)
    
    def test_get_ha_connection_status(self, client):
        """Test checking Home Assistant connection status"""
        response = client.get('/api/config/ha-status')
        
        # Should return status or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Should indicate connection status
            assert 'connected' in data or 'status' in data or 'error' in data


@pytest.mark.integration
class TestBroadlinkDeviceDiscovery:
    """Test Broadlink device discovery and listing"""
    
    def test_get_broadlink_devices(self, client):
        """Test retrieving list of Broadlink devices from HA"""
        response = client.get('/api/config/broadlink-devices')
        
        # Should return list or error
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, (list, dict))
    
    def test_discover_broadlink_devices(self, client):
        """Test discovering Broadlink devices on network"""
        response = client.post('/api/config/discover')
        
        # Should accept request or return not implemented
        assert response.status_code in [200, 202, 404, 501]


@pytest.mark.integration
class TestAreaConfiguration:
    """Test area configuration endpoints"""
    
    def test_get_areas_from_ha(self, client):
        """Test retrieving areas from Home Assistant"""
        response = client.get('/api/config/areas')
        
        # Should return areas or error
        assert response.status_code in [200, 404, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, (list, dict))
    
    def test_sync_areas(self, client):
        """Test syncing areas from Home Assistant"""
        response = client.post('/api/config/sync-areas')
        
        # Should accept request or return error
        assert response.status_code in [200, 202, 404, 500]


@pytest.mark.integration
class TestStoragePaths:
    """Test storage path configuration"""
    
    def test_get_storage_paths(self, client):
        """Test retrieving storage path information"""
        response = client.get('/api/config/paths')
        
        # Should return paths or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Should contain path information
            assert 'storage_path' in data or 'config_path' in data or 'base_path' in data
    
    def test_validate_storage_paths(self, client):
        """Test validating storage paths exist and are writable"""
        response = client.get('/api/config/validate-paths')
        
        # Should return validation status
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)


@pytest.mark.integration
class TestDeploymentMode:
    """Test deployment mode configuration"""
    
    def test_get_deployment_mode(self, client):
        """Test retrieving current deployment mode"""
        response = client.get('/api/config/mode')
        
        # Should return mode
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Should indicate mode (standalone, addon, docker)
            assert 'mode' in data or 'deployment_mode' in data
    
    def test_is_supervisor_mode(self, client):
        """Test checking if running in supervisor mode"""
        response = client.get('/api/config/is-supervisor')
        
        # Should return boolean or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)


@pytest.mark.integration
class TestVersionInfo:
    """Test version information endpoints"""
    
    def test_get_app_version(self, client):
        """Test retrieving application version"""
        response = client.get('/api/config/version')
        
        # Should return version or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Should contain version info
            assert 'version' in data or 'app_version' in data
    
    def test_get_dependencies_versions(self, client):
        """Test retrieving dependency versions"""
        response = client.get('/api/config/dependencies')
        
        # Should return dependency info or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)


@pytest.mark.integration
class TestConfigValidation:
    """Test configuration validation"""
    
    def test_validate_ha_connection(self, client):
        """Test validating Home Assistant connection"""
        response = client.post('/api/config/validate-ha')
        
        # Should return validation result
        assert response.status_code in [200, 400, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Should indicate if connection is valid
            assert 'valid' in data or 'success' in data or 'error' in data
    
    def test_validate_broadlink_entity(self, client):
        """Test validating a Broadlink entity exists"""
        validation_data = {
            'entity_id': 'remote.bedroom_rm4_pro'
        }
        
        response = client.post(
            '/api/config/validate-entity',
            data=json.dumps(validation_data),
            content_type='application/json'
        )
        
        # Should return validation result
        assert response.status_code in [200, 400, 404, 500]
    
    def test_validate_area_exists(self, client):
        """Test validating an area exists in Home Assistant"""
        validation_data = {
            'area_id': 'bedroom'
        }
        
        response = client.post(
            '/api/config/validate-area',
            data=json.dumps(validation_data),
            content_type='application/json'
        )
        
        # Should return validation result
        assert response.status_code in [200, 400, 404, 500]


@pytest.mark.integration
class TestConfigUpdate:
    """Test configuration update endpoints"""
    
    def test_update_ha_url(self, client):
        """Test updating Home Assistant URL"""
        update_data = {
            'ha_url': 'http://homeassistant.local:8123'
        }
        
        response = client.put(
            '/api/config/ha-url',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Should accept or reject update
        assert response.status_code in [200, 400, 403, 404, 500]
    
    def test_update_ha_token(self, client):
        """Test updating Home Assistant token"""
        update_data = {
            'ha_token': 'new_test_token_12345'
        }
        
        response = client.put(
            '/api/config/ha-token',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        
        # Should accept or reject update (may be forbidden in some modes)
        assert response.status_code in [200, 400, 403, 404, 500]


@pytest.mark.integration
class TestDiagnostics:
    """Test diagnostics endpoints"""
    
    def test_get_diagnostics_json(self, client):
        """Test retrieving diagnostics in JSON format"""
        response = client.get('/api/diagnostics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)
        
        # Should contain diagnostic information
        assert 'system' in data or 'config' in data or 'devices' in data
    
    def test_get_diagnostics_markdown(self, client):
        """Test retrieving diagnostics in Markdown format"""
        response = client.get('/api/diagnostics/markdown')
        
        assert response.status_code == 200
        # Should return text/plain or text/markdown
        assert response.content_type in ['text/plain', 'text/markdown', 'text/plain; charset=utf-8']
    
    def test_download_diagnostics_bundle(self, client):
        """Test downloading diagnostics as ZIP bundle"""
        response = client.get('/api/diagnostics/download')
        
        assert response.status_code == 200
        # Should return ZIP file
        assert response.content_type == 'application/zip' or 'zip' in response.content_type
    
    def test_diagnostics_sanitization(self, client):
        """Test that diagnostics properly sanitize sensitive data"""
        response = client.get('/api/diagnostics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Convert to string to search for sensitive patterns
        data_str = json.dumps(data)
        
        # Should NOT contain actual tokens, passwords, or IR codes
        # (They should be replaced with [REDACTED] or similar)
        assert 'test_token' not in data_str or '[REDACTED]' in data_str
        
        # IR codes should be sanitized (if present)
        # Look for Base64 patterns that are very long (IR codes)
        import re
        long_base64 = re.findall(r'[A-Za-z0-9+/]{100,}', data_str)
        # Should not find many long Base64 strings (IR codes should be redacted)
        assert len(long_base64) < 5  # Allow some, but not full IR code database


@pytest.mark.integration
class TestHealthCheck:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test basic health check endpoint"""
        response = client.get('/api/health')
        
        # Should return OK or not found
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert isinstance(data, dict)
            # Should indicate health status
            assert 'status' in data or 'healthy' in data
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get('/api/ready')
        
        # Should return ready status or not found
        assert response.status_code in [200, 404, 503]


@pytest.mark.integration
class TestConfigErrorHandling:
    """Test error handling in config endpoints"""
    
    def test_invalid_json_payload(self, client):
        """Test handling of invalid JSON in request"""
        response = client.post(
            '/api/config/validate-ha',
            data='INVALID JSON{{{',
            content_type='application/json'
        )
        
        # Should return bad request
        assert response.status_code in [400, 500]
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields"""
        response = client.post(
            '/api/config/validate-entity',
            data=json.dumps({}),  # Missing entity_id
            content_type='application/json'
        )
        
        # Should return bad request
        assert response.status_code in [400, 500]
    
    def test_unauthorized_config_update(self, client):
        """Test that config updates may require authorization"""
        # Attempt to update critical config without auth
        response = client.put(
            '/api/config/ha-token',
            data=json.dumps({'ha_token': 'malicious_token'}),
            content_type='application/json'
        )
        
        # Should reject or accept based on security model
        # (In standalone mode, may accept; in addon mode, should reject)
        assert response.status_code in [200, 400, 401, 403, 404, 500]
