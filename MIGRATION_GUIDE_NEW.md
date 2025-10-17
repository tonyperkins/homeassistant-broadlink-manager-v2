# Migration Guide

## Automatic Migration

**Good news!** Broadlink Manager automatically migrates your existing setup when you upgrade.

### What Gets Migrated

If you have existing Broadlink commands from the official Broadlink integration, Broadlink Manager will automatically:

- ✅ Discover all learned IR/RF commands from your Broadlink storage files
- ✅ Create device entries for each set of commands
- ✅ Detect entity types (lights, fans, switches, media players, climate)
- ✅ Assign areas based on your Broadlink device locations
- ✅ Make everything ready for entity generation

### How It Works

**On first startup**, the migration manager:

1. **Checks** if you have existing Broadlink commands
2. **Scans** your Home Assistant storage for command files
3. **Groups** commands by device (e.g., all "tv" commands together)
4. **Creates** device metadata automatically
5. **Preserves** all your learned commands

**No manual action required!** 🎉

---

## Migration API (Advanced)

For advanced users who need manual control:

### Check Migration Status

```bash
GET /api/migration/status
```

Returns current migration state and what was migrated.

### Force Re-migration

```bash
POST /api/migration/force
{
  "overwrite": false  // Set to true to replace existing devices
}
```

Use this if you want to re-run migration or if something went wrong.

---

## After Migration

Once migration completes:

1. **Review Devices**: Check the Devices page to see what was created
2. **Adjust if Needed**: Edit device names, areas, or entity types
3. **Generate Entities**: Click "Generate Entities" to create Home Assistant YAML
4. **Restart HA**: Restart Home Assistant to load your new entities

---

## Troubleshooting

### Migration didn't run

**Check**: Do you have existing Broadlink commands?
- Look in Home Assistant's `.storage` folder for `broadlink_remote_*_codes` files
- If no commands exist, there's nothing to migrate

### Devices created incorrectly

**Solution**: Delete the auto-created devices and create them manually
- The migration does its best to group commands intelligently
- Sometimes manual organization works better for your setup

### Commands missing

**Check**: Migration only migrates commands from Broadlink storage files
- Commands must be learned via the official Broadlink integration first
- Broadlink Manager doesn't create commands, it organizes existing ones

---

## What Changed in v2?

The new device-based structure provides:

- **Better Organization**: Devices group related commands together
- **Flexible Control**: One Broadlink can control devices in multiple areas
- **SmartIR Support**: Use pre-configured device profiles alongside learned commands
- **Area Management**: Proper area assignment for better Home Assistant organization

---

## Need Help?

- **Documentation**: See [README.md](README.md) for full feature guide
- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical details
- **Issues**: Report problems on GitHub with diagnostics (Settings → Copy Diagnostics)
