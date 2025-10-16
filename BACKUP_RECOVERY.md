# Automatic Backup & Recovery System

## Overview

Both `devices.json` and `metadata.json` now have automatic backup and recovery protection to prevent data loss.

## How It Works

### **Automatic Backups**

Every time a file is saved:
1. **Backup created** - Current file is copied to `.backup` before any changes
2. **Atomic write** - New data written to `.tmp` file first
3. **Safe rename** - Temp file atomically renamed to main file
4. **Rollback ready** - If anything fails, backup is available

### **Automatic Recovery**

When the app starts:
1. **Check for missing files** - If `devices.json` or `metadata.json` is missing
2. **Look for backup** - Check if `.backup` file exists
3. **Auto-restore** - Automatically restore from backup
4. **Log the recovery** - Warning logged for visibility

### **Failure Protection**

If a save operation fails:
1. **Cleanup temp file** - Remove incomplete `.tmp` file
2. **Check for damage** - If main file was deleted/corrupted
3. **Auto-restore** - Restore from backup immediately
4. **Log the incident** - Error logged with details

## Backup Files

### **Location**
```
/config/broadlink_manager/
├── devices.json          # SmartIR devices
├── devices.json.backup   # Auto-backup of devices.json
├── metadata.json         # Broadlink devices  
└── metadata.json.backup  # Auto-backup of metadata.json
```

### **When Backups Are Created**
- Before every save operation
- Automatically on every update
- No user action required

### **When Backups Are Used**
- File missing on startup → Auto-restore
- Save operation fails → Auto-restore
- File corrupted → Manual restore possible

## Manual Recovery

If you need to manually restore from backup:

### **PowerShell**
```powershell
# Restore devices.json
Copy-Item h:\broadlink_manager\devices.json.backup h:\broadlink_manager\devices.json

# Restore metadata.json
Copy-Item h:\broadlink_manager\metadata.json.backup h:\broadlink_manager\metadata.json
```

### **Linux/Docker**
```bash
# Restore devices.json
cp /config/broadlink_manager/devices.json.backup /config/broadlink_manager/devices.json

# Restore metadata.json
cp /config/broadlink_manager/metadata.json.backup /config/broadlink_manager/metadata.json
```

## Log Messages

### **Normal Operation**
```
DEBUG - Created backup of devices.json
INFO - Metadata saved successfully
```

### **Auto-Recovery on Startup**
```
WARNING - devices.json missing but backup found - restoring from backup
INFO - Successfully restored devices.json from backup
```

### **Auto-Recovery After Failed Save**
```
ERROR - Error saving devices: [error details]
WARNING - Save failed - restoring from backup
INFO - Restored devices.json from backup after failed save
```

## Benefits

✅ **Zero data loss** - Backup created before every change  
✅ **Automatic recovery** - No user intervention needed  
✅ **Atomic writes** - Prevents corruption from interruptions  
✅ **Crash protection** - Safe even if process is killed  
✅ **Transparent** - Works silently in background  
✅ **Logged** - All recovery actions are logged  

## Technical Details

### **Atomic Write Process**
1. Create backup: `file.json` → `file.json.backup`
2. Write new data: `file.json.tmp`
3. Atomic rename: `file.json.tmp` → `file.json`
4. Result: Either complete success or complete failure (no partial writes)

### **Why This Works**
- **Backup first** - Original data preserved before any changes
- **Temp file** - New data written to separate file
- **Atomic rename** - OS-level operation that can't be interrupted
- **No partial writes** - File is either old version or new version, never corrupted

### **Race Condition Protection**
- Multiple simultaneous writes won't corrupt the file
- Each write gets its own temp file
- Last write wins (atomic rename)
- Backup always has previous valid state

## Migration Notes

### **Existing Installations**
- Backups created automatically on first save after upgrade
- No manual action required
- Existing data is safe

### **New Installations**
- Backup system active from first use
- Empty backups created initially
- Protection starts immediately

## Troubleshooting

### **"Restored from backup" message on every startup**
- Main file keeps getting deleted
- Check for disk space issues
- Check file permissions
- Look for other processes modifying the file

### **Backup file is also corrupted**
- Very rare - would require corruption during backup creation
- Check disk health
- Consider external backup solution

### **No backup file exists**
- File was never successfully saved
- Fresh installation
- Backup file manually deleted

## Best Practices

1. **Don't delete backup files** - They're your safety net
2. **Monitor logs** - Watch for recovery messages
3. **Keep external backups** - For disaster recovery
4. **Check disk space** - Ensure enough space for backups
5. **Test recovery** - Occasionally verify backups work

## Future Enhancements

Potential improvements:
- Multiple backup versions (rolling backups)
- Scheduled backup snapshots
- Backup compression
- Cloud backup integration
- Backup verification/validation
