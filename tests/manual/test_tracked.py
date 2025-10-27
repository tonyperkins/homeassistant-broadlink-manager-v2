import json
from pathlib import Path

# Check devices.json
devices_file = Path('/config/devices.json')
if devices_file.exists():
    with open(devices_file, 'r') as f:
        devices_data = json.load(f)
        print(f'Tracked devices in devices.json: {len(devices_data)}')
        for device_id, device_info in devices_data.items():
            device_type = device_info.get('device_type', 'unknown')
            print(f'  - {device_id} (type: {device_type})')
else:
    print('devices.json not found')

print()

# Check metadata.json
metadata_file = Path('/config/metadata.json')
if metadata_file.exists():
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
        entities = metadata.get('entities', {})
        print(f'Tracked entities in metadata.json: {len(entities)}')
        for entity_id, entity_data in entities.items():
            device_name = entity_data.get('device', 'unknown')
            print(f'  - {entity_id} -> device: {device_name}')
else:
    print('metadata.json not found')
