"""
Unit tests for API commands endpoints
Tests command learning, sending, and testing functionality
"""

import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from flask import Flask
from app.api import api_bp


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.register_blueprint(api_bp, url_prefix='/api')
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def mock_web_server():
    """Create mock web server"""
    web_server = Mock()
    web_server._learn_command = AsyncMock(return_value={"success": True})
    web_server._get_all_broadlink_commands = AsyncMock(return_value={})
    web_server._make_ha_request = AsyncMock(return_value={})
    return web_server


@pytest.fixture
def mock_storage_manager():
    """Create mock storage manager"""
    storage = Mock()
    storage.get_entity = Mock(return_value=None)
    storage.get_all_entities = Mock(return_value={})
    return storage


@pytest.fixture
def mock_device_manager():
    """Create mock device manager"""
    device_mgr = Mock()
    device_mgr.get_device = Mock(return_value=None)
    return device_mgr


class TestLearnCommand:
    """Test /commands/learn endpoint"""

    def test_learn_command_success(self, app, client, mock_web_server):
        """Test successful command learning"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            # Mock successful learning with code retrieval
            mock_web_server._learn_command = AsyncMock(return_value={"success": True})
            mock_web_server._get_all_broadlink_commands = AsyncMock(return_value={
                "test_device": {"power": "JgBQAAABKJETETcROBE4ERQRFBEUERQRFBE4ETgROBEUERQRFBE4ERQRFBE="}
            })
            
            response = client.post('/api/commands/learn', 
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power",
                    "command_type": "ir"
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_learn_command_missing_entity_id(self, app, client, mock_web_server):
        """Test learning command with missing entity_id"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            response = client.post('/api/commands/learn',
                json={
                    "device": "test_device",
                    "command": "power"
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "entity_id" in data["error"]

    def test_learn_command_missing_device(self, app, client, mock_web_server):
        """Test learning command with missing device"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            response = client.post('/api/commands/learn',
                json={
                    "entity_id": "remote.test",
                    "command": "power"
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "device" in data["error"]

    def test_learn_command_missing_command(self, app, client, mock_web_server):
        """Test learning command with missing command name"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            response = client.post('/api/commands/learn',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device"
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "command" in data["error"]

    def test_learn_command_derives_device_from_device_id(self, app, client, mock_web_server):
        """Test that device name is derived from device_id"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            mock_web_server._learn_command = AsyncMock(return_value={"success": True})
            mock_web_server._get_all_broadlink_commands = AsyncMock(return_value={})
            
            response = client.post('/api/commands/learn',
                json={
                    "entity_id": "remote.test",
                    "device_id": "switch.office_lamp",
                    "command": "power"
                })
            
            # Should derive device="office_lamp" from device_id
            assert response.status_code == 200

    def test_learn_command_no_web_server(self, app, client):
        """Test learning command when web server is not available"""
        with app.app_context():
            app.config['web_server'] = None
            
            response = client.post('/api/commands/learn',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power"
                })
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert "Web server not available" in data["error"]

    def test_learn_command_ha_api_failure(self, app, client, mock_web_server):
        """Test learning command when HA API fails"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            mock_web_server._learn_command = AsyncMock(return_value={"success": False, "error": "HA API error"})
            
            response = client.post('/api/commands/learn',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power"
                })
            
            assert response.status_code == 400


