#!/usr/bin/env python3
"""
Test script to check what HA entity attributes contain for Broadlink devices
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from web_server import BroadlinkWebServer
import json

def test_entity_attributes():
    """Test what attributes we get from HA for a Broadlink entity"""
    
    # Initialize web server (this also initializes the HA client)
    server = BroadlinkWebServer()
    server.initialize()
    
    # Get entity info for your RM4 Pro
    entity_id = "remote.tony_s_office_rm4_pro"
    
    print(f"Testing entity: {entity_id}")
    print("=" * 60)
    
    # Get the entity info
    entity = server.broadlink_device_manager.get_ha_entity_info(entity_id)
    
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
        
    print("\n" + "=" * 60)
    print("Testing discovery to see what devices are found...")
    
    # Test discovery
    discovered = server.broadlink_device_manager.discover_devices(timeout=5)
    
    if discovered:
        print(f"\nFound {len(discovered)} devices:")
        for i, device in enumerate(discovered):
            print(f"\nDevice {i+1}:")
            print(json.dumps(device, indent=2))
    else:
        print("No devices discovered!")

if __name__ == "__main__":
    test_entity_attributes()
