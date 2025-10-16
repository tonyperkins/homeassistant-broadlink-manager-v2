"""
Mock Home Assistant REST API for testing
"""
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class MockHAAPI:
    """Mock Home Assistant REST API"""
    
    def __init__(self):
        self.states = []
        self.services_called = []
        self.notifications = []
        self.areas = []
        self.entities = {}
        self._notification_counter = 0
    
    def add_notification(self, title: str, message: str):
        """Add a notification to the mock"""
        self._notification_counter += 1
        notification_id = f"notification_{self._notification_counter}"
        self.notifications.append({
            "notification_id": notification_id,
            "title": title,
            "message": message
        })
        
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """
        Mock _make_ha_request method
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Optional request data
            
        Returns:
            Mocked response data
        """
        
        # Service calls
        if endpoint == "services/remote/learn_command":
            return await self._mock_learn_command(data)
        elif endpoint == "services/remote/delete_command":
            return await self._mock_delete_command(data)
        elif endpoint == "services/remote/send_command":
            return await self._mock_send_command(data)
        
        # State queries
        elif endpoint == "states":
            return self.states
        elif endpoint.startswith("states/"):
            entity_id = endpoint.replace("states/", "")
            return self._get_state(entity_id)
        
        # Notifications
        elif endpoint == "persistent_notification":
            return self.notifications
        
        # Areas
        elif endpoint == "config/area_registry/list":
            return self.areas
        
        return None
    
    async def _mock_learn_command(self, data: Dict) -> List:
        """
        Mock learning a command
        
        Simulates the Broadlink integration's learn_command service.
        Creates a notification to simulate HA's behavior.
        """
        # Handle both new (target/data) and legacy formats
        entity_id = data.get("target", {}).get("entity_id") or data.get("entity_id")
        device = data.get("data", {}).get("device") or data.get("device")
        command = data.get("data", {}).get("command") or data.get("command")
        command_type = data.get("data", {}).get("command_type", "ir")
        
        # Record the service call
        self.services_called.append({
            "service": "remote.learn_command",
            "entity_id": entity_id,
            "device": device,
            "command": command,
            "command_type": command_type,
            "timestamp": datetime.now().isoformat()
        })
        
        # Create a notification (simulating HA behavior)
        self._notification_counter += 1
        self.notifications.append({
            "notification_id": f"broadlink_learn_{self._notification_counter}",
            "title": "Learn Command",
            "message": f"Press the button to learn '{command}' for device '{device}'",
            "created_at": datetime.now().isoformat()
        })
        
        # Return empty list (HA returns [] on success)
        return []
    
    async def _mock_delete_command(self, data: Dict) -> List:
        """
        Mock deleting a command
        
        Simulates the Broadlink integration's delete_command service.
        """
        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        
        self.services_called.append({
            "service": "remote.delete_command",
            "entity_id": entity_id,
            "device": device,
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        return []
    
    async def _mock_send_command(self, data: Dict) -> List:
        """
        Mock sending a command
        
        Simulates the Broadlink integration's send_command service.
        """
        entity_id = data.get("entity_id")
        device = data.get("device")
        command = data.get("command")
        
        self.services_called.append({
            "service": "remote.send_command",
            "entity_id": entity_id,
            "device": device,
            "command": command,
            "timestamp": datetime.now().isoformat()
        })
        
        return []
    
    def _get_state(self, entity_id: str) -> Optional[Dict]:
        """Get state for an entity"""
        for state in self.states:
            if state.get("entity_id") == entity_id:
                return state
        return None
    
    def add_broadlink_device(self, entity_id: str, name: str, area_id: str = None, unique_id: str = None):
        """
        Add a mock Broadlink device
        
        Args:
            entity_id: Entity ID (e.g., "remote.bedroom_rm4_pro")
            name: Friendly name
            area_id: Optional area ID
            unique_id: Optional unique ID for storage file mapping
        """
        self.states.append({
            "entity_id": entity_id,
            "state": "idle",
            "attributes": {
                "friendly_name": name,
                "supported_features": 0
            },
            "area_id": area_id,
            "unique_id": unique_id or entity_id.split(".")[-1]
        })
    
    def add_area(self, area_id: str, name: str):
        """
        Add a mock area
        
        Args:
            area_id: Area ID (e.g., "master_bedroom")
            name: Area name (e.g., "Master Bedroom")
        """
        self.areas.append({
            "area_id": area_id,
            "name": name
        })
    
    def add_state(self, entity_id: str, state: str, attributes: Dict = None):
        """
        Add a generic entity state
        
        Args:
            entity_id: Entity ID
            state: Entity state
            attributes: Optional attributes dict
        """
        self.states.append({
            "entity_id": entity_id,
            "state": state,
            "attributes": attributes or {}
        })
    
    def get_service_calls(self, service_name: str = None) -> List[Dict]:
        """
        Get recorded service calls, optionally filtered by service name
        
        Args:
            service_name: Optional service name to filter (e.g., "remote.learn_command")
            
        Returns:
            List of service call records
        """
        if service_name:
            return [call for call in self.services_called if call["service"] == service_name]
        return self.services_called
    
    def clear_service_calls(self):
        """Clear all recorded service calls"""
        self.services_called = []
    
    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications = []
        self._notification_counter = 0
    
    def reset(self):
        """Reset all mock data"""
        self.states = []
        self.services_called = []
        self.notifications = []
        self.areas = []
        self.entities = {}
        self._notification_counter = 0
