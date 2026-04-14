#!/usr/bin/env python3
"""
Simple test to check HA entity attributes via API
"""

import requests
import json
import os

# Get HA token from environment or use a hardcoded one for testing
HA_TOKEN = os.getenv('SUPERVISOR_TOKEN', '')
if not HA_TOKEN:
    # Try to read from addon config
    try:
        with open('/data/options.json', 'r') as f:
            options = json.load(f)
            HA_TOKEN = options.get('ha_token', '')
    except:
        pass

if not HA_TOKEN:
    print("No HA token found - this needs to run in the add-on environment")
    exit(1)

# HA API endpoint
HA_URL = "http://supervisor/core/api"

def get_entity_info(entity_id):
    """Get entity info from HA API"""
    headers = {
        'Authorization': f'Bearer {HA_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(f"{HA_URL}/states/{entity_id}", headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error getting entity: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    entity_id = "remote.tony_s_office_rm4_pro"
    
    print(f"Testing entity: {entity_id}")
    print("=" * 60)
    
    entity = get_entity_info(entity_id)
    
    if entity:
        print("Entity found!")
        print("\nFull entity data:")
        print(json.dumps(entity, indent=2))
        
        # Show just the attributes
        attributes = entity.get("attributes", {})
        print("\n" + "=" * 60)
        print("Attributes only:")
        print(json.dumps(attributes, indent=2))
        
        # Check for key fields
        print("\n" + "=" * 60)
        print("Key connection fields:")
        print(f"Host: {attributes.get('host')}")
        print(f"MAC: {attributes.get('mac')}")
        print(f"Type: {attributes.get('type')}")
        print(f"Model: {attributes.get('model')}")
        print(f"Manufacturer: {attributes.get('manufacturer')}")
        print(f"Friendly Name: {attributes.get('friendly_name')}")
        
    else:
        print("Entity not found!")

if __name__ == "__main__":
    main()
