"""
Unit tests for command learning functionality
"""
import pytest


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandLearning:
    """Test command learning with mocked HA API"""
    
    async def test_learn_command_success(self, web_server_with_mocks, mock_ha_api):
        """Test successful command learning"""
        server = web_server_with_mocks
        
        # Learn a command
        result = await server._learn_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "power",
            "command_type": "ir"
        })
        
        # Verify success
        assert result["success"] is True
        assert "message" in result
        
        # Verify service was called
        assert len(mock_ha_api.services_called) == 1
        service_call = mock_ha_api.services_called[0]
        assert service_call["service"] == "remote.learn_command"
        assert service_call["device"] == "samsung_tv"
        assert service_call["command"] == "power"
        assert service_call["command_type"] == "ir"
        
        # Verify notification was created
        assert len(mock_ha_api.notifications) >= 1
        # Check that at least one notification mentions the command and device
        notifications_text = " ".join([n["message"] for n in mock_ha_api.notifications])
        assert "power" in notifications_text
        assert "samsung_tv" in notifications_text
    
    async def test_learn_command_rf_type(self, web_server_with_mocks, mock_ha_api):
        """Test learning RF command"""
        server = web_server_with_mocks
        
        result = await server._learn_command({
            "entity_id": "remote.living_room_rm_mini",
            "device": "ceiling_fan",
            "command": "fan_on",
            "command_type": "rf"
        })
        
        assert result["success"] is True
        
        # Verify RF command type was passed
        service_call = mock_ha_api.services_called[0]
        assert service_call["command_type"] == "rf"
    
    async def test_learn_command_legacy_format(self, web_server_with_mocks, mock_ha_api):
        """Test learning command with legacy format (no target/data wrapper)"""
        server = web_server_with_mocks
        
        # Use legacy format (flat structure)
        result = await server._learn_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "tv",
            "command": "volume_up"
        })
        
        assert result["success"] is True
        service_call = mock_ha_api.services_called[0]
        assert service_call["command"] == "volume_up"
    
    async def test_learn_multiple_commands(self, web_server_with_mocks, mock_ha_api):
        """Test learning multiple commands in sequence"""
        server = web_server_with_mocks
        
        commands = ["power", "volume_up", "volume_down", "mute"]
        
        for cmd in commands:
            result = await server._learn_command({
                "entity_id": "remote.master_bedroom_rm4_pro",
                "device": "tv",
                "command": cmd,
                "command_type": "ir"
            })
            assert result["success"] is True
        
        # Verify all commands were recorded
        assert len(mock_ha_api.services_called) == len(commands)
        learned_commands = [call["command"] for call in mock_ha_api.services_called]
        assert learned_commands == commands
    
    async def test_learn_command_creates_notification(self, web_server_with_mocks, mock_ha_api):
        """Test that learning creates a notification for user"""
        server = web_server_with_mocks
        
        # Clear any existing notifications
        mock_ha_api.clear_notifications()
        
        result = await server._learn_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "tv",
            "command": "power"
        })
        
        assert result["success"] is True
        
        # Verify notification was created with correct details
        assert len(mock_ha_api.notifications) >= 1
        # Check that at least one notification mentions the command and device
        notifications_text = " ".join([n["message"] for n in mock_ha_api.notifications])
        assert "power" in notifications_text
        assert "tv" in notifications_text
        assert mock_ha_api.notifications[0]["title"] == "Learn Command"
        assert "Press the button" in mock_ha_api.notifications[0]["message"]


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandLearningIntegration:
    """Test command learning integrated with device manager"""
    
    async def test_learn_and_store_command(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage,
        sample_device_data
    ):
        """Test learning a command and storing it in device manager"""
        server = web_server_with_mocks
        device_id = "test_tv"
        
        # Create device
        server.device_manager.create_device(device_id, sample_device_data)
        
        # Learn command
        result = await server._learn_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": device_id,
            "command": "power",
            "command_type": "ir"
        })
        
        assert result["success"] is True
        
        # Simulate HA writing to storage
        mock_broadlink_storage.add_command(
            "abc123",
            device_id,
            "power",
            "JgBQAAABKZIUEhQSFDcUNxQ3FDcUEhQSFBIUNxQSFBIUEhQSFBIUNxQSFBIUEhQ3FDcUNxQ3FBIUNxQ3FDcUNxQ3FAANBQ=="
        )
        
        # Add to device manager
        server.device_manager.add_command(device_id, "power", {
            "command_type": "ir",
            "learned_at": "2025-01-10T12:00:00"
        })
        
        # Verify command was stored
        device = server.device_manager.get_device(device_id)
        assert "power" in device["commands"]
        
        # Verify command exists in storage
        assert mock_broadlink_storage.command_exists("abc123", device_id, "power")
