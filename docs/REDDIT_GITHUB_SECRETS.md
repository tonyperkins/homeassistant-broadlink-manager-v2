# GitHub Secrets Setup for Reddit Updates

To enable automated Reddit post updates via GitHub Actions, you need to configure repository secrets.

## Required Secrets

Go to your repository on GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

Add the following secrets:

### 1. REDDIT_CLIENT_ID
- **Value**: Your Reddit app client ID
- **Get it from**: https://www.reddit.com/prefs/apps (shown under app name)

### 2. REDDIT_CLIENT_SECRET
- **Value**: Your Reddit app client secret
- **Get it from**: https://www.reddit.com/prefs/apps (shown as "secret")

### 3. REDDIT_USERNAME
- **Value**: Your Reddit username (without /u/)
- **Example**: `YourUsername` (not `/u/YourUsername`)

### 4. REDDIT_PASSWORD
- **Value**: Your Reddit account password
- **Security**: This is stored encrypted by GitHub

### 5. REDDIT_USER_AGENT
- **Value**: A descriptive user agent string
- **Format**: `AppName:Version:Script (by /u/YourUsername)`
- **Example**: `BroadlinkManager:v2.0:script (by /u/YourUsername)`

### 6. REDDIT_POST_ID
- **Value**: The ID of your Reddit post to update
- **Get it from**: Post URL `https://reddit.com/r/homeassistant/comments/abc123/title/`
- **Example**: `abc123` (just the ID, not the full URL)

## Verification

After adding all secrets:

1. Go to **Actions** tab in your repository
2. Find the "Update Reddit Post" workflow
3. Click "Run workflow" to test manually
4. Check the workflow run for success/errors

## Security Notes

- ✅ GitHub encrypts all secrets
- ✅ Secrets are never exposed in logs
- ✅ Only repository admins can view/edit secrets
- ⚠️ Use a dedicated Reddit account if concerned about security
- ⚠️ Consider using 2FA with app-specific password

## Workflow Triggers

The workflow runs automatically when:
- ✅ A new release is published
- ✅ Manually triggered via Actions tab

## Troubleshooting

### Workflow fails with authentication error
- Verify all credentials are correct
- Check Reddit account has verified email
- Ensure 2FA is disabled or using app password

### Workflow fails with permission error
- Verify you own the Reddit post
- Check the post ID is correct
- Confirm the post is a self-post (text), not link post

### Secrets not found
- Ensure secret names match exactly (case-sensitive)
- Verify secrets are added to the correct repository
- Check you have admin access to the repository
