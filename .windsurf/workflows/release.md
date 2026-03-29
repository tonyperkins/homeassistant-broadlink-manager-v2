---
description: Complete release process for new versions
---

# Release Workflow

This workflow covers the complete release process including version bumping, changelog updates, Git operations, GitHub releases, and Docker image builds.

## Pre-Release Checklist

Before starting the release process, ensure:

- [ ] All features/fixes are merged to `develop` branch
- [ ] All tests are passing
- [ ] Code is formatted and linted
- [ ] Frontend is built with latest changes
- [ ] Documentation is updated

## Step 1: Format and Lint Code

// turbo
```bash
python -m black app/
```

// turbo
```bash
python -m flake8 app/ --count --show-source --statistics
```

**Expected:** `0` errors from flake8

## Step 2: Run Tests

// turbo
```bash
python -m pytest tests/unit/ -v
```

**Expected:** All tests pass

## Step 3: Commit Outstanding Changes

```bash
git add -A
git commit -m "chore: prepare for release"
```

## Step 4: Determine Version Bump Type

Choose the appropriate version bump:
- `patch` - Bug fixes, minor changes (0.4.0-beta.9 → 0.4.0-beta.10)
- `minor` - New features, backward compatible (0.4.0-beta.9 → 0.5.0-beta.1)
- `major` - Breaking changes (0.4.0-beta.9 → 1.0.0-beta.1)

## Step 5: Run Release Script

```bash
python scripts/quick_release.py <patch|minor|major> -m "Release description"
```

**Example:**
```bash
python scripts/quick_release.py patch -m "Add stateless device mode for one-way control devices"
```

**What this does automatically:**
1. Updates version in `config.yaml`
2. Updates version in `frontend/package.json`
3. Updates `CHANGELOG.md` with new version section

## Step 6: Rebuild Frontend with New Version

**CRITICAL:** The frontend must be rebuilt AFTER the version bump to ensure the version string is correctly embedded in the compiled JavaScript.

```bash
cd frontend
npm run build
cd ..
```

**Expected:** Build completes successfully with new version number

**Verify the version is correct:**
```bash
# Check that the new version is in the built assets
grep -o "0\.4\.0-beta\.[0-9]*" app/static/assets/index-*.js | uniq
```

## Step 7: Commit Frontend Build

```bash
git add app/static/
git commit -m "chore: rebuild frontend with v<VERSION> version string"
```

**Why this step is critical:**
- The release script updates `frontend/package.json` version
- But the compiled JavaScript still has the OLD version embedded
- We must rebuild AFTER version bump to get the correct version in the UI
- This prevents version mismatch between add-on info page and web UI footer

## Step 8: Push Changes to GitHub

```bash
git push origin develop
```

The release script already pushed develop and created the tag, but we need to push our frontend rebuild:

```bash
# Merge to main
git checkout main
git pull origin main
git merge develop
git push origin main

# Update the tag to point to the new commit with correct frontend
git tag -d v<VERSION>
git tag v<VERSION>
git push origin v<VERSION> --force
```

**What was already done by the release script:**
- ✅ Committed changes to `develop`
- ✅ Pushed `develop` to GitHub
- ✅ Merged `develop` into `main`
- ✅ Created Git tag
- ✅ Created GitHub release

**What we're doing now:**
- Pushing the frontend rebuild commit
- Updating the tag to include the correct frontend version

## Step 9: Verify GitHub Release

1. Go to https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases
2. Verify the new release is created
3. Check that release notes are correct
4. Verify tag is created and points to latest commit

## Step 10: Trigger Docker Builds

The GitHub release automatically triggers Docker builds via GitHub Actions:

**Workflows triggered:**
- `.github/workflows/docker-publish-standalone.yml` - Standalone Docker images
- Builds for: `linux/amd64`, `linux/arm64`, `linux/arm/v7`
- Creates tags: `standalone`, `standalone-<version>`, `standalone-latest` (if stable)

**Monitor builds:**
```bash
gh run list --workflow="docker-publish-standalone.yml" --limit 1
```

**Or visit:**
https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/actions

## Step 11: Verify Docker Images

Wait for builds to complete (~20 minutes), then verify:

```bash
# Check standalone image
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone

# Verify version
docker run --rm ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone sh -c "grep -o '0\.4\.0-beta\.[0-9]*' /app/static/assets/index-*.js | uniq"
```

**Expected:** Should show the new version number

## Step 12: Verify Home Assistant Add-on Update

For HA add-on users:

1. Wait 5-10 minutes for HA to detect the update
2. Check in HA: Settings → Add-ons → Broadlink Manager
3. Should show "Update available" badge
4. Version should match the new release

**Note:** HA reads from `main` branch, which is why step 6 merges to main.

## Step 13: Post-Release Tasks

- [ ] Test the new version in a development environment
- [ ] Update any related documentation
- [ ] Announce release (if significant)
- [ ] Monitor for issues from users

## Rollback Procedure

If issues are found after release:

```bash
# Delete the tag locally and remotely
git tag -d v0.4.0-beta.10
git push origin :refs/tags/v0.4.0-beta.10

# Delete the GitHub release
gh release delete v0.4.0-beta.10

# Revert main to previous version
git checkout main
git reset --hard <previous-commit-hash>
git push origin main --force

# Fix issues on develop and re-release
```

## Troubleshooting

### Docker build fails
- Check GitHub Actions logs
- Verify Dockerfile.standalone is valid
- Check if all required files exist in the repository

### Version mismatch in Docker image
- Frontend may not have been rebuilt before release
- Re-run frontend build and create a new patch release

### HA add-on not showing update
- Verify changes are on `main` branch (not just `develop`)
- Wait 10-15 minutes for HA to check for updates
- Try reloading the add-on store page

### Release script fails
- Check if you have uncommitted changes
- Verify you're on `develop` branch
- Ensure you have push access to the repository
- Check if the tag already exists

## Quick Reference

```bash
# Complete release process
python -m black app/
python -m flake8 app/ --count --show-source --statistics
python -m pytest tests/unit/ -v
git add -A
git commit -m "chore: prepare for release"

# Run release script (bumps version)
python scripts/quick_release.py patch -m "Description"

# CRITICAL: Rebuild frontend with new version
cd frontend && npm run build && cd ..
git add app/static/
git commit -m "chore: rebuild frontend with v<VERSION> version string"
git push origin develop

# Update main and tag
git checkout main
git pull origin main
git merge develop
git push origin main
git tag -d v<VERSION>
git tag v<VERSION>
git push origin v<VERSION> --force

# Monitor Docker build
gh run list --workflow="docker-publish-standalone.yml" --limit 1

# Verify Docker image has correct version
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone
docker run --rm ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone sh -c "grep -o '0\.4\.0-beta\.[0-9]*' /app/static/assets/index-*.js | uniq"
```
