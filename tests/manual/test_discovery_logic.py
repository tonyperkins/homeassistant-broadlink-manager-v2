"""Test the discovery logic"""
import json
from pathlib import Path

# Read storage files
storage_path = Path('h:/.storage')
broadlink_commands = {}

for storage_file in storage_path.glob('broadlink_remote_*_codes'):
    with open(storage_file, 'r') as f:
        data = json.load(f)
        for device_name, commands in data.get('data', {}).items():
            if isinstance(commands, dict):
                broadlink_commands[device_name] = commands

print(f"Devices in Broadlink storage: {list(broadlink_commands.keys())}")
print()

# Read tracked devices
devices_file = Path('h:/broadlink_manager/devices.json')
tracked_device_names = set()

if devices_file.exists():
    with open(devices_file, 'r') as f:
        devices = json.load(f)
        for device_id, device_data in devices.items():
            if device_data.get('device_type') == 'broadlink':
                tracked_device_names.add(device_id)
                print(f"Tracked: {device_id}")

print()
print(f"Total tracked devices: {len(tracked_device_names)}")
print()

# Find untracked
untracked_devices = []
for device_name, commands in broadlink_commands.items():
    if device_name not in tracked_device_names:
        untracked_devices.append({
            'device_name': device_name,
            'command_count': len(commands),
            'commands': list(commands.keys())
        })
        print(f"✅ UNTRACKED: {device_name} ({len(commands)} commands)")
    else:
        print(f"❌ Tracked: {device_name}")

print()
print(f"Total untracked devices: {len(untracked_devices)}")
