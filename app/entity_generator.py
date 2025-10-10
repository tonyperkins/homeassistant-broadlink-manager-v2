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
    
    def __init__(self, storage_manager, broadlink_device_id: str):
        """
        Initialize entity generator
        
        Args:
            storage_manager: StorageManager instance
            broadlink_device_id: HA device ID for the Broadlink device
        """
        self.storage = storage_manager
        self.device_id = broadlink_device_id
    
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
                    'friendly_name': entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                }
            }
        }
        
        light_config = config['lights'][entity_id]
        
        if has_on_off:
            # Separate on/off commands
            light_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': self.device_id},
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
                    'target': {'entity_id': self.device_id},
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
                    'target': {'entity_id': self.device_id},
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
                    'target': {'entity_id': self.device_id},
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
        
        # Count speed commands
        speed_commands = {k: v for k, v in commands.items() if k.startswith('speed_')}
        speed_count = len(speed_commands)
        
        if speed_count == 0:
            logger.warning(f"Fan {entity_id} has no speed commands")
            return None
        
        # Check if reverse/direction command exists
        has_direction = 'reverse' in commands or 'direction' in commands
        
        config = {
            'platform': 'template',
            'fans': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                    'speed_count': speed_count,
                }
            }
        }
        
        fan_config = config['fans'][entity_id]
        
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
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': commands.get(f'speed_{default_speed}', list(speed_commands.values())[0])
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
        
        # Turn off
        if 'turn_off' in commands:
            fan_config['turn_off'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': self.device_id},
                    'data': {
                        'device': device,
                        'command': commands['turn_off']
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
                f"  {commands.get(f'speed_{i}', '')}"
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
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': (
                        "{% if percentage == 0 %}\n"
                        f"  {commands.get('turn_off', '')}\n" +
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
            direction_command = commands.get('reverse') or commands.get('direction')
            fan_config['set_direction'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': self.device_id},
                    'data': {
                        'device': device,
                        'command': direction_command
                    }
                },
                {
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
                }
            ]
        
        return config
    
    def _generate_switch(self, entity_id: str, entity_data: Dict[str, Any],
                        broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template switch configuration"""
        # Similar to light but simpler
        return self._generate_light(entity_id, entity_data, broadlink_commands)
    
    def _generate_media_player(self, entity_id: str, entity_data: Dict[str, Any],
                               broadlink_commands: Dict[str, Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """Generate template media player configuration"""
        device = entity_data['device']
        commands = entity_data['commands']
        
        # Build the media player configuration
        config = {
            'platform': 'template',
            'media_players': {
                entity_id: {
                    'unique_id': entity_id,
                    'friendly_name': entity_data.get('friendly_name', entity_id.replace('_', ' ').title()),
                    'value_template': f"{{{{ is_state('input_boolean.{entity_id}_state', 'on') }}}}",
                }
            }
        }
        
        media_player_config = config['media_players'][entity_id]
        
        # Turn on command
        if 'turn_on' in commands or 'power_on' in commands:
            turn_on_cmd = commands.get('turn_on') or commands.get('power_on')
            media_player_config['turn_on'] = [
                {
                    'service': 'remote.send_command',
                    'target': {'entity_id': self.device_id},
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
                    'target': {'entity_id': self.device_id},
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
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': commands['volume_up']
                }
            }
        
        # Volume down command
        if 'volume_down' in commands:
            media_player_config['volume_down'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': self.device_id},
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
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': mute_cmd
                }
            }
        
        # Play/Pause commands
        if 'play' in commands:
            media_player_config['media_play'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': commands['play']
                }
            }
        
        if 'pause' in commands:
            media_player_config['media_pause'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': commands['pause']
                }
            }
        
        if 'play_pause' in commands:
            media_player_config['media_play_pause'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': commands['play_pause']
                }
            }
        
        # Stop command
        if 'stop' in commands:
            media_player_config['media_stop'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': self.device_id},
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
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': next_cmd
                }
            }
        
        if 'previous' in commands or 'previous_track' in commands:
            prev_cmd = commands.get('previous') or commands.get('previous_track')
            media_player_config['media_previous_track'] = {
                'service': 'remote.send_command',
                'target': {'entity_id': self.device_id},
                'data': {
                    'device': device,
                    'command': prev_cmd
                }
            }
        
        logger.info(f"Generated media player configuration for {entity_id} with {len(commands)} commands")
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
            
            # All entities need a state tracker
            helpers['input_boolean'][f'{entity_id}_state'] = {
                'name': f"{entity_data.get('friendly_name', entity_id)} State",
                'initial': False
            }
            
            # Fans need speed selector
            if entity_type == 'fan':
                speed_commands = {k: v for k, v in entity_data['commands'].items() if k.startswith('speed_')}
                speed_count = len(speed_commands)
                
                options = ['off'] + [str(i) for i in range(1, speed_count + 1)]
                
                helpers['input_select'][f'{entity_id}_speed'] = {
                    'name': f"{entity_data.get('friendly_name', entity_id)} Speed",
                    'options': options,
                    'initial': 'off'
                }
                
                # Add direction selector if reverse/direction command exists
                commands = entity_data.get('commands', {})
                if 'reverse' in commands or 'direction' in commands:
                    helpers['input_select'][f'{entity_id}_direction'] = {
                        'name': f"{entity_data.get('friendly_name', entity_id)} Direction",
                        'options': ['forward', 'reverse'],
                        'initial': 'forward'
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
                "input_boolean: !include broadlink_manager/helpers.yaml\n"
                "input_select: !include broadlink_manager/helpers.yaml"
            ),
            "step2": "Check your configuration (Developer Tools → YAML → Check Configuration)",
            "step3": "Restart Home Assistant",
            "step4": "Your entities will appear in Home Assistant!"
        }
