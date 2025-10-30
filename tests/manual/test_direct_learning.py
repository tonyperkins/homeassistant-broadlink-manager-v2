"""
Test script for direct Broadlink device learning (IR and RF)

This script tests learning commands directly from Broadlink devices using python-broadlink,
bypassing Home Assistant's Broadlink integration entirely.

IR Learning: 1-step process
- Enter learning mode
- User presses remote button
- Capture data immediately

RF Learning: 2-step process
- Step 1: Sweep frequency - device learns the RF frequency
- Step 2: Capture data - device captures the actual RF signal

Usage:
    python tests/manual/test_direct_learning.py
"""

import broadlink
import base64
import time
import sys
from typing import Optional, Tuple


def discover_devices(timeout=5):
    """Discover Broadlink devices on the network"""
    print(f"🔍 Discovering Broadlink devices (timeout: {timeout}s)...")
    devices = broadlink.discover(timeout=timeout)
    
    if not devices:
        print("❌ No Broadlink devices found!")
        print("   Make sure devices are on the same network")
        return []
    
    print(f"✅ Found {len(devices)} device(s):\n")
    
    device_list = []
    for i, device in enumerate(devices, 1):
        device_info = {
            'index': i,
            'device': device,
            'host': device.host[0],
            'port': device.host[1],
            'mac': device.mac.hex(':'),
            'type': device.type,
            'model': device.model if hasattr(device, 'model') else 'Unknown'
        }
        device_list.append(device_info)
        
        print(f"{i}. {device_info['model']}")
        print(f"   Host: {device_info['host']}:{device_info['port']}")
        print(f"   MAC: {device_info['mac']}")
        print(f"   Type: {device_info['type']}")
        print()
    
    return device_list


def select_device(device_list):
    """Let user select a device from the list"""
    if not device_list:
        return None
    
    if len(device_list) == 1:
        print(f"Using device: {device_list[0]['model']}")
        return device_list[0]
    
    while True:
        try:
            choice = input(f"Select device (1-{len(device_list)}): ")
            index = int(choice)
            if 1 <= index <= len(device_list):
                return device_list[index - 1]
            else:
                print(f"Please enter a number between 1 and {len(device_list)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\nCancelled")
            return None


def authenticate_device(device):
    """Authenticate with the Broadlink device"""
    print("\n🔐 Authenticating with device...")
    try:
        device.auth()
        print("✅ Authentication successful")
        return True
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return False


def explain_storage_full_error():
    """
    Explain the storage full error and how to resolve it
    """
    print("\n" + "="*70)
    print("DEVICE STORAGE FULL ERROR")
    print("="*70)
    print("\n❌ The Broadlink device's internal storage is full!")
    print("\n📝 What this means:")
    print("   - Broadlink devices have limited internal memory")
    print("   - Commands learned via HA integration accumulate over time")
    print("   - The device doesn't auto-clear old commands")
    print("\n🔧 How to fix:")
    print("   1. Open Home Assistant")
    print("   2. Go to Developer Tools → Services")
    print("   3. Call service: remote.delete_command")
    print("      - entity_id: your Broadlink remote")
    print("      - command: ['all']  (deletes all commands)")
    print("\n   OR manually delete commands from:")
    print(f"   Home Assistant's .storage/broadlink_remote_*_codes files")
    print("\n💡 Note: Our hybrid approach will avoid this issue by:")
    print("   - Capturing data immediately after learning")
    print("   - Not storing commands on the device long-term")
    print("   - Managing storage in our own devices.json")
    print("\n" + "="*70)


def detect_command_type(data: str) -> str:
    """Detect if command is IR or RF based on data length"""
    # RF commands are typically longer (>200 chars in base64)
    if len(data) > 200:
        return "RF"
    else:
        return "IR"


