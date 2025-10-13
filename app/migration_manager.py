#!/usr/bin/env python3
"""
Migration Manager for Broadlink Manager Add-on
Automatically discovers existing Broadlink commands and creates metadata
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class MigrationManager:
    """Manage automatic migration of existing Broadlink setups"""
    
    def __init__(self, storage_manager, entity_detector, storage_path: Path):
        """
        Initialize migration manager
        
        Args:
            storage_manager: StorageManager instance
            entity_detector: EntityDetector instance
            storage_path: Path to HA .storage directory
        """
        self.storage = storage_manager
        self.detector = entity_detector
        self.storage_path = storage_path
    
    async def check_and_migrate(self, broadlink_devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check if migration is needed and perform it
        
        Handles three scenarios:
        1. First-time users: No commands, no metadata → Skip (nothing to migrate)
        2. Existing BL Manager users: Has metadata → Skip (already migrated)
        3. Existing Broadlink users: Has commands, no metadata → Migrate!
        
        Args:
            broadlink_devices: List of detected Broadlink devices
            
        Returns:
            Dict with migration results
        """
        try:
            # Check if metadata already exists and has entities
            existing_entities = self.storage.get_all_entities()
            
            # Scenario 2: Existing BL Manager users
            if existing_entities:
                logger.info(f"📋 Existing Broadlink Manager user detected: {len(existing_entities)} entities already configured")
                logger.info("ℹ️  Skipping automatic migration (metadata already exists)")
                return {
                    'needed': False,
                    'reason': 'Existing Broadlink Manager installation',
                    'scenario': 'existing_bl_manager_user',
                    'existing_entities': len(existing_entities),
                    'message': f'Found existing configuration with {len(existing_entities)} entities'
                }
            
            # Check if there are any learned commands
            learned_commands = await self._discover_learned_commands(broadlink_devices)
            
            # Scenario 1: First-time users (no commands learned yet)
            if not learned_commands:
                logger.info("👋 Welcome! First-time Broadlink Manager user detected")
                logger.info("ℹ️  No learned commands found - you can start learning commands via the web interface")
                return {
                    'needed': False,
                    'reason': 'No learned commands found',
                    'scenario': 'first_time_user',
                    'message': 'Welcome! Start by learning commands via the web interface'
                }
            
            # Scenario 3: Existing Broadlink users (new to BL Manager)
            logger.info(f"🎉 Existing Broadlink user detected: Found {len(learned_commands)} devices with learned commands")
            logger.info("🔄 Starting automatic migration to Broadlink Manager...")
            result = await self._perform_migration(learned_commands, broadlink_devices)
            result['scenario'] = 'existing_broadlink_user'
            
            return result
            
        except Exception as e:
            logger.error(f"Error during migration check: {e}", exc_info=True)
            return {
                'needed': False,
                'error': str(e),
                'scenario': 'error'
            }
    
    async def _discover_learned_commands(self, broadlink_devices: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Discover all learned commands from storage files
        
        Returns:
            Dict of {device_name: {commands, broadlink_entity, area}}
        """
        try:
            # Find all Broadlink command storage files
            storage_files = list(self.storage_path.glob("broadlink_remote_*_codes"))
            
            if not storage_files:
                logger.info("No Broadlink command storage files found")
                return {}
            
            logger.info(f"Found {len(storage_files)} Broadlink storage files")
            
            # Create mapping of storage files to Broadlink devices
            device_map = self._create_device_map(storage_files, broadlink_devices)
            
            all_commands = {}
            
            for storage_file in storage_files:
                try:
                    with open(storage_file, 'r') as f:
                        data = json.load(f)
                    
                    # Get device info for this storage file
                    device_info = device_map.get(storage_file.name, {})
                    broadlink_entity = device_info.get('entity_id', 'remote.broadlink')
                    area_name = device_info.get('area_name', 'Unknown')
                    
                    # Extract commands for each device
                    for device_name, commands in data.get('data', {}).items():
                        if isinstance(commands, dict) and commands:
                            all_commands[device_name] = {
                                'commands': commands,
                                'broadlink_entity': broadlink_entity,
                                'area_name': area_name,
                                'storage_file': storage_file.name
                            }
                            logger.info(f"Discovered device '{device_name}' with {len(commands)} commands (Broadlink: {broadlink_entity}, Area: {area_name})")
                
                except Exception as e:
                    logger.warning(f"Error reading storage file {storage_file}: {e}")
                    continue
            
            return all_commands
            
        except Exception as e:
            logger.error(f"Error discovering learned commands: {e}")
            return {}
    
    def _create_device_map(self, storage_files: List[Path], broadlink_devices: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Create mapping from storage file names to Broadlink device info
        
        Returns:
            Dict of {storage_filename: {entity_id, area_name, ...}}
        """
        device_map = {}
        
        for device in broadlink_devices:
            unique_id = device.get('unique_id', '')
            if unique_id:
                storage_filename = f"broadlink_remote_{unique_id}_codes"
                device_map[storage_filename] = {
                    'entity_id': device.get('entity_id', 'remote.broadlink'),
                    'area_name': device.get('area_name', 'Unknown'),
                    'device_name': device.get('name', 'Broadlink'),
                    'area_id': device.get('area_id')
                }
        
        return device_map
    
    async def _perform_migration(self, learned_commands: Dict[str, Dict[str, Any]], 
                                 broadlink_devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform the actual migration
        
        Args:
            learned_commands: Dict of discovered commands
            broadlink_devices: List of Broadlink devices
            
        Returns:
            Dict with migration results
        """
        migrated_entities = {}
        skipped_devices = []
        errors = []
        
        for device_name, device_data in learned_commands.items():
            try:
                commands = device_data['commands']
                broadlink_entity = device_data['broadlink_entity']
                area_name = device_data['area_name']
                
                # Use entity detector to identify potential entities
                detected_entities = self.detector.group_commands_by_entity(
                    device_name=device_name,
                    commands=commands,
                    area_name=area_name,
                    broadlink_entity=broadlink_entity
                )
                
                if detected_entities:
                    # Save each detected entity
                    for entity_id, entity_data in detected_entities.items():
                        self.storage.save_entity(entity_id, entity_data)
                        migrated_entities[entity_id] = entity_data
                        logger.info(f"Migrated entity: {entity_id} ({entity_data['entity_type']})")
                else:
                    skipped_devices.append({
                        'device_name': device_name,
                        'reason': 'No valid entities detected from commands',
                        'command_count': len(commands)
                    })
                    logger.warning(f"Could not detect entities for device: {device_name}")
                
            except Exception as e:
                error_msg = f"Error migrating device {device_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Update migration timestamp
        migration_info = {
            'migrated_at': datetime.now().isoformat(),
            'migrated_entities': len(migrated_entities),
            'skipped_devices': len(skipped_devices),
            'errors': len(errors),
            'broadlink_devices': len(broadlink_devices)
        }
        
        # Store migration info in metadata
        metadata = self.storage.metadata
        metadata['migration'] = migration_info
        self.storage._save_metadata()
        
        result = {
            'success': True,
            'needed': True,
            'migrated_entities': len(migrated_entities),
            'entities': list(migrated_entities.keys()),
            'skipped_devices': skipped_devices,
            'errors': errors,
            'migration_info': migration_info,
            'message': f"Successfully migrated {len(migrated_entities)} entities from {len(learned_commands)} devices"
        }
        
        logger.info(f"Migration complete: {result['message']}")
        
        return result
    
    async def force_migration(self, broadlink_devices: List[Dict[str, Any]], 
                             overwrite: bool = False) -> Dict[str, Any]:
        """
        Force migration even if metadata exists
        
        Args:
            broadlink_devices: List of detected Broadlink devices
            overwrite: If True, overwrites existing entities. If False, only adds new ones.
            
        Returns:
            Dict with migration results
        """
        try:
            learned_commands = await self._discover_learned_commands(broadlink_devices)
            
            if not learned_commands:
                return {
                    'success': False,
                    'message': 'No learned commands found to migrate'
                }
            
            if not overwrite:
                # Filter out devices that already have entities
                existing_entities = self.storage.get_all_entities()
                existing_devices = set(e.get('device') for e in existing_entities.values())
                
                learned_commands = {
                    device_name: data 
                    for device_name, data in learned_commands.items()
                    if device_name not in existing_devices
                }
                
                if not learned_commands:
                    return {
                        'success': False,
                        'message': 'All discovered devices already have entities'
                    }
            
            result = await self._perform_migration(learned_commands, broadlink_devices)
            result['forced'] = True
            result['overwrite'] = overwrite
            
            return result
            
        except Exception as e:
            logger.error(f"Error during forced migration: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status
        
        Returns:
            Dict with migration status information
        """
        metadata = self.storage.metadata
        migration_info = metadata.get('migration', {})
        
        has_entities = len(self.storage.get_all_entities()) > 0
        
        return {
            'has_metadata': has_entities,
            'entity_count': len(self.storage.get_all_entities()),
            'migration_performed': bool(migration_info),
            'migration_info': migration_info
        }
