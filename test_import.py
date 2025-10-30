#!/usr/bin/env python3
"""Quick test to verify import endpoint works"""

import requests
import json

# Test data
device_id = "tony_s_office_workbench_lamp"
source_device = "tony_s_office_workbench_lamp"
commands = ["bright"]

print("🧪 Testing import endpoint...")
print(f"Device ID: {device_id}")
print(f"Source Device: {source_device}")
print(f"Commands: {commands}")
print()

# Make request
url = "http://localhost:8099/api/commands/import"
payload = {
    "device_id": device_id,
    "source_device": source_device,
    "commands": commands
}

print(f"POST {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! Import worked!")
    else:
        print(f"\n❌ FAILED with status {response.status_code}")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
