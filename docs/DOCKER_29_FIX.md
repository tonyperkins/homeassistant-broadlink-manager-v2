# Fix for Docker 29.x Permission Issues on Supervised

## Problem

Docker version 29.x has breaking changes that cause permission denied errors when starting Home Assistant Supervised add-ons.

**Symptoms**:
- Add-ons timeout during startup
- `[Errno 13] Permission denied` when binding to ports
- Multiple add-ons affected
- Issue persists even with AppArmor disabled

## Root Cause

Docker 29.0.x introduced changes to user namespace handling and security policies that are incompatible with Home Assistant Supervised's current architecture.

## Solution: Downgrade to Docker 27.x or 28.x

### Step 1: Check Current Version

```bash
docker --version
```

If you see `Docker version 29.0.x`, you need to downgrade.

### Step 2: Stop All Containers

```bash
# Stop Home Assistant
ha core stop

# Stop all add-ons
ha addons stop --all

# Stop Supervisor (optional, but recommended)
systemctl stop hassio-supervisor
```

### Step 3: Downgrade Docker

```bash
# Uninstall Docker 29.x
sudo apt-get remove docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Install Docker 27.x (stable, tested version)
sudo apt-get install -y \
  docker-ce=5:27.3.1-1~debian.12~bookworm \
  docker-ce-cli=5:27.3.1-1~debian.12~bookworm \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# Or install Docker 28.x (newer, but still compatible)
sudo apt-get install -y \
  docker-ce=5:28.5.2-1~debian.12~bookworm \
  docker-ce-cli=5:28.5.2-1~debian.12~bookworm \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin
```

### Step 4: Hold Docker Version

Prevent automatic upgrades to Docker 29.x:

```bash
sudo apt-mark hold docker-ce docker-ce-cli
```

### Step 5: Restart Services

```bash
# Restart Docker
sudo systemctl restart docker

# Start Supervisor
systemctl start hassio-supervisor

# Wait for Supervisor to be ready (30-60 seconds)
sleep 60

# Check Supervisor status
ha supervisor info
```

### Step 6: Test Add-on Installation

```bash
# Try installing a simple add-on
ha addons install core_configurator
ha addons start core_configurator

# Check if it starts successfully
ha addons logs core_configurator
```

If the add-on starts without permission errors, the fix worked!

### Step 7: Reinstall Your Add-ons

```bash
# Reinstall Broadlink Manager
ha addons install 1ed199ed_broadlink-manager-v2
ha addons start 1ed199ed_broadlink-manager-v2

# Check logs
ha addons logs 1ed199ed_broadlink-manager-v2
```

## Verification

After downgrading, verify everything works:

```bash
# Check Docker version
docker --version
# Should show: Docker version 27.3.1 or 28.5.2

# Check Supervisor
ha supervisor info

# Check add-ons
ha addons list

# Try starting an add-on
ha addons start 1ed199ed_broadlink-manager-v2
```

## Alternative: Use Docker 27.3.1 (Most Stable)

If Docker 28.x still has issues, use 27.3.1:

```bash
sudo apt-get install -y \
  docker-ce=5:27.3.1-1~debian.12~bookworm \
  docker-ce-cli=5:27.3.1-1~debian.12~bookworm \
  containerd.io

sudo apt-mark hold docker-ce docker-ce-cli
```

## Unhold Docker (When Fixed)

When Home Assistant Supervised officially supports Docker 29.x:

```bash
sudo apt-mark unhold docker-ce docker-ce-cli
sudo apt-get update
sudo apt-get upgrade
```

## Quick Fix Script

Save this as `fix-docker-29.sh`:

```bash
#!/bin/bash
set -e

echo "Fixing Docker 29.x issues for Home Assistant Supervised"
echo "========================================================="

# Stop services
echo "Stopping services..."
ha core stop
systemctl stop hassio-supervisor

# Downgrade Docker
echo "Downgrading Docker to 27.3.1..."
sudo apt-get remove -y docker-ce docker-ce-cli
sudo apt-get install -y \
  docker-ce=5:27.3.1-1~debian.12~bookworm \
  docker-ce-cli=5:27.3.1-1~debian.12~bookworm \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# Hold version
echo "Holding Docker version..."
sudo apt-mark hold docker-ce docker-ce-cli

# Restart
echo "Restarting services..."
sudo systemctl restart docker
systemctl start hassio-supervisor

echo "Waiting for Supervisor to be ready..."
sleep 60

echo "Done! Check status with: ha supervisor info"
docker --version
```

Run it:

```bash
chmod +x fix-docker-29.sh
sudo ./fix-docker-29.sh
```

## References

- [Home Assistant Supervised Installation](https://github.com/home-assistant/supervised-installer)
- [Docker Release Notes](https://docs.docker.com/engine/release-notes/)
- [Home Assistant Community Forum - Docker 29 Issues](https://community.home-assistant.io/)

## Summary

**Docker 29.x is incompatible with Home Assistant Supervised**. Downgrade to Docker 27.3.1 or 28.5.2 to fix permission denied errors when starting add-ons.

This is a known issue affecting all add-ons, not specific to Broadlink Manager.