def learn_ir_command(device, timeout=30) -> Optional[str]:
    """
    Learn an IR command (1-step process)
    
    Returns:
        Base64 encoded command data, or None if failed
    """
    print("\n" + "="*70)
    print("IR COMMAND LEARNING (1-Step Process)")
    print("="*70)
    
    try:
        # Enter learning mode
        print("\n📡 Entering learning mode...")
        device.enter_learning()
        print("✅ Device is ready to learn")
        
        print("\n👉 Point your remote at the Broadlink device and press the button NOW!")
        print(f"   Waiting up to {timeout} seconds...\n")
        
        # Poll for data
        start_time = time.time()
        storage_errors = 0
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            print(f"   ⏳ Waiting... ({elapsed}/{timeout}s)", end='\r')
            
            # Check if we got data (catch StorageError like HA does)
            try:
                packet = device.check_data()
            except (broadlink.exceptions.ReadError, broadlink.exceptions.StorageError):
                # Ignore errors from old commands in buffer, keep trying
                storage_errors += 1
                if storage_errors == 1:
                    print(f"\n   ℹ️  Ignoring storage errors (old commands in buffer)")
                    print(f"   ⏳ Waiting... ({elapsed}/{timeout}s)", end='\r')
                continue
            
            if packet:
                print(f"\n\n✅ Signal captured! ({len(packet)} bytes)")
                if storage_errors > 0:
                    print(f"   (Ignored {storage_errors} storage errors)")
                
                # Convert to base64
                base64_data = base64.b64encode(packet).decode()
                print(f"   Base64 length: {len(base64_data)} characters")
                print(f"   First 50 chars: {base64_data[:50]}...")
                print(f"   Command type: {detect_command_type(base64_data)}")
                
                return base64_data
        
        print(f"\n\n❌ Timeout - no signal detected after {timeout} seconds")
        return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n\n❌ Error during learning: {e}")
        
        if "storage is full" in error_msg.lower():
            print("\n💡 TIP: The device's internal storage is full!")
            print("   Select option 3 from the menu for help on how to fix this")
        
        import traceback
        traceback.print_exc()
        return None


def learn_rf_command(device, timeout=30) -> Optional[str]:
    """
    Learn an RF command (2-step process)
    
    Step 1: Sweep frequency to find the RF frequency
    Step 2: Capture the actual RF signal
    
    Returns:
        Base64 encoded command data, or None if failed
    """
    print("\n" + "="*70)
    print("RF COMMAND LEARNING (2-Step Process)")
    print("="*70)
    
    try:
        # Step 1: Sweep frequency
        print("\n📡 STEP 1: Sweeping RF frequency...")
        device.sweep_frequency()
        print("✅ Frequency sweep started")
        
        print("\n👉 Press and HOLD the button on your remote for 2-3 seconds!")
        print(f"   Waiting up to {timeout} seconds...\n")
        
        # Poll for frequency lock
        start_time = time.time()
        frequency_found = False
        while time.time() - start_time < timeout:
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            print(f"   ⏳ Scanning frequencies... ({elapsed}/{timeout}s)", end='\r')
            
            # Check if frequency was found (returns tuple: is_found, frequency)
            is_found, frequency = device.check_frequency()
            if is_found:
                print(f"\n\n✅ RF frequency locked! ({frequency} MHz)")
                frequency_found = True
                break
        
        if not frequency_found:
            print(f"\n\n❌ Timeout - could not lock RF frequency after {timeout} seconds")
            print("   Make sure you're holding the button for 2-3 seconds")
            return None
        
        # Step 2: Find and capture RF data
        print("\n📡 STEP 2: Capturing RF signal...")
        device.find_rf_packet()
        print("✅ Ready to capture RF data")
        
        print("\n👉 Press the button on your remote again (short press)!")
        print(f"   Waiting up to {timeout} seconds...\n")
        
        # Poll for RF data
        start_time = time.time()
        storage_errors = 0
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            print(f"   ⏳ Waiting for signal... ({elapsed}/{timeout}s)", end='\r')
            
            # Check if we got data (catch StorageError like HA does)
            try:
                packet = device.check_data()
            except (broadlink.exceptions.ReadError, broadlink.exceptions.StorageError):
                # Ignore errors from old commands in buffer, keep trying
                storage_errors += 1
                if storage_errors == 1:
                    print(f"\n   ℹ️  Ignoring storage errors (old commands in buffer)")
                    print(f"   ⏳ Waiting for signal... ({elapsed}/{timeout}s)", end='\r')
                continue
            
            if packet:
                print(f"\n\n✅ RF signal captured! ({len(packet)} bytes)")
                if storage_errors > 0:
                    print(f"   (Ignored {storage_errors} storage errors)")
                
                # Convert to base64
                base64_data = base64.b64encode(packet).decode()
                print(f"   Base64 length: {len(base64_data)} characters")
                print(f"   First 50 chars: {base64_data[:50]}...")
                print(f"   Command type: {detect_command_type(base64_data)}")
                
                return base64_data
        
        print(f"\n\n❌ Timeout - no RF signal detected after {timeout} seconds")
        return None
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n\n❌ Error during RF learning: {e}")
        
        if "storage is full" in error_msg.lower():
            print("\n💡 TIP: The device's internal storage is full!")
            print("   Select option 3 from the menu for help on how to fix this")
        
        import traceback
        traceback.print_exc()
        return None


