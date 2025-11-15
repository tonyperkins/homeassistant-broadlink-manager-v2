# Alpha 16 Fix for Supervised Permission Issues

## Problem
Users on Home Assistant Supervised were experiencing "Permission denied" errors when the add-on tried to bind to ports, causing startup timeouts.

## Root Causes Identified

### 1. Docker 29.x Incompatibility
- Docker version 29.0.x has breaking changes incompatible with HA Supervised
- Causes permission denied errors even with correct configuration
- **Solution**: Downgrade to Docker 27.3.1

### 2. Missing `host_network: true`
- Ingress add-ons in Supervised mode need host network access
- ESPHome uses `host_network: true` and works correctly
- Our add-on was missing this critical setting
- **Solution**: Added `host_network: true` to config.yaml

## Changes in Alpha 16

### config.yaml
```yaml
version: "0.3.0-alpha.16"
image: ghcr.io/home-assistant/{arch}-addon-base-python:latest  # Added proper base image
host_network: true                                              # Added for port binding
ports:
  8099/tcp: null                                               # Declared port
ingress: true
# Removed ingress_port (Supervisor handles routing)
```

### Code Changes
- Port 8099 (instead of 8888)
- Waitress WSGI server (production-ready)
- Fallback to Flask if Waitress unavailable
- Proper base image specification

## For Users Experiencing Issues

### Step 1: Check Docker Version
```bash
docker --version
```

If you see Docker 29.x, you need to downgrade:

### Step 2: Downgrade Docker (if needed)
```bash
# Stop services
ha core stop
systemctl stop hassio-supervisor

# Downgrade to Docker 27.3.1
sudo apt-get remove -y docker-ce docker-ce-cli
sudo apt-get install -y --allow-downgrades \
  docker-ce=5:27.3.1-1~debian.12~bookworm \
  docker-ce-cli=5:27.3.1-1~debian.12~bookworm \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

# Hold version
sudo apt-mark hold docker-ce docker-ce-cli

# Restart
sudo systemctl restart docker
systemctl start hassio-supervisor
sleep 60
```

### Step 3: Update to Alpha 16
```bash
# Reload add-on store
ha addons reload

# Update add-on
ha addons update 1ed199ed_broadlink-manager-v2

# Start add-on
ha addons start 1ed199ed_broadlink-manager-v2
```

### Step 4: Verify
```bash
# Check logs
docker logs addon_1ed199ed_broadlink-manager-v2 2>&1 | tail -20

# Should see:
# - "Starting web server on port 8099"
# - "Using Waitress WSGI server"
# - "Serving on http://0.0.0.0:8099"
# - NO "Permission denied" errors
```

## Verification

### Working Configuration
- ✅ Docker 27.3.1 or 28.5.x
- ✅ Alpha 16 installed
- ✅ Add-on starts successfully
- ✅ No permission denied errors
- ✅ Accessible via ingress

### Network Mode Check
```bash
docker inspect addon_1ed199ed_broadlink-manager-v2 | grep NetworkMode
```
Should show: `"NetworkMode": "host"`

## Comparison: Alpha 15 vs Alpha 16

| Feature | Alpha 15 | Alpha 16 |
|---------|----------|----------|
| Port | 8888 | 8099 |
| Network Mode | bridge | host |
| Base Image | Not specified | ghcr.io/home-assistant/amd64-base-python |
| Server | Flask dev | Waitress production |
| Ports Section | No | Yes (8099/tcp) |
| Docker 29.x | ❌ Fails | ❌ Still fails (need 27.x) |
| Docker 27.x | ❌ Fails | ✅ Works |

## Known Limitations

### Supervised-Specific
- Requires Docker 27.3.1 or 28.5.x (not 29.x)
- Requires `host_network: true` for port binding
- Repository cache may delay updates (use `ha addons reload`)

### HAOS (Not Affected)
- Works with any Docker version
- No special configuration needed
- Alpha 15 and 16 both work

## Troubleshooting

### Still Getting Permission Denied?
1. Verify Docker version: `docker --version`
2. Check network mode: `docker inspect addon_1ed199ed_broadlink-manager-v2 | grep NetworkMode`
3. Verify alpha 16 installed: `ha addons info 1ed199ed_broadlink-manager-v2 | grep version`
4. Check logs: `docker logs addon_1ed199ed_broadlink-manager-v2 2>&1 | tail -50`

### Add-on Won't Update?
1. Reload repository: `ha addons reload`
2. Wait 30 seconds for cache refresh
3. Check version available: `ha addons info 1ed199ed_broadlink-manager-v2`
4. If still alpha 15, remove and re-add repository

### Network Detection Issues?
```bash
# Reload network
ha network reload

# Check status
ha network info

# Should show:
# host_internet: true
# supervisor_internet: true
```

## Documentation

- Full Docker 29.x fix guide: `docs/DOCKER_29_FIX.md`
- General Supervised troubleshooting: `docs/SUPERVISED_TROUBLESHOOTING.md`
- Deployment guide: `DEPLOYMENT_GUIDE.md`

## Summary

**Alpha 16 fixes Supervised permission issues by:**
1. Adding `host_network: true` (like ESPHome)
2. Using proper base image
3. Declaring ports explicitly
4. Using production WSGI server

**Users must also:**
- Downgrade from Docker 29.x to 27.3.1
- Reload add-on store to get alpha 16
- Uninstall/reinstall to apply network mode change

**Result:** Add-on starts successfully on Supervised with Docker 27.3.1 + Alpha 16
