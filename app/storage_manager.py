#!/usr/bin/env python3
"""
Storage Manager for Broadlink Manager Add-on
Manages entity metadata in /config/broadlink_manager/
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class StorageManager:
    """Manage addon storage in /config/broadlink_manager/"""
    
    def __init__(self, base_path: str = "/config/broadlink_manager"):
        self.base_path = Path(base_path)
        self.metadata_file = self.base_path / "metadata.json"
        self.entities_file = self.base_path / "entities.yaml"
        self.helpers_file = self.base_path / "helpers.yaml"
        self.package_file = self.base_path / "package.yaml"
        self.readme_file = self.base_path / "README.md"
        
        self._ensure_directory()
        self._ensure_readme()
        self.metadata = self._load_metadata()
    
    def _ensure_directory(self):
        """Create base directory if it doesn't exist"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directory ready: {self.base_path}")
        except Exception as e:
            logger.error(f"Failed to create storage directory: {e}")
            raise
    
    def _ensure_readme(self):
        """Create README if it doesn't exist"""
        if self.readme_file.exists():
            return
        
        readme_content = """# Broadlink Manager Files

This folder contains auto-generated Home Assistant entities for your Broadlink devices.

## Files

- `metadata.json` - Your entity configurations (edit via addon UI)
  - Each entity specifies which Broadlink device transmits its commands
  - Area assignment is for the controlled device location, not the transmitter
  - Supports custom names and icons
- `entities.yaml` - Generated HA entities (auto-generated, do not edit)
- `helpers.yaml` - Generated helper entities (auto-generated, do not edit)

## Metadata Structure

Each entity in `metadata.json` can have these fields:

```json
{
  "entity_id": {
    "entity_type": "fan",
    "device": "device_name",
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Living Room",
    "friendly_name": "Living Room Ceiling Fan",
    "name": "Office Fan",
    "icon": "mdi:ceiling-fan",
    "commands": {...},
    "enabled": true
  }
}
```

### Field Descriptions

- `entity_type`: Type of HA entity (light, fan, switch, media_player)
- `device`: Command storage key in Broadlink
- `broadlink_entity`: Which Broadlink remote sends commands
- `area`: Where the controlled device is located
- `friendly_name`: Default display name (auto-generated)
- `name`: Custom display name (optional, overrides friendly_name)
- `icon`: Custom MDI icon (optional, e.g., "mdi:ceiling-fan")
- `commands`: Mapping of actions to learned command names
- `enabled`: Whether to generate this entity (true/false)

## Setup

Add these lines to your `configuration.yaml`:

```yaml
# Option 1: Include each platform separately
light: !include broadlink_manager/entities.yaml
fan: !include broadlink_manager/entities.yaml
switch: !include broadlink_manager/entities.yaml
media_player: !include broadlink_manager/entities.yaml
input_boolean: !include broadlink_manager/helpers.yaml
input_select: !include broadlink_manager/helpers.yaml
```

Or use packages (recommended):

```yaml
# Option 2: Use packages (cleaner)
homeassistant:
  packages:
    broadlink_manager: !include broadlink_manager/entities.yaml
```

After adding the includes:
1. Check Configuration (Developer Tools → YAML)
2. Restart Home Assistant
3. Your Broadlink entities will appear!

## Backup

To backup your Broadlink entity configurations, backup this entire folder.

## Support

For issues or questions, visit the Broadlink Manager add-on page.
"""
        try:
            self.readme_file.write_text(readme_content)
            logger.info("Created README.md")
        except Exception as e:
            logger.warning(f"Could not create README: {e}")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load metadata from file"""
        if not self.metadata_file.exists():
            logger.info("No metadata file found, creating new one")
            return {
                "version": 1,
                "entities": {},
                "last_generated": None
            }
        
        try:
            with open(self.metadata_file, 'r') as f:
                data = json.load(f)
                logger.info(f"Loaded metadata with {len(data.get('entities', {}))} entities")
                return data
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")
            return {
                "version": 1,
                "entities": {},
                "last_generated": None
            }
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info("Metadata saved successfully")
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
            raise
    
    def get_entity(self, entity_id: str) -> Optional[Dict[str, Any]]:
        """Get entity metadata by ID"""
        return self.metadata["entities"].get(entity_id)
    
    def get_all_entities(self) -> Dict[str, Dict[str, Any]]:
        """Get all entity metadata"""
        return self.metadata["entities"]
    
    def get_entities_by_type(self, entity_type: str) -> Dict[str, Dict[str, Any]]:
        """Get entities filtered by type"""
        return {
            entity_id: entity_data
            for entity_id, entity_data in self.metadata["entities"].items()
            if entity_data.get("entity_type") == entity_type
        }
    
    def save_entity(self, entity_id: str, entity_data: Dict[str, Any]):
        """Save or update entity metadata"""
        self.metadata["entities"][entity_id] = entity_data
        self._save_metadata()
        logger.info(f"Saved entity: {entity_id}")
    
    def delete_entity(self, entity_id: str) -> bool:
        """Delete entity metadata"""
        if entity_id in self.metadata["entities"]:
            del self.metadata["entities"][entity_id]
            self._save_metadata()
            logger.info(f"Deleted entity: {entity_id}")
            return True
        return False
    
    def update_entity_field(self, entity_id: str, field: str, value: Any):
        """Update a specific field in entity metadata"""
        if entity_id in self.metadata["entities"]:
            self.metadata["entities"][entity_id][field] = value
            self._save_metadata()
            logger.info(f"Updated {field} for entity: {entity_id}")
        else:
            raise ValueError(f"Entity not found: {entity_id}")
    
    def get_entities_by_device(self, device_name: str) -> Dict[str, Dict[str, Any]]:
        """Get all entities for a specific device"""
        return {
            entity_id: entity_data
            for entity_id, entity_data in self.metadata["entities"].items()
            if entity_data.get("device") == device_name
        }
    
    def set_last_generated(self, timestamp: str):
        """Update last generation timestamp"""
        self.metadata["last_generated"] = timestamp
        self._save_metadata()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        entities_by_type = {}
        for entity_data in self.metadata["entities"].values():
            entity_type = entity_data.get("entity_type", "unknown")
            entities_by_type[entity_type] = entities_by_type.get(entity_type, 0) + 1
        
        return {
            "total_entities": len(self.metadata["entities"]),
            "entities_by_type": entities_by_type,
            "last_generated": self.metadata.get("last_generated"),
            "storage_path": str(self.base_path),
            "files_exist": {
                "metadata": self.metadata_file.exists(),
                "entities": self.entities_file.exists(),
                "helpers": self.helpers_file.exists(),
                "readme": self.readme_file.exists()
            }
        }
