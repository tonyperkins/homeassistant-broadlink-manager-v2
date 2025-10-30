"""
Simple learning test that mimics exactly what HA does

This script does ONLY what HA's integration does:
1. Authenticate
2. Enter learning mode
3. Wait for button press
4. Check for data
5. Return data

NO buffer clearing, NO extra logic - just the basics.
"""

import broadlink
import base64
import time


def main():
    print("="*70)
    print("Simple Learning Test (Mimics HA Integration)")
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
    print("LEARNING MODE (Exactly like HA)")
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
        while time.time() - start_time < 30:
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            print(f"   ⏳ Waiting... ({elapsed}/30s)", end='\r')
            
            # Check for data (this is what HA does)
            try:
                packet = device.check_data()
                if packet:
                    print(f"\n\n✅ SUCCESS! Got {len(packet)} bytes")
                    
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
            except Exception as e:
                # If check_data fails, show the error
                print(f"\n\n❌ Error checking data: {e}")
                print(f"   Error type: {type(e).__name__}")
                
                if "storage is full" in str(e).lower():
                    print("\n🔍 Got 'storage full' error while checking for NEW data")
                    print("   This means the device buffer has unread old commands")
                    print("   that are blocking new learning.")
                    print("\n💡 Solution:")
                    print("   1. Go to Home Assistant")
                    print("   2. Developer Tools → Services")
                    print("   3. Call: remote.delete_command")
                    print("      entity_id: <your_remote>")
                    print("      command: ['all']")
                
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
