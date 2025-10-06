#!/usr/bin/env python3
"""
Area Manager for Broadlink Manager Add-on
Handles automatic area assignment for generated entities
"""

import logging
import aiohttp
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AreaManager:
    """Manage area assignments for Home Assistant entities"""
    
    def __init__(self, ha_url: str, ha_token: str):
        """
        Initialize area manager
        
        Args:
            ha_url: Home Assistant API URL (e.g., http://supervisor/core)
            ha_token: Supervisor token for authentication
        """
        self.ha_url = ha_url
        self.ha_token = ha_token
    
    async def get_or_create_area(self, area_name: str) -> Optional[str]:
        """
        Get area ID by name, or create it if it doesn't exist
        
        Args:
            area_name: Human-readable area name (e.g., "Tony's Office")
            
        Returns:
            Area ID if found/created, None on error
        """
        try:
            # Get all areas
            areas = await self._get_areas()
            
            # Look for existing area (case-insensitive)
            for area in areas:
                if area.get('name', '').lower() == area_name.lower():
                    logger.info(f"Found existing area: {area_name} (ID: {area['area_id']})")
                    return area['area_id']
            
            # Area doesn't exist, create it
            logger.info(f"Creating new area: {area_name}")
            new_area = await self._create_area(area_name)
            
            if new_area and 'area_id' in new_area:
                logger.info(f"Created area: {area_name} (ID: {new_area['area_id']})")
                return new_area['area_id']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting/creating area '{area_name}': {e}")
            return None
    
    async def assign_entity_to_area(self, entity_id: str, area_id: str) -> bool:
        """
        Assign an entity to an area
        
        Args:
            entity_id: Full entity ID (e.g., "light.office_ceiling_fan_light")
            area_id: Area ID to assign to
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get the entity to find its entry_id
            get_url = f"{self.ha_url}/api/config/entity_registry"
            headers = {
                'Authorization': f'Bearer {self.ha_token}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                # Get all entities to find the entry_id
                async with session.get(get_url, headers=headers) as response:
                    if response.status != 200:
                        logger.error(f"Failed to get entity registry: {response.status}")
                        return False
                    
                    entities = await response.json()
                    
                    # Find the entity
                    entity_entry = None
                    if isinstance(entities, list):
                        for entity in entities:
                            if entity.get('entity_id') == entity_id:
                                entity_entry = entity
                                break
                    elif isinstance(entities, dict) and 'entities' in entities:
                        for entity in entities['entities']:
                            if entity.get('entity_id') == entity_id:
                                entity_entry = entity
                                break
                    
                    if not entity_entry:
                        logger.warning(f"Entity {entity_id} not found in registry (may not exist yet)")
                        return False
                    
                    entry_id = entity_entry.get('id') or entity_entry.get('entry_id')
                    if not entry_id:
                        logger.error(f"No entry_id found for {entity_id}")
                        return False
                    
                    # Update the entity with area_id
                    update_url = f"{self.ha_url}/api/config/entity_registry/{entry_id}"
                    async with session.post(update_url, headers=headers, json={'area_id': area_id}) as update_response:
                        if update_response.status == 200:
                            logger.info(f"Assigned {entity_id} to area {area_id}")
                            return True
                        else:
                            error_text = await update_response.text()
                            logger.error(f"Failed to assign {entity_id} to area: {update_response.status} - {error_text}")
                            return False
                        
        except Exception as e:
            logger.error(f"Error assigning entity {entity_id} to area: {e}")
            return False
    
    async def assign_entities_to_areas(self, entities_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Assign multiple entities to their areas based on metadata
        
        Args:
            entities_metadata: Dict of entity configurations with area information
            
        Returns:
            Dict with assignment results
        """
        results = {
            'total': len(entities_metadata),
            'assigned': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        # Group entities by area
        entities_by_area = {}
        for entity_id, entity_data in entities_metadata.items():
            area_name = entity_data.get('area')
            if not area_name:
                results['skipped'] += 1
                results['details'].append({
                    'entity_id': entity_id,
                    'status': 'skipped',
                    'reason': 'No area specified'
                })
                continue
            
            if area_name not in entities_by_area:
                entities_by_area[area_name] = []
            entities_by_area[area_name].append(entity_id)
        
        # Process each area
        for area_name, entity_ids in entities_by_area.items():
            # Get or create the area
            area_id = await self.get_or_create_area(area_name)
            
            if not area_id:
                # Failed to get/create area
                for entity_id in entity_ids:
                    results['failed'] += 1
                    results['details'].append({
                        'entity_id': entity_id,
                        'status': 'failed',
                        'reason': f'Could not get/create area: {area_name}'
                    })
                continue
            
            # Assign each entity to the area
            for entity_id in entity_ids:
                # Convert entity_id to full format (add platform prefix)
                entity_data = entities_metadata[entity_id]
                entity_type = entity_data.get('entity_type', 'light')
                full_entity_id = f"{entity_type}.{entity_id}"
                
                success = await self.assign_entity_to_area(full_entity_id, area_id)
                
                if success:
                    results['assigned'] += 1
                    results['details'].append({
                        'entity_id': full_entity_id,
                        'area': area_name,
                        'status': 'success'
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'entity_id': full_entity_id,
                        'area': area_name,
                        'status': 'failed',
                        'reason': 'API call failed'
                    })
        
        logger.info(f"Area assignment complete: {results['assigned']} assigned, {results['failed']} failed, {results['skipped']} skipped")
        return results
    
    async def _get_areas(self) -> List[Dict[str, Any]]:
        """Get all areas from Home Assistant"""
        try:
            # Use WebSocket API to get areas
            url = f"{self.ha_url}/api/websocket"
            
            async with aiohttp.ClientSession() as session:
                # First try REST API endpoint
                rest_url = f"{self.ha_url}/api/config/area_registry"
                headers = {
                    'Authorization': f'Bearer {self.ha_token}',
                    'Content-Type': 'application/json'
                }
                
                async with session.get(rest_url, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        # Result might be a list or dict with 'areas' key
                        if isinstance(result, list):
                            return result
                        elif isinstance(result, dict) and 'areas' in result:
                            return result['areas']
                        else:
                            logger.warning(f"Unexpected areas response format: {type(result)}")
                            return []
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to get areas: {response.status} - {error_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting areas: {e}")
            return []
    
    async def _create_area(self, area_name: str) -> Optional[Dict[str, Any]]:
        """Create a new area in Home Assistant"""
        try:
            url = f"{self.ha_url}/api/config/area_registry"
            headers = {
                'Authorization': f'Bearer {self.ha_token}',
                'Content-Type': 'application/json'
            }
            
            # Just send the name, HA will generate the area_id
            data = {
                'name': area_name
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        logger.info(f"Created area successfully: {result}")
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to create area: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error creating area: {e}")
            return None
