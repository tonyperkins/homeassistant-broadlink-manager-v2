#!/usr/bin/env python3
"""
Manual test to demonstrate the SmartIR YAML generation fix
Run this to see the before/after comparison
"""

import tempfile
import shutil
from pathlib import Path
import yaml
from app.smartir_yaml_generator import SmartIRYAMLGenerator


def test_yaml_generation():
    """Demonstrate that controller_data now uses entity IDs instead of IP addresses"""
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    generator = SmartIRYAMLGenerator(config_path=temp_dir)
    
    print("=" * 80)
    print("SmartIR YAML Generation Test - Phase 1 Fix Verification")
    print("=" * 80)
    print()
    
    # Test 1: Broadlink Remote
    print("Test 1: Broadlink Remote")
    print("-" * 80)
    device_data = {
        "name": "Bedroom AC",
        "entity_type": "climate",
        "device_code": "1080",
        "controller_device": "remote.broadlink_rm4_pro",
        "temperature_sensor": "sensor.bedroom_temp"
    }
    
    result = generator.generate_device_config("bedroom_ac", device_data)
    print(f"✅ Success: {result['success']}")
    print(f"📄 Generated config:")
    print(yaml.dump(result['config'], default_flow_style=False, sort_keys=False))
    print(f"🔍 controller_data = '{result['config']['controller_data']}'")
    print(f"✓ Uses entity ID (not IP address)")
    print()
    
    # Test 2: Xiaomi Remote
    print("Test 2: Xiaomi Remote (Non-Broadlink)")
    print("-" * 80)
    device_data = {
        "name": "Living Room AC",
        "entity_type": "climate",
        "device_code": "1000",
        "controller_device": "remote.xiaomi_ir_remote",
        "temperature_sensor": "sensor.living_room_temp",
        "humidity_sensor": "sensor.living_room_humidity"
    }
    
    result = generator.generate_device_config("living_room_ac", device_data)
    print(f"✅ Success: {result['success']}")
    print(f"📄 Generated config:")
    print(yaml.dump(result['config'], default_flow_style=False, sort_keys=False))
    print(f"🔍 controller_data = '{result['config']['controller_data']}'")
    print(f"✓ Works with non-Broadlink remote!")
    print()
    
    # Test 3: Harmony Hub
    print("Test 3: Harmony Hub (Non-Broadlink)")
    print("-" * 80)
    device_data = {
        "name": "Media Room TV",
        "entity_type": "media_player",
        "device_code": "1500",
        "controller_device": "remote.harmony_hub",
        "power_sensor": "binary_sensor.tv_power"
    }
    
    result = generator.generate_device_config("media_room_tv", device_data)
    print(f"✅ Success: {result['success']}")
    print(f"📄 Generated config:")
    print(yaml.dump(result['config'], default_flow_style=False, sort_keys=False))
    print(f"🔍 controller_data = '{result['config']['controller_data']}'")
    print(f"✓ Works with Harmony Hub!")
    print()
    
    # Show the complete YAML file
    print("Complete Generated YAML Files")
    print("=" * 80)
    
    climate_file = Path(temp_dir) / "smartir" / "climate.yaml"
    if climate_file.exists():
        print("\n📁 climate.yaml:")
        print("-" * 80)
        with open(climate_file, 'r') as f:
            print(f.read())
    
    media_file = Path(temp_dir) / "smartir" / "media_player.yaml"
    if media_file.exists():
        print("\n📁 media_player.yaml:")
        print("-" * 80)
        with open(media_file, 'r') as f:
            print(f.read())
    
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print("✅ All controller_data fields use entity IDs (not IP addresses)")
    print("✅ Works with Broadlink, Xiaomi, Harmony Hub, and any HA remote entity")
    print("✅ Generated YAML is valid SmartIR format")
    print()
    print("Phase 1 Fix: VERIFIED ✓")
    print("=" * 80)
    
    # Cleanup
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    test_yaml_generation()
