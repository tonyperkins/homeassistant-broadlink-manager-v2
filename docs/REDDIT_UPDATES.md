# Reddit Post Updates

This guide explains how to automatically update Reddit posts with the latest Broadlink Manager information.

## Overview

The `scripts/update_reddit_post.py` script allows you to programmatically update a Reddit self-post with:
- Latest features and capabilities
- Current changelog/release notes
- Installation instructions
- Links to documentation and resources
- Automatically updated timestamp

## Setup

### 1. Create a Reddit App

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the details:
   - **Name**: Broadlink Manager Updater
   - **App type**: Select "script"
   - **Description**: Script to update Broadlink Manager Reddit posts
   - **About URL**: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2
   - **Redirect URI**: http://localhost:8080 (required but not used)
4. Click "Create app"
5. Note your **client_id** (under the app name) and **client_secret**

### 2. Set Environment Variables

Create a `.env` file or set environment variables:

```bash
# Windows PowerShell
$env:REDDIT_CLIENT_ID="your_client_id_here"
$env:REDDIT_CLIENT_SECRET="your_client_secret_here"
$env:REDDIT_USERNAME="your_reddit_username"
$env:REDDIT_PASSWORD="your_reddit_password"
$env:REDDIT_USER_AGENT="BroadlinkManager:v2.0:script (by /u/YourUsername)"

# Linux/Mac
export REDDIT_CLIENT_ID="your_client_id_here"
export REDDIT_CLIENT_SECRET="your_client_secret_here"
export REDDIT_USERNAME="your_reddit_username"
export REDDIT_PASSWORD="your_reddit_password"
export REDDIT_USER_AGENT="BroadlinkManager:v2.0:script (by /u/YourUsername)"
```

**Security Note**: Never commit credentials to git. Add `.env` to `.gitignore`.

### 3. Install Dependencies

```bash
pip install praw
```

## Usage

### Preview Post Content (Dry Run)

Preview what will be posted without actually updating Reddit:

```bash
python scripts/update_reddit_post.py --dry-run
```

### Create Initial Reddit Post

1. Go to the appropriate subreddit (e.g., r/homeassistant)
2. Create a new self-post with your initial content
3. Note the post ID from the URL:
   - URL: `https://reddit.com/r/homeassistant/comments/abc123/title/`
   - Post ID: `abc123`

### Update Existing Post

```bash
python scripts/update_reddit_post.py abc123
```

Replace `abc123` with your actual post ID.

### Automated Updates

You can automate updates using:

**GitHub Actions** (on release):
```yaml
name: Update Reddit Post
on:
  release:
    types: [published]
jobs:
  update-reddit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install praw
      - name: Update Reddit post
        env:
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          REDDIT_USERNAME: ${{ secrets.REDDIT_USERNAME }}
          REDDIT_PASSWORD: ${{ secrets.REDDIT_PASSWORD }}
        run: python scripts/update_reddit_post.py ${{ secrets.REDDIT_POST_ID }}
```

**Cron Job** (scheduled):
```bash
# Update every Monday at 9 AM
0 9 * * 1 cd /path/to/project && python scripts/update_reddit_post.py abc123
```

## Customization

### Modify Post Template

Edit `scripts/update_reddit_post.py` in the `generate_reddit_post()` function to customize:
- Sections included
- Formatting and layout
- Links and resources
- Feature highlights

### Add Screenshots

To include Reddit-hosted images:
1. Upload images to Reddit via a post or your profile
2. Get the image URLs
3. Add them to the post template using Reddit's markdown:
   ```markdown
   ![Alt text](https://i.redd.it/your_image_id.png)
   ```

### Multiple Posts

To manage multiple Reddit posts (e.g., different subreddits):
1. Store post IDs in a config file
2. Loop through and update each one
3. Customize content per subreddit if needed

## Limitations

- **Can only edit self-posts** (text posts), not link posts
- **Cannot change post title** after creation
- **Rate limits**: 60 requests per minute (PRAW handles this automatically)
- **Must be the post author** to edit

## Troubleshooting

### Authentication Errors
- Verify credentials are correct
- Check that your Reddit account has verified email
- Ensure 2FA is disabled or use app-specific password

### Permission Errors
- Confirm you're the author of the post
- Check that the post ID is correct
- Verify the post is a self-post (not a link post)

### Rate Limiting
- PRAW automatically handles rate limits
- If updating multiple posts, add delays between updates
- Reddit allows 60 requests per minute

## Best Practices

1. **Test with dry-run first**: Always preview changes before posting
2. **Keep credentials secure**: Use environment variables, never commit to git
3. **Update regularly**: Keep information current (weekly/monthly or on releases)
4. **Add timestamp**: Include "Last Updated" date in post
5. **Link to source**: Always link to GitHub for most current info
6. **Follow subreddit rules**: Check posting guidelines for each subreddit

## Resources

- **PRAW Documentation**: https://praw.readthedocs.io/
- **Reddit API**: https://www.reddit.com/dev/api/
- **Reddit Apps**: https://www.reddit.com/prefs/apps
- **API Terms**: https://www.redditinc.com/policies/data-api-terms

## Example Workflow

1. **Initial Setup** (one-time):
   ```bash
   # Create Reddit app, get credentials
   # Set environment variables
   pip install praw
   ```

2. **Create Post** (manual):
   - Post to r/homeassistant
   - Save post ID: `abc123`

3. **Test Update**:
   ```bash
   python scripts/update_reddit_post.py --dry-run
   python scripts/update_reddit_post.py abc123
   ```

4. **Automate** (optional):
   - Add GitHub Action for releases
   - Or set up cron job for regular updates

5. **Maintain**:
   - Update script template as project evolves
   - Keep CHANGELOG.md current
   - Run updates after major releases
