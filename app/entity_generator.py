#!/usr/bin/env python3
"""
Entity Generator for Broadlink Manager Add-on
Generates Home Assistant YAML entity configurations
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


class EntityGenerator:
    """Generate Home Assistant entity YAML configurations"""
    
    def __init__(self, storage_manager, broadlink_device_id: str = None):
        """
        Initialize entity generator
        
        Args:
            storage_manager: StorageManager instance
            broadlink_device_id: Optional default HA device ID for the Broadlink device (for backward compatibility)
        """
        self.storage = storage_manager
        self.default_device_id = broadlink_device_id
    
    def _get_broadlink_entity(self, entity_data: Dict[str, Any]) -> Optional[str]:
        """
        Get the Broadlink entity ID from entity data.
        Checks both 'broadlink_entity' and 'device_id' fields for compatibility.
        
        Args:
            entity_data: Entity configuration dictionary
            
        Returns:
            Broadlink entity ID or None if not found
        """
        return entity_data.get('broadlink_entity') or entity_data.get('device_id') or self.default_device_id
    
    def generate_all(self, broadlink_commands: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate all entity YAML files
        
        Args:
            broadlink_commands: Dict of {device_name: {command_name: command_code}}
            
        Returns:
            Dict with generation results
        """
        try:
            # Get all entities from metadata
            entities = self.storage.get_all_entities()
            
            if not entities:
                logger.warning("No entities configured for generation")
                return {
                    "success": False,
                    "message": "No entities configured. Please configure entities first.",
                    "entities_count": 0
                }
            
            # Build YAML structures
            entities_yaml = self._build_entities_yaml(entities, broadlink_commands)
            helpers_yaml = self._build_helpers_yaml(entities)
            
            # Merge entities and helpers for packages compatibility
            package_yaml = {**entities_yaml, **helpers_yaml}
            
            # Write files
            self._write_yaml_file(self.storage.entities_file, entities_yaml)
            self._write_yaml_file(self.storage.helpers_file, helpers_yaml)
            self._write_yaml_file(self.storage.package_file, package_yaml)
            
            # Update last generated timestamp
            timestamp = datetime.now().isoformat()
            self.storage.set_last_generated(timestamp)
            
            # Count entities by type
            entity_counts = {}
            for entity_data in entities.values():
                entity_type = entity_data.get('entity_type', 'unknown')
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            logger.info(f"Generated entities: {entity_counts}")
            
            return {
                "success": True,
                "message": "Entity files generated successfully",
                "entities_count": len(entities),
                "entity_counts": entity_counts,
                "files": {
                    "entities": str(self.storage.entities_file),
                    "helpers": str(self.storage.helpers_file)
                },
                "timestamp": timestamp,
                "instructions": self._get_setup_instructions()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate entities: {e}", exc_info=True)
            return {
                "success": False,
                "message": f"Generation failed: {str(e)}",
                "entities_count": 0
            }
    
    def _build_entities_yaml(self, entities: Dict[str, Dict[str, Any]], 
                            broadlink_commands: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
        """Build the entities YAML structure"""
        yaml_structure = {}
        
        for entity_id, entity_data in entities.items():
            if not entity_data.get('enabled', True):
                continue
            
            entity_type = entity_data['entity_type']
            
            if entity_type == 'light':
                config = self._generate_light(entity_id, entity_data, broadlink_commands)
            elif entity_type == 'fan':
                config = self._generate_fan(entity_id, entity_data, broadlink_commands)
            elif entity_type == 'switch':
                config = self._generate_switch(entity_id, entity_data, broadlink_commands)
            elif entity_type == 'media_player':
                config = self._generate_media_player(entity_id, entity_data, broadlink_commands)
            elif entity_type == 'climate':
                config = self._generate_climate(entity_id, entity_data, broadlink_commands)
            elif entity_type == 'cover':
                config = self._generate_cover(entity_id, entity_data, broadlink_commands)
            else:
                logger.warning(f"Unknown entity type: {entity_type} for {entity_id}")
                continue
            
            if config:
                # Initialize platform list if needed
                if entity_type not in yaml_structure:
                    yaml_structure[entity_type] = []
                
                yaml_structure[entity_type].append(config)
        
        return yaml_structure
    
    def _generate_light(self, entity_id: str, entity_data: Dict[str, Any],
                       broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template light configuration"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(f"No broadlink_entity specified for {entity_id} and no default device_id")
            return None
        
        # Check if we have the required commands
        has_on_off = 'turn_on' in commands and 'turn_off' in commands
        has_toggle = 'toggle' in commands
        
        if not (has_on_off or has_toggle):
            logger.warning(f"Light {entity_id} missing required commands")
            return None
        
        config = {
            'platform': 'template',
            'lights': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('name') or entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                }
            }
        }
        
        light_config = config['lights'][entity_id]
        
        # Add icon if specified
        if entity_data.get('icon'):
            light_config['icon_template'] = entity_data['icon']
        
        if has_on_off:
            # Separate on/off commands
            light_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_on']
                    }
                },
                {
                    'service': 'input_boolean.turn_on',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
            
            light_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_off']
                    }
                },
                {
                    'service': 'input_boolean.turn_off',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        else:
            # Toggle command
            light_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['toggle']
                    }
                },
                {
                    'service': 'input_boolean.turn_on',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
            
            light_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['toggle']
                    }
                },
                {
                    'service': 'input_boolean.turn_off',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        
        return config
    
    def _generate_fan(self, entity_id: str, entity_data: Dict[str, Any],
                     broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template fan configuration"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(f"No broadlink_entity specified for {entity_id} and no default device_id")
            return None
        
        # Count speed commands - support both 'speed_N' and 'fan_speed_N' patterns
        speed_commands = {}
        for k, v in commands.items():
            if k.startswith('speed_') or k.startswith('fan_speed_'):
                # Extract speed number from command name
                if k.startswith('fan_speed_'):
                    speed_num = k.replace('fan_speed_', '')
                else:
                    speed_num = k.replace('speed_', '')
                
                # Store with normalized key 'speed_N'
                if speed_num.isdigit():
                    speed_commands[f'speed_{speed_num}'] = v
        
        speed_count = len(speed_commands)
        
        if speed_count == 0:
            logger.warning(f"Fan {entity_id} has no speed commands")
            return None
        
        # Check if reverse/direction command exists (support fan_reverse too)
        has_direction = 'reverse' in commands or 'direction' in commands or 'fan_reverse' in commands
        
        # For now, always enable direction support for fans (even if no command exists yet)
        # This allows the UI to show direction controls
        has_direction = True
        
        config = {
            'platform': 'template',
            'fans': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('name') or entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                    'speed_count': speed_count,
                }
            }
        }
        
        fan_config = config['fans'][entity_id]
        
        # Note: icon_template is not supported for fan entities in HA
        # Icons must be set via entity customization in HA UI or entity registry
        
        # Percentage template
        percentage_conditions = []
        for i in range(1, speed_count + 1):
            percentage = int((i / speed_count) * 100)
            percentage_conditions.append(f"{{%- elif is_state('input_select.{entity_id}_speed', '{i}') -%}}")
            percentage_conditions.append(f"  {percentage}")
        
        fan_config['percentage_template'] = (
            f"{{%- if is_state('input_select.{entity_id}_speed', 'off') -%}}\n"
            f"  0\n" +
            '\n'.join(percentage_conditions) +
            f"\n{{%- endif -%}}"
        )
        
        # Turn on (default to medium speed)
        default_speed = (speed_count + 1) // 2
        fan_config['turn_on'] = [
            {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': speed_commands.get(f'speed_{default_speed}', list(speed_commands.values())[0])
                }
            },
            {
                'service': 'input_boolean.turn_on',
                'target': {'entity_id': f'input_boolean.{entity_id}_state'}
            },
            {
                'service': 'input_select.select_option',
                'target': {'entity_id': f'input_select.{entity_id}_speed'},
                'data': {'option': str(default_speed)}
            }
        ]
        
        # Turn off (required for fan entities)
        # Prefer fan_off, then turn_off, then fallback to lowest speed
        turn_off_command = commands.get('fan_off') or commands.get('turn_off', speed_commands.get('speed_1', list(speed_commands.values())[0]))
        fan_config['turn_off'] = [
            {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': turn_off_command
                }
            },
            {
                'service': 'input_boolean.turn_off',
                'target': {'entity_id': f'input_boolean.{entity_id}_state'}
            },
            {
                'service': 'input_select.select_option',
                'target': {'entity_id': f'input_select.{entity_id}_speed'},
                'data': {'option': 'off'}
            }
        ]
        
        # Set percentage
        set_percentage_option_conditions = []  # For input_select (speed numbers)
        set_percentage_command_conditions = []  # For remote commands
        
        for i in range(1, speed_count + 1):
            percentage = int((i / speed_count) * 100)
            
            # Template for input_select option (just the number)
            set_percentage_option_conditions.append(
                f"{{%- elif percentage <= {percentage} -%}}\n"
                f"  {i}"
            )
            
            # Template for remote command (the actual command name)
            set_percentage_command_conditions.append(
                f"{{%- elif percentage <= {percentage} -%}}\n"
                f"  {speed_commands.get(f'speed_{i}', '')}"
            )
        
        fan_config['set_percentage'] = [
            {
                'service': 'input_select.select_option',
                'target': {'entity_id': f'input_select.{entity_id}_speed'},
                'data': {
                    'option': (
                        "{% if percentage == 0 %}\n"
                        "  off\n" +
                        '\n'.join(set_percentage_option_conditions) +
                        "\n{% endif %}"
                    )
                }
            },
            {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': (
                        "{% if percentage == 0 %}\n"
                        f"  {commands.get('fan_off') or commands.get('turn_off', '')}\n" +
                        '\n'.join(set_percentage_command_conditions) +
                        "\n{% endif %}"
                    )
                }
            }
        ]
        
        # Add direction support if reverse/direction command exists
        if has_direction:
            # Direction template
            fan_config['direction_template'] = f"{{{{ states('input_select.{entity_id}_direction') }}}}"
            
            # Set direction action
            direction_command = commands.get('reverse') or commands.get('direction') or commands.get('fan_reverse')
            
            # Build set_direction actions
            set_direction_actions = []
            
            # Only send remote command if direction command exists
            if direction_command:
                set_direction_actions.append({
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': direction_command
                    }
                })
            
            # Always update the input_select to track direction state
            set_direction_actions.append({
                'service': 'input_select.select_option',
                'target': {'entity_id': f'input_select.{entity_id}_direction'},
                'data': {
                    'option': (
                        "{% if direction == 'forward' %}\n"
                        "  reverse\n"
                        "{% else %}\n"
                        "  forward\n"
                        "{% endif %}"
                    )
                }
            })
            
            fan_config['set_direction'] = set_direction_actions
        
        return config
    
    def _generate_switch(self, entity_id: str, entity_data: Dict[str, Any],
                        broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template switch configuration"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(f"No broadlink_entity specified for {entity_id} and no default device_id")
            return None
        
        # Check if we have the required commands
        has_on_off = 'turn_on' in commands and 'turn_off' in commands
        has_toggle = 'toggle' in commands
        
        if not (has_on_off or has_toggle):
            logger.warning(f"Switch {entity_id} missing required commands")
            return None
        
        config = {
            'platform': 'template',
            'switches': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('name') or entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                }
            }
        }
        
        switch_config = config['switches'][entity_id]
        
        # Add icon if specified
        if entity_data.get('icon'):
            switch_config['icon_template'] = entity_data['icon']
        
        if has_on_off:
            # Separate on/off commands
            switch_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_on']
                    }
                },
                {
                    'service': 'input_boolean.turn_on',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
            
            switch_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_off']
                    }
                },
                {
                    'service': 'input_boolean.turn_off',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        else:
            # Toggle command
            switch_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['toggle']
                    }
                },
                {
                    'service': 'input_boolean.turn_on',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
            
            switch_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['toggle']
                    }
                },
                {
                    'service': 'input_boolean.turn_off',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        
        return config
    
    def _generate_media_player(self, entity_id: str, entity_data: Dict[str, Any],
                               broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template media player configuration"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(f"No broadlink_entity specified for {entity_id} and no default device_id")
            return None
        
        # Build the media player configuration
        config = {
            'platform': 'template',
            'media_players': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('name') or entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                }
            }
        }
        
        media_player_config = config['media_players'][entity_id]
        
        # Note: icon_template support varies by platform
        # For media_player, icons should be set via entity customization
        # Keeping icon in metadata for future use/documentation
        
        # Turn on command
        if 'turn_on' in commands or 'power_on' in commands:
            turn_on_cmd = commands.get('turn_on') or commands.get('power_on')
            media_player_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': turn_on_cmd
                    }
                },
                {
                    'service': 'input_boolean.turn_on',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        
        # Turn off command
        if 'turn_off' in commands or 'power_off' in commands:
            turn_off_cmd = commands.get('turn_off') or commands.get('power_off')
            media_player_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': turn_off_cmd
                    }
                },
                {
                    'service': 'input_boolean.turn_off',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        
        # Volume up command
        if 'volume_up' in commands:
            media_player_config['volume_up'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['volume_up']
                }
            }
        
        # Volume down command
        if 'volume_down' in commands:
            media_player_config['volume_down'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['volume_down']
                }
            }
        
        # Mute command
        if 'mute' in commands or 'volume_mute' in commands:
            mute_cmd = commands.get('mute') or commands.get('volume_mute')
            media_player_config['volume_mute'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': mute_cmd
                }
            }
        
        # Play/Pause commands
        if 'play' in commands:
            media_player_config['media_play'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['play']
                }
            }
        
        if 'pause' in commands:
            media_player_config['media_pause'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['pause']
                }
            }
        
        if 'play_pause' in commands:
            media_player_config['media_play_pause'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['play_pause']
                }
            }
        
        # Stop command
        if 'stop' in commands:
            media_player_config['media_stop'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['stop']
                }
            }
        
        # Next/Previous track
        if 'next' in commands or 'next_track' in commands:
            next_cmd = commands.get('next') or commands.get('next_track')
            media_player_config['media_next_track'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': next_cmd
                }
            }
        
        if 'previous' in commands or 'previous_track' in commands:
            prev_cmd = commands.get('previous') or commands.get('previous_track')
            media_player_config['media_previous_track'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': prev_cmd
                }
            }
        
        logger.info(f"Generated media player configuration for {entity_id} with {len(commands)} commands")
        return config
    
    def _generate_climate(self, entity_id: str, entity_data: Dict[str, Any],
                         broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template climate configuration for IR/RF AC units"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(f"No broadlink_entity specified for {entity_id} and no default device_id")
            return None
        
        # Check for basic on/off commands
        has_on = 'turn_on' in commands
        has_off = 'turn_off' in commands
        
        if not (has_on or has_off):
            logger.warning(f"Climate {entity_id} missing turn_on or turn_off commands")
            return None
        
        # Build the climate configuration using template platform
        config = {
            'platform': 'template',
            'climates': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('name') or entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                    'current_temperature_template': "{{ 22 }}",  # Static temperature since IR/RF has no feedback
                    'target_temperature_template': "{{ states('input_number.{}_target_temp'.format('" + entity_id + "')) | float }}",
                    'min_temp': 16,
                    'max_temp': 30,
                }
            }
        }
        
        climate_config = config['climates'][entity_id]
        
        # Add icon if specified
        if entity_data.get('icon'):
            climate_config['icon_template'] = entity_data['icon']
        
        # Add turn_on action
        if has_on:
            climate_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_on']
                    }
                },
                {
                    'service': 'input_boolean.turn_on',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        
        # Add turn_off action
        if has_off:
            climate_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_off']
                    }
                },
                {
                    'service': 'input_boolean.turn_off',
                    'target': {'entity_id': f'input_boolean.{entity_id}_state'}
                }
            ]
        
        # Add set_temperature action (uses turn_on for now)
        if has_on:
            climate_config['set_temperature'] = [
                {
                    'service': 'input_number.set_value',
                    'target': {'entity_id': f'input_number.{entity_id}_target_temp'},
                    'data': {
                        'value': '{{ temperature }}'
                    }
                },
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['turn_on']
                    }
                }
            ]
        
        logger.info(f"Generated template climate configuration for {entity_id}")
        
        return config
    
    def _generate_cover(self, entity_id: str, entity_data: Dict[str, Any],
                       broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template cover configuration"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Get the Broadlink entity to use (from entity data or default)
        broadlink_entity = self._get_broadlink_entity(entity_data)
        if not broadlink_entity:
            logger.error(f"No broadlink_entity specified for {entity_id} and no default device_id")
            return None
        
        # Check for required commands
        has_open = 'open' in commands
        has_close = 'close' in commands
        has_stop = 'stop' in commands
        
        if not (has_open or has_close):
            logger.warning(f"Cover {entity_id} missing open or close commands")
            return None
        
        # Build the cover configuration
        config = {
            'platform': 'template',
            'covers': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('name') or entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_select.{entity_id}_position', 'open') }}}}",
                }
            }
        }
        
        cover_config = config['covers'][entity_id]
        
        # Add icon if specified
        if entity_data.get('icon'):
            cover_config['icon_template'] = entity_data['icon']
        
        # Open cover command
        if has_open:
            cover_config['open_cover'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['open']
                    }
                },
                {
                    'service': 'input_select.select_option',
                    'target': {'entity_id': f'input_select.{entity_id}_position'},
                    'data': {'option': 'open'}
                }
            ]
        
        # Close cover command
        if has_close:
            cover_config['close_cover'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['close']
                    }
                },
                {
                    'service': 'input_select.select_option',
                    'target': {'entity_id': f'input_select.{entity_id}_position'},
                    'data': {'option': 'closed'}
                }
            ]
        
        # Stop cover command (optional but recommended)
        if has_stop:
            cover_config['stop_cover'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': commands['stop']
                }
            }
        
        # Check for position commands
        position_commands = {k: v for k, v in commands.items() if k.startswith('position_')}
        if position_commands:
            # Add position template
            cover_config['position_template'] = f"{{{{ states('input_number.{entity_id}_position') | int }}}}"
            
            # Add set position action
            position_conditions = []
            for pos_key in sorted(position_commands.keys()):
                pos_value = int(pos_key.split('_')[1])
                position_conditions.append(
                    f"{{%- elif position == {pos_value} -%}}\n"
                    f"  {position_commands[pos_key]}"
                )
            
            cover_config['set_cover_position'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': broadlink_entity},
                'data': {
                    'device': device,
                    'command': (
                        "{% if position == 0 %}\n"
                        f"  {commands.get('close', '')}\n" +
                        '\n'.join(position_conditions) +
                        "\n{% elif position == 100 %}\n"
                        f"  {commands.get('open', '')}\n"
                        "{% endif %}"
                    )
                }
            }
        
        # Check for tilt commands
        has_open_tilt = 'open_tilt' in commands
        has_close_tilt = 'close_tilt' in commands
        
        if has_open_tilt or has_close_tilt:
            if has_open_tilt:
                cover_config['open_cover_tilt'] = {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['open_tilt']
                    }
                }
            
            if has_close_tilt:
                cover_config['close_cover_tilt'] = {
                    'service': 'remote.send_command',
                    'target': {'entity_id': broadlink_entity},
                    'data': {
                        'device': device,
                        'command': commands['close_tilt']
                    }
                }
        
        logger.info(f"Generated cover configuration for {entity_id} with {len(commands)} commands")
        return config
    
    def _build_helpers_yaml(self, entities: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Build helper entities (input_boolean, input_select)"""
        helpers = {
            'input_boolean': {},
            'input_select': {}
        }
        
        for entity_id, entity_data in entities.items():
            if not entity_data.get('enabled', True):
                continue
            
            entity_type = entity_data['entity_type']
            
            # Get display name (prefer 'name' over 'friendly_name')
            display_name = entity_data.get('name') or entity_data.get('friendly_name', entity_id)
            
            # All entities need a state tracker
            helpers['input_boolean'][f'{entity_id}_state'] = {
                'name': f"{display_name} State",
                'initial': False
            }
            
            # Fans need speed selector
            if entity_type == 'fan':
                # Count speed commands - support both 'speed_N' and 'fan_speed_N' patterns
                speed_count = 0
                for k in entity_data['commands'].keys():
                    if k.startswith('speed_') or k.startswith('fan_speed_'):
                        # Extract speed number from command name
                        if k.startswith('fan_speed_'):
                            speed_num = k.replace('fan_speed_', '')
                        else:
                            speed_num = k.replace('speed_', '')
                        
                        if speed_num.isdigit():
                            speed_count += 1
                
                options = ['off'] + [str(i) for i in range(1, speed_count + 1)]
                
                helpers['input_select'][f'{entity_id}_speed'] = {
                    'name': f"{display_name} Speed",
                    'options': options,
                    'initial': 'off'
                }
                
                # Add direction selector if reverse/direction command exists
                commands = entity_data.get('commands', {})
                if 'reverse' in commands or 'direction' in commands or 'fan_reverse' in commands:
                    helpers['input_select'][f'{entity_id}_direction'] = {
                        'name': f"{display_name} Direction",
                        'options': ['forward', 'reverse'],
                        'initial': 'forward'
                    }
            
            # Climate entities need HVAC mode and temperature tracking
            elif entity_type == 'climate':
                commands = entity_data.get('commands', {})
                
                # Add HVAC mode selector if mode commands exist
                hvac_modes = []
                if any(k.startswith('hvac_mode_') for k in commands.keys()):
                    for mode in ['off', 'heat', 'cool', 'auto', 'dry', 'fan_only']:
                        if f'hvac_mode_{mode}' in commands or mode == 'off':
                            hvac_modes.append(mode)
                    
                    if hvac_modes:
                        helpers['input_select'][f'{entity_id}_hvac_mode'] = {
                            'name': f"{display_name} HVAC Mode",
                            'options': hvac_modes,
                            'initial': 'off'
                        }
                
                # Add fan mode selector if fan mode commands exist
                fan_modes = []
                if any(k.startswith('fan_mode_') for k in commands.keys()):
                    for mode in ['auto', 'low', 'medium', 'high', 'turbo']:
                        if f'fan_mode_{mode}' in commands:
                            fan_modes.append(mode)
                    
                    if fan_modes:
                        helpers['input_select'][f'{entity_id}_fan_mode'] = {
                            'name': f"{display_name} Fan Mode",
                            'options': fan_modes,
                            'initial': 'auto' if 'auto' in fan_modes else fan_modes[0]
                        }
                
                # Add temperature tracking
                temp_commands = {k: v for k, v in commands.items() if k.startswith('temperature_') and k not in ['temperature_up', 'temperature_down']}
                if temp_commands:
                    temps = [int(k.split('_')[1]) for k in temp_commands.keys()]
                    min_temp = min(temps)
                    max_temp = max(temps)
                    helpers['input_number'] = helpers.get('input_number', {})
                    helpers['input_number'][f'{entity_id}_target_temp'] = {
                        'name': f"{display_name} Target Temperature",
                        'min': min_temp,
                        'max': max_temp,
                        'step': 1,
                        'initial': (min_temp + max_temp) // 2,
                        'unit_of_measurement': '°C'
                    }
            
            # Cover entities need position tracking
            elif entity_type == 'cover':
                commands = entity_data.get('commands', {})
                
                # Add position selector
                helpers['input_select'][f'{entity_id}_position'] = {
                    'name': f"{display_name} Position",
                    'options': ['open', 'closed', 'partial'],
                    'initial': 'closed'
                }
                
                # Add position slider if position commands exist
                position_commands = {k: v for k, v in commands.items() if k.startswith('position_')}
                if position_commands:
                    helpers['input_number'] = helpers.get('input_number', {})
                    helpers['input_number'][f'{entity_id}_position'] = {
                        'name': f"{display_name} Position",
                        'min': 0,
                        'max': 100,
                        'step': 1,
                        'initial': 0,
                        'unit_of_measurement': '%'
                    }
        
        return helpers
    
    def _write_yaml_file(self, file_path: Path, data: Dict[str, Any]):
        """Write YAML file with proper formatting"""
        try:
            with open(file_path, 'w') as f:
                f.write("# Auto-generated by Broadlink Manager\n")
                f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# DO NOT EDIT THIS FILE MANUALLY - Changes will be overwritten\n\n")
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            logger.info(f"Written YAML file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write YAML file {file_path}: {e}")
            raise
    
    def _get_setup_instructions(self) -> Dict[str, str]:
        """Get setup instructions for the user"""
        return {
            "step1": "Add these lines to your configuration.yaml:",
            "code": (
                "# Broadlink Manager Entities\n"
                "light: !include broadlink_manager/entities.yaml\n"
                "fan: !include broadlink_manager/entities.yaml\n"
                "switch: !include broadlink_manager/entities.yaml\n"
                "media_player: !include broadlink_manager/entities.yaml\n"
                "climate: !include broadlink_manager/entities.yaml\n"
                "cover: !include broadlink_manager/entities.yaml\n"
                "input_boolean: !include broadlink_manager/helpers.yaml\n"
                "input_select: !include broadlink_manager/helpers.yaml\n"
                "input_number: !include broadlink_manager/helpers.yaml"
            ),
            "step2": "Check your configuration (Developer Tools → YAML → Check Configuration)",
            "step3": "Restart Home Assistant",
            "step4": "Your entities will appear in Home Assistant!"
        }
