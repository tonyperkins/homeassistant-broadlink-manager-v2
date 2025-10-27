"""
Quick script to find all remote entities in Home Assistant

Usage:
    python tests/manual/test_find_entities.py
"""

import requests
import json

# Configuration
HA_URL = "http://homeassistant.local:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJlMzcyYmFiYmIyNjQ0YzVkOTI3MTFhNTFjZTcxMTJkNCIsImlhdCI6MTc1NzQ0NDMwOCwiZXhwIjoyMDcyODA0MzA4fQ.hakvxq-vSfZMnBX7dUfVLClx8riDuA4QPxokHz9-x08"


def get_headers():
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json"
    }


def main():
    print("="*70)
    print("Finding All Remote Entities in Home Assistant")
    print("="*70)
    print()
    
    url = f"{HA_URL}/api/states"
    
    try:
        response = requests.get(url, headers=get_headers())
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(response.text)
            return
        
        entities = response.json()
        
        # Find all remote entities
        remotes = [e for e in entities if e.get('entity_id', '').startswith('remote.')]
        
        if not remotes:
            print("❌ No remote entities found!")
            return
        
        print(f"✅ Found {len(remotes)} remote entity/entities:\n")
        
        for remote in remotes:
            entity_id = remote.get('entity_id')
            state = remote.get('state')
            attributes = remote.get('attributes', {})
            
            print(f"{'='*70}")
            print(f"Entity ID: {entity_id}")
            print(f"State: {state}")
            print(f"Friendly Name: {attributes.get('friendly_name', 'N/A')}")
            
            if 'mac' in attributes:
                print(f"MAC: {attributes['mac']}")
            if 'model' in attributes:
                print(f"Model: {attributes['model']}")
            if 'manufacturer' in attributes:
                print(f"Manufacturer: {attributes['manufacturer']}")
            
            # Show if it's available or not
            if state == 'unavailable':
                print("⚠️  STATUS: UNAVAILABLE (device offline or not responding)")
            else:
                print("✅ STATUS: Available")
            
            print()
        
        print("="*70)
        print("Update your test script with the correct entity_id")
        print("="*70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
