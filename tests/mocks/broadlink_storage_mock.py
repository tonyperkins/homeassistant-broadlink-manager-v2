"""
Mock Broadlink storage files for testing
"""
import json
from pathlib import Path
from typing import Dict, Any


class MockBroadlinkStorage:
    """
    Mock Broadlink storage file system
    
    Simulates the ~/.homeassistant/.storage/broadlink_remote_*_codes files
    that the Broadlink integration uses to store learned commands.
    """
    
    def __init__(self, temp_dir: Path):
        """
        Initialize mock storage
        
        Args:
            temp_dir: Temporary directory for storage files
        """
        self.storage_path = temp_dir
        self.storage_files = {}  # {device_unique_id: {device_name: {command: code}}}
        
    def create_storage_file(self, device_unique_id: str, device_name: str, commands: Dict[str, str]):
        """
        Create a mock Broadlink storage file
        
        Args:
            device_unique_id: Unique ID of the Broadlink device
            device_name: Device name (e.g., "samsung_tv")
            commands: Dict of {command_name: command_code}
        """
        filename = f"broadlink_remote_{device_unique_id}_codes"
        filepath = self.storage_path / filename
        
        # Initialize or update storage
        if device_unique_id not in self.storage_files:
            self.storage_files[device_unique_id] = {}
        
        if device_name not in self.storage_files[device_unique_id]:
            self.storage_files[device_unique_id][device_name] = {}
        
        # Add commands
        self.storage_files[device_unique_id][device_name].update(commands)
        
        # Write to file
        data = {
            "version": 1,
            "data": self.storage_files[device_unique_id]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_command(self, device_unique_id: str, device_name: str, command_name: str, code: str):
        """
        Add a single command to storage
        
        Args:
            device_unique_id: Unique ID of the Broadlink device
            device_name: Device name
            command_name: Command name (e.g., "power")
            code: IR/RF code (base64 encoded)
        """
        commands = {command_name: code}
        self.create_storage_file(device_unique_id, device_name, commands)
    
    def delete_command(self, device_unique_id: str, device_name: str, command_name: str):
        """
        Delete a command from storage
        
        Args:
            device_unique_id: Unique ID of the Broadlink device
            device_name: Device name
            command_name: Command name to delete
        """
        if device_unique_id in self.storage_files:
            if device_name in self.storage_files[device_unique_id]:
                if command_name in self.storage_files[device_unique_id][device_name]:
                    del self.storage_files[device_unique_id][device_name][command_name]
                    
                    # Rewrite file
                    filename = f"broadlink_remote_{device_unique_id}_codes"
                    filepath = self.storage_path / filename
                    data = {
                        "version": 1,
                        "data": self.storage_files[device_unique_id]
                    }
                    with open(filepath, 'w') as f:
                        json.dump(data, f, indent=2)
    
    def get_all_commands(self, device_unique_id: str = None) -> Dict:
        """
        Get all commands from storage
        
        Args:
            device_unique_id: Optional device ID to filter by
            
        Returns:
            Dict of commands organized by device
        """
        if device_unique_id:
            return self.storage_files.get(device_unique_id, {})
        return self.storage_files
    
    def get_device_commands(self, device_unique_id: str, device_name: str) -> Dict[str, str]:
        """
        Get commands for a specific device
        
        Args:
            device_unique_id: Unique ID of the Broadlink device
            device_name: Device name
            
        Returns:
            Dict of {command_name: command_code}
        """
        return self.storage_files.get(device_unique_id, {}).get(device_name, {})
    
    def command_exists(self, device_unique_id: str, device_name: str, command_name: str) -> bool:
        """
        Check if a command exists in storage
        
        Args:
            device_unique_id: Unique ID of the Broadlink device
            device_name: Device name
            command_name: Command name
            
        Returns:
            True if command exists, False otherwise
        """
        return command_name in self.get_device_commands(device_unique_id, device_name)
    
    def list_storage_files(self) -> list:
        """
        List all storage files
        
        Returns:
            List of storage file paths
        """
        return list(self.storage_path.glob("broadlink_remote_*_codes"))
    
    def clear(self):
        """Clear all storage"""
        self.storage_files = {}
        for file in self.storage_path.glob("broadlink_remote_*_codes"):
            file.unlink()
    
    def get_storage_file_path(self, device_unique_id: str) -> Path:
        """
        Get the path to a storage file
        
        Args:
            device_unique_id: Unique ID of the Broadlink device
            
        Returns:
            Path to the storage file
        """
        filename = f"broadlink_remote_{device_unique_id}_codes"
        return self.storage_path / filename
