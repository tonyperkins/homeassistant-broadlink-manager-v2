import os
from pathlib import Path

# Check environment variables
print("Environment variables:")
print(f"  HA_CONFIG_PATH: {os.environ.get('HA_CONFIG_PATH', 'NOT SET')}")
print(f"  CONFIG_PATH: {os.environ.get('CONFIG_PATH', 'NOT SET')}")
print()

# Check what the config loader would use
config_path = os.environ.get("HA_CONFIG_PATH") or os.environ.get("CONFIG_PATH", "/config")
storage_path = Path(config_path) / ".storage"

print(f"Config path: {config_path}")
print(f"Storage path: {storage_path}")
print(f"Storage path exists: {storage_path.exists()}")
print()

if storage_path.exists():
    files = list(storage_path.glob('broadlink_remote_*_codes'))
    print(f'Found {len(files)} storage files in {storage_path}')
    for f in files:
        print(f'  - {f.name}')
