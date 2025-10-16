"""
Mock for testing Supervisor add-on mode restrictions
"""
from typing import Dict, Any, Optional
from .ha_api_mock import MockHAAPI


class MockHAAPIWithSupervisorRestrictions(MockHAAPI):
    """
    Mock HA API that simulates restrictions present in Supervisor add-on mode
    
    This mock extends MockHAAPI to simulate the security restrictions that
    may be present when running as a Home Assistant add-on.
    """
    
    def __init__(self, strict_mode: bool = True):
        """
        Initialize mock with optional strict mode
        
        Args:
            strict_mode: If True, restricted endpoints return errors.
                        If False, they return empty results (graceful degradation)
        """
        super().__init__()
        self.strict_mode = strict_mode
        self.restricted_endpoints = [
            "config/config_entries/entry",
            "config/config_entries/entry/",  # Includes reload endpoints
        ]
        self.access_attempts = []  # Track attempts to access restricted endpoints
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """
        Mock _make_ha_request method with supervisor restrictions
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Optional request data
            
        Returns:
            Mocked response data or error
        """
        
        # Check if endpoint is restricted
        is_restricted = any(
            restricted in endpoint 
            for restricted in self.restricted_endpoints
        )
        
        if is_restricted:
            # Log the access attempt
            self.access_attempts.append({
                "method": method,
                "endpoint": endpoint,
                "data": data,
                "restricted": True
            })
            
            if self.strict_mode:
                # Simulate permission denied error
                raise PermissionError(
                    f"Access denied to {endpoint} in Supervisor add-on mode. "
                    "This endpoint requires elevated permissions."
                )
            else:
                # Graceful degradation - return empty result
                return None if method.upper() == "GET" else {}
        
        # For non-restricted endpoints, use parent implementation
        return await super().make_request(method, endpoint, data)
    
    def get_restricted_access_attempts(self) -> list:
        """
        Get list of attempts to access restricted endpoints
        
        Returns:
            List of access attempt records
        """
        return self.access_attempts
    
    def was_restricted_endpoint_accessed(self, endpoint: str) -> bool:
        """
        Check if a restricted endpoint was accessed
        
        Args:
            endpoint: Endpoint to check
            
        Returns:
            True if endpoint was accessed
        """
        return any(
            endpoint in attempt["endpoint"]
            for attempt in self.access_attempts
        )
    
    def clear_access_attempts(self):
        """Clear the access attempts log"""
        self.access_attempts = []


class MockConfigLoaderSupervisorMode:
    """Mock ConfigLoader for Supervisor add-on mode"""
    
    def __init__(self):
        self.mode = 'supervisor'
        self.is_supervisor = True
    
    def get_ha_url(self) -> str:
        return 'http://supervisor/core'
    
    def get_ha_token(self) -> str:
        return 'SUPERVISOR_TOKEN_MOCK'
    
    def get_config_path(self):
        from pathlib import Path
        return Path('/config')
    
    def get_storage_path(self):
        return self.get_config_path() / '.storage'
    
    def get_broadlink_manager_path(self):
        return self.get_config_path() / 'broadlink_manager'


class MockConfigLoaderStandaloneMode:
    """Mock ConfigLoader for standalone mode"""
    
    def __init__(self):
        self.mode = 'standalone'
        self.is_supervisor = False
    
    def get_ha_url(self) -> str:
        return 'http://localhost:8123'
    
    def get_ha_token(self) -> str:
        return 'LONG_LIVED_ACCESS_TOKEN_MOCK'
    
    def get_config_path(self):
        from pathlib import Path
        return Path('/config')
    
    def get_storage_path(self):
        return self.get_config_path() / '.storage'
    
    def get_broadlink_manager_path(self):
        return self.get_config_path() / 'broadlink_manager'
