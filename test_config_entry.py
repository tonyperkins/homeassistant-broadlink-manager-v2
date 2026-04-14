#!/usr/bin/env python3
"""Test HA config entry API to find device connection info"""

import requests
import json

ha_url = "http://homeassistant.local:8123"
ha_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI4YzQ0NzI5NzQxZjQ0MDFmOTMwMGQzZjgxNzA4ZjM0NyIsImlhdCI6MTcwOTc0MzQ1MCwiZXhwIjoxOTk1MTAzNDUwfQ.KaCwVJpucWuQzZrPdM0s6kO8Jv_3WvqJgWjMqQd6k8"

headers = {
    "Authorization": f"Bearer {ha_token}",
    "Content-Type": "application/json",
}

# Get config entries
print("=== Getting config entries ===")
response = requests.get(f"{ha_url}/api/config/config_entries/entry", headers=headers)
if response.status_code == 200:
    entries = response.json()
    print(f"Found {len(entries)} config entries")
    
    for entry in entries:
        if entry.get('domain') == 'broadlink':
            print(f"\nFound Broadlink config entry:")
            print(f"  Entry ID: {entry.get('entry_id')}")
            print(f"  Title: {entry.get('title')}")
            print(f"  Data: {entry.get('data', {})}")
            
            # Check if this matches our entity
            if 'tony' in entry.get('title', '').lower() and 'rm4' in entry.get('title', '').lower():
                print(f"  *** This looks like our device! ***")
                data = entry.get('data', {})
                print(f"  Host: {data.get('host')}")
                print(f"  MAC: {data.get('mac')}")
                print(f"  Type: {data.get('type')}")
else:
    print(f"Config entries failed: {response.status_code}")
