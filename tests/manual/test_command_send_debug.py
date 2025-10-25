"""
Debug script to test command sending and verify device configuration

This script will:
1. List all Broadlink remote entities in Home Assistant
2. Show which storage file corresponds to which entity
3. Test sending a command using the learned command name (baseline)
4. Help identify why commands aren't working

Usage:
    python tests/manual/test_command_send_debug.py
"""

import json
import requests
from pathlib import Path

# Configuration
HA_URL = "http://homeassistant.local:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlMzcyYmFiYmIyNjQ0YzVkOTI3MTFhNTFjZTcxMTJkNCIsImlhdCI6MTc1NzQ0NDMwOCwiZXhwIjoyMDcyODA0MzA4fQ.hakvxq-vSfZMnBX7dUfVLClx8riDuA4QPxokHz9-x08"
STORAGE_PATH = Path("h:/.storage")


def get_headers():
    """Get headers for HA API requests"""
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }


def get_all_entities():
    """Get all entities from Home Assistant"""
    url = f"{HA_URL}/api/states"
    try:
        response = requests.get(url, headers=get_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get entities: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting entities: {e}")
        return []


def find_broadlink_remotes(entities):
    """Find all Broadlink remote entities"""
    remotes = []
    for entity in entities:
        entity_id = entity.get('entity_id', '')
        if entity_id.startswith('remote.') and 'broadlink' in entity.get('attributes', {}).get('friendly_name', '').lower():
            remotes.append({
                'entity_id': entity_id,
                'friendly_name': entity.get('attributes', {}).get('friendly_name', ''),
                'state': entity.get('state', ''),
                'mac': entity.get('attributes', {}).get('mac', 'unknown')
            })
    return remotes


def list_storage_files():
    """List all Broadlink storage files"""
    pattern = "broadlink_remote_*_codes"
    files = []
    for file in STORAGE_PATH.glob(pattern):
        # Extract MAC from filename
        # Format: broadlink_remote_e870723f13a5_codes
        filename = file.name
        mac_part = filename.replace('broadlink_remote_', '').replace('_codes', '')
        
        # Read file to get command count
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                command_count = len(data.get('data', {}))
        except:
            command_count = 0
        
        files.append({
            'path': file,
            'mac_part': mac_part,
            'command_count': command_count
        })
    return files


def send_test_command(entity_id, command_name):
    """Send a test command using the learned command name"""
    url = f"{HA_URL}/api/services/remote/send_command"
    
    payload = {
        "entity_id": entity_id,
        "command": command_name
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {entity_id}")
    print(f"Command: {command_name}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Command sent successfully")
            return True
        else:
            print(f"❌ Command failed")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("="*60)
    print("Broadlink Command Send Debug")
    print("="*60)
    print()
    
    # Step 1: List all Broadlink remotes in HA
    print("Step 1: Finding Broadlink remote entities in Home Assistant...")
    entities = get_all_entities()
    remotes = find_broadlink_remotes(entities)
    
    if not remotes:
        print("❌ No Broadlink remote entities found!")
        print("   Make sure Broadlink integration is installed and configured")
        return
    
    print(f"✅ Found {len(remotes)} Broadlink remote(s):")
    for i, remote in enumerate(remotes, 1):
        print(f"\n{i}. {remote['entity_id']}")
        print(f"   Name: {remote['friendly_name']}")
        print(f"   State: {remote['state']}")
        print(f"   MAC: {remote['mac']}")
    print()
    
    # Step 2: List storage files
    print("Step 2: Finding Broadlink storage files...")
    storage_files = list_storage_files()
    
    if not storage_files:
        print("❌ No Broadlink storage files found!")
        return
    
    print(f"✅ Found {len(storage_files)} storage file(s):")
    for i, file in enumerate(storage_files, 1):
        print(f"\n{i}. {file['path'].name}")
        print(f"   MAC part: {file['mac_part']}")
        print(f"   Commands: {file['command_count']}")
    print()
    
    # Step 3: Match entities to storage files
    print("Step 3: Matching entities to storage files...")
    matches = []
    for remote in remotes:
        remote_mac = remote['mac'].replace(':', '').lower()
        for file in storage_files:
            if file['mac_part'] in remote_mac or remote_mac in file['mac_part']:
                matches.append({
                    'entity_id': remote['entity_id'],
                    'friendly_name': remote['friendly_name'],
                    'storage_file': file['path'],
                    'command_count': file['command_count']
                })
                print(f"✅ MATCH: {remote['entity_id']} → {file['path'].name}")
    
    if not matches:
        print("⚠️  No matches found - MAC addresses don't align")
        print("\nManual mapping needed:")
        print("Entities:")
        for remote in remotes:
            print(f"  - {remote['entity_id']} (MAC: {remote['mac']})")
        print("\nStorage files:")
        for file in storage_files:
            print(f"  - {file['path'].name} (MAC part: {file['mac_part']})")
    print()
    
    # Step 4: Test sending a command
    print("Step 4: Testing command send...")
    print("\nWhich entity should we test?")
    for i, remote in enumerate(remotes, 1):
        print(f"{i}. {remote['entity_id']} ({remote['friendly_name']})")
    
    try:
        choice = int(input("\nEnter number (or 0 to skip): "))
        if choice > 0 and choice <= len(remotes):
            selected_remote = remotes[choice - 1]
            entity_id = selected_remote['entity_id']
            
            # Find storage file for this entity
            storage_file = None
            for match in matches:
                if match['entity_id'] == entity_id:
                    storage_file = match['storage_file']
                    break
            
            if not storage_file and storage_files:
                storage_file = storage_files[0]['path']
            
            if storage_file:
                # Read commands from storage
                with open(storage_file, 'r') as f:
                    data = json.load(f)
                    commands = data.get('data', {})
                
                print(f"\nAvailable command groups:")
                for i, cmd in enumerate(commands.keys(), 1):
                    print(f"{i}. {cmd}")
                
                cmd_choice = int(input("\nEnter command group number: "))
                if cmd_choice > 0 and cmd_choice <= len(commands):
                    cmd_group = list(commands.keys())[cmd_choice - 1]
                    
                    # Check if it's a group or single command
                    cmd_data = commands[cmd_group]
                    if isinstance(cmd_data, dict):
                        print(f"\nSub-commands in '{cmd_group}':")
                        for i, subcmd in enumerate(cmd_data.keys(), 1):
                            print(f"{i}. {subcmd}")
                        
                        subcmd_choice = int(input("\nEnter sub-command number: "))
                        if subcmd_choice > 0 and subcmd_choice <= len(cmd_data):
                            subcmd = list(cmd_data.keys())[subcmd_choice - 1]
                            
                            # Send using group.subcommand format
                            full_command = f"{cmd_group}.{subcmd}"
                            print(f"\n⚠️  This will send IR/RF signal!")
                            input("Press Enter to send command...")
                            send_test_command(entity_id, full_command)
                    else:
                        # Single command
                        print(f"\n⚠️  This will send IR/RF signal!")
                        input("Press Enter to send command...")
                        send_test_command(entity_id, cmd_group)
    except (ValueError, KeyboardInterrupt):
        print("\nSkipped")
    
    print("\n" + "="*60)
    print("Debug Complete")
    print("="*60)


if __name__ == "__main__":
    main()
