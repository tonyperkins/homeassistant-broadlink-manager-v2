#!/usr/bin/env python3
"""
Fix entity IDs in metadata.json by removing entity type prefix

This script fixes the bug where entity IDs were created with type prefix
(e.g., "light.bedroom_light" instead of "bedroom_light")
"""

import json
from pathlib import Path
import sys


def fix_entity_ids(metadata_path):
    """Fix entity IDs by removing type prefix and removing duplicates"""

    # Read metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    entities = metadata.get("entities", {})
    fixed_entities = {}
    removed_count = 0
    fixed_count = 0

    print(f"Found {len(entities)} entities in metadata")
    print("\nProcessing entities...")

    for entity_id, entity_data in entities.items():
        # Check if entity_id has a type prefix (contains a dot)
        if "." in entity_id:
            # Extract the actual device name (part after the dot)
            entity_type, device_name = entity_id.split(".", 1)

            # Check if there's already a correct entry without prefix
            if device_name in entities or device_name in fixed_entities:
                print(f"  ❌ Removing duplicate: {entity_id} (correct version exists: {device_name})")
                removed_count += 1
                continue
            else:
                # No correct version exists, so fix this one
                print(f"  🔧 Fixing: {entity_id} -> {device_name}")
                fixed_entities[device_name] = entity_data
                fixed_count += 1
        else:
            # Entity ID is already correct (no prefix)
            print(f"  ✅ Keeping: {entity_id}")
            fixed_entities[entity_id] = entity_data

    # Update metadata
    metadata["entities"] = fixed_entities

    # Backup original file
    backup_path = metadata_path.parent / f"{metadata_path.stem}_backup.json"
    print(f"\n📁 Creating backup: {backup_path}")
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # Write fixed metadata
    print(f"💾 Writing fixed metadata: {metadata_path}")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n✅ Done!")
    print(f"   - Fixed: {fixed_count} entities")
    print(f"   - Removed: {removed_count} duplicate entities")
    print(f"   - Total: {len(fixed_entities)} entities")

    return fixed_count, removed_count


if __name__ == "__main__":
    # Default path
    metadata_path = Path("h:/broadlink_manager/metadata.json")

    # Allow custom path as argument
    if len(sys.argv) > 1:
        metadata_path = Path(sys.argv[1])

    if not metadata_path.exists():
        print(f"❌ Error: Metadata file not found: {metadata_path}")
        sys.exit(1)

    print(f"🔧 Fixing entity IDs in: {metadata_path}\n")

    try:
        fixed, removed = fix_entity_ids(metadata_path)
        print(f"\n🎉 Successfully fixed metadata!")
        print(f"\nNext steps:")
        print(f"1. Restart the Broadlink Manager")
        print(f"2. Click 'Generate Entities' button")
        print(f"3. Restart Home Assistant")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
