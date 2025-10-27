from pathlib import Path
import json

storage_path = Path('h:/.storage')
files = list(storage_path.glob('broadlink_remote_*_codes'))
print(f'Found {len(files)} storage files:')
for f in files:
    print(f'  - {f.name}')
    
    # Read and parse the file
    with open(f, 'r') as file:
        data = json.load(file)
        devices = data.get('data', {})
        print(f'    Devices in file: {list(devices.keys())}')
        for device_name, commands in devices.items():
            if isinstance(commands, dict):
                print(f'      {device_name}: {len(commands)} commands')
