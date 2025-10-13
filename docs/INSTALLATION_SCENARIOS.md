# Installation Scenarios Guide

This guide explains how Broadlink Manager handles different installation scenarios automatically.

## Quick Reference

| Scenario | Has Commands? | Has Metadata? | What Happens |
|----------|---------------|---------------|--------------|
| **First-Time User** | ❌ No | ❌ No | Welcome message, ready to learn commands |
| **Existing BL Manager** | ✅ Yes | ✅ Yes | Configuration preserved, continues normally |
| **Existing Broadlink User** | ✅ Yes | ❌ No | **Automatic migration** - entities created |

---

## Scenario 1: First-Time User 👋

### Profile
- Just installed Broadlink Manager
- Have Broadlink devices in Home Assistant
- Haven't learned any commands yet

### Detection Logic
```
No learned commands found
→ No metadata exists
→ First-time user scenario
```

### What You'll See

**In Logs:**
```
============================================================
👋 WELCOME TO BROADLINK MANAGER!
============================================================
No learned commands found yet
🎯 Get started:
   1. Open the web interface
   2. Select a Broadlink device
   3. Learn IR/RF commands
   4. Auto-generate entities
============================================================
```

**In Web Interface:**
- Empty command list
- Device selection available
- Learning interface ready

### Next Steps
1. Open web interface at `http://homeassistant.local:8099`
2. Select your Broadlink device
3. Start learning commands (e.g., `light_on`, `light_off`)
4. Use auto-detection to create entities
5. Generate YAML files
6. Add to `configuration.yaml`
7. Restart Home Assistant

### Example Timeline
```
Install → Start → Welcome → Learn Commands → Create Entities → Done!
         (1 min)           (5-10 min)        (2 min)
```

---

## Scenario 2: Existing Broadlink Manager User 📋

### Profile
- Already using Broadlink Manager
- Have configured entities in metadata
- Upgrading or restarting the add-on

### Detection Logic
```
Metadata file exists
→ Contains entities
→ Existing BL Manager user scenario
```

### What You'll See

**In Logs:**
```
============================================================
📋 EXISTING INSTALLATION DETECTED
============================================================
Found 15 existing entities
No migration needed - your configuration is preserved
============================================================
```

**In Web Interface:**
- All your entities visible
- Configuration preserved
- Everything works as before

### What's Protected
✅ Entity configurations  
✅ Area assignments  
✅ Broadlink device associations  
✅ Custom friendly names  
✅ Enabled/disabled states  
✅ Generated YAML files  

### Next Steps
- Continue using normally
- No action required
- Your configuration is safe

### Example Timeline
```
Restart → Detect Existing → Continue Normally
         (5 sec)
```

---

## Scenario 3: Existing Broadlink User (New to BL Manager) 🎉

### Profile
- Have been using Broadlink integration
- Learned many commands over time
- Installing Broadlink Manager for first time

### Detection Logic
```
Learned commands found in storage
→ No metadata exists
→ Existing Broadlink user scenario
→ AUTOMATIC MIGRATION TRIGGERED
```

### What You'll See

**In Logs:**
```
🎉 Existing Broadlink user detected: Found 8 devices with learned commands
🔄 Starting automatic migration to Broadlink Manager...

============================================================
✅ AUTOMATIC MIGRATION COMPLETED
============================================================
📊 Migrated: 15 entities
📁 From: 8 devices
⚠️  Skipped: 2 devices (no valid entities)
🎯 Next steps:
   1. Review entities in the web interface
   2. Adjust areas if needed
   3. Generate YAML entities
   4. Restart Home Assistant
============================================================
```

**In Web Interface:**
- All detected entities visible
- Organized by type (lights, fans, switches)
- Ready to customize and generate

### What Gets Migrated

**Discovered:**
- ✅ All learned IR/RF commands
- ✅ Device names
- ✅ Command codes

**Auto-Created:**
- ✅ Entity metadata
- ✅ Entity type detection (light, fan, switch, media_player)
- ✅ Command role mapping (turn_on, turn_off, speed_1, etc.)
- ✅ Broadlink device associations
- ✅ Area assignments (from Broadlink device location)
- ✅ Friendly names

### Migration Details

**Example: Fan with Multiple Commands**

**Before (in Broadlink storage):**
```json
{
  "living_room_ceiling_fan": {
    "fan_off": "JgBQAAABK...",
    "fan_speed_1": "JgBQAAABL...",
    "fan_speed_2": "JgBQAAABM...",
    "fan_speed_3": "JgBQAAABN..."
  }
}
```

**After (in BL Manager metadata):**
```json
{
  "living_room_ceiling_fan": {
    "entity_type": "fan",
    "device": "living_room_ceiling_fan",
    "broadlink_entity": "remote.kitchen_broadlink",
    "area": "Kitchen",
    "commands": {
      "turn_off": "fan_off",
      "speed_1": "fan_speed_1",
      "speed_2": "fan_speed_2",
      "speed_3": "fan_speed_3"
    },
    "friendly_name": "Living Room Ceiling Fan",
    "enabled": true,
    "auto_detected": true
  }
}
```

### Next Steps

1. **Review Entities** (2-5 min)
   - Open web interface
   - Check detected entities
   - Verify entity types are correct

