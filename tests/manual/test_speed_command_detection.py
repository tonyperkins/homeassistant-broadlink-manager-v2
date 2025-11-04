#!/usr/bin/env python3
"""
Manual test for speed command detection in entity generator.
Tests the fix for named speed commands (speed_low, speed_medium, speed_high).
"""

import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from entity_generator import EntityGenerator


def test_named_speed_commands():
    """Test that named speed commands are properly detected"""
    print("\n" + "=" * 60)
    print("TEST: Named Speed Commands (speed_low, speed_medium, speed_high)")
    print("=" * 60)

    # Mock storage manager
    class MockStorage:
        def get_all_entities(self):
            return {}

    generator = EntityGenerator(MockStorage())

    # Test device with named speed commands
    entity_data = {
        "device": "test_fan",
        "name": "Test Fan",
        "broadlink_entity": "remote.test_broadlink",
        "commands": {
            "turn_on": "turn_on_cmd",
            "turn_off": "turn_off_cmd",
            "speed_low": "speed_low_cmd",
            "speed_medium": "speed_medium_cmd",
            "speed_high": "speed_high_cmd",
        },
    }

    # Mock broadlink commands
    broadlink_commands = {
        "test_fan": {
            "turn_on_cmd": "base64_turn_on",
            "turn_off_cmd": "base64_turn_off",
            "speed_low_cmd": "base64_speed_low",
            "speed_medium_cmd": "base64_speed_medium",
            "speed_high_cmd": "base64_speed_high",
        }
    }

    result = generator._generate_fan("fan.test_fan", entity_data, broadlink_commands)

    if result is None:
        print("❌ FAILED: Entity generator returned None")
        print("   Expected: Valid fan configuration")
        return False

    # Check speed_count
    fan_config = result["fans"]["fan.test_fan"]
    speed_count = fan_config.get("speed_count", 0)

    print(f"\n✅ Entity generated successfully")
    print(f"   Speed count: {speed_count}")
    print(f"   Expected: 3 (low=1, medium=2, high=3)")

    if speed_count == 3:
        print("✅ PASSED: Correct speed count")
        return True
    else:
        print(f"❌ FAILED: Expected 3 speeds, got {speed_count}")
        return False


def test_numeric_speed_commands():
    """Test that numeric speed commands still work"""
    print("\n" + "=" * 60)
    print("TEST: Numeric Speed Commands (fan_speed_1, fan_speed_2, etc.)")
    print("=" * 60)

    class MockStorage:
        def get_all_entities(self):
            return {}

    generator = EntityGenerator(MockStorage())

    entity_data = {
        "device": "test_fan",
        "name": "Test Fan",
        "broadlink_entity": "remote.test_broadlink",
        "commands": {
            "turn_on": "turn_on_cmd",
            "turn_off": "turn_off_cmd",
            "fan_speed_1": "speed_1_cmd",
            "fan_speed_2": "speed_2_cmd",
            "fan_speed_3": "speed_3_cmd",
            "fan_speed_4": "speed_4_cmd",
        },
    }

    broadlink_commands = {
        "test_fan": {
            "turn_on_cmd": "base64_turn_on",
            "turn_off_cmd": "base64_turn_off",
            "speed_1_cmd": "base64_speed_1",
            "speed_2_cmd": "base64_speed_2",
            "speed_3_cmd": "base64_speed_3",
            "speed_4_cmd": "base64_speed_4",
        }
    }

    result = generator._generate_fan("fan.test_fan", entity_data, broadlink_commands)

    if result is None:
        print("❌ FAILED: Entity generator returned None")
        return False

    fan_config = result["fans"]["fan.test_fan"]
    speed_count = fan_config.get("speed_count", 0)

    print(f"\n✅ Entity generated successfully")
    print(f"   Speed count: {speed_count}")
    print(f"   Expected: 4")

    if speed_count == 4:
        print("✅ PASSED: Correct speed count")
        return True
    else:
        print(f"❌ FAILED: Expected 4 speeds, got {speed_count}")
        return False


def test_mixed_speed_commands():
    """Test mixed numeric and named speed commands"""
    print("\n" + "=" * 60)
    print("TEST: Mixed Speed Commands (speed_low, speed_high)")
    print("=" * 60)

    class MockStorage:
        def get_all_entities(self):
            return {}

    generator = EntityGenerator(MockStorage())

    entity_data = {
        "device": "test_fan",
        "name": "Test Fan",
        "broadlink_entity": "remote.test_broadlink",
        "commands": {
            "turn_on": "turn_on_cmd",
            "turn_off": "turn_off_cmd",
            "speed_low": "speed_low_cmd",
            "speed_high": "speed_high_cmd",
        },
    }

    broadlink_commands = {
        "test_fan": {
            "turn_on_cmd": "base64_turn_on",
            "turn_off_cmd": "base64_turn_off",
            "speed_low_cmd": "base64_speed_low",
            "speed_high_cmd": "base64_speed_high",
        }
    }

    result = generator._generate_fan("fan.test_fan", entity_data, broadlink_commands)

    if result is None:
        print("❌ FAILED: Entity generator returned None")
        return False

    fan_config = result["fans"]["fan.test_fan"]
    speed_count = fan_config.get("speed_count", 0)

    print(f"\n✅ Entity generated successfully")
    print(f"   Speed count: {speed_count}")
    print(f"   Expected: 2 (low=1, high=3)")
    print(f"   Note: Medium (2) is skipped, which is expected")

    if speed_count == 2:
        print("✅ PASSED: Correct speed count")
        return True
    else:
        print(f"❌ FAILED: Expected 2 speeds, got {speed_count}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SPEED COMMAND DETECTION TEST SUITE")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Named Speed Commands", test_named_speed_commands()))
    results.append(("Numeric Speed Commands", test_numeric_speed_commands()))
    results.append(("Mixed Speed Commands", test_mixed_speed_commands()))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
