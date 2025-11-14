#!/usr/bin/env python3
"""
Quick Release Script for Broadlink Manager v2 Alpha Releases

Automates the entire release process:
1. Bumps version in config.yaml and package.json
2. Updates CHANGELOG.md
3. Commits changes
4. Pushes to develop
5. Optionally creates GitHub release

Usage:
    # Patch release (0.3.0-alpha.4 -> 0.3.0-alpha.5)
    python scripts/quick_release.py patch

    # Minor release (0.3.0-alpha.5 -> 0.4.0-alpha.1)
    python scripts/quick_release.py minor

    # Specific version
    python scripts/quick_release.py 0.3.0-alpha.5

    # With custom message
    python scripts/quick_release.py patch -m "Fix area sync error"

    # Skip GitHub release creation
    python scripts/quick_release.py patch --no-github
"""

import sys
import re
import subprocess
from pathlib import Path
from datetime import date
import argparse


def get_current_version(root_dir: Path) -> str:
    """Get current version from config.yaml"""
    config_file = root_dir / "config.yaml"
    content = config_file.read_text(encoding="utf-8")
    match = re.search(r'version:\s*"([^"]*)"', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in config.yaml")


def parse_version(version: str) -> dict:
    """Parse version string into components"""
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:-alpha\.(\d+))?$", version)
    if not match:
        raise ValueError(f"Invalid version format: {version}")

    return {
        "major": int(match.group(1)),
        "minor": int(match.group(2)),
        "patch": int(match.group(3)),
        "alpha": int(match.group(4)) if match.group(4) else None,
    }


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type"""
    parts = parse_version(current)

    if bump_type == "patch":
        # Increment alpha number
        if parts["alpha"] is None:
            parts["alpha"] = 1
        else:
            parts["alpha"] += 1
    elif bump_type == "minor":
        # Increment minor, reset patch and alpha
        parts["minor"] += 1
        parts["patch"] = 0
        parts["alpha"] = 1
    elif bump_type == "major":
        # Increment major, reset minor, patch and alpha
        parts["major"] += 1
        parts["minor"] = 0
        parts["patch"] = 0
        parts["alpha"] = 1

    # Build version string
    version = f"{parts['major']}.{parts['minor']}.{parts['patch']}"
    if parts["alpha"]:
        version += f"-alpha.{parts['alpha']}"

    return version


def update_config_yaml(version: str, root_dir: Path) -> bool:
    """Update version in config.yaml"""
    config_file = root_dir / "config.yaml"
    content = config_file.read_text(encoding="utf-8")
    new_content = re.sub(r'version:\s*"[^"]*"', f'version: "{version}"', content)
    config_file.write_text(new_content, encoding="utf-8")
    print(f"✅ Updated config.yaml")
    return True


def update_package_json(version: str, root_dir: Path) -> bool:
    """Update version in frontend/package.json"""
    package_file = root_dir / "frontend" / "package.json"
    content = package_file.read_text(encoding="utf-8")
    new_content = re.sub(r'"version":\s*"[^"]*"', f'"version": "{version}"', content)
    package_file.write_text(new_content, encoding="utf-8")
    print(f"✅ Updated frontend/package.json")
    return True


def update_changelog(version: str, root_dir: Path, message: str = None) -> bool:
    """Add new version section to CHANGELOG.md"""
    changelog_file = root_dir / "CHANGELOG.md"
    content = changelog_file.read_text(encoding="utf-8")

    # Check if version already exists
    if f"## [{version}]" in content:
        print(f"⚠️  Version {version} already in CHANGELOG.md, skipping")
        return True

    # Build changelog entry
    today = date.today().strftime("%Y-%m-%d")
    if message:
        new_section = f"\n## [{version}] - {today}\n\n### Fixed\n- {message}\n\n"
    else:
        new_section = (
            f"\n## [{version}] - {today}\n\n### Added\n\n### Changed\n\n### Fixed\n\n"
        )

    new_content = content.replace("## [Unreleased]", f"## [Unreleased]{new_section}")
    changelog_file.write_text(new_content, encoding="utf-8")
    print(f"✅ Updated CHANGELOG.md")
    return True


def run_command(cmd: list, cwd: Path = None) -> tuple:
    """Run shell command and return (success, output)"""
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


def main():
    parser = argparse.ArgumentParser(description="Quick release for alpha versions")
    parser.add_argument(
        "version",
        help="Version bump type (patch/minor/major) or specific version (0.3.0-alpha.5)",
    )
    parser.add_argument(
        "-m", "--message", help="Release message for CHANGELOG", default=None
    )
    parser.add_argument(
        "--no-github", action="store_true", help="Skip GitHub release creation"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be done without doing it"
    )

    args = parser.parse_args()

    root_dir = Path(__file__).parent.parent

    # Get current version
    current_version = get_current_version(root_dir)
    print(f"📦 Current version: {current_version}")

    # Determine new version
    if args.version in ["patch", "minor", "major"]:
        new_version = bump_version(current_version, args.version)
    else:
        # Validate custom version
        try:
            parse_version(args.version)
            new_version = args.version
        except ValueError as e:
            print(f"❌ {e}")
            sys.exit(1)

    print(f"🚀 New version: {new_version}")

    if args.dry_run:
        print("\n🔍 DRY RUN - No changes will be made\n")
        print("Would update:")
        print("  - config.yaml")
        print("  - frontend/package.json")
        print("  - CHANGELOG.md")
        print(f"\nWould commit: 'chore: release {new_version}'")
        print("Would push to: develop")
        if not args.no_github:
            print("Would create GitHub release")
        return

    # Update version files
    print(f"\n📝 Updating version files...")
    update_config_yaml(new_version, root_dir)
    update_package_json(new_version, root_dir)
    update_changelog(new_version, root_dir, args.message)

    # Git operations
    print(f"\n📦 Committing changes...")

    # Stage files
    success, output = run_command(
        ["git", "add", "config.yaml", "frontend/package.json", "CHANGELOG.md"],
        cwd=root_dir,
    )
    if not success:
        print(f"❌ Failed to stage files: {output}")
        sys.exit(1)

    # Commit
    commit_msg = f"chore: release {new_version}"
    if args.message:
        commit_msg += f"\n\n{args.message}"

    success, output = run_command(["git", "commit", "-m", commit_msg], cwd=root_dir)
    if not success:
        print(f"❌ Failed to commit: {output}")
        sys.exit(1)
    print(f"✅ Committed changes")

    # Push to develop
    print(f"\n🚀 Pushing to develop...")
    success, output = run_command(["git", "push", "origin", "develop"], cwd=root_dir)
    if not success:
        print(f"❌ Failed to push: {output}")
        sys.exit(1)
    print(f"✅ Pushed to develop")

    # Also push to main for Home Assistant compatibility
    print(f"\n🚀 Pushing to main...")
    success, output = run_command(["git", "push", "origin", "develop:main"], cwd=root_dir)
    if not success:
        print(f"❌ Failed to push to main: {output}")
        sys.exit(1)
    print(f"✅ Pushed to main")

    # Create tag
    print(f"\n🏷️  Creating tag v{new_version}...")
    success, output = run_command(
        ["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"],
        cwd=root_dir,
    )
    if not success:
        print(f"❌ Failed to create tag: {output}")
        sys.exit(1)

    # Push tag
    success, output = run_command(
        ["git", "push", "origin", f"v{new_version}"], cwd=root_dir
    )
    if not success:
        print(f"❌ Failed to push tag: {output}")
        sys.exit(1)
    print(f"✅ Created and pushed tag v{new_version}")

    # GitHub release
    if not args.no_github:
        print(f"\n📢 Creating GitHub release...")
        
        # Try to use GitHub CLI first
        success, output = run_command(
            ["gh", "release", "create", f"v{new_version}", 
             "--prerelease", 
             "--generate-notes",
             "--title", f"v{new_version}"],
            cwd=root_dir
        )
        
        if success:
            print(f"✅ GitHub release created successfully!")
            print(f"   View at: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v{new_version}")
        else:
            # Fallback to manual instructions
            print(f"⚠️  GitHub CLI not available or failed")
            print(f"   Install: https://cli.github.com/")
            print(f"   Or create manually:")
            print(f"   Visit: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/new?tag=v{new_version}")

    print(f"\n✅ Release {new_version} complete!")
    print(f"\n📋 Next steps:")
    print(f"   1. Test installation in Home Assistant")
    print(f"   2. Update Reddit/forum posts if needed")


if __name__ == "__main__":
    main()
