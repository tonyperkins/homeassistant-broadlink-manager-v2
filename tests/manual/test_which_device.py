"""
Test to identify which Broadlink device has the ceiling fan light commands

This will:
1. Find all Broadlink devices
2. Show which storage file has the ceiling fan light commands
3. Test sending the command from each device to see which one works

Usage:
    python tests/manual/test_which_device.py
"""

import json
import requests
from pathlib import Path
import time

# Configuration
HA_URL = "http://homeassistant.local:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlMzcyYmFiYmIyNjQ0YzVkOTI3MTFhNTFjZTcxMTJkNCIsImlhdCI6MTc1NzQ0NDMwOCwiZXhwIjoyMDcyODA0MzA4fQ.hakvxq-vSfZMnBX7dUfVLClx8riDuA4QPxokHz9-x08"
STORAGE_PATH = Path("h:/.storage")
TEST_COMMAND_GROUP = "tony_s_office_ceiling_fan_light"


def get_headers():
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
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def find_broadlink_remotes(entities):
    """Find all Broadlink remote entities"""
    remotes = []
    for entity in entities:
        entity_id = entity.get('entity_id', '')
        if entity_id.startswith('remote.'):
            attributes = entity.get('attributes', {})
            # Check if it's a Broadlink device
            if 'mac' in attributes or 'broadlink' in attributes.get('friendly_name', '').lower():
                remotes.append({
                    'entity_id': entity_id,
                    'friendly_name': attributes.get('friendly_name', entity_id),
                    'state': entity.get('state', ''),
                    'mac': attributes.get('mac', 'unknown'),
                    'model': attributes.get('model', 'unknown')
                })
    return remotes


def find_storage_files():
    """Find all Broadlink storage files and check for ceiling fan commands"""
    pattern = "broadlink_remote_*_codes"
    files_with_commands = []
    
    for file in STORAGE_PATH.glob(pattern):
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                commands = data.get('data', {})
                
                # Check if this file has the ceiling fan light commands
                has_ceiling_fan = TEST_COMMAND_GROUP in commands
                
                # Extract MAC from filename
                mac_part = file.name.replace('broadlink_remote_', '').replace('_codes', '')
                
                files_with_commands.append({
                    'path': file,
                    'mac_part': mac_part,
                    'has_ceiling_fan': has_ceiling_fan,
                    'command_groups': list(commands.keys()),
                    'commands': commands
                })
        except Exception as e:
            print(f"Error reading {file}: {e}")
    
    return files_with_commands


def send_command(entity_id, command_name):
    """Send a command and return success status"""
    url = f"{HA_URL}/api/services/remote/send_command"
    payload = {
        "entity_id": entity_id,
        "command": command_name
    }
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        return response.status_code == 200
    except:
        return False


def main():
    print("="*70)
    print("Which Broadlink Device Has the Ceiling Fan Light Commands?")
    print("="*70)
    print()
    
    # Find all Broadlink remotes
    print("Step 1: Finding Broadlink remote entities...")
    entities = get_all_entities()
    remotes = find_broadlink_remotes(entities)
    
    if not remotes:
        print("❌ No Broadlink remotes found!")
        return
    
    print(f"✅ Found {len(remotes)} Broadlink device(s):\n")
    for i, remote in enumerate(remotes, 1):
        print(f"{i}. {remote['entity_id']}")
        print(f"   Name: {remote['friendly_name']}")
        print(f"   State: {remote['state']}")
        print(f"   MAC: {remote['mac']}")
        print(f"   Model: {remote['model']}")
        print()
    
    # Find storage files
    print("Step 2: Checking storage files for ceiling fan commands...")
    storage_files = find_storage_files()
    
    ceiling_fan_file = None
    for file_info in storage_files:
        print(f"\n📁 {file_info['path'].name}")
        print(f"   MAC part: {file_info['mac_part']}")
        print(f"   Command groups: {len(file_info['command_groups'])}")
        
        if file_info['has_ceiling_fan']:
            print(f"   ✅ HAS CEILING FAN LIGHT COMMANDS!")
            ceiling_fan_file = file_info
            
            # Show sub-commands
            ceiling_fan_cmds = file_info['commands'][TEST_COMMAND_GROUP]
            if isinstance(ceiling_fan_cmds, dict):
                print(f"   Sub-commands: {', '.join(ceiling_fan_cmds.keys())}")
        else:
            print(f"   ❌ No ceiling fan commands")
            print(f"   Has: {', '.join(file_info['command_groups'][:3])}...")
    
    if not ceiling_fan_file:
        print("\n❌ Ceiling fan light commands not found in any storage file!")
        return
    
    print("\n" + "="*70)
    print("Step 3: Matching storage file to entity...")
    print("="*70)
    
    # Try to match MAC address
    ceiling_fan_mac = ceiling_fan_file['mac_part']
    matched_entity = None
    
    for remote in remotes:
        remote_mac = remote['mac'].replace(':', '').lower()
        if ceiling_fan_mac in remote_mac or remote_mac in ceiling_fan_mac:
            matched_entity = remote
            print(f"\n✅ MATCH FOUND!")
            print(f"   Entity: {remote['entity_id']}")
            print(f"   Storage: {ceiling_fan_file['path'].name}")
            print(f"   MAC: {remote['mac']} ↔ {ceiling_fan_mac}")
            break
    
    if not matched_entity:
        print(f"\n⚠️  Could not auto-match based on MAC address")
        print(f"   Storage file MAC: {ceiling_fan_mac}")
        print(f"   Entity MACs: {[r['mac'] for r in remotes]}")
    
    # Test sending from each device
    print("\n" + "="*70)
    print("Step 4: Testing which device can control the light...")
    print("="*70)
    print("\n⚠️  This will send the light_on command from EACH Broadlink device")
    print("   Watch your ceiling fan light to see which device makes it turn on!")
    print()
    input("Press Enter to start testing...")
    
    for i, remote in enumerate(remotes, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(remotes)}: {remote['entity_id']}")
        print(f"Name: {remote['friendly_name']}")
        print(f"{'='*70}")
        
        # Try sending the command
        command_name = f"{TEST_COMMAND_GROUP}.light_on"
        print(f"Sending: {command_name}")
        
        success = send_command(remote['entity_id'], command_name)
        
        if success:
            print("✅ Command sent (HTTP 200)")
            print("\n👀 DID THE LIGHT TURN ON?")
            response = input("   Enter 'y' if light turned on, 'n' if not: ").lower()
            
            if response == 'y':
                print(f"\n🎉 SUCCESS! This is the correct device:")
                print(f"   Entity ID: {remote['entity_id']}")
                print(f"   Name: {remote['friendly_name']}")
                print(f"   MAC: {remote['mac']}")
                print(f"\n💡 Update your test script to use: {remote['entity_id']}")
                
                # Turn off the light
                print("\nTurning light off...")
                send_command(remote['entity_id'], f"{TEST_COMMAND_GROUP}.light_off")
                return
            else:
                print("   Light did not turn on with this device")
        else:
            print("❌ Command failed to send")
        
        if i < len(remotes):
            print("\nWaiting 3 seconds before next test...")
            time.sleep(3)
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)
    print("\nIf none of the devices turned on the light, possible issues:")
    print("1. The IR code might be incorrect")
    print("2. The Broadlink device might not have line-of-sight to the light")
    print("3. The command might have been learned from a different remote")
    print("4. The light might not be responding to IR signals")


if __name__ == "__main__":
    main()
