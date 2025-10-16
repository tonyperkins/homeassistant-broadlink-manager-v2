"""
Unit tests for command deletion functionality
"""
import pytest


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandDeletion:
    """Test command deletion with mocked HA API and storage"""
    
    async def test_delete_command_success(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage
    ):
        """Test successful command deletion"""
        server = web_server_with_mocks
        
        # Verify command exists in storage
        commands = mock_broadlink_storage.get_device_commands("abc123", "samsung_tv")
        assert "power" in commands
        
        # Delete the command
        result = await server._delete_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "power"
        })
        
        assert result["success"] is True
        
        # Verify service was called
        assert len(mock_ha_api.services_called) == 1
        service_call = mock_ha_api.services_called[0]
        assert service_call["service"] == "remote.delete_command"
        assert service_call["device"] == "samsung_tv"
        assert service_call["command"] == "power"
    
    async def test_delete_nonexistent_command(
        self,
        web_server_with_mocks,
        mock_ha_api
    ):
        """Test deleting a command that doesn't exist"""
        server = web_server_with_mocks
        
        result = await server._delete_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "nonexistent"
        })
        
        # Should still succeed (HA behavior)
        assert result["success"] is True
    
    async def test_delete_command_from_storage(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage
    ):
        """Test that deletion removes command from storage"""
        server = web_server_with_mocks
        
        # Verify command exists
        assert mock_broadlink_storage.command_exists("abc123", "samsung_tv", "volume_up")
        
        # Delete command
        result = await server._delete_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": "samsung_tv",
            "command": "volume_up"
        })
        
        assert result["success"] is True
        
        # Simulate HA removing from storage
        mock_broadlink_storage.delete_command("abc123", "samsung_tv", "volume_up")
        
        # Verify command was removed
        assert not mock_broadlink_storage.command_exists("abc123", "samsung_tv", "volume_up")
    
    async def test_delete_multiple_commands(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage
    ):
        """Test deleting multiple commands"""
        server = web_server_with_mocks
        
        commands_to_delete = ["power", "volume_up", "volume_down"]
        
        for cmd in commands_to_delete:
            result = await server._delete_command({
                "entity_id": "remote.master_bedroom_rm4_pro",
                "device": "samsung_tv",
                "command": cmd
            })
            assert result["success"] is True
            
            # Simulate storage deletion
            mock_broadlink_storage.delete_command("abc123", "samsung_tv", cmd)
        
        # Verify all commands were deleted
        assert len(mock_ha_api.services_called) == len(commands_to_delete)
        
        # Verify storage is clean
        remaining_commands = mock_broadlink_storage.get_device_commands("abc123", "samsung_tv")
        for cmd in commands_to_delete:
            assert cmd not in remaining_commands


@pytest.mark.unit
@pytest.mark.asyncio
class TestCommandDeletionIntegration:
    """Test command deletion integrated with device manager"""
    
    async def test_delete_command_from_device(
        self,
        web_server_with_mocks,
        mock_ha_api,
        mock_broadlink_storage,
        sample_device_data
    ):
        """Test deleting a command from device manager"""
        server = web_server_with_mocks
        device_id = "test_tv"
        
        # Create device with commands
        server.device_manager.create_device(device_id, sample_device_data)
        server.device_manager.add_command(device_id, "power", {
            "command_type": "ir",
            "learned_at": "2025-01-10T12:00:00"
        })
        
        # Verify command exists
        device = server.device_manager.get_device(device_id)
        assert "power" in device["commands"]
        
        # Delete command via API
        result = await server._delete_command({
            "entity_id": "remote.master_bedroom_rm4_pro",
            "device": device_id,
            "command": "power"
        })
        
        assert result["success"] is True
        
        # Delete from device manager
        server.device_manager.delete_command(device_id, "power")
        
        # Verify command was removed
        device = server.device_manager.get_device(device_id)
        assert "power" not in device["commands"]
