# Deployment Guide - Broadlink Manager v2

## Running v2 Alongside v1

**Good news!** v2 can run side-by-side with v1 for testing.

### Key Differences

| Aspect | v1 | v2 |
|--------|----|----|
| **Name** | Broadlink Manager | Broadlink Manager v2 (Beta) |
| **Slug** | `broadlink-manager` | `broadlink-manager-v2` |
| **Directory** | `/addons/local/broadlink-manager` | `/addons/local/broadlink-manager-v2` |
| **Port** | 8099 | 8099 (same, but different ingress) |
| **Data** | `/config/broadlink_manager` | `/config/broadlink_manager` (shared!) |

### ⚠️ Important Notes

1. **Shared Data**: Both versions use `/config/broadlink_manager` for storage
   - They'll see the same learned commands
   - They'll see the same entity metadata
   - Changes in one affect the other

2. **Don't Run Both Simultaneously**: While they can be installed together, only run one at a time to avoid conflicts

3. **Testing Strategy**:
   - Keep v1 running for production
   - Install v2 for testing
   - Stop v1, start v2 to test
   - Switch back to v1 if needed

## Deployment Steps

### 1. Build Frontend (Required)

```bash
cd frontend
npm run build
```

This creates the production build in `app/static/`.

### 2. Deploy to Home Assistant

Run the deployment script:

```powershell
.\deploy-to-haos.ps1
```

**What it does:**
- Copies files to `\\homeassistant.local\addons\local\broadlink-manager-v2`
- Excludes `__pycache__`, `.pyc`, `.log` files
- Preserves directory structure

### 3. Install in Home Assistant

1. Open Home Assistant web interface
2. Go to **Settings** → **Add-ons**
3. Click **Add-on Store** (bottom right)
4. Click **⋮** (three dots, top right)
5. Select **Check for updates**
6. Look for **"Broadlink Manager v2 (Beta)"** in Local add-ons
7. Click **Install**

### 4. Configure & Start

**Configuration** (same as v1):
```yaml
log_level: info
web_port: 8099
auto_discover: true
```

**Start Options:**
- ✅ **Start on boot**: No (for testing)
- ✅ **Watchdog**: Yes
- ✅ **Auto update**: No (manual control during beta)

### 5. Access the Interface

**Via Ingress (Recommended):**
- Settings → Add-ons → Broadlink Manager v2 (Beta) → **Open Web UI**

**Direct Access:**
- `http://homeassistant.local:8099`

## Testing Checklist

### SmartIR Integration
- [ ] Banner appears on dashboard
- [ ] Banner shows correct status (installed/not installed)
- [ ] Banner dismissible
- [ ] Entity form shows climate option
- [ ] Climate option disabled without SmartIR
- [ ] Climate option enabled with SmartIR
- [ ] Warning/success notices appear correctly

### Core Functionality
- [ ] Device discovery works
- [ ] Command learning works
- [ ] Command sending works
- [ ] Entity generation works
- [ ] Area detection works

### UI/UX
- [ ] Dark mode toggle works
- [ ] Responsive design on mobile
- [ ] Icons display correctly
- [ ] Forms validate properly

## Switching Between v1 and v2

### To Test v2:
1. Stop v1 add-on
2. Start v2 add-on
3. Test features
4. Check logs for errors

### To Return to v1:
1. Stop v2 add-on
2. Start v1 add-on
3. Everything should work as before

## Troubleshooting

### Add-on Doesn't Appear

**Solution 1:** Refresh the page
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

**Solution 2:** Check file permissions
```bash
# SSH into Home Assistant
ls -la /addons/local/broadlink-manager-v2
```

**Solution 3:** Restart Home Assistant
- Settings → System → Restart

### Port Conflict

If both v1 and v2 are running:
```
Error: Port 8099 already in use
```

**Solution:** Stop one of them
- Only run one version at a time

### SmartIR Not Detected

**Check installation:**
```bash
# SSH into Home Assistant
ls -la /config/custom_components/smartir
```

**Should see:**
- `manifest.json`
- `__init__.py`
- `climate.py`, etc.

**If missing:** Install SmartIR via HACS

### Frontend Not Loading

**Symptom:** Blank page or old interface

**Solution:** Rebuild frontend
```bash
cd frontend
npm run build
```

Then redeploy:
```powershell
.\deploy-to-haos.ps1
```

## Rollback Plan

If v2 has issues:

1. **Stop v2 add-on**
2. **Start v1 add-on**
3. **Uninstall v2** (optional)
   - Settings → Add-ons → Broadlink Manager v2 (Beta)
   - Click **Uninstall**

Your data in `/config/broadlink_manager` is safe - it's not deleted when uninstalling.

## Production Deployment

When v2 is stable and ready to replace v1:

1. **Backup your data:**
   ```bash
   # SSH into Home Assistant
   tar -czf /backup/broadlink_manager_backup.tar.gz /config/broadlink_manager
   ```

2. **Stop v1:**
   - Settings → Add-ons → Broadlink Manager → Stop

3. **Uninstall v1:**
   - Settings → Add-ons → Broadlink Manager → Uninstall

4. **Rename v2 slug** (optional):
   - Edit `config.yaml`: Change slug to `broadlink-manager`
   - Redeploy
   - This makes v2 the "official" version

5. **Enable auto-start:**
   - Configuration → Start on boot: Yes

## Support

**Issues?** Check:
- Add-on logs: Settings → Add-ons → Broadlink Manager v2 (Beta) → Log
- Home Assistant logs: Settings → System → Logs
- Browser console: F12 → Console tab

**Report bugs:**
- GitHub Issues: [Your repo URL]
- Include logs and screenshots
