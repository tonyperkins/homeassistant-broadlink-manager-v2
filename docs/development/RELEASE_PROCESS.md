# Release Process

This document outlines the complete process for creating a new release of Broadlink Manager v2.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):
- **0.x.x** = Alpha (current phase)
- **1.x.x** = Stable release
- **x.MINOR.x** = New features, backward compatible
- **x.x.PATCH** = Bug fixes, backward compatible

### Alpha Versioning
- `0.3.0-alpha.1` = First alpha of 0.3.0
- `0.3.0-alpha.2` = Second alpha of 0.3.0
- `0.3.0` = Stable 0.3.0 release

## Files to Update

When creating a new release, update version numbers in these files:

1. **`config.yaml`** (line 2)
   - `version: "0.3.0-alpha.2"`
   - Also update `name` if changing status (Alpha/Beta/Stable)

2. **`frontend/package.json`** (line 3)
   - `"version": "0.3.0-alpha.2"`

3. **`CHANGELOG.md`**
   - Add new version section with date
   - Move items from `[Unreleased]` to new version
   - Document all changes (Added, Changed, Fixed, Removed)

## Release Process

### Step 1: Prepare Release Branch

```bash
# Make sure develop is up to date
git checkout develop
git pull origin develop

# Create release branch
git checkout -b release/0.3.0-alpha.2
```

### Step 2: Update Version Numbers

1. Update `config.yaml`:
   ```yaml
   version: "0.3.0-alpha.2"
   ```

2. Update `frontend/package.json`:
   ```json
   "version": "0.3.0-alpha.2"
   ```

3. Update `CHANGELOG.md`:
   ```markdown
   ## [Unreleased]

   ## [0.3.0-alpha.2] - 2025-10-20

   ### Added
   - Feature 1
   - Feature 2

   ### Changed
   - Change 1

   ### Fixed
   - Bug fix 1
   ```

### Step 3: Commit Version Updates

```bash
git add config.yaml frontend/package.json CHANGELOG.md
git commit -m "chore: bump version to 0.3.0-alpha.2"
git push origin release/0.3.0-alpha.2
```

### Step 4: Merge to Main

```bash
# Switch to main and pull latest
git checkout main
git pull origin main

# Merge release branch (no fast-forward to preserve history)
git merge --no-ff release/0.3.0-alpha.2 -m "Release 0.3.0-alpha.2"

# Push to main
git push origin main
```

### Step 5: Create Git Tag

```bash
# Create annotated tag
git tag -a v0.3.0-alpha.2 -m "Release v0.3.0-alpha.2"

# Push tag
git push origin v0.3.0-alpha.2
```

### Step 6: Create GitHub Release

1. Go to: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/new
2. Select tag: `v0.3.0-alpha.2`
3. Release title: `v0.3.0-alpha.2`
4. Description: Copy from CHANGELOG.md
5. Check "Set as a pre-release" (for alpha/beta)
6. Click "Publish release"

### Step 7: Merge Back to Develop

```bash
# Switch to develop
git checkout develop

# Merge main back to develop
git merge --no-ff main -m "Merge release 0.3.0-alpha.2 back to develop"

# Push to develop
git push origin develop
```

### Step 8: Clean Up

```bash
# Delete release branch (optional)
git branch -d release/0.3.0-alpha.2
git push origin --delete release/0.3.0-alpha.2
```

## Quick Release Checklist

- [ ] Create release branch from develop
- [ ] Update `config.yaml` version
- [ ] Update `frontend/package.json` version
- [ ] Update `CHANGELOG.md` with release date and changes
- [ ] Commit version updates
- [ ] Merge release branch to main
- [ ] Create and push git tag
- [ ] Create GitHub release (mark as pre-release for alpha/beta)
- [ ] Merge main back to develop
- [ ] Delete release branch

## Post-Release

After creating a GitHub release:

1. **Reddit Post** (if configured):
   - GitHub Action automatically updates Reddit post
   - Or run manually: `python scripts/update_reddit_post.py <post_id>`

2. **Home Assistant Forum**:
   - Update forum post with release notes
   - Or run: `python scripts/update_ha_forum_post.py`

3. **Test Installation**:
   - Install/update add-on in Home Assistant
   - Verify version number shows correctly
   - Test key features

## Hotfix Process

For urgent fixes to main:

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/0.3.0-alpha.3

# Make fixes, update version, update CHANGELOG
# ... make changes ...

# Commit
git commit -am "fix: critical bug description"
git commit -am "chore: bump version to 0.3.0-alpha.3"

# Merge to main
git checkout main
git merge --no-ff hotfix/0.3.0-alpha.3

# Tag and push
git tag -a v0.3.0-alpha.3 -m "Hotfix v0.3.0-alpha.3"
git push origin main --tags

# Merge to develop
git checkout develop
git merge --no-ff main

# Push and clean up
git push origin develop
git branch -d hotfix/0.3.0-alpha.3
```

## Version History

- `0.3.0-alpha.1` - 2025-10-19 - SmartIR Profile Browser, Code Tester, Enhanced Diagnostics
- `0.2.0-alpha.1` - Previous release
- `0.1.0-alpha.1` - Initial alpha release

## Notes

- **Always** create releases from `main` branch
- **Always** tag releases on `main` branch
- **Never** tag or release from `develop` or feature branches
- Use `--no-ff` for merges to preserve branch history
- Mark alpha/beta releases as "pre-release" on GitHub
- Keep CHANGELOG.md up to date with every change
