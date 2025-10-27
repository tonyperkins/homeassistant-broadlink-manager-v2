"""
Test if Home Assistant Broadlink integration accepts raw base64 data in remote.send_command

This is a CRITICAL test that determines our entire architectural approach:
- If YES: We can use simple template entities with embedded base64 data
- If NO: We need to use REST API entities or custom integration

Usage:
    python tests/manual/test_raw_base64_send.py

Prerequisites:
    - Home Assistant running
    - Broadlink integration installed
    - At least one Broadlink device configured
    - A learned command in Broadlink storage (for comparison)

What this test does:
    1. Gets a real command from Broadlink storage
    2. Attempts to send it using raw base64 format: "b64:..."
    3. Attempts to send it using raw base64 without prefix
    4. Attempts to send it using the command name (baseline)
    5. Reports which methods work

Expected outcomes:
    - Baseline (command name): Should work ✅
    - Raw base64 with prefix: Unknown ❓
    - Raw base64 without prefix: Unknown ❓
"""

import json
import requests
import base64
from pathlib import Path
import time

# Configuration
HA_URL = "http://homeassistant.local:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlMzcyYmFiYmIyNjQ0YzVkOTI3MTFhNTFjZTcxMTJkNCIsImlhdCI6MTc1NzQ0NDMwOCwiZXhwIjoyMDcyODA0MzA4fQ.hakvxq-vSfZMnBX7dUfVLClx8riDuA4QPxokHz9-x08"  # Get from HA profile
BROADLINK_ENTITY_ID = "remote.tony_s_office_rm4_pro"  # Tony's Office RM4 Pro

# Test configuration
STORAGE_PATH = Path("h:/.storage")
TEST_COMMAND_GROUP = "tony_s_office_ceiling_fan_light"  # Group name
TEST_COMMAND_ON = "light_on"  # Command to turn on
TEST_COMMAND_OFF = "light_off"  # Command to turn off


def get_headers():
    """Get headers for HA API requests"""
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }


def find_broadlink_storage_file(entity_id):
    """Find the Broadlink storage file for the given entity"""
    # Extract device identifier from entity_id
    # Example: remote.bedroom_rm4 -> bedroom_rm4
    device_name = entity_id.replace("remote.", "")
    
    # Look for storage files matching pattern
    pattern = f"broadlink_remote_*_codes"
    
    for file in STORAGE_PATH.glob(pattern):
        print(f"Found storage file: {file}")
        return file
    
    print(f"❌ No Broadlink storage file found matching pattern: {pattern}")
    return None


