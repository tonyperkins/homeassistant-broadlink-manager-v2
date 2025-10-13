"""
Unit tests for AreaManager
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.unit
class TestAreaManager:
    """Test AreaManager functionality"""

    def test_initialization(self, area_manager):
        """Test AreaManager initializes correctly"""
        assert area_manager.ha_url == "http://localhost:8123"
        assert area_manager.ha_token == "test_token"
        assert area_manager.ws_url == "ws://localhost:8123/api/websocket"
        assert area_manager.message_id == 1

    @pytest.mark.asyncio
    async def test_get_or_create_area_existing(self, area_manager):
        """Test getting an existing area"""
        # Mock WebSocket response with existing area
        mock_areas = [
            {"area_id": "master_bedroom", "name": "Master Bedroom"},
            {"area_id": "living_room", "name": "Living Room"},
        ]

        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = mock_areas
            result = await area_manager.get_or_create_area("Master Bedroom")

            assert result == "master_bedroom"
            mock_ws.assert_called_once_with("config/area_registry/list")

    @pytest.mark.asyncio
    async def test_get_or_create_area_new(self, area_manager):
        """Test creating a new area"""
        # Mock WebSocket responses - return list with existing areas (but not matching)
        # then return the newly created area
        mock_existing_areas = [{"area_id": "other_area", "name": "Other Area"}]
        mock_new_area = {"area_id": "new_area", "name": "New Area"}

        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            # First call returns list without our area, second call returns new area
            mock_ws.side_effect = [mock_existing_areas, mock_new_area]
            result = await area_manager.get_or_create_area("New Area")

            assert result == "new_area"
            assert mock_ws.call_count == 2
            # Verify the create call was made
            mock_ws.assert_any_call("config/area_registry/create", name="New Area")

    @pytest.mark.asyncio
    async def test_assign_entity_to_area(self, area_manager):
        """Test assigning an entity to an area"""
        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = {"entity_id": "light.bedroom", "area_id": "bedroom"}
            result = await area_manager.assign_entity_to_area(
                "light.bedroom", "bedroom"
            )

            assert result is True
            mock_ws.assert_called_once_with(
                "config/entity_registry/update",
                entity_id="light.bedroom",
                area_id="bedroom",
            )

    @pytest.mark.asyncio
    async def test_assign_entity_to_area_failure(self, area_manager):
        """Test failed entity assignment"""
        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = None
            result = await area_manager.assign_entity_to_area(
                "light.bedroom", "bedroom"
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_check_entity_exists(self, area_manager):
        """Test checking if entity exists"""
        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = {"entity_id": "light.bedroom"}
            result = await area_manager.check_entity_exists("light.bedroom")

            assert result is True
            mock_ws.assert_called_once_with(
                "config/entity_registry/get", entity_id="light.bedroom"
            )

    @pytest.mark.asyncio
    async def test_check_entity_not_exists(self, area_manager):
        """Test checking for non-existent entity"""
        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = None
            result = await area_manager.check_entity_exists("light.nonexistent")

            assert result is False

    @pytest.mark.asyncio
    async def test_reload_config(self, area_manager):
        """Test reloading Home Assistant configuration"""
        with patch.object(
            area_manager, "_send_ws_command", new_callable=AsyncMock
        ) as mock_ws:
            mock_ws.return_value = {}
            result = await area_manager.reload_config()

            assert result is True
            mock_ws.assert_called_once_with(
                "call_service",
                domain="homeassistant",
                service="reload_core_config",
                service_data={},
                return_response=False,
            )
