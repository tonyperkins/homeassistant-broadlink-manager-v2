#!/usr/bin/env python3
"""
Update Home Assistant Community Forum post with latest Broadlink Manager information.

This script updates a Discourse forum post with current project details.
"""

import os
import sys
import requests
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_readme_content():
    """Load and extract relevant sections from README.md"""
    readme_path = Path(__file__).parent.parent / "README.md"
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def load_changelog():
    """Load latest changelog entry"""
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    if not changelog_path.exists():
        return None
    
    with open(changelog_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Extract the latest version section
    latest_version = []
    in_version = False
    for line in lines:
        if line.startswith('## [') and not in_version:
            in_version = True
            latest_version.append(line)
        elif line.startswith('## [') and in_version:
            break
        elif in_version:
            latest_version.append(line)
    
    return ''.join(latest_version).strip()


def generate_forum_post():
    """Generate the forum post content"""
    readme = load_readme_content()
    changelog = load_changelog()
    
    # Discourse supports full markdown
    post_content = f"""# Broadlink Manager v2 - IR/RF Device Management for Home Assistant

**The ultimate Home Assistant companion for Broadlink devices**  
Learn, manage, and automate infrared and radio frequency commands with a beautiful, modern interface.

---

## :dart: Why Broadlink Manager?

Tired of juggling multiple remotes? Want to control your TV, AC, fans, and legacy devices through Home Assistant? **Broadlink Manager v2** makes it effortless.

:sparkles: **Point. Click. Control.** Learn any IR/RF command in seconds with our intuitive interface. No coding required.

:art: **Beautiful by Design.** A completely rewritten Vue 3 interface that's as pleasant to use as it is powerful. Light, medium, and dark themes adapt to your preference.

:rocket: **SmartIR Supercharged.** First-class SmartIR integration means instant access to thousands of pre-configured device profiles. Set up your AC, TV, or media player in minutes, not hours.

:brain: **Intelligent & Automatic.** Discovers existing commands, migrates your setup seamlessly, and auto-generates Home Assistant entities. It just works.

---

## :package: Installation

### Home Assistant Add-on (Recommended)
1. Add this repository to your Home Assistant add-on store
2. Install "Broadlink Manager"
3. Start the add-on
4. Access via the Web UI button

**Add-on Repository**: `https://github.com/tonyperkins/homeassistant-broadlink-manager-v2`

### Docker Standalone
```bash
docker run -d \\
  --name broadlink-manager \\
  -p 5000:5000 \\
  -v /path/to/data:/data \\
  ghcr.io/tonyperkins/broadlink-manager:latest
```

---

## :link: Links

- **GitHub Repository**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2
- **Documentation**: Complete guides in the repository
- **SmartIR Code Database**: https://github.com/tonyperkins/smartir-code-aggregator
- **Issue Tracker**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues

---

## :camera: Screenshots

### Light Theme
![Dashboard Overview](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/dashboard-overview.png)

![Device Management](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/device-list.png)

### Dark Theme
![Dark Mode Dashboard](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/dashboard-dark.png)

![Dark Mode Device List](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/device-list-dark.png)

[View full gallery](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2#screenshots) including mobile and tablet views

---

## :new: Latest Updates

{changelog if changelog else "See [CHANGELOG.md](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/CHANGELOG.md) for version history."}

---

## :handshake: Contributing

Contributions are welcome! Please check the GitHub repository for:
- Issue reporting
- Feature requests
- Pull requests
- Documentation improvements

---

## :page_facing_up: License

MIT License - See [repository](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/LICENSE) for details

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

*This post is automatically updated. For the most current information, visit the [GitHub repository](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2).*
"""
    
    return post_content


def update_forum_post(post_id: int, dry_run: bool = False):
    """
    Update a Home Assistant forum post with new content.
    
    Args:
        post_id: Discourse post ID (numeric)
        dry_run: If True, print content instead of posting
    """
    content = generate_forum_post()
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN - Post content that would be uploaded:")
        print("=" * 80)
        print(content)
        print("=" * 80)
        return
    
    # Get credentials from environment variables
    api_key = os.getenv('DISCOURSE_API_KEY')
    username = os.getenv('DISCOURSE_USERNAME')
    forum_url = os.getenv('DISCOURSE_URL', 'https://community.home-assistant.io')
    
    if not all([api_key, username]):
        print("ERROR: Missing Discourse credentials in environment variables.")
        print("Required: DISCOURSE_API_KEY, DISCOURSE_USERNAME")
        print("\nTo get your API key:")
        print("1. Go to https://community.home-assistant.io/u/{username}/preferences/security")
        print("2. Generate a new API key")
        print("3. Set DISCOURSE_API_KEY environment variable")
        sys.exit(1)
    
    try:
        print(f"🔐 Authenticating as: {username}")
        print(f"🌐 Forum URL: {forum_url}")
        print(f"📄 Updating post: {post_id}")
        
        headers = {
            "Api-Key": api_key,
            "Api-Username": username,
            "Content-Type": "application/json"
        }
        
        data = {
            "post": {
                "raw": content
            }
        }
        
        response = requests.put(
            f"{forum_url}/posts/{post_id}.json",
            headers=headers,
            json=data
        )
        
        response.raise_for_status()
        
        post_data = response.json()
        topic_id = post_data['post']['topic_id']
        topic_slug = post_data['post']['topic_slug']
        
        print(f"✅ Successfully updated forum post!")
        print(f"   View at: {forum_url}/t/{topic_slug}/{topic_id}/{post_id}")
        
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error updating forum post: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update HA forum post with Broadlink Manager info')
    parser.add_argument('post_id', nargs='?', type=int, help='Discourse post ID (numeric)')
    parser.add_argument('--dry-run', action='store_true', help='Preview content without posting')
    
    args = parser.parse_args()
    
    if not args.post_id and not args.dry_run:
        parser.print_help()
        print("\nTip: Use --dry-run to preview the post content first")
        print("\nTo find your post ID:")
        print("1. Go to your forum post")
        print("2. Click the share button or link icon")
        print("3. The URL will be like: .../t/topic-name/12345/67")
        print("4. The last number (67) is your post ID")
        sys.exit(1)
    
    update_forum_post(args.post_id or 0, dry_run=args.dry_run)
