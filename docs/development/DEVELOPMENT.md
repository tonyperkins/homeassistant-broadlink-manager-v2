# Development Workflow Guide

This guide covers the recommended development workflow for Broadlink Manager, including testing strategies for both add-on and standalone Docker modes.

## Table of Contents

- [Branch Strategy](#branch-strategy)
- [Development Setup](#development-setup)
- [Testing Workflows](#testing-workflows)
- [Release Process](#release-process)
- [Troubleshooting](#troubleshooting)

---

## Branch Strategy

### Recommended Branches

```
main (or master)
├── Stable releases only
├── Tagged with version numbers
└── Used by production add-on installations

dev
├── Active development
├── Beta versions
├── Testing and validation
└── Merge to main when stable
```

### Version Numbering

- **Stable releases (main):** `1.10.25`, `1.11.0`, `2.0.0`
- **Beta releases (dev):** `1.10.25-beta`, `1.11.0-beta.1`, `2.0.0-rc1`
- **Dev builds (local):** `1.10.25-dev`, `1.11.0-dev.20251009`

---

## Development Setup

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/tonyperkins/homeassistant-broadlink-manager.git
cd homeassistant-broadlink-manager

# Create and checkout dev branch
git checkout -b dev

# Set up for local development
cp .env.example .env
# Edit .env with your local HA instance details
```

### Local Development Environment

**Option A: Standalone Docker (Recommended for rapid iteration)**

```bash
# Edit code in your IDE
# Test immediately with Docker

# Build and run
bash build-standalone.sh
docker-compose up -d

# View logs
docker-compose logs -f

# Make changes, then rebuild
docker-compose down
bash build-standalone.sh
docker-compose up -d
```

**Option B: Local Python Environment**

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export HA_URL=http://localhost:8123
export HA_TOKEN=your_token_here
export LOG_LEVEL=debug

# Run directly
cd app
python main.py
```

---

## Testing Workflows

### Workflow 1: Rapid Development (Standalone Docker)

**Best for:** Quick iterations, testing core functionality

```bash
# 1. Make code changes on dev branch
git checkout dev
# Edit files...

# 2. Test with standalone Docker
docker-compose down
bash build-standalone.sh
docker-compose up -d

# 3. Check logs and test functionality
docker-compose logs -f
# Open http://localhost:8099

# 4. Iterate until satisfied
# Repeat steps 1-3 as needed

# 5. Commit when ready
git add .
git commit -m "feat: add new feature"
git push origin dev
```

**Pros:**
- ✅ Fastest iteration cycle
- ✅ No need to touch HA installation
- ✅ Easy to debug
- ✅ Can test both modes (supervisor and standalone)

**Cons:**
- ❌ Doesn't test add-on installation process
- ❌ Doesn't test Supervisor integration

---

### Workflow 2: Add-on Testing (Local Add-on)

**Best for:** Testing add-on installation, Supervisor integration, final validation

#### Setup (One-time)

```bash
# SSH into your Home Assistant instance
ssh root@homeassistant.local

# Create local add-on directory
mkdir -p /addons/local
cd /addons/local

# Clone your repository
git clone https://github.com/tonyperkins/homeassistant-broadlink-manager.git broadlink-manager
cd broadlink-manager

# Checkout dev branch
git checkout dev
```

**Note:** Local add-ons must be in `/addons/local/` to be automatically detected by Home Assistant.

#### In Home Assistant UI

1. Go to **Settings → Add-ons → Add-on Store**
2. Click **⋮** (top right) → **Reload**
3. Find **"Broadlink Manager"** under **"Local add-ons"**
4. Click it and install

#### Testing Cycle

```bash
# 1. Make changes on your dev machine
# Push to dev branch
git add .
git commit -m "fix: bug fix"
git push origin dev

# 2. SSH to Home Assistant and pull changes
ssh root@homeassistant.local
cd /addons/local/broadlink-manager
git pull origin dev

# 3. Restart the add-on in HA UI
# Settings → Add-ons → Broadlink Manager → Restart

# 4. Check logs in HA UI
# Settings → Add-ons → Broadlink Manager → Log tab

# 5. Test functionality
```

**Pros:**
- ✅ Tests actual add-on installation
- ✅ Tests Supervisor integration
- ✅ Tests in real HA environment
- ✅ Can test Ingress functionality

**Cons:**
- ❌ Slower iteration cycle
- ❌ Requires SSH access to HA
- ❌ Need to restart add-on each time

---

### Workflow 3: Hybrid Approach (Recommended)

**Combine both workflows for best results:**

```
Phase 1: Rapid Development
├── Develop on dev branch
├── Test with standalone Docker
├── Iterate quickly
└── Fix bugs and add features

Phase 2: Add-on Validation
├── Push to dev branch
├── Test as local add-on
├── Verify Supervisor integration
└── Final validation

Phase 3: Release
├── Merge dev to main
├── Tag release
├── Users get update
└── Monitor for issues
```

**Example workflow:**

```bash
# Day 1-3: Feature development
git checkout dev
# Edit code...
docker-compose up -d  # Test locally
# Iterate...

# Day 4: Add-on testing
git push origin dev
ssh root@homeassistant.local
cd /addons/local/broadlink-manager
git pull
# Restart add-on in UI, test thoroughly

# Day 5: Release
git checkout main
git merge dev
git tag v1.11.0
git push origin main --tags
```

---

## Release Process

### Pre-Release Checklist

- [ ] All tests pass in standalone Docker mode
- [ ] All tests pass in add-on mode
- [ ] Documentation updated (README.md, CHANGELOG.md)
- [ ] Version bumped in `config.yaml`
- [ ] Version bumped in `Dockerfile` labels (if applicable)
- [ ] No debug code or console.logs left in
- [ ] Breaking changes documented

### Release Steps

#### 1. Prepare Release on Dev Branch

```bash
git checkout dev

# Update version in config.yaml
# version: "1.11.0"

# Update CHANGELOG.md
# Add release notes

# Update Dockerfile label if needed
# io.hass.version="1.11.0"

# Commit
git add config.yaml CHANGELOG.md Dockerfile
git commit -m "chore: prepare release v1.11.0"
git push origin dev
```

#### 2. Final Testing

```bash
# Test standalone Docker
bash build-standalone.sh
docker-compose up -d
# Test all functionality

# Test as local add-on
ssh root@homeassistant.local
cd /addons/local/broadlink-manager
git pull
# Restart and test in HA
```

#### 3. Merge to Main

```bash
git checkout main
git merge dev

# Tag the release
git tag -a v1.11.0 -m "Release v1.11.0

- Add standalone Docker support
- Add dual-mode configuration
- Improve error handling
- Update documentation"

# Push to GitHub
git push origin main
git push origin v1.11.0
```

#### 4. Create GitHub Release

1. Go to GitHub repository
2. Click **Releases** → **Create a new release**
3. Select tag `v1.11.0`
4. Title: `v1.11.0 - Standalone Docker Support`
5. Description: Copy from CHANGELOG.md
6. Attach any binaries if needed
7. Click **Publish release**

#### 5. Verify Add-on Update

Users with your repository added will see the update:
1. Settings → Add-ons → Add-on Store
2. Click **⋮** → **Check for updates**
3. Update should appear

---

## Testing Checklist

### Core Functionality Tests

**Both Modes (Standalone & Add-on):**
- [ ] Application starts successfully
- [ ] Web interface loads at port 8099
- [ ] Correct mode detected (supervisor/standalone)
- [ ] Home Assistant connection established
- [ ] Broadlink devices discovered
- [ ] Device list displays correctly
- [ ] Command learning works
- [ ] Command testing works
- [ ] Command storage works
- [ ] Entity generation works
- [ ] Entity files created correctly
- [ ] Area assignment works
- [ ] Configuration reload works

**Add-on Specific:**
- [ ] Ingress works (sidebar access)
- [ ] Configuration UI works
- [ ] Start on boot works
- [ ] Watchdog works
- [ ] Logs appear in HA UI

**Standalone Docker Specific:**
- [ ] Environment variables respected
- [ ] Volume mounts work correctly
- [ ] Health check passes
- [ ] Container restarts properly
- [ ] Network modes work (host/bridge)

### Configuration Tests

- [ ] Valid configuration accepted
- [ ] Invalid HA_TOKEN rejected with clear error
- [ ] Invalid HA_URL rejected with clear error
- [ ] Missing config path detected
- [ ] Default values applied correctly
- [ ] Log level changes work

### Error Handling Tests

- [ ] Graceful failure on HA connection loss
- [ ] Clear error messages for common issues
- [ ] Proper validation on startup
- [ ] No crashes on invalid input

---

## Development Tips

### Quick Commands

```bash
# View logs (Docker)
docker-compose logs -f broadlink-manager

# View logs (Add-on)
# Use HA UI: Settings → Add-ons → Broadlink Manager → Log

# Rebuild and restart (Docker)
docker-compose down && bash build-standalone.sh && docker-compose up -d

# Check container status
docker-compose ps

# Execute commands in container
docker-compose exec broadlink-manager bash

# View environment variables
docker-compose exec broadlink-manager env

# Test HA connection from container
docker-compose exec broadlink-manager curl -I $HA_URL
```

### Debugging

**Enable debug logging:**

```bash
# Standalone Docker - edit .env
LOG_LEVEL=debug

# Add-on - edit configuration in HA UI
log_level: debug
```

**Common issues:**

1. **"Configuration validation failed"**
   - Check HA_TOKEN is set correctly
   - Verify HA_URL is accessible
   - Ensure config path exists

2. **"Running in wrong mode"**
   - Check SUPERVISOR_TOKEN presence
   - Verify using correct startup script

3. **"Can't connect to Home Assistant"**
   - Test: `curl -I $HA_URL`
   - Check network connectivity
   - Verify token is valid

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Keep functions small and focused
- Add comments for complex logic
- Update type hints

### Git Commit Messages

Follow conventional commits:

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: add tests
chore: maintenance tasks
```

Examples:
```bash
git commit -m "feat: add support for standalone Docker mode"
git commit -m "fix: resolve authentication issue in standalone mode"
git commit -m "docs: update README with Docker instructions"
```

---

## Troubleshooting Development Issues

### Local Add-on Not Appearing

```bash
# SSH to HA
ssh root@homeassistant.local

# Check directory exists
ls -la /addons/local/broadlink-manager

# Check config.yaml is valid
cat /addons/local/broadlink-manager/config.yaml

# Reload add-on store in HA UI
# Settings → Add-ons → ⋮ → Check for updates
```

### Docker Build Fails

```bash
# Check Dockerfile syntax
docker build -f Dockerfile.standalone -t test .

# Check requirements.txt
cat requirements.txt

# Try building without cache
docker build --no-cache -f Dockerfile.standalone -t test .
```

### Changes Not Reflected

**Docker:**
```bash
# Ensure you're rebuilding
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Add-on:**
```bash
# Ensure you pulled latest
cd /addons/local/broadlink-manager
git status
git pull origin dev

# Restart add-on (not just reload)
# Use HA UI: Stop → Start
```

**Windows Deployment Script:**
```powershell
# From your development machine
.\deploy-to-haos.ps1
# Then restart the add-on in HA UI
```

### Can't Connect to Home Assistant

**Check from container:**
```bash
docker-compose exec broadlink-manager curl -v $HA_URL/api/
```

**Check token:**
```bash
docker-compose exec broadlink-manager curl -H "Authorization: Bearer $HA_TOKEN" $HA_URL/api/
```

---

## CI/CD (Future Enhancement)

Consider setting up GitHub Actions for:

- **Automated testing** on push to dev
- **Docker image builds** on tag
- **Linting and formatting** checks
- **Documentation generation**
- **Release automation**

Example `.github/workflows/build.yml`:

```yaml
name: Build and Test

on:
  push:
    branches: [dev, main]
  pull_request:
    branches: [dev, main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build standalone image
        run: docker build -f Dockerfile.standalone .
      - name: Run tests
        run: docker-compose up -d && sleep 10 && docker-compose logs
```

---

## Resources

- [Home Assistant Add-on Development](https://developers.home-assistant.io/docs/add-ons)
- [Docker Documentation](https://docs.docker.com/)
- [Python Best Practices](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

## Support

For development questions:
1. Check this guide
2. Review [DUAL_MODE_IMPLEMENTATION.md](DUAL_MODE_IMPLEMENTATION.md)
3. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
4. Open a discussion on GitHub

---

**Happy coding! 🚀**
