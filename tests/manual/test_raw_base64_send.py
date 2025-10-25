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
HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"  # Get from HA profile
BROADLINK_ENTITY_ID = "remote.bedroom_rm4"  # Change to your device

# Test configuration
STORAGE_PATH = Path("/config/.storage")
TEST_COMMAND_NAME = "power"  # Change to a command you have learned


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


def get_command_from_storage(storage_file, command_name):
    """Read a command from Broadlink storage file"""
    try:
        with open(storage_file, 'r') as f:
            data = json.load(f)
            
        # Broadlink storage format:
        # {"data": {"command_name": "base64_data", ...}}
        if "data" in data and command_name in data["data"]:
            command_data = data["data"][command_name]
            print(f"✅ Found command '{command_name}' in storage")
            print(f"   Data length: {len(command_data)} characters")
            print(f"   First 50 chars: {command_data[:50]}...")
            return command_data
        else:
            print(f"❌ Command '{command_name}' not found in storage")
            if "data" in data:
                print(f"   Available commands: {list(data['data'].keys())}")
            return None
            
    except Exception as e:
        print(f"❌ Error reading storage file: {e}")
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
    print(f"✅ Test Command: {TEST_COMMAND_NAME}")
    print()
    
    # Step 2: Find storage file
    print("Step 2: Finding Broadlink storage file...")
    storage_file = find_broadlink_storage_file(BROADLINK_ENTITY_ID)
    if not storage_file:
        print("❌ ERROR: Could not find Broadlink storage file")
        print("   Make sure Broadlink integration is installed and configured")
        return
    print()
    
    # Step 3: Get command data
    print("Step 3: Reading command from storage...")
    command_data = get_command_from_storage(storage_file, TEST_COMMAND_NAME)
    if not command_data:
        print("❌ ERROR: Could not read command from storage")
        print(f"   Make sure command '{TEST_COMMAND_NAME}' exists")
        return
    print()
    
    # Step 4: Run tests
    print("Step 4: Running send tests...")
    print("⚠️  WARNING: These tests will actually send IR/RF signals!")
    print("   Make sure your device is ready to receive commands")
    input("Press Enter to continue...")
    print()
    
    results = {}
    
    # Test 1: Baseline - Send using command name (should work)
    results['command_name'] = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        TEST_COMMAND_NAME,
        "Baseline: Command Name"
    )
    time.sleep(2)
    
    # Test 2: Raw base64 with "b64:" prefix
    results['b64_prefix'] = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        f"b64:{command_data}",
        "Raw Base64 with 'b64:' prefix"
    )
    time.sleep(2)
    
    # Test 3: Raw base64 without prefix
    results['b64_no_prefix'] = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        command_data,
        "Raw Base64 without prefix"
    )
    time.sleep(2)
    
    # Test 4: Raw base64 with "base64:" prefix
    results['base64_prefix'] = send_command_via_ha(
        BROADLINK_ENTITY_ID,
        f"base64:{command_data}",
        "Raw Base64 with 'base64:' prefix"
    )
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
