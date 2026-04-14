#!/usr/bin/env python3
"""Test HA entity registry API to find device_id"""

import requests
import json

# Get token from config
ha_url = "http://homeassistant.local:8123"
ha_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiI4YzQ0NzI5NzQxZjQ0MDFmOTMwMGQzZjgxNzA4ZjM0NyIsImlhdCI6MTcwOTc0MzQ1MCwiZXhwIjoxOTk1MTAzNDUwfQ.KaCwVJpucWuQzZrPdM0s6kO8Jv_3WvqJgWjMqQd6k8"

headers = {
    "Authorization": f"Bearer {ha_token}",
    "Content-Type": "application/json",
}

# Try different entity registry endpoints
endpoints = [
    "/api/config/entity_registry/list",
    "/api/entity_registry/list",
    "/api/registry/entity",
    "/api/registry/list",
]

for endpoint in endpoints:
    print(f"\n=== Testing {endpoint} ===")
    try:
        response = requests.get(f"{ha_url}{endpoint}", headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                # Look for our entity
                for entity in data:
                    if entity.get("entity_id") == "remote.tony_s_office_rm4_pro":
                        print(f"Found entity: {json.dumps(entity, indent=2)}")
                        break
                else:
                    print(f"Entity not found in {len(data)} entities")
            else:
                print(f"Response: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"Error: {response.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")

# Also try the single entity endpoint
print(f"\n=== Testing single entity endpoint ===")
try:
    response = requests.get(f"{ha_url}/api/config/entity_registry/remote.tony_s_office_rm4_pro", headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