def get_specific_command_from_storage(storage_file, group_name, command_name):
    """Read a specific command from a group in Broadlink storage file"""
    try:
        with open(storage_file, 'r') as f:
            data = json.load(f)
            
        if "data" not in data:
            print(f"❌ No 'data' key in storage file")
            return None
        
        storage_data = data["data"]
        
        # Check if group exists
        if group_name not in storage_data:
            print(f"❌ Group '{group_name}' not found in storage")
            return None
        
        group_data = storage_data[group_name]
        
        # Check if it's a dict (nested format)
        if not isinstance(group_data, dict):
            print(f"❌ '{group_name}' is not a group")
            return None
        
        # Get specific command
        if command_name not in group_data:
            print(f"❌ Command '{command_name}' not found in group '{group_name}'")
            print(f"   Available: {list(group_data.keys())}")
            return None
        
        command_data = group_data[command_name]
        print(f"✅ Found '{group_name}.{command_name}'")
        print(f"   Data length: {len(command_data)} characters")
        print(f"   First 50 chars: {command_data[:50]}...")
        return command_data
            
    except Exception as e:
        print(f"❌ Error reading storage file: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_command_from_storage(storage_file, command_name):
    """Read a command from Broadlink storage file"""
    try:
        with open(storage_file, 'r') as f:
            data = json.load(f)
            
        # Broadlink storage can have two formats:
        # Format 1 (flat): {"data": {"command_name": "base64_data", ...}}
        # Format 2 (nested): {"data": {"group": {"command_name": "base64_data", ...}}}
        
        if "data" not in data:
            print(f"❌ No 'data' key in storage file")
            return None
        
        storage_data = data["data"]
        
        # Try flat format first
        if command_name in storage_data:
            command_data = storage_data[command_name]
            
            # Check if it's a string (actual command) or nested object
            if isinstance(command_data, str):
                print(f"✅ Found command '{command_name}' in storage (flat format)")
                print(f"   Data length: {len(command_data)} characters")
                print(f"   First 50 chars: {command_data[:50]}...")
                return command_data
            elif isinstance(command_data, dict):
                # Nested format - command_name is a group
                print(f"⚠️  '{command_name}' is a group with sub-commands:")
                print(f"   Available sub-commands: {list(command_data.keys())}")
                
                # If there's a command with the same name as the group, use it
                if command_name in command_data:
                    actual_command = command_data[command_name]
                    print(f"✅ Using '{command_name}.{command_name}' command")
                    print(f"   Data length: {len(actual_command)} characters")
                    print(f"   First 50 chars: {actual_command[:50]}...")
                    return actual_command
                else:
                    # Use the first command in the group
                    first_key = list(command_data.keys())[0]
                    actual_command = command_data[first_key]
                    print(f"✅ Using first command '{command_name}.{first_key}'")
                    print(f"   Data length: {len(actual_command)} characters")
                    print(f"   First 50 chars: {actual_command[:50]}...")
                    return actual_command
        
        # Command not found - list available
        print(f"❌ Command '{command_name}' not found in storage")
        all_commands = []
        for key, value in storage_data.items():
            if isinstance(value, str):
                all_commands.append(key)
            elif isinstance(value, dict):
                all_commands.append(f"{key} (group with: {', '.join(value.keys())})")
        print(f"   Available: {all_commands}")
        return None
            
    except Exception as e:
        print(f"❌ Error reading storage file: {e}")
        import traceback
        traceback.print_exc()
        return None


def send_command_via_ha(entity_id, command_data, method_name):
    """Send a command via Home Assistant API"""
    url = f"{HA_URL}/api/services/remote/send_command"
    
    payload = {
        "entity_id": entity_id,
        "command": command_data
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {method_name}")
    print(f"{'='*60}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=get_headers(), json=payload)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ {method_name}: SUCCESS")
            return True
        else:
            print(f"❌ {method_name}: FAILED")
            return False
            
    except Exception as e:
        print(f"❌ {method_name}: ERROR - {e}")
        return False


def main():
    """Run the test suite"""
    print("="*60)
    print("Broadlink Raw Base64 Send Test")
    print("="*60)
    print()
    
    # Step 1: Validate configuration
    print("Step 1: Validating configuration...")
    if HA_TOKEN == "YOUR_LONG_LIVED_ACCESS_TOKEN":
        print("❌ ERROR: Please set your HA_TOKEN in the script")
        print("   Get a long-lived access token from your HA profile")
        return
    
    print(f"✅ HA URL: {HA_URL}")
    print(f"✅ Entity ID: {BROADLINK_ENTITY_ID}")
    print(f"✅ Test Group: {TEST_COMMAND_GROUP}")
    print(f"✅ Test Commands: {TEST_COMMAND_ON} / {TEST_COMMAND_OFF}")
    print()
    
    # Step 2: Find storage file
    print("Step 2: Finding Broadlink storage file...")
    storage_file = find_broadlink_storage_file(BROADLINK_ENTITY_ID)
    if not storage_file:
        print("❌ ERROR: Could not find Broadlink storage file")
        print("   Make sure Broadlink integration is installed and configured")
        return
    print()
    
    # Step 3: Get command data for both ON and OFF
    print("Step 3: Reading commands from storage...")
    print(f"Group: {TEST_COMMAND_GROUP}")
    print(f"Commands: {TEST_COMMAND_ON}, {TEST_COMMAND_OFF}")
    print()
    
    command_on_data = get_specific_command_from_storage(storage_file, TEST_COMMAND_GROUP, TEST_COMMAND_ON)
    if not command_on_data:
        print(f"❌ ERROR: Could not read '{TEST_COMMAND_ON}' command")
        return
    print()
    
    command_off_data = get_specific_command_from_storage(storage_file, TEST_COMMAND_GROUP, TEST_COMMAND_OFF)
    if not command_off_data:
        print(f"❌ ERROR: Could not read '{TEST_COMMAND_OFF}' command")
        return
    print()
    
    # Step 4: Run tests
    print("Step 4: Running send tests...")
    print("⚠️  WARNING: These tests will actually send IR/RF signals!")
    print("   Your light should turn ON, wait 5 seconds, then turn OFF for each test")
    input("Press Enter to continue...")
    print()
    
    results = {}
    
    # Test 1: Raw base64 with "b64:" prefix
    print("\n" + "="*60)
    print("TEST 1: Raw Base64 with 'b64:' prefix")
    print("="*60)
    print("Sending LIGHT ON...")
    on_result = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        f"b64:{command_on_data}",
        "Light ON with 'b64:' prefix"
    )
    print("⏳ Waiting 5 seconds...")
    time.sleep(5)
    print("Sending LIGHT OFF...")
    off_result = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        f"b64:{command_off_data}",
        "Light OFF with 'b64:' prefix"
    )
    results['b64_prefix'] = on_result and off_result
    time.sleep(2)
    
    # Test 2: Raw base64 without prefix
    print("\n" + "="*60)
    print("TEST 2: Raw Base64 without prefix")
    print("="*60)
    print("Sending LIGHT ON...")
    on_result = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        command_on_data,
        "Light ON without prefix"
    )
    print("⏳ Waiting 5 seconds...")
    time.sleep(5)
    print("Sending LIGHT OFF...")
    off_result = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        command_off_data,
        "Light OFF without prefix"
    )
    results['b64_no_prefix'] = on_result and off_result
    time.sleep(2)
    
    # Test 3: Raw base64 with "base64:" prefix
    print("\n" + "="*60)
    print("TEST 3: Raw Base64 with 'base64:' prefix")
    print("="*60)
    print("Sending LIGHT ON...")
    on_result = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        f"base64:{command_on_data}",
        "Light ON with 'base64:' prefix"
    )
    print("⏳ Waiting 5 seconds...")
    time.sleep(5)
    print("Sending LIGHT OFF...")
    off_result = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        f"base64:{command_off_data}",
        "Light OFF with 'base64:' prefix"
    )
    results['base64_prefix'] = on_result and off_result
    time.sleep(2)
    
    # Step 5: Summary
    print("\n" + "="*60)
    print("TEST RESULTS SUMMARY")
    print("="*60)
    
    for method, success in results.items():
        status = "✅ WORKS" if success else "❌ FAILED"
        print(f"{method:20s}: {status}")
    
    print("\n" + "="*60)
    print("ARCHITECTURAL DECISION")
    print("="*60)
    
    if results.get('b64_prefix') or results.get('b64_no_prefix') or results.get('base64_prefix'):
        print("✅ RAW BASE64 WORKS!")
        print()
        print("Recommendation: Use Option 1 (Template Entities with Raw Base64)")
        print()
        print("This means we can:")
        print("- Store commands in our devices.json")
        print("- Generate simple template entities with embedded base64 data")
        print("- Still use Broadlink integration for sending")
        print("- No need for REST API entities or custom integration")
        print()
        print("Next steps:")
        print("1. Expand devices.json schema to store command data")
        print("2. Update learning workflow to save to our storage")
        print("3. Update entity generator to embed base64 data")
        print("4. Test and validate")
    else:
        print("❌ RAW BASE64 DOES NOT WORK")
        print()
        print("Recommendation: Use Option 2 (REST API Entities)")
        print()
        print("This means we need to:")
        print("- Store commands in our devices.json")
        print("- Implement /api/commands/send endpoint")
        print("- Generate REST API entities")
        print("- Send commands directly via python-broadlink")
        print()
        print("Next steps:")
        print("1. Expand devices.json schema to store command data")
        print("2. Implement /api/commands/send with python-broadlink")
        print("3. Update entity generator to create REST entities")
        print("4. Test and validate")
    
    print("="*60)


if __name__ == "__main__":
    main()
