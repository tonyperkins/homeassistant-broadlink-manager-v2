# Broadlink Manager Add-on - Deployment Guide

This guide will walk you through building and deploying the Broadlink Manager add-on to your Home Assistant installation.

## Prerequisites

- Home Assistant OS or Supervised installation
- SSH access to your Home Assistant system (or access to the Terminal add-on)
- Docker installed (usually included with Home Assistant OS)
- Git (for cloning repositories)

## Deployment Methods

### Method 1: Local Add-on Repository (Recommended for Development)

This method creates a local add-on repository that you can install directly in Home Assistant.

#### Step 1: Prepare the Add-on Directory

1. **Access your Home Assistant system** via SSH or Terminal add-on
2. **Navigate to the addons directory**:
   ```bash
   cd /addons
   ```
   
3. **Create a local repository directory**:
   ```bash
   mkdir -p local-addons/broadlink-manager
   ```

#### Step 2: Copy Add-on Files

Copy all the add-on files to the local repository:

```bash
# Copy all files from your development directory to the addons directory
# Replace the source path with your actual project path
cp -r /path/to/broadlink_manager_addon/* /addons/local-addons/broadlink-manager/
```

**Alternative: Using Windows/File Manager**
If you're on Windows, you can copy the files using:
- Navigate to `\\homeassistant.local\addons` (or your HA IP)
- Create folder: `local-addons\broadlink-manager`
- Copy all files from your project directory to this folder

#### Step 3: Install the Add-on

1. **Open Home Assistant web interface**
2. **Go to Settings → Add-ons**
3. **Click "Add-on Store"**
4. **Click the three dots (⋮) in the top right**
5. **Select "Repositories"**
6. **Add local repository**: `/addons/local-addons`
7. **Refresh the add-on store**
8. **Find "Broadlink Manager"** in the local add-ons section
9. **Click "Install"**

### Method 2: GitHub Repository (Recommended for Production)

#### Step 1: Create GitHub Repository

1. **Create a new GitHub repository** (e.g., `homeassistant-broadlink-manager`)
2. **Upload all add-on files** to the repository
3. **Ensure the repository structure looks like this**:
   ```
   homeassistant-broadlink-manager/
   ├── broadlink-manager/
   │   ├── config.yaml
   │   ├── Dockerfile
   │   ├── run.sh
   │   ├── requirements.txt
   │   ├── app/
   │   │   ├── main.py
   │   │   └── web_server.py
   │   ├── README.md
   │   ├── CHANGELOG.md
   │   ├── build.yaml
   │   └── apparmor.txt
   └── repository.yaml
   ```

#### Step 2: Create repository.yaml

Create a `repository.yaml` file in the root of your GitHub repository:

```yaml
name: "Broadlink Manager Add-ons"
url: "https://github.com/tonyperkins/homeassistant-broadlink-manager"
maintainer: "Tony Perkins"
```

#### Step 3: Add Repository to Home Assistant

1. **Open Home Assistant web interface**
2. **Go to Settings → Add-ons**
3. **Click "Add-on Store"**
4. **Click the three dots (⋮) in the top right**
5. **Select "Repositories"**
6. **Add your GitHub repository URL**: `https://github.com/tonyperkins/homeassistant-broadlink-manager`
7. **Refresh the add-on store**
8. **Install the add-on**

### Method 3: Manual Docker Build (Advanced)

If you want to build the Docker image manually:

#### Step 1: Build the Image

```bash
# Navigate to your add-on directory
cd /path/to/broadlink_manager_addon

# Build for your architecture (replace with amd64, aarch64, armv7, etc.)
docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/amd64-base:3.18" -t local/broadlink-manager .
```

#### Step 2: Tag and Use

```bash
# Tag the image
docker tag local/broadlink-manager homeassistant/amd64-addon-broadlink-manager:latest

# The add-on can now reference this local image
```

## Configuration

After installation, configure the add-on:

### Basic Configuration

```yaml
log_level: info
web_port: 8099
auto_discover: true
```

### Advanced Configuration Options

- **log_level**: `trace`, `debug`, `info`, `warning`, `error`, `fatal`
- **web_port**: Any available port (default: 8099)
- **auto_discover**: Enable/disable automatic device discovery

## Post-Installation Steps

### Step 1: Start the Add-on

1. **Go to Settings → Add-ons**
2. **Click on "Broadlink Manager"**
3. **Click "Start"**
4. **Enable "Start on boot"** if desired
5. **Enable "Watchdog"** for automatic restart on crashes

### Step 2: Access the Web Interface

1. **Open your browser**
2. **Navigate to**: `http://homeassistant.local:8099`
   - Replace `homeassistant.local` with your Home Assistant IP if needed
   - Use the port you configured (default: 8099)

### Step 3: Configure Broadlink Devices

1. **Ensure your Broadlink devices are set up** in Home Assistant
2. **The add-on will automatically discover** remote entities
3. **Select your device** from the dropdown in the web interface

## Troubleshooting

### Common Issues

#### Add-on Won't Start
- Check the logs in the add-on page
- Verify all files are present and have correct permissions
- Ensure the port isn't already in use

#### Web Interface Not Accessible
- Check if the add-on is running
- Verify the port configuration
- Check firewall settings
- Try accessing via IP address instead of hostname

#### Can't See Broadlink Devices
- Ensure Broadlink integration is installed and configured
- Check that devices are online and working in Home Assistant
- Verify the devices appear as `remote.` entities

#### Commands Not Learning
- Ensure the Broadlink device supports learning (RM series)
- Check that the device is not in use by other processes
- Verify Home Assistant can communicate with the device

### Debug Mode

Enable debug logging for troubleshooting:

```yaml
log_level: debug
```

### Log Locations

- **Add-on logs**: Available in the Home Assistant add-on interface
- **Home Assistant logs**: Settings → System → Logs
- **Container logs**: `docker logs addon_local_broadlink-manager` (if using local method)

## Updates

### Updating Local Add-on

1. **Copy new files** to the add-on directory
2. **Restart the add-on** from the Home Assistant interface

### Updating GitHub Repository Add-on

1. **Push updates** to your GitHub repository
2. **Refresh** the add-on store in Home Assistant
3. **Update** the add-on when prompted

## Security Considerations

- The add-on requires read-only access to `/config` for reading storage files
- Web interface is only accessible on your local network by default
- Consider using Home Assistant's authentication proxy for external access
- Regular updates ensure security patches are applied

## Support

If you encounter issues:

1. **Check the logs** first
2. **Verify your configuration** matches the examples
3. **Ensure prerequisites** are met
4. **Test with a minimal configuration** first
5. **Check Home Assistant community forums** for similar issues

## File Permissions

Ensure proper file permissions after copying:

```bash
chmod +x /addons/local-addons/broadlink-manager/run.sh
chown -R root:root /addons/local-addons/broadlink-manager/
```
