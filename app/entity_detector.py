#!/usr/bin/env python3
"""
Entity Detector for Broadlink Manager Add-on
Detects entity types and roles from command names
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
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
        (r'^power_on$', 'media_player', 'turn_on'),
        (r'^power_off$', 'media_player', 'turn_off'),
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
        
        # Climate patterns (AC, heater, heat pump)
        (r'^ac_on$', 'climate', 'turn_on'),
        (r'^ac_off$', 'climate', 'turn_off'),
        (r'^heat_on$', 'climate', 'turn_on'),
        (r'^heat_off$', 'climate', 'turn_off'),
        (r'^cool_on$', 'climate', 'turn_on'),
        (r'^cool_off$', 'climate', 'turn_off'),
        (r'^hvac_off$', 'climate', 'turn_off'),
        
        # Temperature settings
        (r'^temp_(\d+)$', 'climate', 'temperature'),
        (r'^temperature_(\d+)$', 'climate', 'temperature'),
        (r'^set_temp_(\d+)$', 'climate', 'temperature'),
        (r'^temp_up$', 'climate', 'temperature_up'),
        (r'^temp_down$', 'climate', 'temperature_down'),
        (r'^temperature_up$', 'climate', 'temperature_up'),
        (r'^temperature_down$', 'climate', 'temperature_down'),
        
        # HVAC modes
        (r'^mode_heat$', 'climate', 'hvac_mode_heat'),
        (r'^mode_cool$', 'climate', 'hvac_mode_cool'),
        (r'^mode_auto$', 'climate', 'hvac_mode_auto'),
        (r'^mode_dry$', 'climate', 'hvac_mode_dry'),
        (r'^mode_fan$', 'climate', 'hvac_mode_fan_only'),
        (r'^mode_fan_only$', 'climate', 'hvac_mode_fan_only'),
        (r'^heat$', 'climate', 'hvac_mode_heat'),
        (r'^cool$', 'climate', 'hvac_mode_cool'),
        (r'^auto$', 'climate', 'hvac_mode_auto'),
        (r'^dry$', 'climate', 'hvac_mode_dry'),
        
        # Fan modes for climate
        (r'^fan_auto$', 'climate', 'fan_mode_auto'),
        (r'^fan_low$', 'climate', 'fan_mode_low'),
        (r'^fan_medium$', 'climate', 'fan_mode_medium'),
        (r'^fan_high$', 'climate', 'fan_mode_high'),
        (r'^fan_turbo$', 'climate', 'fan_mode_turbo'),
        
        # Swing modes
        (r'^swing_on$', 'climate', 'swing_mode_on'),
        (r'^swing_off$', 'climate', 'swing_mode_off'),
        (r'^swing_vertical$', 'climate', 'swing_mode_vertical'),
        (r'^swing_horizontal$', 'climate', 'swing_mode_horizontal'),
        (r'^swing_both$', 'climate', 'swing_mode_both'),
        
        # Cover patterns (blinds, curtains, shades, garage doors)
        (r'^open$', 'cover', 'open'),
        (r'^close$', 'cover', 'close'),
        (r'^stop$', 'cover', 'stop'),
        (r'^cover_open$', 'cover', 'open'),
        (r'^cover_close$', 'cover', 'close'),
        (r'^cover_stop$', 'cover', 'stop'),
        (r'^blinds_open$', 'cover', 'open'),
        (r'^blinds_close$', 'cover', 'close'),
        (r'^blinds_stop$', 'cover', 'stop'),
        (r'^curtain_open$', 'cover', 'open'),
        (r'^curtain_close$', 'cover', 'close'),
        (r'^curtain_stop$', 'cover', 'stop'),
        (r'^shade_open$', 'cover', 'open'),
        (r'^shade_close$', 'cover', 'close'),
        (r'^shade_stop$', 'cover', 'stop'),
        (r'^garage_open$', 'cover', 'open'),
        (r'^garage_close$', 'cover', 'close'),
        (r'^garage_stop$', 'cover', 'stop'),
        
        # Cover position presets
        (r'^position_(\d+)$', 'cover', 'position'),
        (r'^preset_(\d+)$', 'cover', 'position'),
        
        # Tilt controls for venetian blinds
        (r'^tilt_open$', 'cover', 'open_tilt'),
        (r'^tilt_close$', 'cover', 'close_tilt'),
        (r'^tilt_up$', 'cover', 'open_tilt'),
        (r'^tilt_down$', 'cover', 'close_tilt'),
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
                # Handle speed numbers for fans
                if command_role == 'speed' and match.groups():
                    speed_num = match.group(1)
                    return entity_type, f'speed_{speed_num}'
                
                # Handle temperature numbers for climate
                if command_role == 'temperature' and match.groups():
                    temp_num = match.group(1)
                    return entity_type, f'temperature_{temp_num}'
                
                # Handle position numbers for covers
                if command_role == 'position' and match.groups():
                    position_num = match.group(1)
                    return entity_type, f'position_{position_num}'
                
                logger.debug(f"Detected '{command_name}' as {entity_type}.{command_role}")
                return entity_type, command_role
        
        logger.debug(f"No pattern match for command: {command_name}")
        return None, None
    
    def group_commands_by_entity(self, device_name: str, commands: Dict[str, str], area_name: str = None, broadlink_entity: str = None) -> Dict[str, Dict[str, Any]]:
        """
        Group commands into potential entities
        
        Args:
            device_name: Name of the device
            commands: Dict of {command_name: command_code}
            area_name: Optional area name to assign to entities
            broadlink_entity: Optional Broadlink entity ID that will send these commands (e.g., 'remote.kitchen_broadlink')
            
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
        
        # Extract area from device name if not provided
        if not area_name:
            area_name = self._extract_area_from_device_name(device_name)
        
        # Convert to entity configurations
        entities = {}
        
        for entity_type, command_roles in grouped.items():
            # Generate entity ID
            entity_id = self._generate_entity_id(device_name, entity_type)
            
            # Validate entity has required commands
            if self._is_valid_entity(entity_type, command_roles):
                entity_data = {
                    "entity_type": entity_type,
                    "device": device_name,
                    "commands": dict(command_roles),
                    "friendly_name": self.generate_friendly_name(device_name, entity_type),
                    "area": area_name,
                    "icon": self._suggest_icon(entity_type, device_name),
                    "enabled": True,
                    "auto_detected": True
                }
                
                # Add broadlink_entity if provided
                if broadlink_entity:
                    entity_data["broadlink_entity"] = broadlink_entity
                
                entities[entity_id] = entity_data
                logger.info(f"Detected {entity_type} entity: {entity_id} (area: {area_name}, broadlink: {broadlink_entity or 'not specified'}) with {len(command_roles)} commands")
        
        return entities
    
    def _generate_entity_id(self, device_name: str, entity_type: str) -> str:
        """Generate a Home Assistant entity ID"""
        # Clean device name
        clean_name = device_name.lower()
        clean_name = re.sub(r'[^a-z0-9_]', '_', clean_name)
        clean_name = re.sub(r'_+', '_', clean_name)
        clean_name = clean_name.strip('_')
        
        # The device_name from Broadlink storage already includes area and device
        # (e.g., "tony_s_office_workbench_lamp")
        # Just use it as-is since it already uniquely identifies the device
        return clean_name
    
    def _extract_area_from_device_name(self, device_name: str) -> str:
        """
        Extract area name from device name
        
        Examples:
            tony_s_office_ceiling_fan → Tony's Office
            master_bedroom_lamp → Master Bedroom
            living_room_tv → Living Room
        """
        parts = device_name.split('_')
        
        # Common device types to remove from area name
        device_types = ['ceiling', 'fan', 'lamp', 'light', 'tv', 'workbench', 
                       'table', 'floor', 'desk', 'wall', 'pendant']
        
        # Find where the device type starts
        area_parts = []
        for i, part in enumerate(parts):
            if part.lower() in device_types:
                # Everything before this is the area
                area_parts = parts[:i]
                break
        
        # If no device type found, assume last 1-2 words are device name
        if not area_parts:
            # Take all but last word as area
            area_parts = parts[:-1] if len(parts) > 1 else parts
        
        # Convert to friendly format with possessives
        friendly_parts = []
        i = 0
        while i < len(area_parts):
            part = area_parts[i]
            
            # Check if next part is 's' (possessive)
            if i + 1 < len(area_parts) and area_parts[i + 1] == 's':
                friendly_parts.append(part.title() + "'s")
                i += 2
            else:
                friendly_parts.append(part.title())
                i += 1
        
        return ' '.join(friendly_parts) if friendly_parts else 'Unknown'
    
    def generate_friendly_name(self, device_name: str, entity_type: str) -> str:
        """
        Generate a human-friendly name from device name
        
        Handles possessives: tony_s_office → Tony's Office
        """
        # Split by underscores
        parts = device_name.split('_')
        
        # Process each part
        friendly_parts = []
        i = 0
        while i < len(parts):
            part = parts[i]
            
            # Check if next part is 's' (possessive)
            if i + 1 < len(parts) and parts[i + 1] == 's':
                # This is a possessive: tony_s → Tony's
                friendly_parts.append(part.title() + "'s")
                i += 2  # Skip the 's' part
            else:
                # Regular word
                friendly_parts.append(part.title())
                i += 1
        
        friendly_name = ' '.join(friendly_parts)
        
        # Add entity type suffix if not already in the name
        entity_type_title = entity_type.replace('_', ' ').title()
        if entity_type_title.lower() not in friendly_name.lower():
            friendly_name = f"{friendly_name} {entity_type_title}"
        
        return friendly_name
    
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
            has_power = 'power' in command_roles or ('turn_on' in command_roles and 'turn_off' in command_roles)
            has_volume = 'volume_up' in command_roles or 'volume_down' in command_roles
            return has_power or has_volume
        
        elif entity_type == 'climate':
            # Climate needs at least on/off or temperature control or hvac modes
            has_on_off = 'turn_on' in command_roles and 'turn_off' in command_roles
            has_temps = any(role.startswith('temperature_') for role in command_roles)
            has_temp_control = 'temperature_up' in command_roles or 'temperature_down' in command_roles
            has_hvac_modes = any(role.startswith('hvac_mode_') for role in command_roles)
            return has_on_off or has_temps or has_temp_control or has_hvac_modes
        
        elif entity_type == 'cover':
            # Cover needs at least open/close or stop
            has_open = 'open' in command_roles
            has_close = 'close' in command_roles
            has_stop = 'stop' in command_roles
            has_positions = any(role.startswith('position_') for role in command_roles)
            return has_open or has_close or has_stop or has_positions
        
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
        return ['light', 'fan', 'switch', 'media_player', 'climate', 'cover']
    
    def get_command_roles_for_type(self, entity_type: str) -> List[str]:
        """Get possible command roles for an entity type"""
        roles = {
            'light': ['turn_on', 'turn_off', 'toggle'],
            'fan': ['turn_on', 'turn_off', 'speed_1', 'speed_2', 'speed_3', 'speed_4', 'speed_5', 'speed_6', 'reverse'],
            'switch': ['turn_on', 'turn_off', 'toggle'],
            'media_player': ['power', 'volume_up', 'volume_down', 'mute', 'play', 'pause', 'stop', 
                           'play_pause', 'next', 'previous', 'channel_up', 'channel_down'],
            'climate': ['turn_on', 'turn_off', 'temperature_16', 'temperature_17', 'temperature_18', 'temperature_19',
                       'temperature_20', 'temperature_21', 'temperature_22', 'temperature_23', 'temperature_24',
                       'temperature_25', 'temperature_26', 'temperature_27', 'temperature_28', 'temperature_29',
                       'temperature_30', 'temperature_up', 'temperature_down',
                       'hvac_mode_heat', 'hvac_mode_cool', 'hvac_mode_auto', 'hvac_mode_dry', 'hvac_mode_fan_only',
                       'fan_mode_auto', 'fan_mode_low', 'fan_mode_medium', 'fan_mode_high', 'fan_mode_turbo',
                       'swing_mode_on', 'swing_mode_off', 'swing_mode_vertical', 'swing_mode_horizontal', 'swing_mode_both'],
            'cover': ['open', 'close', 'stop', 'position_0', 'position_25', 'position_50', 'position_75', 'position_100',
                     'open_tilt', 'close_tilt']
        }
        return roles.get(entity_type, [])
    
    def _suggest_icon(self, entity_type: str, device_name: str) -> Optional[str]:
        """
        Suggest an appropriate icon based on entity type and device name
        
        Args:
            entity_type: Type of entity (light, fan, switch, media_player, climate, cover)
            device_name: Name of the device
            
        Returns:
            Suggested MDI icon name or None
        """
        device_lower = device_name.lower()
        
        # Check device name for specific keywords
        if entity_type == 'light':
            if 'ceiling' in device_lower:
                return 'mdi:ceiling-light'
            elif 'lamp' in device_lower or 'table' in device_lower:
                return 'mdi:lamp'
            elif 'floor' in device_lower:
                return 'mdi:floor-lamp'
            elif 'pendant' in device_lower:
                return 'mdi:ceiling-light-outline'
            elif 'wall' in device_lower:
                return 'mdi:wall-sconce'
            else:
                return 'mdi:lightbulb'
        
        elif entity_type == 'fan':
            if 'ceiling' in device_lower:
                return 'mdi:ceiling-fan'
            elif 'tower' in device_lower:
                return 'mdi:fan'
            elif 'desk' in device_lower or 'table' in device_lower:
                return 'mdi:fan'
            else:
                return 'mdi:fan'
        
        elif entity_type == 'switch':
            if 'outlet' in device_lower or 'plug' in device_lower:
                return 'mdi:power-plug'
            elif 'power' in device_lower:
                return 'mdi:power'
            else:
                return 'mdi:light-switch'
        
        elif entity_type == 'media_player':
            if 'tv' in device_lower or 'television' in device_lower:
                return 'mdi:television'
            elif 'speaker' in device_lower or 'audio' in device_lower:
                return 'mdi:speaker'
            elif 'receiver' in device_lower or 'amplifier' in device_lower:
                return 'mdi:amplifier'
            elif 'projector' in device_lower:
                return 'mdi:projector'
            else:
                return 'mdi:play-box'
        
        elif entity_type == 'climate':
            if 'ac' in device_lower or 'air' in device_lower and 'condition' in device_lower:
                return 'mdi:air-conditioner'
            elif 'heat' in device_lower and 'pump' in device_lower:
                return 'mdi:heat-pump'
            elif 'heat' in device_lower:
                return 'mdi:radiator'
            elif 'thermostat' in device_lower:
                return 'mdi:thermostat'
            else:
                return 'mdi:thermostat'
        
        elif entity_type == 'cover':
            if 'blind' in device_lower:
                return 'mdi:blinds'
            elif 'curtain' in device_lower or 'drape' in device_lower:
                return 'mdi:curtains'
            elif 'shade' in device_lower or 'roller' in device_lower:
                return 'mdi:roller-shade'
            elif 'garage' in device_lower:
                return 'mdi:garage'
            elif 'door' in device_lower:
                return 'mdi:door'
            elif 'window' in device_lower:
                return 'mdi:window-shutter'
            else:
                return 'mdi:window-shutter'
        
        return None
