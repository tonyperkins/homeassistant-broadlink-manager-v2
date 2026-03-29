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

## Step 3: Build Frontend

```bash
cd frontend
npm run build
cd ..
```

**Expected:** Build completes successfully, `app/static/` updated

## Step 4: Commit Outstanding Changes

```bash
git add -A
git commit -m "chore: prepare for release"
```

## Step 5: Determine Version Bump Type

Choose the appropriate version bump:
- `patch` - Bug fixes, minor changes (0.4.0-beta.9 → 0.4.0-beta.10)
- `minor` - New features, backward compatible (0.4.0-beta.9 → 0.5.0-beta.1)
- `major` - Breaking changes (0.4.0-beta.9 → 1.0.0-beta.1)

## Step 6: Run Release Script

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
4. Commits changes to `develop`
5. Pushes `develop` to GitHub
6. Merges `develop` into `main`
7. Pushes `main` to GitHub (required for HA add-on updates)
8. Creates and pushes Git tag (e.g., `v0.4.0-beta.10`)
9. Creates GitHub release with auto-generated notes

## Step 7: Verify GitHub Release

1. Go to https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases
2. Verify the new release is created
3. Check that release notes are correct
4. Verify tag is created

## Step 8: Trigger Docker Builds

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

## Step 9: Verify Docker Images

Wait for builds to complete (~20 minutes), then verify:

```bash
# Check standalone image
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone

# Verify version
docker run --rm ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone sh -c "grep -o '0\.4\.0-beta\.[0-9]*' /app/static/assets/index-*.js | uniq"
```

**Expected:** Should show the new version number

## Step 10: Verify Home Assistant Add-on Update

For HA add-on users:

1. Wait 5-10 minutes for HA to detect the update
2. Check in HA: Settings → Add-ons → Broadlink Manager
3. Should show "Update available" badge
4. Version should match the new release

**Note:** HA reads from `main` branch, which is why step 6 merges to main.

## Step 11: Post-Release Tasks

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
# Complete release in one go (after pre-checks)
python -m black app/
python -m flake8 app/ --count --show-source --statistics
python -m pytest tests/unit/ -v
cd frontend && npm run build && cd ..
git add -A
git commit -m "chore: prepare for release"
python scripts/quick_release.py patch -m "Description"

# Monitor Docker build
gh run list --workflow="docker-publish-standalone.yml" --limit 1

# Verify Docker image
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone
docker run --rm ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone cat /app/static/index.html | grep "index-"
```
