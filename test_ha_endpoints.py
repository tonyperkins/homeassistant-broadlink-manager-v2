#!/usr/bin/env python3
"""Test HA API endpoints to find the correct one"""

import requests
import json

ha_url = "http://homeassistant.local:8123"
ha_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI4YzQ0NzI5NzQxZjQ0MDFmOTMwMGQzZjgxNzA4ZjM0NyIsImlhdCI6MTcwOTc0MzQ1MCwiZXhwIjoxOTk1MTAzNDUwfQ.KaCwVJpucWuQzZrPdM0s6kO8Jv_3WvqJgWjMqQd6k8"

headers = {
    "Authorization": f"Bearer {ha_token}",
    "Content-Type": "application/json",
}

# Get entity info first
print("=== Getting entity info ===")
response = requests.get(f"{ha_url}/api/states/remote.tony_s_office_rm4_pro", headers=headers)
if response.status_code == 200:
    entity = response.json()
    print(f"Entity context: {entity.get('context', {})}")
    
    # Check if context has device_id
    device_id = entity.get('context', {}).get('device_id')
    if device_id:
        print(f"Found device_id in context: {device_id}")
        
        # Try to get device info
        print("\n=== Getting device info ===")
        device_response = requests.get(f"{ha_url}/api/devices/{device_id}", headers=headers)
        if device_response.status_code == 200:
            device = device_response.json()
            print(f"Device connections: {device.get('connections', [])}")
        else:
            print(f"Device info failed: {device_response.status_code}")
    else:
        print("No device_id in context")

# Try the device registry list
print("\n=== Trying device registry list ===")
response = requests.get(f"{ha_url}/api/devices", headers=headers)
if response.status_code == 200:
    devices = response.json()
    print(f"Found {len(devices)} devices")
    
    for device in devices:
        # Check if this device has our entity
        if device.get('name', '').lower() == 'tony_s office rm4 pro' or 'tony' in device.get('name', '').lower() and 'rm4' in device.get('name', '').lower():
            print(f"\nFound matching device: {device.get('name')}")
            print(f"  Device ID: {device.get('id')}")
            print(f"  Connections: {device.get('connections', [])}")
            print(f"  Attributes: {device.get('attributes', {})}")
            break
else:
    print(f"Device registry failed: {response.status_code}")
