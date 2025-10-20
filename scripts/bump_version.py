#!/usr/bin/env python3
"""
Version Bump Script for Broadlink Manager v2

Updates version numbers in:
- config.yaml
- frontend/package.json
- CHANGELOG.md (adds new version section)

Usage:
    python scripts/bump_version.py 0.3.0-alpha.2
"""

import sys
import re
from pathlib import Path
from datetime import date

def update_config_yaml(version: str, root_dir: Path) -> bool:
    """Update version in config.yaml"""
    config_file = root_dir / "config.yaml"
    
    if not config_file.exists():
        print(f"❌ Error: {config_file} not found")
        return False
    
    content = config_file.read_text(encoding='utf-8')
    
    # Update version line
    new_content = re.sub(
        r'version:\s*"[^"]*"',
        f'version: "{version}"',
        content
    )
    
    if content == new_content:
        print(f"⚠️  Warning: No version found in {config_file}")
        return False
    
    config_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Updated {config_file}")
    return True

def update_package_json(version: str, root_dir: Path) -> bool:
    """Update version in frontend/package.json"""
    package_file = root_dir / "frontend" / "package.json"
    
    if not package_file.exists():
        print(f"❌ Error: {package_file} not found")
        return False
    
    content = package_file.read_text(encoding='utf-8')
    
    # Update version line
    new_content = re.sub(
        r'"version":\s*"[^"]*"',
        f'"version": "{version}"',
        content
    )
    
    if content == new_content:
        print(f"⚠️  Warning: No version found in {package_file}")
        return False
    
    package_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Updated {package_file}")
    return True

def update_changelog(version: str, root_dir: Path) -> bool:
    """Add new version section to CHANGELOG.md"""
    changelog_file = root_dir / "CHANGELOG.md"
    
    if not changelog_file.exists():
        print(f"❌ Error: {changelog_file} not found")
        return False
    
    content = changelog_file.read_text(encoding='utf-8')
    
    # Check if version already exists
    if f"## [{version}]" in content:
        print(f"⚠️  Warning: Version {version} already exists in CHANGELOG.md")
        return False
    
    # Add new version section after [Unreleased]
    today = date.today().strftime("%Y-%m-%d")
    new_section = f"\n## [{version}] - {today}\n\n### Added\n\n### Changed\n\n### Fixed\n\n"
    
    new_content = content.replace(
        "## [Unreleased]",
        f"## [Unreleased]{new_section}"
    )
    
    if content == new_content:
        print(f"⚠️  Warning: Could not find [Unreleased] section in {changelog_file}")
        return False
    
    changelog_file.write_text(new_content, encoding='utf-8')
    print(f"✅ Updated {changelog_file} (added section for {version})")
    print(f"   📝 Remember to fill in the Added/Changed/Fixed sections!")
    return True

def validate_version(version: str) -> bool:
    """Validate version format"""
    # Match: 0.3.0, 0.3.0-alpha.1, 1.0.0-beta.2, etc.
    pattern = r'^\d+\.\d+\.\d+(-(?:alpha|beta|rc)\.\d+)?$'
    
    if not re.match(pattern, version):
        print(f"❌ Error: Invalid version format: {version}")
        print(f"   Expected format: X.Y.Z or X.Y.Z-alpha.N or X.Y.Z-beta.N")
        print(f"   Examples: 0.3.0, 0.3.0-alpha.2, 1.0.0-beta.1")
        return False
    
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <version>")
        print("Example: python scripts/bump_version.py 0.3.0-alpha.2")
        sys.exit(1)
    
    version = sys.argv[1]
    
    # Validate version format
    if not validate_version(version):
        sys.exit(1)
    
    # Get root directory
    root_dir = Path(__file__).parent.parent
    
    print(f"\n🚀 Bumping version to {version}...\n")
    
    # Update all files
    success = True
    success &= update_config_yaml(version, root_dir)
    success &= update_package_json(version, root_dir)
    success &= update_changelog(version, root_dir)
    
    if success:
        print(f"\n✅ Version bumped to {version} successfully!")
        print(f"\n📋 Next steps:")
        print(f"   1. Fill in CHANGELOG.md with changes")
        print(f"   2. git add config.yaml frontend/package.json CHANGELOG.md")
        print(f"   3. git commit -m 'chore: bump version to {version}'")
        print(f"   4. Follow the release process in docs/RELEASE_PROCESS.md")
    else:
        print(f"\n❌ Version bump failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
