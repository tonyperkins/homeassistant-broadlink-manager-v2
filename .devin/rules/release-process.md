---
trigger: model_decision
description: When the user asks to "release", "publish", or "push a new version", follow this process.
---
# Release Process Workflow

When the user asks to "release", "publish", or "push a new version", follow this complete automated process.

## Automated Release Process

The `quick_release.py` script handles the entire release workflow:

### What the Script Does Automatically:

1. **Version Bumping** - Updates version in config.yaml and package.json
2. **Changelog Update** - Adds new version section to CHANGELOG.md
3. **Git Commit** - Commits all version changes
4. **Push to Develop** - Pushes changes to develop branch
5. **Push to Main** - Pushes develop to main (for HA add-on updates)
6. **Create Tag** - Creates and pushes version tag (e.g., v0.3.0-alpha.5)
7. **GitHub Release** - Creates GitHub release with auto-generated notes
8. **Trigger Docker Builds** - GitHub Actions automatically builds standalone Docker images

### Pre-Release Checklist:

```bash
# 1. Ensure all Python changes are formatted
python -m black app/

# 2. Run flake8 linting checks
python -m flake8 app/ --count --show-source --statistics
# Must show "0" errors before proceeding

# 3. Stage and commit any outstanding changes
git add -A
git commit -m 'Brief description of changes'

# 4. Run quick release script (does everything else automatically)
python scripts/quick_release.py patch -m 'Description of changes'