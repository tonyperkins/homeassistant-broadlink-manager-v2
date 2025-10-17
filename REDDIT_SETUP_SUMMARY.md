# Reddit Post Updates - Quick Setup Summary

Automated Reddit post updates have been implemented for Broadlink Manager v2.

## 📁 Files Created

### Scripts
- **`scripts/update_reddit_post.py`** - Main script to update Reddit posts
  - Generates post content from README and CHANGELOG
  - Supports dry-run mode for preview
  - Uses PRAW (Python Reddit API Wrapper)

### Documentation
- **`docs/REDDIT_UPDATES.md`** - Complete guide with setup, usage, and automation
- **`docs/REDDIT_GITHUB_SECRETS.md`** - GitHub Secrets configuration guide
- **`scripts/README.md`** - Updated with Reddit script documentation

### Configuration
- **`.env.example`** - Added Reddit API credentials section
- **`requirements-test.txt`** - Added `praw>=7.7.0` dependency

### Automation
- **`.github/workflows/update-reddit-post.yml`** - GitHub Action for automatic updates on releases

## 🚀 Quick Start

### 1. Create Reddit App
```
1. Go to: https://www.reddit.com/prefs/apps
2. Click "Create App" → Choose "script"
3. Note your client_id and client_secret
```

### 2. Set Environment Variables
```bash
# Windows PowerShell
$env:REDDIT_CLIENT_ID="your_client_id"
$env:REDDIT_CLIENT_SECRET="your_secret"
$env:REDDIT_USERNAME="your_username"
$env:REDDIT_PASSWORD="your_password"
```

### 3. Install Dependencies
```bash
pip install praw
```

### 4. Test (Dry Run)
```bash
python scripts/update_reddit_post.py --dry-run
```

### 5. Update Post
```bash
python scripts/update_reddit_post.py abc123
```
Replace `abc123` with your Reddit post ID.

## 🤖 Automated Updates

### GitHub Actions (Recommended)
1. Add secrets to GitHub repository (see `docs/REDDIT_GITHUB_SECRETS.md`)
2. Workflow runs automatically on new releases
3. Can also trigger manually from Actions tab

### Cron Job
```bash
# Update every Monday at 9 AM
0 9 * * 1 cd /path/to/project && python scripts/update_reddit_post.py abc123
```

## 📋 What Gets Updated

The script automatically generates a Reddit post with:
- ✅ Project description and key features
- ✅ Installation instructions (Add-on and Docker)
- ✅ Links to GitHub and documentation
- ✅ Latest changelog entry
- ✅ Screenshots reference
- ✅ Contributing information
- ✅ License information
- ✅ Auto-generated timestamp

## 🔧 Customization

Edit `scripts/update_reddit_post.py` in the `generate_reddit_post()` function to:
- Change post template and layout
- Add/remove sections
- Modify formatting
- Include different content

## 📚 Full Documentation

- **Setup Guide**: `docs/REDDIT_UPDATES.md`
- **GitHub Secrets**: `docs/REDDIT_GITHUB_SECRETS.md`
- **Script Docs**: `scripts/README.md`

## ⚠️ Important Notes

### Limitations
- Can only edit **self-posts** (text posts), not link posts
- Cannot change post **title** after creation
- Must be the **post author** to edit
- Rate limited to 60 requests/minute

### Security
- Never commit credentials to git
- Use environment variables or GitHub Secrets
- Consider using a dedicated Reddit account
- GitHub encrypts all secrets

### Best Practices
- Always test with `--dry-run` first
- Update after major releases or changes
- Keep CHANGELOG.md current
- Link to GitHub for most current info

## 🎯 Next Steps

1. **Create Reddit Post** - Post your initial announcement
2. **Get Post ID** - Note the ID from the URL
3. **Test Locally** - Run dry-run to preview
4. **Update Post** - Run script to update
5. **Setup Automation** - Configure GitHub Actions (optional)

## 💡 Example Workflow

```bash
# 1. Preview what will be posted
python scripts/update_reddit_post.py --dry-run

# 2. Update your Reddit post
python scripts/update_reddit_post.py abc123

# 3. Verify on Reddit
# Check: https://reddit.com/r/homeassistant/comments/abc123/
```

## 🔗 Resources

- **PRAW Docs**: https://praw.readthedocs.io/
- **Reddit API**: https://www.reddit.com/dev/api/
- **Create App**: https://www.reddit.com/prefs/apps

---

**Ready to automate your Reddit updates!** 🚀

See `docs/REDDIT_UPDATES.md` for complete documentation.
