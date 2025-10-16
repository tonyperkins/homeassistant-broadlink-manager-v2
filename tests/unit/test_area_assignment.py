"""
Unit tests for area assignment functionality
"""
import pytest


@pytest.mark.unit
@pytest.mark.asyncio
class TestAreaManagement:
    """Test area management with mocked WebSocket API"""
    
    async def test_get_existing_area(self, area_manager_with_mock, mock_websocket_api):
        """Test getting an existing area"""
        manager = area_manager_with_mock
        
        area_id = await manager.get_or_create_area("Master Bedroom")
        
        assert area_id is not None
        assert area_id == "master_bedroom"
    
    async def test_create_new_area(self, area_manager_with_mock, mock_websocket_api):
        """Test creating a new area"""
        manager = area_manager_with_mock
        
        # Create new area
        area_id = await manager.get_or_create_area("Kitchen")
        
        assert area_id is not None
        assert area_id == "kitchen"
        
        # Verify area was added to mock
        assert mock_websocket_api.area_exists("kitchen")
    
    async def test_assign_entity_to_area(self, area_manager_with_mock, mock_websocket_api):
        """Test assigning an entity to an area"""
        manager = area_manager_with_mock
        
        # Add entity to mock registry
        mock_websocket_api.add_entity("light.bedroom_light")
        
        # Assign to area
        success = await manager.assign_entity_to_area("light.bedroom_light", "master_bedroom")
        
        assert success is True
        
        # Verify entity was assigned
        entity = mock_websocket_api.get_entity("light.bedroom_light")
        assert entity["area_id"] == "master_bedroom"
    
    async def test_assign_nonexistent_entity(self, area_manager_with_mock, mock_websocket_api):
        """Test assigning a non-existent entity"""
        manager = area_manager_with_mock
        
        # Try to assign entity that doesn't exist
        success = await manager.assign_entity_to_area("light.nonexistent", "master_bedroom")
        
        assert success is False
    
    async def test_check_entity_exists(self, area_manager_with_mock, mock_websocket_api):
        """Test checking if entity exists"""
        manager = area_manager_with_mock
        
        # Add entity
        mock_websocket_api.add_entity("light.bedroom_light")
        
        # Check existence
        exists = await manager.check_entity_exists("light.bedroom_light")
        assert exists is True
        
        # Check non-existent
        exists = await manager.check_entity_exists("light.nonexistent")
        assert exists is False


@pytest.mark.unit
@pytest.mark.asyncio
class TestBulkAreaAssignment:
    """Test bulk area assignment operations"""
    
    async def test_assign_multiple_entities(self, area_manager_with_mock, mock_websocket_api):
        """Test assigning multiple entities to areas"""
        manager = area_manager_with_mock
        
        # Create test entities
        entities_metadata = {
            "bedroom_light": {
                "entity_type": "light",
                "area": "Master Bedroom"
            },
            "living_room_fan": {
                "entity_type": "fan",
                "area": "Living Room"
            },
            "office_lamp": {
                "entity_type": "light",
                "area": "Office"
            }
        }
        
        # Add entities to mock registry
        for entity_id, data in entities_metadata.items():
            full_id = f"{data['entity_type']}.{entity_id}"
            mock_websocket_api.add_entity(full_id)
        
        # Assign all entities
        results = await manager.assign_entities_to_areas(entities_metadata)
        
        assert results["total"] == 3
        assert results["assigned"] == 3
        assert results["failed"] == 0
        assert results["skipped"] == 0
    
    async def test_assign_entities_creates_areas(self, area_manager_with_mock, mock_websocket_api):
        """Test that assigning entities creates missing areas"""
        manager = area_manager_with_mock
        
        # Don't clear areas - just verify Kitchen doesn't exist yet
        assert not mock_websocket_api.area_exists("kitchen")
        
        entities_metadata = {
            "kitchen_light": {
                "entity_type": "light",
                "area": "Kitchen"
            }
        }
        
        # Add entity to registry
        mock_websocket_api.add_entity("light.kitchen_light")
        
        # Assign entity (should create area)
        results = await manager.assign_entities_to_areas(entities_metadata)
        
        assert results["assigned"] == 1
        
        # Verify area was created
        assert mock_websocket_api.area_exists("kitchen")
    
    async def test_skip_entities_without_area(self, area_manager_with_mock, mock_websocket_api):
        """Test that entities without area are skipped"""
        manager = area_manager_with_mock
        
        entities_metadata = {
            "bedroom_light": {
                "entity_type": "light",
                "area": "Master Bedroom"
            },
            "no_area_light": {
                "entity_type": "light"
                # No area specified
            }
        }
        
        # Add entities to registry
        mock_websocket_api.add_entity("light.bedroom_light")
        mock_websocket_api.add_entity("light.no_area_light")
        
        results = await manager.assign_entities_to_areas(entities_metadata)
        
        assert results["assigned"] == 1
        assert results["skipped"] == 1
