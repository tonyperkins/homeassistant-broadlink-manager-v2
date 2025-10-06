#!/usr/bin/env python3
"""
Entity Detector for Broadlink Manager Add-on
Detects entity types and roles from command names
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class EntityDetector:
    """Detect entity types and command roles from command names"""
    
    # Pattern definitions: (regex, entity_type, command_role)
    PATTERNS = [
        # Light patterns
        (r'^light_on$', 'light', 'turn_on'),
        (r'^light_off$', 'light', 'turn_off'),
        (r'^light_toggle$', 'light', 'toggle'),
        (r'^lamp_on$', 'light', 'turn_on'),
        (r'^lamp_off$', 'light', 'turn_off'),
        (r'^lamp_toggle$', 'light', 'toggle'),
        
        # Fan patterns
        (r'^fan_off$', 'fan', 'turn_off'),
        (r'^fan_on$', 'fan', 'turn_on'),
        (r'^fan_speed_(\d+)$', 'fan', 'speed'),
        (r'^fan_low$', 'fan', 'speed_low'),
        (r'^fan_medium$', 'fan', 'speed_medium'),
        (r'^fan_high$', 'fan', 'speed_high'),
        (r'^fan_reverse$', 'fan', 'reverse'),
        (r'^fan_direction$', 'fan', 'direction'),
        
        # Switch patterns
        (r'^power$', 'switch', 'toggle'),
        (r'^toggle$', 'switch', 'toggle'),
        (r'^on$', 'switch', 'turn_on'),
        (r'^off$', 'switch', 'turn_off'),
        
        # Media player patterns
        (r'^(power|power_toggle)$', 'media_player', 'power'),
        (r'^vol_up$', 'media_player', 'volume_up'),
        (r'^vol_down$', 'media_player', 'volume_down'),
        (r'^volume_up$', 'media_player', 'volume_up'),
        (r'^volume_down$', 'media_player', 'volume_down'),
        (r'^mute$', 'media_player', 'mute'),
        (r'^play$', 'media_player', 'play'),
        (r'^pause$', 'media_player', 'pause'),
        (r'^stop$', 'media_player', 'stop'),
        (r'^play_pause$', 'media_player', 'play_pause'),
        (r'^next$', 'media_player', 'next'),
        (r'^previous$', 'media_player', 'previous'),
        (r'^ch_up$', 'media_player', 'channel_up'),
        (r'^ch_down$', 'media_player', 'channel_down'),
        (r'^channel_up$', 'media_player', 'channel_up'),
        (r'^channel_down$', 'media_player', 'channel_down'),
    ]
    
    def detect(self, command_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect entity type and command role from command name
        
        Args:
            command_name: The command name to analyze
            
        Returns:
            Tuple of (entity_type, command_role) or (None, None) if no match
        """
        command_lower = command_name.lower().strip()
        
        for pattern, entity_type, command_role in self.PATTERNS:
            match = re.match(pattern, command_lower)
            if match:
                # Handle speed numbers
                if command_role == 'speed' and match.groups():
                    speed_num = match.group(1)
                    return entity_type, f'speed_{speed_num}'
                
                logger.debug(f"Detected '{command_name}' as {entity_type}.{command_role}")
                return entity_type, command_role
        
        logger.debug(f"No pattern match for command: {command_name}")
        return None, None
    
    def group_commands_by_entity(self, device_name: str, commands: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """
        Group commands into potential entities
        
        Args:
            device_name: Name of the device
            commands: Dict of {command_name: command_code}
            
        Returns:
            Dict of potential entities with their commands
        """
        # Group by entity type
        grouped = defaultdict(lambda: defaultdict(dict))
        
        for command_name, command_code in commands.items():
            entity_type, command_role = self.detect(command_name)
            
            if entity_type:
                # Use entity type as key (e.g., "light", "fan")
                grouped[entity_type][command_role] = command_name
        
        # Convert to entity configurations
        entities = {}
        
        for entity_type, command_roles in grouped.items():
            # Generate entity ID
            entity_id = self._generate_entity_id(device_name, entity_type)
            
            # Validate entity has required commands
            if self._is_valid_entity(entity_type, command_roles):
                entities[entity_id] = {
                    "entity_type": entity_type,
                    "device": device_name,
                    "commands": dict(command_roles),
                    "enabled": True,
                    "auto_detected": True
                }
                logger.info(f"Detected {entity_type} entity: {entity_id} with {len(command_roles)} commands")
        
        return entities
    
    def _generate_entity_id(self, device_name: str, entity_type: str) -> str:
        """Generate a Home Assistant entity ID"""
        # Clean device name
        clean_name = device_name.lower()
        clean_name = re.sub(r'[^a-z0-9_]', '_', clean_name)
        clean_name = re.sub(r'_+', '_', clean_name)
        clean_name = clean_name.strip('_')
        
        # Add entity type suffix if not already present
        if entity_type not in clean_name:
            return f"{clean_name}_{entity_type}"
        return clean_name
    
    def _is_valid_entity(self, entity_type: str, command_roles: Dict[str, str]) -> bool:
        """
        Check if the detected entity has the minimum required commands
        
        Args:
            entity_type: Type of entity
            command_roles: Dict of detected command roles
            
        Returns:
            True if entity is valid
        """
        if entity_type == 'light':
            # Light needs either on/off or toggle
            has_on_off = 'turn_on' in command_roles and 'turn_off' in command_roles
            has_toggle = 'toggle' in command_roles
            return has_on_off or has_toggle
        
        elif entity_type == 'fan':
            # Fan needs at least off command or speed commands
            has_off = 'turn_off' in command_roles
            has_speeds = any(role.startswith('speed') for role in command_roles)
            return has_off or has_speeds
        
        elif entity_type == 'switch':
            # Switch needs on/off or toggle
            has_on_off = 'turn_on' in command_roles and 'turn_off' in command_roles
            has_toggle = 'toggle' in command_roles
            return has_on_off or has_toggle
        
        elif entity_type == 'media_player':
            # Media player needs at least power or volume control
            has_power = 'power' in command_roles
            has_volume = 'volume_up' in command_roles or 'volume_down' in command_roles
            return has_power or has_volume
        
        return False
    
    def suggest_missing_commands(self, entity_type: str, existing_commands: List[str]) -> List[str]:
        """
        Suggest commands that would be useful for this entity type
        
        Args:
            entity_type: Type of entity
            existing_commands: List of command roles already present
            
        Returns:
            List of suggested command names
        """
        suggestions = []
        
        if entity_type == 'light':
            if 'turn_on' not in existing_commands:
                suggestions.append('light_on')
            if 'turn_off' not in existing_commands:
                suggestions.append('light_off')
        
        elif entity_type == 'fan':
            if 'turn_off' not in existing_commands:
                suggestions.append('fan_off')
            # Suggest speed commands if none exist
            has_speeds = any(cmd.startswith('speed') for cmd in existing_commands)
            if not has_speeds:
                suggestions.extend(['fan_speed_1', 'fan_speed_2', 'fan_speed_3'])
        
        elif entity_type == 'switch':
            if 'turn_on' not in existing_commands:
                suggestions.append('on')
            if 'turn_off' not in existing_commands:
                suggestions.append('off')
        
        return suggestions
    
    def get_entity_types(self) -> List[str]:
        """Get list of supported entity types"""
        return ['light', 'fan', 'switch', 'media_player']
    
    def get_command_roles_for_type(self, entity_type: str) -> List[str]:
        """Get possible command roles for an entity type"""
        roles = {
            'light': ['turn_on', 'turn_off', 'toggle'],
            'fan': ['turn_on', 'turn_off', 'speed_1', 'speed_2', 'speed_3', 'speed_4', 'speed_5', 'speed_6', 'reverse'],
            'switch': ['turn_on', 'turn_off', 'toggle'],
            'media_player': ['power', 'volume_up', 'volume_down', 'mute', 'play', 'pause', 'stop', 
                           'play_pause', 'next', 'previous', 'channel_up', 'channel_down']
        }
        return roles.get(entity_type, [])
