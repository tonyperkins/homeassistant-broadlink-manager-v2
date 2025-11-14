# Quick Release Guide for Alpha Releases

**For frequent alpha releases during active development**

## TL;DR - One Command Release

```bash
# Fix release (0.3.0-alpha.4 → 0.3.0-alpha.5)
python scripts/quick_release.py patch -m "Your fix description"
```

That's it! The script handles **everything** automatically, including creating the GitHub release.

---

## What the Script Does

The `quick_release.py` script automates the entire release process:

1. ✅ Bumps version in `config.yaml` and `frontend/package.json`
2. ✅ Updates `CHANGELOG.md` with new version section
3. ✅ Commits changes with proper message
4. ✅ Pushes to `develop` branch
5. ✅ Creates and pushes git tag
6. ✅ **Creates GitHub release automatically** (using GitHub CLI)

**Time saved**: ~10 minutes per release  
**Requirements**: GitHub CLI installed and authenticated (`gh auth login`)

---

## Usage Examples

### Patch Release (Most Common)
Increments alpha number: `0.3.0-alpha.4` → `0.3.0-alpha.5`

```bash
python scripts/quick_release.py patch -m "Fix area sync error"
```

### Minor Release
New feature set: `0.3.0-alpha.5` → `0.4.0-alpha.1`

```bash
python scripts/quick_release.py minor -m "Add new SmartIR features"
```

### Specific Version
```bash
python scripts/quick_release.py 0.3.0-alpha.6 -m "Custom version"
```

### Dry Run (Preview)
See what would happen without making changes:

```bash
python scripts/quick_release.py patch --dry-run
```

---

## Complete Workflow

### 1. Make Your Changes
```bash
# Work on your fix/feature
git add .
git commit -m "Fix: your fix description"
git push origin develop
```

### 2. Run Quick Release
```bash
python scripts/quick_release.py patch -m "Fix area sync 404 error"
```

**Output:**
```
📦 Current version: 0.3.0-alpha.4
🚀 New version: 0.3.0-alpha.5

📝 Updating version files...
✅ Updated config.yaml
✅ Updated frontend/package.json
✅ Updated CHANGELOG.md

📦 Committing changes...
✅ Committed changes

🚀 Pushing to develop...
✅ Pushed to develop

🏷️  Creating tag v0.3.0-alpha.5...
✅ Created and pushed tag v0.3.0-alpha.5

📢 Creating GitHub release...
   Visit: https://github.com/.../releases/new?tag=v0.3.0-alpha.5

✅ Release 0.3.0-alpha.5 complete!
```

### 3. ✅ GitHub Release Created Automatically!

The script automatically creates the GitHub release using GitHub CLI.

**Output:**
```
📢 Creating GitHub release...
✅ GitHub release created successfully!
   View at: https://github.com/.../releases/tag/v0.3.0-alpha.5
```

**If GitHub CLI is not available:**
- Install: `winget install GitHub.cli` (Windows) or visit https://cli.github.com/
- Authenticate: `gh auth login`
- Script will fall back to providing manual link if CLI fails

### 4. Test in Home Assistant
```bash
# In HA, update the add-on
# Verify version shows as 0.3.0-alpha.5
# Test the fix
```

---

## Command Reference

### Basic Commands
```bash
# Patch release (alpha.4 → alpha.5)
python scripts/quick_release.py patch

# With custom message
python scripts/quick_release.py patch -m "Your message"

# Minor release (0.3.x → 0.4.0-alpha.1)
python scripts/quick_release.py minor

# Specific version
python scripts/quick_release.py 0.3.0-alpha.6
```

### Options
```bash
-m, --message "msg"    # Custom message for CHANGELOG
--dry-run              # Preview without making changes
--no-github            # Skip GitHub release link
```

---

## When to Use This vs Full Release Process

### Use Quick Release For (Develop Branch):
- ✅ **Alpha releases** (0.x.x-alpha.x)
- ✅ **Bug fixes** during testing
- ✅ **Frequent releases** to testers
- ✅ **Rapid iteration** during development
- ✅ **User-driven QA** - Let testers find issues

**Strategy**: Release on `develop` branch, users act as QA, merge to `main` when stable

### Use Full Release Process For (Main Branch):
- ❌ **Beta releases** (0.x.x-beta.x)
- ❌ **Stable releases** (1.x.x)
- ❌ **Major versions** (1.0.0, 2.0.0)
- ❌ **Production releases**
- ❌ **Merging tested code from develop to main**

**Strategy**: Merge develop to main, tag on main, broader release

See `RELEASE_PROCESS.md` for full release process.

---

## Troubleshooting

### "Version already in CHANGELOG.md"
The version was already released. Use a different version or bump type.

### "Failed to push"
Make sure you've committed all changes to develop first:
```bash
git status
git add .
git commit -m "Your changes"
git push origin develop
```

### "Failed to create tag"
Tag already exists. Delete it first:
```bash
git tag -d v0.3.0-alpha.5
git push origin :refs/tags/v0.3.0-alpha.5
```

---

## Release Frequency Recommendations

### Alpha Phase (Current)
- **Release often**: Every 1-3 bug fixes or features
- **Don't wait**: Get fixes to testers quickly
- **Iterate fast**: Gather feedback and improve

### Typical Schedule
- Monday: Fix bugs from weekend testing
- Wednesday: Release new features
- Friday: Stabilization fixes

**Goal**: Keep testers on latest code with minimal friction

---

## Comparison: Old vs New Process

### Old Process (9 Steps, ~10 minutes)
1. Create release branch
2. Update config.yaml manually
3. Update package.json manually
4. Update CHANGELOG.md manually
5. Commit and push release branch
6. Merge to main
7. Create tag
8. Create GitHub release manually
9. Merge back to develop

### New Process (1 Command, ~30 seconds)
```bash
python scripts/quick_release.py patch -m "Fix description"
# Done! Everything automated including GitHub release
```

**Time saved**: ~10 minutes per release  
**Releases per week**: 3-5 instead of 1-2  
**Manual steps**: 0 (fully automated)

---

## Tips for Frequent Releases

1. **Commit often**: Each fix/feature gets its own commit
2. **Release daily**: Don't batch fixes unnecessarily
3. **Clear messages**: Use `-m` flag with descriptive text
4. **Test quickly**: Quick smoke test before releasing
5. **Communicate**: Let testers know about new releases

---

## GitHub Release Notes

The script provides a link to create the GitHub release. You can:

1. **Auto-generate notes** (recommended for alpha):
   - Click "Generate release notes" button
   - GitHub pulls from commit messages
   - Quick and accurate

2. **Manual notes** (for important releases):
   - Copy from CHANGELOG.md
   - Add screenshots or examples
   - More detailed explanations

---

## Integration with CI/CD

The quick release script can be integrated into GitHub Actions:

```yaml
# .github/workflows/quick-release.yml
name: Quick Release
on:
  workflow_dispatch:
    inputs:
      bump_type:
        description: 'Bump type (patch/minor)'
        required: true
        default: 'patch'
      message:
        description: 'Release message'
        required: true

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Quick Release
        run: python scripts/quick_release.py ${{ inputs.bump_type }} -m "${{ inputs.message }}"
```

---

## Summary

**Quick Release Script = Fast, Frequent Alpha Releases**

- One command to release
- Automated version bumping
- Automatic CHANGELOG updates
- Git operations handled
- GitHub release link provided

**Perfect for active alpha development with frequent tester feedback!**
