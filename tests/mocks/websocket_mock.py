"""
Mock WebSocket API for area management
"""
from typing import Dict, Any, Optional


class MockWebSocketAPI:
    """
    Mock Home Assistant WebSocket API
    
    Simulates the WebSocket API used for area management and entity registry operations.
    """
    
    def __init__(self):
        self.areas = {}
        self.entities = {}
        self.message_id = 1
        self.connected = True
        
    async def send_command(self, command_type: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Mock _send_ws_command method
        
        Args:
            command_type: WebSocket command type
            **kwargs: Command parameters
            
        Returns:
            Command result or None on error
        """
        
        if not self.connected:
            return None
        
        if command_type == "config/area_registry/list":
            return list(self.areas.values())
        
        elif command_type == "config/area_registry/create":
            area_name = kwargs.get("name")
            area_id = area_name.lower().replace(" ", "_").replace("'", "")
            area = {
                "area_id": area_id,
                "name": area_name
            }
            self.areas[area_id] = area
            return area
        
        elif command_type == "config/entity_registry/update":
            entity_id = kwargs.get("entity_id")
            area_id = kwargs.get("area_id")
            
            if entity_id in self.entities:
                self.entities[entity_id]["area_id"] = area_id
                return self.entities[entity_id]
            return None
        
        elif command_type == "config/entity_registry/get":
            entity_id = kwargs.get("entity_id")
            return self.entities.get(entity_id)
        
        elif command_type == "config/entity_registry/list":
            return list(self.entities.values())
        
        elif command_type == "call_service":
            # Mock service calls
            domain = kwargs.get("domain")
            service = kwargs.get("service")
            service_data = kwargs.get("service_data", {})
            
            # Return success for reload operations
            if domain == "homeassistant" and service == "reload_core_config":
                return {"success": True}
            
            return None
        
        return None
    
    def add_entity(self, entity_id: str, area_id: str = None, **kwargs):
        """
        Add a mock entity to registry
        
        Args:
            entity_id: Entity ID (e.g., "light.bedroom_light")
            area_id: Optional area ID
            **kwargs: Additional entity attributes
        """
        self.entities[entity_id] = {
            "entity_id": entity_id,
            "area_id": area_id,
            "platform": entity_id.split(".")[0],
            **kwargs
        }
    
    def add_area(self, area_id: str, name: str):
        """
        Add a mock area
        
        Args:
            area_id: Area ID (e.g., "master_bedroom")
            name: Area name (e.g., "Master Bedroom")
        """
        self.areas[area_id] = {
            "area_id": area_id,
            "name": name
        }
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """
        Get entity from registry
        
        Args:
            entity_id: Entity ID
            
        Returns:
            Entity data or None
        """
        return self.entities.get(entity_id)
    
    def get_area(self, area_id: str) -> Optional[Dict]:
        """
        Get area from registry
        
        Args:
            area_id: Area ID
            
        Returns:
            Area data or None
        """
        return self.areas.get(area_id)
    
    def entity_exists(self, entity_id: str) -> bool:
        """
        Check if entity exists in registry
        
        Args:
            entity_id: Entity ID
            
        Returns:
            True if entity exists
        """
        return entity_id in self.entities
    
    def area_exists(self, area_id: str) -> bool:
        """
        Check if area exists
        
        Args:
            area_id: Area ID
            
        Returns:
            True if area exists
        """
        return area_id in self.areas
    
    def set_connected(self, connected: bool):
        """
        Set connection status
        
        Args:
            connected: Connection status
        """
        self.connected = connected
    
    def clear_entities(self):
        """Clear all entities"""
        self.entities = {}
    
    def clear_areas(self):
        """Clear all areas"""
        self.areas = {}
    
    def reset(self):
        """Reset all mock data"""
        self.areas = {}
        self.entities = {}
        self.message_id = 1
        self.connected = True
