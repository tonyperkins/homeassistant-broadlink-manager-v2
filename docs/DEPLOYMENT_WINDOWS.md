# Windows Deployment Guide for Broadlink Manager

This guide covers deploying the Broadlink Manager add-on to Home Assistant OS from a Windows development machine.

## Prerequisites

- **Windows 10/11** with PowerShell 5.1 or later
- **Home Assistant OS** installed and running
- **Network access** to your Home Assistant instance
- **Samba share** enabled on Home Assistant (usually enabled by default)

## Quick Start

The easiest way to deploy from Windows is using the included PowerShell deployment script.

### Step 1: Access Home Assistant Addons Share

First, ensure you can access the Home Assistant addons network share:

1. Open **File Explorer**
2. In the address bar, type: `\\homeassistant.local\addons`
   - Or use your HA IP: `\\192.168.1.100\addons`
3. If prompted for credentials, use your Home Assistant login

If you can't access the share, you may need to:
- Enable the Samba share add-on in Home Assistant
- Check your network connectivity
- Verify Windows network discovery is enabled

### Step 2: Run the Deployment Script

From your project directory in PowerShell:

```powershell
.\deploy-to-haos.ps1
```

The script will:
1. ✅ Validate the Home Assistant addons path is accessible
2. ✅ Create the `/addons/local/broadlink-manager/` directory
3. ✅ Copy all necessary add-on files
4. ✅ Exclude unnecessary files (cache, logs, etc.)
5. ✅ Provide next steps for installation

### Step 3: Install in Home Assistant

1. Open **Home Assistant** web interface
2. Go to **Settings → Add-ons → Add-on Store**
3. Click the **three dots (⋮)** in the top right
4. Select **"Check for updates"** to refresh
5. Look for **"Broadlink Manager"** in the **"Local add-ons"** section (at the top)
6. Click on it and click **"Install"**

## Deployment Script Details

### What Gets Deployed

