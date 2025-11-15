# Troubleshooting Home Assistant Supervised on Debian 12

This guide addresses issues specific to Home Assistant Supervised installations, particularly permission denied errors when starting add-ons.

## Symptoms

- Add-ons timeout during startup (120 second timeout)
- Docker logs show: `[Errno 13] Permission denied` when binding to ports
- Multiple add-ons affected (not just Broadlink Manager)
- Issue persists even with AppArmor disabled

## Root Cause Analysis

The permission denied error when binding to ports in Supervised mode is typically caused by:

1. **Docker user namespace remapping issues**
2. **SELinux or security module conflicts**
3. **Incomplete Supervised installation**
4. **Docker socket permission problems**

## Diagnostic Steps

### 1. Check Docker Configuration

```bash
# Check Docker version
docker --version

# Check Docker info
docker info | grep -i "security\|user"

# Check if user namespaces are enabled
cat /proc/sys/kernel/unprivileged_userns_clone

# Check Docker daemon config
cat /etc/docker/daemon.json
```

### 2. Check Supervisor Status

```bash
# Check Supervisor status
ha supervisor info

# Check Supervisor logs
ha supervisor logs

# Check system info
ha info --raw-json
```

### 3. Check File Permissions

```bash
# Check Docker socket permissions
ls -la /var/run/docker.sock

# Check Supervisor directories
ls -la /usr/share/hassio/
ls -la /addons/

# Check if current user is in docker group
groups
```

### 4. Check Security Modules

```bash
# Check SELinux status (should be disabled on Debian)
getenforce 2>/dev/null || echo "SELinux not installed"

# Check AppArmor status
sudo aa-status

# Check if any security modules are blocking
dmesg | grep -i "denied\|permission"
```

### 5. Test Simple Add-on

Try installing a simple, well-known add-on to see if the issue is systemic:

```bash
# Try installing ESPHome
ha addons install 5c53de3b_esphome

# Try installing File Editor
ha addons install core_configurator

# Check if they start successfully
ha addons start 5c53de3b_esphome
```

If these also fail, the issue is with your Supervised installation, not the add-on.

## Common Fixes

### Fix 1: Docker User Namespace Issues

If Docker is using user namespace remapping, it can cause permission issues:

```bash
# Check current Docker daemon config
cat /etc/docker/daemon.json

# If user namespace remapping is enabled, try disabling it
sudo nano /etc/docker/daemon.json
```

Remove or comment out any `userns-remap` entries:

```json
{
  "log-driver": "journald",
  "storage-driver": "overlay2"
}
```

Then restart Docker:

```bash
sudo systemctl restart docker
ha supervisor restart
```

### Fix 2: Docker Socket Permissions

Ensure the Docker socket has correct permissions:

```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock

# Add user to docker group
sudo usermod -aG docker $USER

# Restart Docker
sudo systemctl restart docker
```

### Fix 3: Reinstall Supervisor

If the installation is corrupted, reinstall Supervisor:

```bash
# Download latest Supervised installer
wget https://github.com/home-assistant/supervised-installer/releases/latest/download/homeassistant-supervised.deb

# Reinstall
sudo dpkg -i homeassistant-supervised.deb
```

### Fix 4: Check Docker Compose Version

Supervised requires specific Docker Compose versions:

```bash
# Check Docker Compose version
docker-compose --version

# If needed, update Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### Fix 5: Disable Problematic Security Features

As a last resort, temporarily disable security features to isolate the issue:

```bash
# Disable AppArmor
sudo systemctl stop apparmor
sudo systemctl disable apparmor

# Restart Supervisor
ha supervisor restart
```

**⚠️ Warning**: Only do this for testing. Re-enable security features after identifying the root cause.

## Verification Steps

After applying fixes:

1. **Restart everything**:
   ```bash
   sudo systemctl restart docker
   ha supervisor restart
   ```

2. **Wait for Supervisor to be ready**:
   ```bash
   ha supervisor info
   ```

3. **Try installing a test add-on**:
   ```bash
   ha addons install core_configurator
   ha addons start core_configurator
   ```

4. **Check logs**:
   ```bash
   ha addons logs core_configurator
   docker logs addon_core_configurator
   ```

## Known Working Configuration

A working Debian 12 Supervised installation should have:

- **Docker**: 24.0+ (but not 25.0+ which has known issues)
- **Docker Compose**: 2.20+
- **Kernel**: 5.10+ with user namespaces enabled
- **AppArmor**: Enabled with proper profiles
- **SELinux**: Disabled (not used on Debian)

Check your versions:

```bash
docker --version
docker-compose --version
uname -r
```

## Alternative Solutions

If you cannot resolve the Supervised issues:

### Option 1: Use HAOS Instead

Home Assistant OS is more stable and has fewer permission issues:

- Download HAOS image for your platform
- Flash to disk/VM
- Restore from backup

### Option 2: Use Docker Compose (Standalone)

Run Home Assistant and add-ons via Docker Compose:

```yaml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: ghcr.io/home-assistant/home-assistant:stable
    volumes:
      - ./config:/config
    ports:
      - "8123:8123"
    restart: unless-stopped

  broadlink-manager:
    build: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2.git#develop
    ports:
      - "8099:8099"
    volumes:
      - ./config:/config
    environment:
      - HA_URL=http://homeassistant:8123
      - HA_TOKEN=your_token_here
    restart: unless-stopped
```

### Option 3: Fresh Supervised Installation

If all else fails, start fresh:

1. Backup your Home Assistant configuration
2. Wipe the system
3. Install Debian 12 fresh
4. Follow the [official Supervised installation guide](https://github.com/home-assistant/supervised-installer)
5. Restore from backup

## Reporting Issues

If you've tried all the above and still have issues:

1. **Collect diagnostics**:
   ```bash
   ha supervisor info > supervisor_info.txt
   docker info > docker_info.txt
   dmesg | grep -i "denied\|permission" > dmesg_errors.txt
   ```

2. **Create a GitHub issue** with:
   - Your diagnostic files
   - Steps you've tried
   - Docker and Supervisor versions
   - Whether other add-ons work

3. **Check the Home Assistant Community Forum**:
   - Search for similar Supervised issues
   - Post in the Supervised Installation category

## Summary

The "Permission denied" error in Supervised mode is usually a Docker/system configuration issue, not an add-on problem. If multiple add-ons fail (ESPHome, File Editor, etc.), focus on fixing the underlying Supervised installation rather than individual add-ons.

**Key Indicators of System Issues**:
- ✅ Add-on works on HAOS but not Supervised
- ✅ Multiple different add-ons fail with same error
- ✅ Error persists with AppArmor disabled
- ✅ Simple add-ons like File Editor also fail

In these cases, the Supervised installation needs attention, not the add-on code.