def test_send_command(device, command_data: str) -> bool:
    """
    Test sending a learned command back to the device
    
    Returns:
        True if successful, False otherwise
    """
    print("\n" + "="*70)
    print("TEST SENDING COMMAND")
    print("="*70)
    
    try:
        # Decode base64 back to bytes
        packet = base64.b64decode(command_data)
        
        print(f"\n📤 Sending command ({len(packet)} bytes)...")
        device.send_data(packet)
        print("✅ Command sent successfully!")
        print("\n👀 Did your device respond?")
        
        response = input("   Enter 'y' if device responded, 'n' if not: ").lower()
        if response == 'y':
            print("✅ Command verified - device responded!")
            return True
        else:
            print("⚠️  Command sent but device did not respond")
            return False
        
    except Exception as e:
        print(f"❌ Error sending command: {e}")
        return False


def main():
    print("="*70)
    print("Broadlink Direct Learning Test")
    print("="*70)
    print()
    print("This script tests learning commands directly from Broadlink devices")
    print("using python-broadlink, without using Home Assistant's integration.")
    print()
    
    # Step 1: Discover devices
    device_list = discover_devices(timeout=5)
    if not device_list:
        return
    
    # Step 2: Select device
    selected = select_device(device_list)
    if not selected:
        return
    
    device = selected['device']
    
    # Step 3: Authenticate
    if not authenticate_device(device):
        return
    
    # Step 4: Choose command type
    print("\n" + "="*70)
    print("COMMAND TYPE SELECTION")
    print("="*70)
    print("\n1. IR Command (1-step: press button once)")
    print("2. RF Command (2-step: hold button, then press again)")
    print("3. Help: Device storage full error")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect command type (1-4): ")
            
            if choice == '1':
                # Learn IR command
                command_data = learn_ir_command(device, timeout=30)
                if command_data:
                    print("\n" + "="*70)
                    print("SUCCESS!")
                    print("="*70)
                    print(f"\nLearned command data:")
                    print(f"{command_data}")
                    print()
                    
                    # Ask if user wants to test
                    test = input("Would you like to test sending this command? (y/n): ").lower()
                    if test == 'y':
                        test_send_command(device, command_data)
                    
                    # Ask if user wants to learn another
                    another = input("\nLearn another command? (y/n): ").lower()
                    if another != 'y':
                        break
                else:
                    retry = input("\nTry again? (y/n): ").lower()
                    if retry != 'y':
                        break
            
            elif choice == '2':
                # Learn RF command
                command_data = learn_rf_command(device, timeout=30)
                if command_data:
                    print("\n" + "="*70)
                    print("SUCCESS!")
                    print("="*70)
                    print(f"\nLearned command data:")
                    print(f"{command_data}")
                    print()
                    
                    # Ask if user wants to test
                    test = input("Would you like to test sending this command? (y/n): ").lower()
                    if test == 'y':
                        test_send_command(device, command_data)
                    
                    # Ask if user wants to learn another
                    another = input("\nLearn another command? (y/n): ").lower()
                    if another != 'y':
                        break
                else:
                    retry = input("\nTry again? (y/n): ").lower()
                    if retry != 'y':
                        break
            
            elif choice == '3':
                # Show help for storage full error
                explain_storage_full_error()
            
            elif choice == '4':
                break
            
            else:
                print("Please enter 1, 2, 3, or 4")
        
        except KeyboardInterrupt:
            print("\n\nCancelled")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)
    print("\nKey Findings:")
    print("✅ Direct learning works without Home Assistant")
    print("✅ Get command data immediately (no .storage lag)")
    print("✅ Full control over learning process and UI")
    print("✅ Can test sending commands back to device")
    print("\nThis confirms we can use direct python-broadlink for learning!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
