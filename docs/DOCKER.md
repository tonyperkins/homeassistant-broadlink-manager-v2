# Broadlink Manager - Standalone Docker Deployment Guide

This guide covers deploying Broadlink Manager as a standalone Docker container for Home Assistant installations that don't support add-ons (e.g., Home Assistant Container/Docker installations).

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Installation Methods](#installation-methods)
  - [Docker Compose (Recommended)](#docker-compose-recommended)
  - [Docker CLI](#docker-cli)
- [Configuration](#configuration)
- [Network Configuration](#network-configuration)
- [Troubleshooting](#troubleshooting)
- [Upgrading](#upgrading)

---

## Overview

Broadlink Manager can run in two modes:

1. **Supervisor Add-on Mode** - For Home Assistant OS and Supervised installations
2. **Standalone Docker Mode** - For any Home Assistant installation without Supervisor (this guide)

The standalone mode works with:
- **Home Assistant Container** (Docker)
- **Home Assistant Core** (Python venv)
- **Any other non-Supervisor setup**

It requires manual configuration of the Home Assistant connection but provides the same functionality as the add-on version.

---

## Prerequisites

### Required

- **Home Assistant** (any installation type: Container, Core, etc.)
- **Docker** and **Docker Compose** installed on your host machine
- **Network access** to your Home Assistant instance
- **Access to Home Assistant's config folder** (for mounting as a volume)
- **Broadlink devices** configured in Home Assistant
- **Long-lived access token** from Home Assistant

**Note:** Home Assistant itself does NOT need to be running in Docker. The standalone Broadlink Manager runs in Docker, but it can connect to any Home Assistant installation as long as it has network access and can mount the config folder.

### Creating a Long-Lived Access Token

1. Open your Home Assistant web interface
2. Click on your **profile** (your name in the sidebar)
3. Scroll down to **"Long-Lived Access Tokens"**
4. Click **"Create Token"**
5. Give it a name like `Broadlink Manager`
6. **Copy the token** - you'll need it for configuration

⚠️ **Important:** Save this token securely. You won't be able to see it again!

---

## Available Docker Images

The standalone Docker image is available from GitHub Container Registry:

```
ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone
```

**Available Tags:**
- `:standalone` - Latest stable standalone release
- `:standalone-latest` - Alias for latest stable release
- `:standalone-X.X.X` - Specific version (e.g., `:standalone-0.3.0`)

**Supported Architectures:**
- `linux/amd64` - x86-64 systems
- `linux/arm64` - ARM 64-bit (e.g., Raspberry Pi 4)
- `linux/arm/v7` - ARM 32-bit (e.g., older Raspberry Pi)

The image automatically selects the correct architecture for your platform.

---

## Quick Start

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/tonyperkins/homeassistant-broadlink-manager.git
cd homeassistant-broadlink-manager

# Copy the example environment file
cp .env.example .env

# Edit .env and set your HA_URL and HA_TOKEN
nano .env

# Update docker-compose.yml with your Home Assistant config path
nano docker-compose.yml
# Change: /path/to/homeassistant/config:/config

# Start the container
docker-compose up -d

# View logs
docker-compose logs -f
```

Access the web interface at `http://your-host-ip:8099`

---

## Installation Methods

### Docker Compose (Recommended)

Docker Compose provides the easiest way to manage the container.

#### Step 1: Create Configuration Directory

```bash
mkdir -p ~/broadlink-manager
cd ~/broadlink-manager
```

#### Step 2: Download Files

Download these files from the repository:
- `docker-compose.yml`
- `.env.example`

Or create them manually using the examples below.

#### Step 3: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings
nano .env
```

Set these required values in `.env`:

```env
HA_URL=http://192.168.1.100:8123  # Your Home Assistant URL
HA_TOKEN=your_long_lived_token_here
```

#### Step 4: Update Docker Compose

Edit `docker-compose.yml` and update the volume mount to point to your Home Assistant config directory:

```yaml
volumes:
  - /path/to/homeassistant/config:/config  # Update this path!
```

**Finding your HA config path:**
- If HA is in Docker: Usually `/home/user/homeassistant` or similar
- Check your HA container: `docker inspect homeassistant | grep -A 5 Mounts`

#### Step 5: Start the Container

```bash
# Start in detached mode
docker-compose up -d

# View logs
docker-compose logs -f broadlink-manager

# Check status
docker-compose ps
```

#### Step 6: Access the Interface

Open your browser to: `http://your-host-ip:8099`

---

### Docker CLI

If you prefer using Docker directly without Compose:

```bash
docker run -d \
  --name broadlink-manager \
  --network host \
  -e HA_URL=http://192.168.1.100:8123 \
  -e HA_TOKEN=your_long_lived_token_here \
  -e LOG_LEVEL=info \
  -e WEB_PORT=8099 \
  -e AUTO_DISCOVER=true \
  -v /path/to/homeassistant/config:/config \
  --restart unless-stopped \
  ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone
```

**Note:** Replace the paths and values with your actual configuration.

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HA_URL` | **Yes** | `http://localhost:8123` | Home Assistant URL |
| `HA_TOKEN` | **Yes** | - | Long-lived access token |
| `LOG_LEVEL` | No | `info` | Logging level (trace\|debug\|info\|warning\|error\|fatal) |
| `WEB_PORT` | No | `8099` | Web interface port |
| `AUTO_DISCOVER` | No | `true` | Auto-discover Broadlink devices |
| `CONFIG_PATH` | No | `/config` | HA config directory (inside container) |

### Volume Mounts

| Host Path | Container Path | Description |
|-----------|----------------|-------------|
| `/path/to/ha/config` | `/config` | **Required** - Home Assistant config directory |

### Port Mapping

| Port | Description |
|------|-------------|
| `8099` | Web interface (configurable via `WEB_PORT`) |

---

## Network Configuration

You have two options for networking:

### Option 1: Host Network (Recommended)

Best for Broadlink device discovery:

```yaml
services:
  broadlink-manager:
    network_mode: host
    environment:
      - HA_URL=http://localhost:8123  # Use localhost if HA is on same host
```

**Pros:**
- Broadlink device discovery works reliably
- No port mapping needed
- Direct network access

**Cons:**
- Less network isolation

### Option 2: Bridge Network

Better isolation but may affect device discovery:

```yaml
services:
  broadlink-manager:
    ports:
      - "8099:8099"
    environment:
      - HA_URL=http://homeassistant:8123  # Use container name
    networks:
      - homeassistant
```

**Pros:**
- Better network isolation
- Can control port mapping

**Cons:**
- Broadlink device discovery may not work
- Requires proper network configuration

### Running with Home Assistant in Same Docker Network

If both containers are on the same Docker network:

```yaml
version: '3.8'

networks:
  homeassistant:
    name: homeassistant

services:
  homeassistant:
    image: homeassistant/home-assistant:latest
    container_name: homeassistant
    network_mode: host
    volumes:
      - /path/to/ha/config:/config

  broadlink-manager:
    image: ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone
    container_name: broadlink-manager
    network_mode: host
    environment:
      - HA_URL=http://localhost:8123
      - HA_TOKEN=${HA_TOKEN}
    volumes:
      - /path/to/ha/config:/config
    depends_on:
      - homeassistant
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker-compose logs broadlink-manager
```

**Common issues:**

1. **Missing HA_TOKEN:**
   ```
   ERROR: HA_TOKEN environment variable is required
   ```
   **Solution:** Set `HA_TOKEN` in your `.env` file

2. **Config path doesn't exist:**
   ```
   ERROR: Config path does not exist: /config
   ```
   **Solution:** Check your volume mount points to the correct HA config directory

3. **Can't connect to Home Assistant:**
   ```
   ERROR: Could not connect to Home Assistant
   ```
   **Solution:** 
   - Verify `HA_URL` is correct
   - Check if HA is running: `docker ps | grep homeassistant`
   - Test connectivity: `docker exec broadlink-manager curl -I $HA_URL`

### Authentication Errors

**Token invalid:**
```
ERROR: Authentication failed
```

**Solutions:**
1. Verify token is correct (no extra spaces)
2. Create a new long-lived access token
3. Check token hasn't been revoked in HA

### Device Discovery Not Working

**Issue:** Broadlink devices not appearing

**Solutions:**
1. Use `network_mode: host` in docker-compose.yml
2. Ensure Broadlink devices are on the same network
3. Check if devices are configured in Home Assistant
4. Verify `AUTO_DISCOVER=true` is set

### Web Interface Not Accessible

**Issue:** Can't access `http://host:8099`

**Solutions:**
1. Check container is running: `docker ps`
2. Verify port mapping: `docker port broadlink-manager`
3. Check firewall rules on host
4. Try accessing from host: `curl http://localhost:8099`

### Permission Issues

**Issue:** Can't write to config directory

**Solutions:**
1. Check volume mount permissions
2. Ensure config directory is readable/writable
3. Check Docker user permissions

---

## Upgrading

### Docker Compose

```bash
# Pull latest image
docker-compose pull

# Restart with new image
docker-compose up -d

# View logs
docker-compose logs -f
```

### Docker CLI

```bash
# Stop and remove old container
docker stop broadlink-manager
docker rm broadlink-manager

# Pull latest image
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone

# Start new container (use your previous docker run command)
docker run -d ...
```

### Backup Before Upgrading

Always backup your Broadlink Manager data:

```bash
# Backup metadata and learned commands
cp -r /path/to/ha/config/broadlink_manager ~/broadlink_manager_backup
```

---

## Advanced Configuration

### Custom Build

Build your own image:

```bash
# Clone repository
git clone https://github.com/tonyperkins/homeassistant-broadlink-manager.git
cd homeassistant-broadlink-manager

# Build standalone image
docker build -f Dockerfile.standalone -t broadlink-manager:custom .

# Run your custom image
docker run -d --name broadlink-manager ... broadlink-manager:custom
```

### Running Multiple Instances

You can run multiple instances for different HA installations:

```bash
# Instance 1
docker run -d \
  --name broadlink-manager-1 \
  -e HA_URL=http://192.168.1.100:8123 \
  -e WEB_PORT=8099 \
  -p 8099:8099 \
  ...

# Instance 2
docker run -d \
  --name broadlink-manager-2 \
  -e HA_URL=http://192.168.1.101:8123 \
  -e WEB_PORT=8100 \
  -p 8100:8100 \
  ...
```

---

## Support

For issues specific to standalone Docker deployment:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review logs: `docker-compose logs -f`
3. Open an issue on [GitHub](https://github.com/tonyperkins/homeassistant-broadlink-manager/issues)

For general usage questions, see:
- [README.md](README.md) - Main documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting
- [API.md](API.md) - API reference

---

## Comparison: Add-on vs Standalone

| Feature | Supervisor Add-on | Standalone Docker |
|---------|-------------------|-------------------|
| **Installation** | One-click in HA | Manual Docker setup |
| **Configuration** | UI-based | Environment variables |
| **Authentication** | Automatic | Manual token |
| **Updates** | Automatic | Manual pull |
| **Network** | Automatic | Manual configuration |
| **Functionality** | ✅ Full | ✅ Full |

Both modes provide identical functionality - choose based on your Home Assistant installation type.

---

## License

MIT License - See [LICENSE](LICENSE) for details.