The script copies these files to `\\homeassistant.local\addons\local\broadlink-manager\`:

**Core Files:**
- `config.yaml` - Add-on configuration
- `Dockerfile` - Docker image definition
- `run.sh` - Startup script
- `requirements.txt` - Python dependencies
- `apparmor.txt` - Security profile
- `icon.png` - Add-on icon

**Documentation:**
- `README.md`
- `CHANGELOG.md`
- `DOCS.md`
- `API.md`
- `TROUBLESHOOTING.md`

**Application Code:**
- `app/` directory (all Python files and templates)

### What Gets Excluded

The script automatically excludes:
- `__pycache__/` directories
- `*.pyc`, `*.pyo` files
- `*.log` files
- `.DS_Store` files
- Development-only files (`.env`, `docker-compose.yml`, etc.)

### Script Options

The script will prompt you if the target directory already exists:

```
[WARNING] Target directory already exists: \\homeassistant.local\addons\local\broadlink-manager
Do you want to overwrite it? (y/N):
```

- Type `y` to overwrite and deploy new files
- Type `n` to cancel deployment

## Manual Deployment (Alternative)

If you prefer not to use the script, you can deploy manually:

### Option 1: File Explorer

1. Open File Explorer
2. Navigate to `\\homeassistant.local\addons`
3. Create folder: `local\broadlink-manager`
4. Copy these files from your project:
   - `config.yaml`
   - `Dockerfile`
   - `run.sh`
   - `requirements.txt`
   - `apparmor.txt`
   - `icon.png`
   - `README.md`, `CHANGELOG.md`, `DOCS.md`, `API.md`, `TROUBLESHOOTING.md`
   - `app\` folder (entire directory)

### Option 2: Map Network Drive

1. Map `\\homeassistant.local\addons` as a network drive (e.g., `Z:`)
2. Use the deployment script with the mapped drive:
   ```powershell
   # Edit deploy-to-haos.ps1 and change:
   $HA_ADDONS_PATH = "Z:\local"
   ```

## Troubleshooting

### Can't Access \\homeassistant.local\addons

**Problem:** Network path not found

**Solutions:**

1. **Try using IP address instead:**
   ```
   \\192.168.1.100\addons
   ```

2. **Check Samba is enabled:**
   - Install the "Samba share" add-on in Home Assistant
   - Configure it to share the addons directory

3. **Check Windows network discovery:**
   - Open Settings → Network & Internet → Advanced sharing settings
   - Enable "Network discovery"
   - Enable "File and printer sharing"

4. **Verify Home Assistant is reachable:**
   ```powershell
   Test-NetConnection homeassistant.local -Port 445
   ```

### Script Fails with "Path not found"

**Problem:** `\\homeassistant.local\addons\local` doesn't exist

**Solution:** The script will create it automatically. If it fails:

```powershell
# Manually create the directory
New-Item -ItemType Directory -Path "\\homeassistant.local\addons\local" -Force
```

### Add-on Doesn't Appear in Home Assistant

**Problem:** Deployed files but add-on not showing

**Solutions:**

1. **Verify files are in correct location:**
   ```powershell
   Get-ChildItem "\\homeassistant.local\addons\local\broadlink-manager"
   ```
   You should see `config.yaml`, `Dockerfile`, etc.

2. **Check config.yaml is valid:**
   ```powershell
   Get-Content "\\homeassistant.local\addons\local\broadlink-manager\config.yaml"
   ```

3. **Refresh the Add-on Store:**
   - Settings → Add-ons → ⋮ → Check for updates

4. **Restart Home Assistant:**
   - Settings → System → Restart

### Permission Denied Errors

**Problem:** Can't write to network share

**Solutions:**

1. **Check you're logged in to the share:**
   - Disconnect: `net use \\homeassistant.local\addons /delete`
   - Reconnect: `net use \\homeassistant.local\addons`

2. **Run PowerShell as Administrator** (if needed)

3. **Check Samba configuration** in Home Assistant

## Updating the Add-on

To deploy updates after making changes:

1. **Make your code changes** in your local project
2. **Run the deployment script:**
   ```powershell
   .\deploy-to-haos.ps1
   ```
3. **Confirm overwrite** when prompted (type `y`)
4. **In Home Assistant:**
   - Go to the Broadlink Manager add-on page
   - Click the three dots (⋮)
   - Select **"Rebuild"**
   - Or **"Restart"** if only code changed

## Development Workflow

For active development:

1. **Edit code** in your IDE (VS Code, etc.)
2. **Deploy changes:**
   ```powershell
   .\deploy-to-haos.ps1
   ```
3. **Rebuild/Restart** the add-on in Home Assistant
4. **Test** the changes
5. **Repeat** as needed

**Tip:** Keep a PowerShell window open in your project directory for quick deployments.

## Network Share Alternatives

If you can't use `\\homeassistant.local\addons`:

### Option 1: SSH and SCP

Use SSH to copy files (requires SSH add-on):

```powershell
# Using SCP (requires SSH client)
scp -r * root@homeassistant.local:/addons/local/broadlink-manager/
```

### Option 2: Git Clone on HA

SSH into Home Assistant and clone your repository:

```bash
ssh root@homeassistant.local
cd /addons/local
git clone https://github.com/yourusername/broadlink-manager.git
```

Then pull updates:
```bash
ssh root@homeassistant.local
cd /addons/local/broadlink-manager
git pull
```

## Comparison: Deployment Methods

| Method | Speed | Ease | Best For |
|--------|-------|------|----------|
| **PowerShell Script** | ⚡⚡⚡ Fast | ✅ Easy | Regular development |
| **Manual File Copy** | ⚡⚡ Medium | ✅ Easy | One-time deployment |
| **SSH/SCP** | ⚡ Slow | ⚠️ Complex | Advanced users |
| **Git Clone** | ⚡ Slow | ⚠️ Complex | Version control workflow |

## Script Customization

You can modify `deploy-to-haos.ps1` to suit your needs:

### Change Target Path

```powershell
# Edit line 5
$HA_ADDONS_PATH = "\\your-custom-path\addons\local"
```

### Add More Files

```powershell
# Edit the $itemsToCopy array (around line 87)
$itemsToCopy = @(
    "config.yaml",
    "Dockerfile",
    # ... add more files here
)
```

### Change Addon Name

```powershell
# Edit line 6
$ADDON_NAME = "your-addon-name"
```

## Support

For Windows deployment issues:

1. Check this guide's [Troubleshooting](#troubleshooting) section
2. Verify network connectivity to Home Assistant
3. Check the [main DEPLOYMENT.md](DEPLOYMENT.md) for general deployment info
4. Open an issue on [GitHub](https://github.com/tonyperkins/homeassistant-broadlink-manager/issues)

## See Also

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - General deployment guide (Linux/SSH methods)
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow guide
- **[README.md](README.md)** - Main documentation
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - General troubleshooting

---

**Happy deploying! 🚀**
