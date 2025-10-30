"""
Simple learning test that mimics EXACTLY what HA does (with StorageError handling)

This script does what HA's integration does:
1. Authenticate
2. Enter learning mode
3. Wait for button press
4. Check for data (catching StorageError like HA does!)
5. Return data

Key fix: Catch StorageError and ReadError, continue looping (just like HA)
"""

import broadlink
import base64
import time


def main():
    print("="*70)
    print("Simple Learning Test (Fixed - Catches StorageError)")
    print("="*70)
    print()
    
    # Discover
    print("🔍 Discovering devices...")
    devices = broadlink.discover(timeout=5)
    
    if not devices:
        print("❌ No devices found")
        return
    
    print(f"✅ Found {len(devices)} device(s)\n")
    for i, d in enumerate(devices, 1):
        print(f"{i}. {d.host[0]} - {d.mac.hex(':')}")
    
    # Select
    if len(devices) == 1:
        device = devices[0]
    else:
        choice = int(input(f"\nSelect device (1-{len(devices)}): "))
        device = devices[choice - 1]
    
    print()
    
    # Authenticate
    print("🔐 Authenticating...")
    try:
        device.auth()
        print("✅ Authenticated")
    except Exception as e:
        print(f"❌ Auth failed: {e}")
        return
    
    print()
    print("="*70)
    print("LEARNING MODE (Exactly like HA - with StorageError handling)")
    print("="*70)
    print()
    
    # This is EXACTLY what HA does
    try:
        # Step 1: Enter learning mode
        print("📡 Entering learning mode...")
        device.enter_learning()
        print("✅ Ready to learn")
        
        # Step 2: Wait for button press
        print("\n👉 Press your remote button NOW!")
        print("   Waiting up to 30 seconds...\n")
        
        # Step 3: Poll for data (just like HA)
        start_time = time.time()
        storage_errors = 0
        
        while time.time() - start_time < 30:
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            print(f"   ⏳ Waiting... ({elapsed}/30s)", end='\r')
            
            # Check for data - THIS IS THE KEY FIX!
            try:
                packet = device.check_data()
            except (broadlink.exceptions.ReadError, broadlink.exceptions.StorageError) as e:
                # This is what HA does - catch these errors and CONTINUE!
                storage_errors += 1
                if storage_errors == 1:
                    print(f"\n   ℹ️  Ignoring storage errors (buffer has old commands)")
                    print(f"   ⏳ Waiting... ({elapsed}/30s)", end='\r')
                continue
            
            # Got data!
            if packet:
                print(f"\n\n✅ SUCCESS! Got {len(packet)} bytes")
                if storage_errors > 0:
                    print(f"   (Ignored {storage_errors} storage errors from old commands)")
                
                # Convert to base64
                base64_data = base64.b64encode(packet).decode()
                print(f"\nBase64 data ({len(base64_data)} chars):")
                print(base64_data)
                print()
                
                # Ask if user wants to test sending it back
                test = input("Test sending this command? (y/n): ").lower()
                if test == 'y':
                    print("\n📤 Sending command back...")
                    device.send_data(packet)
                    print("✅ Sent! Did your device respond?")
                
                return
        
        print(f"\n\n❌ Timeout - no signal detected after 30 seconds")
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled")
