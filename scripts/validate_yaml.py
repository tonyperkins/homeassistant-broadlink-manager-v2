#!/usr/bin/env python3
"""
CLI tool to validate SmartIR YAML files
Usage: python scripts/validate_yaml.py /config/smartir/climate.yaml
"""

import sys
import os
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

from yaml_validator import YAMLValidator


def validate_file(file_path: str, platform: str = None) -> bool:
    """
    Validate a SmartIR YAML file

    Args:
        file_path: Path to YAML file
        platform: Platform type (auto-detected from filename if not provided)

    Returns:
        True if valid, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    # Auto-detect platform from filename
    if platform is None:
        platform = file_path.stem  # climate.yaml -> climate

    if platform not in ["climate", "media_player", "fan", "light"]:
        print(f"❌ Invalid platform: {platform}")
        print("   Valid platforms: climate, media_player, fan, light")
        return False

    print(f"🔍 Validating {file_path} as {platform} platform...")
    print()

    is_valid, errors = YAMLValidator.validate_existing_file(str(file_path), platform)

    if is_valid:
        print("✅ YAML file is valid!")
        print()
        return True
    else:
        print("❌ YAML file validation failed:")
        print()
        for error in errors:
            print(f"   • {error}")
        print()
        return False


def validate_directory(directory: str) -> bool:
    """
    Validate all SmartIR YAML files in a directory

    Args:
        directory: Path to directory containing YAML files

    Returns:
        True if all files are valid, False otherwise
    """
    directory = Path(directory)

    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return False

    platforms = ["climate", "media_player", "fan", "light"]
    all_valid = True

    for platform in platforms:
        file_path = directory / f"{platform}.yaml"
        if file_path.exists():
            if not validate_file(str(file_path), platform):
                all_valid = False
            print()

    return all_valid


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Validate single file:")
        print("    python scripts/validate_yaml.py /config/smartir/climate.yaml")
        print()
        print("  Validate directory:")
        print("    python scripts/validate_yaml.py /config/smartir/")
        print()
        print("  Specify platform explicitly:")
        print("    python scripts/validate_yaml.py /config/smartir/climate.yaml climate")
        sys.exit(1)

    path = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else None

    path_obj = Path(path)

    if path_obj.is_dir():
        success = validate_directory(path)
    else:
        success = validate_file(path, platform)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
