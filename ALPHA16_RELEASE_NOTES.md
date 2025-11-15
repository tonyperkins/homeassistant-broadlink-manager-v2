# Alpha 16 Release Notes - Supervised Fix

## 🎉 What's Fixed

Alpha 16 resolves the "Permission denied" errors that Supervised users were experiencing during add-on startup.

## 🔧 Changes

### Critical Configuration Updates
- **Added `host_network: true`** - Allows proper port binding on Supervised (learned from ESPHome)
- **Proper base image** - `ghcr.io/home-assistant/{arch}-addon-base-python:latest`
- **Port 8099** - Changed from 8888, with explicit declaration
- **Waitress server** - Production WSGI server instead of Flask dev server
- **Removed `ingress_port`** - Supervisor handles routing automatically

### Code Improvements
- Fallback to Flask if Waitress unavailable
- Better error handling
- Fixed test suite

## ⚠️ Requirements

### Docker Version (CRITICAL)
**You MUST use Docker 27.3.1 or 28.5.x**

Docker 29.x has breaking changes that cause permission issues. If you're on Docker 29.x, downgrade first:

```bash
# Check version
docker --version

# If 29.x, downgrade (see docs/DOCKER_29_FIX.md for full instructions)
sudo apt-get remove -y docker-ce docker-ce-cli
sudo apt-get install -y --allow-downgrades \
  docker-ce=5:27.3.1-1~debian.12~bookworm \
  docker-ce-cli=5:27.3.1-1~debian.12~bookworm \
  containerd.io
sudo apt-mark hold docker-ce docker-ce-cli
sudo systemctl restart docker
systemctl start hassio-supervisor
```

## 📦 Installation

### For New Users
1. Add repository: `https://github.com/tonyperkins/homeassistant-broadlink-manager-v2`
2. Install "Broadlink Manager v2 (Alpha)"
3. Start the add-on

### For Existing Users (Upgrading from Alpha 15)
```bash
# Reload add-on store
ha addons reload

# Update add-on
ha addons update 1ed199ed_broadlink-manager-v2

# Restart add-on
ha addons restart 1ed199ed_broadlink-manager-v2
```

**Note**: If update doesn't appear immediately, wait a few minutes for Supervisor's cache to refresh, then reload again.

## ✅ Verification

After installation, check that it's working:

```bash
# Check version
ha addons info 1ed199ed_broadlink-manager-v2 | grep version
# Should show: version: 0.3.0-alpha.16

# Check logs
docker logs addon_1ed199ed_broadlink-manager-v2 2>&1 | tail -20
```

### Expected Log Output (Success)
```
2025-11-15 17:30:00,000 - __main__ - INFO - Starting web server on port 8099
2025-11-15 17:30:00,000 - web_server - INFO - Using Waitress WSGI server
2025-11-15 17:30:00,000 - waitress - INFO - Serving on http://0.0.0.0:8099
```

### Network Mode Verification
```bash
docker inspect addon_1ed199ed_broadlink-manager-v2 | grep NetworkMode
```
Should show: `"NetworkMode": "host"`

## 🐛 Troubleshooting

### Still Getting Permission Denied?
1. **Check Docker version**: Must be 27.x or 28.x (NOT 29.x)
2. **Verify alpha 16**: `ha addons info 1ed199ed_broadlink-manager-v2`
3. **Check network mode**: Should be "host" not "bridge"
4. **Uninstall/reinstall**: Network mode only applies on fresh install

### Add-on Won't Update?
1. **Reload repository**: `ha addons reload`
2. **Wait 30-60 seconds** for cache refresh
3. **Check again**: `ha addons info 1ed199ed_broadlink-manager-v2`
4. **If still alpha 15**: Remove and re-add repository

### Network Detection Issues?
```bash
ha network reload
ha network info
# Should show: host_internet: true
```

## 📚 Documentation

- **Complete fix guide**: `docs/SUPERVISED_ALPHA16_FIX.md`
- **Docker downgrade**: `docs/DOCKER_29_FIX.md`
- **General troubleshooting**: `docs/SUPERVISED_TROUBLESHOOTING.md`

## 🔍 Technical Details

### Why `host_network: true`?
Supervised mode has stricter security policies than HAOS. Without host network mode, containers can't bind to ports even with proper permissions. ESPHome uses this same approach.

### Why Port 8099?
Port 8888 had additional restrictions on some systems. Port 8099 is higher and less restricted.

### Why Waitress?
Flask's development server isn't designed for production use. Waitress is a production-ready WSGI server that handles concurrent requests better.

## 🎯 Comparison

| Feature | Alpha 15 | Alpha 16 |
|---------|----------|----------|
| Network Mode | bridge | **host** ✅ |
| Port | 8888 | 8099 |
| Base Image | Not specified | Official HA Python |
| Server | Flask dev | Waitress prod |
| Docker 27.x | ❌ Fails | ✅ Works |
| Docker 29.x | ❌ Fails | ❌ Still fails |

## 🙏 Credits

Thanks to the user who reported this issue and helped test the fix! The solution was discovered by analyzing how ESPHome handles the same situation.

## 🚀 Next Steps

If you're still having issues after:
1. Downgrading to Docker 27.3.1
2. Installing Alpha 16
3. Verifying network mode is "host"

Please open a GitHub issue with:
- Docker version
- Supervisor version
- Full logs from `docker logs addon_1ed199ed_broadlink-manager-v2`
- Output of `docker inspect addon_1ed199ed_broadlink-manager-v2 | grep NetworkMode`

## 📝 Release Date

November 15, 2025

## 🔗 Links

- [GitHub Repository](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2)
- [GitHub Release](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/releases/tag/v0.3.0-alpha.16)
- [Docker Images](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/pkgs/container/homeassistant-broadlink-manager-v2)
