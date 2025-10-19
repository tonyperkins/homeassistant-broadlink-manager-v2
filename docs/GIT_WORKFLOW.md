# Git Workflow - Broadlink Manager v2

## Branch Strategy

```
main (production-ready)
  │
  ├── develop (integration)
  │     │
  │     ├── feature/smartir-browser
  │     ├── feature/command-learning
  │     └── feature/xyz
  │
  └── release/X.Y.Z (when ready to release)
```

## Branch Purposes

| Branch | Purpose | Lifespan |
|--------|---------|----------|
| `main` | Production-ready code | Permanent |
| `develop` | Integration of completed features | Permanent |
| `feature/*` | Individual features | Temporary |
| `release/X.Y.Z` | Release preparation | Temporary |
| `hotfix/*` | Critical production fixes | Temporary |

## Common Commands

### Starting a New Feature
```powershell
git checkout develop
git pull origin develop
git checkout -b feature/my-feature-name
# ... work on feature ...
git add .
git commit -m "Descriptive commit message"
git push origin feature/my-feature-name
```

### Completing a Feature
```powershell
# Ensure develop is up to date
git checkout develop
git pull origin develop

# Merge feature
git merge feature/my-feature-name

# Push to remote
git push origin develop

# Delete feature branch
git branch -d feature/my-feature-name
git push origin --delete feature/my-feature-name
```

### Creating a Release
```powershell
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/1.1.0

# Update version in files
# - config.yaml
# - CHANGELOG.md
# - README.md (if needed)

git add .
git commit -m "Bump version to 1.1.0"
git push origin release/1.1.0

# Test thoroughly, fix bugs on this branch
```

### Finalizing a Release
```powershell
# Merge to main
git checkout main
git pull origin main
git merge release/1.1.0
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags

# Merge back to develop (to get any release fixes)
git checkout develop
git pull origin develop
git merge release/1.1.0
git push origin develop

# Delete release branch
git branch -d release/1.1.0
git push origin --delete release/1.1.0
```

### Emergency Hotfix
```powershell
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-fix

# Fix the bug
git add .
git commit -m "Fix critical bug"

# Merge to main
git checkout main
git merge hotfix/critical-bug-fix
git tag -a v1.0.1 -m "Hotfix version 1.0.1"
git push origin main --tags

# Merge to develop
git checkout develop
git merge hotfix/critical-bug-fix
git push origin develop

# Delete hotfix branch
git branch -d hotfix/critical-bug-fix
git push origin --delete hotfix/critical-bug-fix
```

## Versioning

Use [Semantic Versioning](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Pre-release Tags
- `v1.1.0-beta.1` - Beta release
- `v1.1.0-rc.1` - Release candidate
- `v1.1.0` - Final release

## Rules

1. **Never commit directly to `main`** - always go through `develop` or `release/*`
2. **Never commit directly to `develop`** - always use `feature/*` branches
3. **One feature per branch** - keep features focused and small
4. **Delete branches after merging** - keep repository clean
5. **Always pull before creating new branches** - avoid conflicts
6. **Write descriptive commit messages** - explain what and why

## Comparing Branches

```powershell
# See differences between branches
git diff main..develop --stat

# See commits in branch A not in branch B
git log main..develop --oneline

# Visual branch history
git log --graph --oneline --all --decorate
```

## Useful Aliases (Optional)

Add to your `.gitconfig`:

```ini
[alias]
    # Quick status
    st = status -sb
    
    # Pretty log
    lg = log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --date=relative
    
    # List branches
    br = branch -v
    
    # Quick checkout
    co = checkout
    
    # Quick commit
    cm = commit -m
    
    # Undo last commit (keep changes)
    undo = reset HEAD~1 --soft
```

## Current Branch Cleanup

Old branches to delete (after migration):
- `develop-alpha-1`
- `develop-rc1`
- `develop-1`
- `develop-dual-mode`
- `develop-pre-cleanup`
- `release-beta-1.10.30`
- `release-rc1`
- `release-rc2`

## Questions?

- **Q: Can I have multiple feature branches at once?**
  - A: Yes! Just make sure each one is focused on a single feature.

- **Q: What if I need to switch features mid-work?**
  - A: Commit or stash your changes, then checkout the other feature branch.

- **Q: How do I handle conflicts?**
  - A: Pull latest `develop`, merge into your feature branch, resolve conflicts, then merge feature to `develop`.

- **Q: When should I create a release branch?**
  - A: When `develop` has enough features for a release and you want to freeze features for testing.
