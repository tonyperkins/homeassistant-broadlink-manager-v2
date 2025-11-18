# Deployment Guide

## Environment Setup

This project has **two separate Home Assistant instances**:

### 1. Production Instance (HAOS)
- **Host**: `homeassistant.local`
- **Network Path**: `\\homeassistant.local\addons`
- **Purpose**: Main production environment
- **Deployment**: Use `deploy-to-haos.ps1`
- **⚠️ WARNING**: Only deploy tested, stable code here

### 2. Test Instance (Supervised on Debian)
- **Host**: `192.168.50.169`
- **SSH**: `root@192.168.50.169`
- **Purpose**: Testing and development
- **Deployment**: Use `deploy-to-test-ssh.ps1`
- **✅ SAFE**: Test all changes here first

---

## Deployment Scripts

### Deploy to Test Instance (RECOMMENDED)

```powershell
# Build and deploy to test instance
.\deploy-to-test-ssh.ps1

# Skip frontend build (faster for backend-only changes)
.\deploy-to-test-ssh.ps1 -SkipBuild

# Auto-rebuild after deployment
.\deploy-to-test-ssh.ps1 -AutoRebuild
```

**Requirements**:
- SSH access to `192.168.50.169`
- SSH key authentication set up (or password prompt)

**After deployment**:
```bash
# SSH to test instance
ssh root@192.168.50.169

# Rebuild add-on
ha addons rebuild local_broadlink-manager-v2

# Start add-on
ha addons start local_broadlink-manager-v2

# View logs
ha addons logs local_broadlink-manager-v2
```

### Deploy to Production (USE WITH CAUTION)

```powershell
# Build and deploy to production
.\deploy-to-haos.ps1
```

**Requirements**:
- Network share access to `\\homeassistant.local\addons`

**⚠️ Only deploy to production after thorough testing on test instance!**

---

## Port Configuration

The add-on uses **port 8888** for ingress:

- **config.yaml**: `ingress_port: 8888`, `web_port: 8888`
- **Code defaults**: Port `8099` (overridden by config)
- **Supervisor**: Connects to `ingress_port` (8888)

When the add-on starts, it reads `web_port` from `config.yaml` options and binds to that port.

---

## Troubleshooting

### Add-on won't start (timeout after 120 seconds)

**Check logs**:
```bash
ssh root@192.168.50.169
ha addons logs local_broadlink-manager-v2
```

**Common issues**:
1. Port mismatch - ensure `ingress_port` matches `web_port`
2. Python errors - check requirements.txt
3. Missing files - ensure all files copied correctly

### Cannot access test instance via SSH

```powershell
# Test SSH connection
Test-NetConnection -ComputerName 192.168.50.169 -Port 22

# Try manual SSH
ssh root@192.168.50.169
```

### Network share not accessible

For production deployment, ensure:
```powershell
# Test access
Test-Path "\\homeassistant.local\addons"

# Map drive if needed
net use Z: \\homeassistant.local\addons
```

---

## Development Workflow

1. **Make changes** to code
2. **Test locally** (if possible): `python app/main.py`
3. **Deploy to test**: `.\deploy-to-test-ssh.ps1 -AutoRebuild`
4. **Verify on test instance**: Check logs and functionality
5. **If stable**, deploy to production: `.\deploy-to-haos.ps1`
6. **Rebuild** via HA UI or SSH

---

## Quick Reference

| Task | Command |
|------|---------|
| Deploy to test | `.\deploy-to-test-ssh.ps1` |
| Deploy to production | `.\deploy-to-haos.ps1` |
| SSH to test | `ssh root@192.168.50.169` |
| Rebuild add-on | `ha addons rebuild local_broadlink-manager-v2` |
| Start add-on | `ha addons start local_broadlink-manager-v2` |
| View logs | `ha addons logs local_broadlink-manager-v2` |
| Restart add-on | `ha addons restart local_broadlink-manager-v2` |

---

## Safety Checklist

Before deploying to **production**:

- [ ] Tested on test instance (192.168.50.169)
- [ ] Add-on starts successfully
- [ ] No errors in logs
- [ ] Frontend loads correctly
- [ ] Device discovery works
- [ ] Command learning works
- [ ] SmartIR integration works (if applicable)
- [ ] Version number updated in `config.yaml`
- [ ] CHANGELOG.md updated