class TestSendRawCommand:
    """Test /commands/send-raw endpoint"""

    def test_send_raw_command_success(self, app, client, mock_web_server):
        """Test sending raw command successfully"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            mock_web_server._make_ha_request = AsyncMock(return_value={})
            
            response = client.post('/api/commands/send-raw',
                json={
                    "entity_id": "remote.test",
                    "command": "JgBQAAABKJETETcROBE4ERQRFBEUERQRFBE4ETgROBEUERQRFBE4ERQRFBE=",
                    "command_type": "ir"
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_send_raw_command_missing_entity_id(self, app, client, mock_web_server):
        """Test sending raw command without entity_id"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            response = client.post('/api/commands/send-raw',
                json={
                    "command": "JgBQAAABKJETETcROBE4ERQRFBEUERQRFBE4ETgROBEUERQRFBE4ERQRFBE="
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "entity_id" in data["error"]

    def test_send_raw_command_missing_command(self, app, client, mock_web_server):
        """Test sending raw command without command"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            response = client.post('/api/commands/send-raw',
                json={
                    "entity_id": "remote.test"
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "command" in data["error"]

    def test_send_raw_command_pending_status(self, app, client, mock_web_server):
        """Test sending raw command with pending status"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            response = client.post('/api/commands/send-raw',
                json={
                    "entity_id": "remote.test",
                    "command": "pending"
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False
            assert "not been learned yet" in data["error"]

    def test_send_raw_command_null_status(self, app, client, mock_web_server):
        """Test sending raw command with null status"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            for invalid_cmd in ["null", "none", ""]:
                response = client.post('/api/commands/send-raw',
                    json={
                        "entity_id": "remote.test",
                        "command": invalid_cmd
                    })
                
                assert response.status_code == 400

    def test_send_raw_command_no_web_server(self, app, client):
        """Test sending raw command when web server unavailable"""
        with app.app_context():
            app.config['web_server'] = None
            
            response = client.post('/api/commands/send-raw',
                json={
                    "entity_id": "remote.test",
                    "command": "JgBQAAABKJETETcROBE4ERQRFBEUERQRFBE4ETgROBEUERQRFBE4ERQRFBE="
                })
            
            assert response.status_code == 500

    def test_send_raw_command_ha_api_failure(self, app, client, mock_web_server):
        """Test sending raw command when HA API fails"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            mock_web_server._make_ha_request = AsyncMock(return_value=None)
            
            response = client.post('/api/commands/send-raw',
                json={
                    "entity_id": "remote.test",
                    "command": "JgBQAAABKJETETcROBE4ERQRFBEUERQRFBE4ETgROBEUERQRFBE4ERQRFBE="
                })
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["success"] is False


class TestTestCommand:
    """Test /commands/test endpoint"""

    def test_test_command_broadlink_success(self, app, client, mock_web_server, mock_storage_manager):
        """Test testing a Broadlink command successfully"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            app.config['storage_manager'] = mock_storage_manager
            
            # Mock entity with Broadlink device
            mock_storage_manager.get_entity = Mock(return_value={
                "device_type": "broadlink",
                "commands": {"power": "JgBQAAA..."}
            })
            
            mock_web_server._make_ha_request = AsyncMock(return_value={})
            
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power",
                    "device_id": "switch.test_device"
                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_test_command_missing_fields(self, app, client, mock_web_server):
        """Test testing command with missing required fields"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            
            # Missing entity_id
            response = client.post('/api/commands/test',
                json={
                    "device": "test_device",
                    "command": "power"
                })
            assert response.status_code == 400
            
            # Missing device
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "command": "power"
                })
            assert response.status_code == 400
            
            # Missing command
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device"
                })
            assert response.status_code == 400

    def test_test_command_derives_device_from_device_id(self, app, client, mock_web_server, mock_storage_manager):
        """Test that device name is derived from device_id"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            app.config['storage_manager'] = mock_storage_manager
            mock_storage_manager.get_entity = Mock(return_value=None)
            mock_web_server._make_ha_request = AsyncMock(return_value={})
            
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "device_id": "switch.office_lamp",
                    "command": "power"
                })
            
            # Should derive device="office_lamp" from device_id
            assert response.status_code == 200

    def test_test_command_with_command_metadata(self, app, client, mock_web_server, mock_storage_manager):
        """Test command with metadata structure"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            app.config['storage_manager'] = mock_storage_manager
            
            # Mock entity with command metadata
            mock_storage_manager.get_entity = Mock(return_value={
                "device_type": "broadlink",
                "commands": {
                    "power": {
                        "code": "JgBQAAA...",
                        "command_type": "ir",
                        "learned_at": "2024-01-01"
                    }
                }
            })
            
            mock_web_server._make_ha_request = AsyncMock(return_value={})
            
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power",
                    "device_id": "switch.test_device"
                })
            
            assert response.status_code == 200

    def test_test_command_no_web_server(self, app, client):
        """Test testing command when web server unavailable"""
        with app.app_context():
            app.config['web_server'] = None
            
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power"
                })
            
            assert response.status_code == 500

    def test_test_command_ha_api_failure(self, app, client, mock_web_server, mock_storage_manager):
        """Test testing command when HA API fails"""
        with app.app_context():
            app.config['web_server'] = mock_web_server
            app.config['storage_manager'] = mock_storage_manager
            mock_storage_manager.get_entity = Mock(return_value=None)
            mock_web_server._make_ha_request = AsyncMock(return_value=None)
            
            response = client.post('/api/commands/test',
                json={
                    "entity_id": "remote.test",
                    "device": "test_device",
                    "command": "power"
                })
            
            assert response.status_code == 400


class TestVerifyCommandInStorage:
    """Test verify_command_in_storage helper function"""

    @pytest.mark.asyncio
    async def test_verify_command_found_immediately(self):
        """Test verification when command is found immediately"""
        from app.api.commands import verify_command_in_storage
        
        mock_web_server = Mock()
        mock_web_server._get_all_broadlink_commands = AsyncMock(return_value={
            "test_device": {"power": "JgBQAAA..."}
        })
        
        result = await verify_command_in_storage(
            mock_web_server, "test_device", "power", max_retries=3
        )
        
        assert result is True
        mock_web_server._get_all_broadlink_commands.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_command_not_found(self):
        """Test verification when command is not found"""
        from app.api.commands import verify_command_in_storage
        
        mock_web_server = Mock()
        mock_web_server._get_all_broadlink_commands = AsyncMock(return_value={
            "test_device": {}
        })
        
        result = await verify_command_in_storage(
            mock_web_server, "test_device", "power", max_retries=2, delay=0.1
        )
        
        assert result is False
        assert mock_web_server._get_all_broadlink_commands.call_count == 2

    @pytest.mark.asyncio
    async def test_verify_command_found_after_retry(self):
        """Test verification when command is found after retry"""
        from app.api.commands import verify_command_in_storage
        
        mock_web_server = Mock()
        # First call returns empty, second call returns command
        mock_web_server._get_all_broadlink_commands = AsyncMock(
            side_effect=[
                {"test_device": {}},
                {"test_device": {"power": "JgBQAAA..."}}
            ]
        )
        
        result = await verify_command_in_storage(
            mock_web_server, "test_device", "power", max_retries=3, delay=0.1
        )
        
        assert result is True
        assert mock_web_server._get_all_broadlink_commands.call_count == 2

    @pytest.mark.asyncio
    async def test_verify_command_exception_handling(self):
        """Test verification handles exceptions gracefully"""
        from app.api.commands import verify_command_in_storage
        
        mock_web_server = Mock()
        mock_web_server._get_all_broadlink_commands = AsyncMock(
            side_effect=Exception("Test error")
        )
        
        result = await verify_command_in_storage(
            mock_web_server, "test_device", "power", max_retries=1
        )
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
