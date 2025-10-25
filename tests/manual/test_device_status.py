"""
Test script to check Broadlink device status and diagnose "storage full" error

This script will:
1. Discover devices
2. Check device status
3. Try to understand what "storage full" really means
4. Test if it's actually a learning mode issue vs storage issue
"""

import broadlink
import time


def discover_and_test():
    print("="*70)
    print("Broadlink Device Status Check")
    print("="*70)
    print()
    
    # Discover devices
    print("🔍 Discovering devices...")
    devices = broadlink.discover(timeout=5)
    
    if not devices:
        print("❌ No devices found")
        return
    
    print(f"✅ Found {len(devices)} device(s)\n")
    
    for i, device in enumerate(devices, 1):
        print(f"{i}. {device.model if hasattr(device, 'model') else 'Unknown'}")
        print(f"   Host: {device.host[0]}")
        print(f"   MAC: {device.mac.hex(':')}")
        print()
    
    # Select device
    if len(devices) == 1:
        selected = devices[0]
        print(f"Using device: {selected.host[0]}")
    else:
        try:
            choice = int(input(f"Select device (1-{len(devices)}): "))
            selected = devices[choice - 1]
        except:
            print("Invalid choice")
            return
    
    print()
    
    # Authenticate
    print("🔐 Authenticating...")
    try:
        selected.auth()
        print("✅ Authenticated")
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return
    
    print()
    print("="*70)
    print("TESTING LEARNING MODE")
    print("="*70)
    print()
    
    # Test 1: Can we enter learning mode?
    print("Test 1: Entering learning mode...")
    try:
        selected.enter_learning()
        print("✅ Successfully entered learning mode")
        
        # Wait a bit
        print("   Waiting 2 seconds...")
        time.sleep(2)
        
        # Try to check for data (even though we didn't press anything)
        print("   Checking for data (should be None)...")
        data = selected.check_data()
        if data:
            print(f"   ⚠️  Unexpected: Got data ({len(data)} bytes)")
        else:
            print("   ✅ No data (as expected)")
        
    except Exception as e:
        print(f"❌ Error entering learning mode: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        if "storage is full" in str(e).lower():
            print("\n🔍 DIAGNOSIS: 'Storage full' error when entering learning mode")
            print("   This suggests the error happens BEFORE learning, not after")
            print("   Possible causes:")
            print("   1. Device has too many commands stored internally")
            print("   2. Device is in a bad state and needs reset")
            print("   3. Previous learning session wasn't properly closed")
    
    print()
    
    # Test 2: Can we cancel learning?
    print("Test 2: Trying to cancel/exit learning mode...")
    try:
        # Some devices have cancel_sweep for RF
        if hasattr(selected, 'cancel_sweep'):
            selected.cancel_sweep()
            print("✅ Called cancel_sweep()")
        else:
            print("⚠️  Device doesn't have cancel_sweep() method")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print()
    
    # Test 3: Check if there's a way to clear device memory
    print("Test 3: Checking available device methods...")
    methods = [m for m in dir(selected) if not m.startswith('_')]
    
    # Look for relevant methods
    clear_methods = [m for m in methods if any(keyword in m.lower() for keyword in ['clear', 'delete', 'reset', 'cancel', 'exit'])]
    
    if clear_methods:
        print(f"✅ Found potentially relevant methods:")
        for method in clear_methods:
            print(f"   - {method}()")
    else:
        print("❌ No clear/delete/reset methods found")
    
    print()
    print("All device methods:")
    for method in methods:
        print(f"   - {method}()")
    
    print()
    print("="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print()
    
    print("Based on the error occurring when entering learning mode:")
    print()
    print("1. The device's internal memory is likely full from previous learning")
    print("2. The device stores learned commands internally until they're retrieved")
    print("3. Commands learned via HA integration may not be properly cleared")
    print()
    print("Possible solutions:")
    print("A. Power cycle the device (unplug for 10 seconds)")
    print("B. Delete commands via HA: remote.delete_command with command: ['all']")
    print("C. Manually edit .storage/broadlink_remote_*_codes and remove commands")
    print("D. Use HA's Broadlink integration to learn a dummy command, then delete it")
    print("   (This might trigger the device to clear its memory)")
    print()
    print("For our hybrid approach:")
    print("- We'll need to handle this gracefully")
    print("- Maybe add a 'clear device memory' step before learning")
    print("- Or guide users to clear via HA first")


if __name__ == "__main__":
    try:
        discover_and_test()
    except KeyboardInterrupt:
        print("\n\nCancelled")
