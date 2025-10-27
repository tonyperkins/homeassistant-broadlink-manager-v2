"""Test script to debug the discovery API"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / ".env"
print(f"Loading .env from: {env_path}")
print(f".env exists: {env_path.exists()}")
load_dotenv(env_path)

# Check what environment variables are set
print("\nEnvironment variables after loading .env:")
print(f"  HA_CONFIG_PATH: {os.environ.get('HA_CONFIG_PATH', 'NOT SET')}")
print(f"  CONFIG_PATH: {os.environ.get('CONFIG_PATH', 'NOT SET')}")

# Simulate what ConfigLoader does
config_path = os.environ.get("HA_CONFIG_PATH") or os.environ.get("CONFIG_PATH", "/config")
storage_path = Path(config_path) / ".storage"

print(f"\nResolved paths:")
print(f"  Config path: {config_path}")
print(f"  Storage path: {storage_path}")
print(f"  Storage path exists: {storage_path.exists()}")

if storage_path.exists():
    files = list(storage_path.glob('broadlink_remote_*_codes'))
    print(f"\nFound {len(files)} Broadlink storage files:")
    for f in files:
        print(f"  - {f.name}")
        
        # Read the file
        import json
        with open(f, 'r') as file:
            data = json.load(file)
            devices = data.get('data', {})
            print(f"    Devices: {list(devices.keys())}")
else:
    print(f"\n❌ Storage path does not exist: {storage_path}")
