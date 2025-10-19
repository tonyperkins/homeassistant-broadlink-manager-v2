import base64

# Test RF command detection
# Let's check what 'sc' actually decodes to
test_cases = [
    ("JgA", "IR command"),
    ("Jg", "RF command (0x26)"),
    ("sc", "RF 433MHz?"),
    ("sg", "RF 433MHz?"),
    ("1w", "RF 315MHz?"),
]

print("Base64 prefix analysis:")
print("=" * 60)

for prefix, description in test_cases:
    # Pad to make valid base64
    padded = prefix + "AAAA"
    try:
        raw = base64.b64decode(padded)
        print(f"{prefix:4s} -> 0x{raw[0]:02x} {raw[1]:02x} - {description}")
    except Exception as e:
        print(f"{prefix:4s} -> Error: {e}")

print("\n" + "=" * 60)
print("\nKnown Broadlink patterns:")
print("  0x26 0x00 = IR")
print("  0x26 0x01+ = RF")
print("  0xb2 = RF 433MHz")
print("  0xd7 = RF 315MHz")

print("\n" + "=" * 60)
print("\nYour commands start with 'sc' which decodes to:")
raw = base64.b64decode("scAAAA==")
print(f"  First byte: 0x{raw[0]:02x}")
print(f"  This is 0xb1, which is close to 0xb2 (RF 433MHz)")
print(f"  Let me check if 0xb1 is also RF...")

# Check common RF prefixes
rf_prefixes = ['sc', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sp', 'sq', 'sr', 'ss', 'st', 'su', 'sv', 'sw']
print("\n" + "=" * 60)
print("\nChecking 's*' prefixes (0xb0-0xbf range):")
for prefix in rf_prefixes[:8]:
    try:
        raw = base64.b64decode(prefix + "AAAA")
        print(f"  {prefix} -> 0x{raw[0]:02x}")
    except:
        pass
