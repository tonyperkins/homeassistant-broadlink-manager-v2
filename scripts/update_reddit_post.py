#!/usr/bin/env python3
"""
Update Reddit post with latest Broadlink Manager information.

This script updates a Reddit self-post with current project details,
features, and release information.
"""

import os
import sys
import praw
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


def generate_reddit_post():
    """Generate the Reddit post content"""
    readme = load_readme_content()
    changelog = load_changelog()
    
    # Extract key sections from README
    # This is a template - customize based on what you want to highlight
    post_content = f"""# Broadlink Manager v2 - IR/RF Device Management for Home Assistant

**The ultimate Home Assistant companion for Broadlink devices**  
Learn, manage, and automate infrared and radio frequency commands with a beautiful, modern interface.

## 🎯 Why Broadlink Manager?

Tired of juggling multiple remotes? Want to control your TV, AC, fans, and legacy devices through Home Assistant? **Broadlink Manager v2** makes it effortless.

✨ **Point. Click. Control.** Learn any IR/RF command in seconds with our intuitive interface. No coding required.

🎨 **Beautiful by Design.** A completely rewritten Vue 3 interface that's as pleasant to use as it is powerful. Light, medium, and dark themes adapt to your preference.

🚀 **SmartIR Supercharged.** First-class SmartIR integration means instant access to thousands of pre-configured device profiles. Set up your AC, TV, or media player in minutes, not hours.

🧠 **Intelligent & Automatic.** Discovers existing commands, migrates your setup seamlessly, and auto-generates Home Assistant entities. It just works.

## 📦 Installation

### Home Assistant Add-on (Recommended)
1. Add this repository to your Home Assistant add-on store
2. Install "Broadlink Manager"
3. Start the add-on
4. Access via the Web UI button

### Docker Standalone
```bash
docker run -d \\
  --name broadlink-manager \\
  -p 5000:5000 \\
  -v /path/to/data:/data \\
  ghcr.io/tonyperkins/broadlink-manager:latest
```

## 🔗 Links

- **GitHub**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2
- **Documentation**: Full docs in the repository
- **SmartIR Codes**: https://github.com/tonyperkins/smartir-code-aggregator

## 📸 Screenshots

### Light Theme
![Dashboard Overview](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/dashboard-overview.png)

![Device Management](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/device-list.png)

### Dark Theme
![Dark Mode Dashboard](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/dashboard-dark.png)

![Dark Mode Device List](https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/device-list-dark.png)

*View the [full gallery](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2#screenshots) including mobile and tablet views*

## 🆕 Latest Updates

{changelog if changelog else "See CHANGELOG.md in the repository for version history."}

## 🤝 Contributing

Contributions are welcome! Please check the GitHub repository for:
- Issue reporting
- Feature requests
- Pull requests
- Documentation improvements

## 📄 License

MIT License - See repository for details

---

**Last Updated**: {datetime.now().strftime('%Y-%m-%d')}

*This post is automatically updated. For the most current information, visit the GitHub repository.*
"""
    
    return post_content


def update_reddit_post(post_id: str, dry_run: bool = False):
    """
    Update a Reddit post with new content.
    
    Args:
        post_id: Reddit post ID (e.g., 'abc123')
        dry_run: If True, print content instead of posting
    """
    content = generate_reddit_post()
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN - Post content that would be uploaded:")
        print("=" * 80)
        print(content)
        print("=" * 80)
        return
    
    # Get credentials from environment variables
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    username = os.getenv('REDDIT_USERNAME')
    password = os.getenv('REDDIT_PASSWORD')
    user_agent = os.getenv('REDDIT_USER_AGENT', 'BroadlinkManager:v2.0:script (by /u/YourUsername)')
    
    if not all([client_id, client_secret, username, password]):
        print("ERROR: Missing Reddit credentials in environment variables.")
        print("Required: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD")
        sys.exit(1)
    
    try:
        print(f"🔐 Authenticating as: {username}")
        print(f"📝 User agent: {user_agent}")
        print(f"🆔 Client ID: {client_id[:8]}...")
        
        # Initialize Reddit API
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
            username=username,
            password=password
        )
        
        # Test authentication by getting user info
        print(f"✓ Authentication successful")
        print(f"📄 Fetching post: {post_id}")
        
        # Get the submission and edit it
        submission = reddit.submission(id=post_id)
        
        # Check if we're the author
        if submission.author.name != username:
            print(f"❌ Error: You are not the author of this post")
            print(f"   Post author: {submission.author.name}")
            print(f"   Your username: {username}")
            sys.exit(1)
        
        print(f"✓ You are the post author")
        print(f"📝 Updating post...")
        
        submission.edit(content)
        
        print(f"✅ Successfully updated Reddit post: https://reddit.com{submission.permalink}")
        
    except Exception as e:
        print(f"❌ Error updating Reddit post: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Reddit post with Broadlink Manager info')
    parser.add_argument('post_id', nargs='?', help='Reddit post ID (e.g., abc123)')
    parser.add_argument('--dry-run', action='store_true', help='Preview content without posting')
    
    args = parser.parse_args()
    
    if not args.post_id and not args.dry_run:
        parser.print_help()
        print("\nTip: Use --dry-run to preview the post content first")
        sys.exit(1)
    
    update_reddit_post(args.post_id or 'preview', dry_run=args.dry_run)