2. **Adjust Areas** (2-5 min)
   - Update `area` field for entities in different rooms
   - Remember: Area = where the controlled device is, not where Broadlink is

3. **Verify Broadlink Assignments** (1-2 min)
   - Check `broadlink_entity` field
   - Ensure correct Broadlink device assigned

4. **Generate YAML** (1 min)
   - Click "Generate Entities"
   - Files created in `/config/broadlink_manager/`

5. **Add to Configuration** (2 min)
   ```yaml
   light: !include broadlink_manager/entities.yaml
   fan: !include broadlink_manager/entities.yaml
   switch: !include broadlink_manager/entities.yaml
   input_boolean: !include broadlink_manager/helpers.yaml
   input_select: !include broadlink_manager/helpers.yaml
   ```

6. **Restart Home Assistant** (1-2 min)

### Example Timeline
```
Install → Auto-Migrate → Review → Adjust → Generate → Restart → Done!
         (30 sec)        (5 min)  (5 min)  (1 min)   (2 min)
         
Total Time: ~15 minutes (vs. hours of manual configuration!)
```

---

## Comparison Table

| Aspect | First-Time | Existing BL Manager | Existing Broadlink |
|--------|-----------|---------------------|-------------------|
| **Commands** | None | Many | Many |
| **Metadata** | None | Exists | None |
| **Migration** | Not needed | Not needed | **Automatic** |
| **Setup Time** | Start fresh | Instant | ~15 minutes |
| **Action Required** | Learn commands | None | Review & adjust |
| **Entities Created** | Manual | Already exist | **Automatic** |

---

## Special Cases

### Case 1: Partial Migration

**Situation**: Some commands match patterns, others don't

**What Happens**:
- Valid entities created automatically
- Invalid commands skipped
- Logged in "skipped_devices" list

**Example Log**:
```
📊 Migrated: 12 entities
⚠️  Skipped: 3 devices (no valid entities)
```

**Solution**: Manually create entities for skipped devices via web interface

### Case 2: Multiple Broadlink Devices

**Situation**: 3+ Broadlink devices, each with commands

**What Happens**:
- All devices scanned
- Commands associated with correct Broadlink
- Areas assigned per Broadlink location

**Example**:
```
Kitchen Broadlink → 5 entities (area: Kitchen)
Bedroom Broadlink → 8 entities (area: Bedroom)
Office Broadlink → 3 entities (area: Office)
```

### Case 3: Hundreds of Commands

**Situation**: Power user with 100+ learned commands

**What Happens**:
- All commands processed
- Pattern matching applied
- Valid entities created
- May take 30-60 seconds

**Performance**:
- 100 commands: ~30 seconds
- 200 commands: ~60 seconds
- 500 commands: ~2 minutes

### Case 4: Reinstalling BL Manager

**Situation**: Uninstalled and reinstalling

**What Happens**:
- If metadata still exists → Scenario 2 (preserved)
- If metadata deleted → Scenario 3 (re-migration)

**Recommendation**: Backup `/config/broadlink_manager/metadata.json` before uninstalling

---

## Troubleshooting

### "No entities created during migration"

**Possible Causes**:
1. Command names don't match patterns
2. Incomplete command sets (e.g., only `fan_on` without `fan_off`)
3. Storage files corrupted

**Solutions**:
- Check command naming conventions
- Ensure complete command sets
- Manually create entities via web interface

### "Wrong area assigned"

**Cause**: Initial area comes from Broadlink device location

**Solution**: Edit metadata to update `area` field to actual device location

### "Want to re-run migration"

**Situation**: Migration ran but want to redo it

**Solution**: Use force migration API
```bash
POST /api/migration/force
{
  "overwrite": true
}
```

---

## API Reference

### Check Current Scenario

```bash
GET /api/migration/status
```

**Response**:
```json
{
  "has_metadata": false,
  "entity_count": 0,
  "migration_performed": false,
  "migration_info": null
}
```

### Trigger Migration Manually

```bash
POST /api/migration/check
```

### Force Re-Migration

```bash
POST /api/migration/force
{
  "overwrite": false  // true = replace all, false = add new only
}
```

---

## Best Practices

### For First-Time Users
1. Learn commands with descriptive names
2. Follow naming conventions (see pattern guide)
3. Use auto-detection feature
4. Test entities before generating YAML

### For Existing BL Manager Users
1. Backup metadata before major changes
2. Use version control for configuration
3. Document custom configurations
4. Test after updates

### For Existing Broadlink Users
1. Review migrated entities carefully
2. Adjust areas to match reality
3. Verify Broadlink device assignments
4. Test all entities before relying on them
5. Keep original commands as backup

---

## Support

If you encounter issues:

1. **Check Logs**: Look for scenario detection and migration results
2. **Verify Files**: Check `/config/.storage/broadlink_remote_*_codes` exist
3. **Review Metadata**: Check `/config/broadlink_manager/metadata.json`
4. **Check API**: Use `/api/migration/status` endpoint
5. **Report Issues**: Include logs, scenario type, and command count

---

## Summary

Broadlink Manager's intelligent startup system ensures a smooth experience for all users:

- **First-timers** get a welcoming introduction
- **Existing users** have their configuration protected
- **Broadlink veterans** get instant migration

No matter your situation, the system adapts to your needs automatically! 🎉
