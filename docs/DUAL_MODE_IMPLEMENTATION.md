# Dual-Mode Implementation Summary

This document summarizes the changes made to support both Supervisor add-on and standalone Docker modes in a single codebase.

## Implementation Overview

The Broadlink Manager now supports two deployment modes:
1. **Supervisor Add-on Mode** - For Home Assistant OS/Supervised (existing functionality)
2. **Standalone Docker Mode** - For Home Assistant Container/Docker installations (new)

## Changes Made

### Core Files Modified

#### 1. **app/config_loader.py** (NEW)
- Central configuration abstraction layer
- Auto-detects environment (Supervisor vs standalone)
- Provides unified interface for:
  - Home Assistant URL
  - Authentication token
  - Config paths
  - Application options

**Key Methods:**
- `get_ha_url()` - Returns `http://supervisor/core` or user-configured URL
- `get_ha_token()` - Returns `SUPERVISOR_TOKEN` or `HA_TOKEN`
- `load_options()` - Loads from `/data/options.json` or environment variables
- `validate_configuration()` - Ensures required config is present

#### 2. **app/main.py** (MODIFIED)
- Removed hardcoded config loading
- Now uses `ConfigLoader` for all configuration
- Added configuration validation on startup
- Logs environment mode and connection details

**Changes:**
- Removed `_load_config()` method (replaced by ConfigLoader)
- Added ConfigLoader initialization
- Added validation check that exits on failure
- Enhanced startup logging

#### 3. **app/web_server.py** (MODIFIED)
- Accepts optional `ConfigLoader` instance
- Uses ConfigLoader for HA URL, token, and paths
- Logs mode on initialization

**Changes:**
- Added `config_loader` parameter to `__init__`
- Replaced hardcoded values with ConfigLoader calls
- Added mode logging

#### 4. **app/area_manager.py** (NO CHANGES NEEDED)
- Already accepts configurable HA URL in constructor
- Already compatible with both modes

### Deployment Files Created

#### 5. **run-standalone.sh** (NEW)
- Startup script for standalone Docker mode
- Validates required environment variables
- Provides helpful error messages
- No dependency on `bashio`

#### 6. **Dockerfile.standalone** (NEW)
- Docker image for standalone deployment
- Based on Python Alpine
- No Home Assistant Supervisor dependencies
- Includes health check

#### 7. **docker-compose.yml** (NEW)
- Easy deployment configuration
- Supports both host and bridge networking
- Environment variable configuration
- Volume mount for HA config

#### 8. **.env.example** (NEW)
- Template for environment variables
- Documented configuration options
- Easy copy-and-configure setup

#### 9. **build-standalone.sh** (NEW)
- Build script for standalone Docker image
- Auto-tags with version
- Provides usage instructions

### Documentation Created

#### 10. **DOCKER.md** (NEW)
- Comprehensive standalone Docker guide
- Installation instructions
- Configuration reference
- Troubleshooting section
- Network configuration options

#### 11. **README.md** (MODIFIED)
- Added installation method selection
- Added standalone Docker quick start
- Added link to DOCKER.md
- Updated documentation section

## How It Works

### Environment Detection

```python
# ConfigLoader automatically detects the environment
def _detect_supervisor_environment(self) -> bool:
    return os.environ.get('SUPERVISOR_TOKEN') is not None
```

### Configuration Loading

**Supervisor Mode:**
```
SUPERVISOR_TOKEN → Authentication
/data/options.json → Configuration
http://supervisor/core → HA URL
```

**Standalone Mode:**
```
HA_TOKEN → Authentication
Environment variables → Configuration
HA_URL env var → HA URL
```

### Backward Compatibility

✅ **Existing add-on installations continue to work unchanged**
- No configuration changes required
- Same behavior as before
- Auto-detects Supervisor environment

## Testing Checklist

### Supervisor Add-on Mode
- [ ] Install as add-on in HA OS/Supervised
- [ ] Verify auto-detection logs "Running in supervisor mode"
- [ ] Verify web interface loads
- [ ] Verify device discovery works
- [ ] Verify command learning works
- [ ] Verify entity generation works

### Standalone Docker Mode
- [ ] Build standalone image: `bash build-standalone.sh`
- [ ] Configure `.env` file with HA_URL and HA_TOKEN
- [ ] Update docker-compose.yml volume mount
- [ ] Start container: `docker-compose up -d`
- [ ] Verify logs show "Running in standalone mode"
- [ ] Verify web interface accessible at port 8099
- [ ] Verify connection to Home Assistant
- [ ] Verify device discovery works
- [ ] Verify command learning works
- [ ] Verify entity generation works

### Configuration Validation
- [ ] Test with missing HA_TOKEN (should fail with clear error)
- [ ] Test with invalid HA_URL (should fail gracefully)
- [ ] Test with missing config path (should fail with clear error)
- [ ] Test with valid configuration (should start successfully)

## Environment Variables Reference

### Supervisor Mode (Auto-detected)
- `SUPERVISOR_TOKEN` - Provided by Supervisor
- `/data/options.json` - Configuration file

### Standalone Mode (User-configured)
- `HA_URL` - Home Assistant URL (required)
- `HA_TOKEN` - Long-lived access token (required)
- `LOG_LEVEL` - Logging level (optional, default: info)
- `WEB_PORT` - Web interface port (optional, default: 8099)
- `AUTO_DISCOVER` - Auto-discover devices (optional, default: true)
- `CONFIG_PATH` - HA config directory (optional, default: /config)

## File Structure

```
broadlink_manager_addon/
├── app/
│   ├── config_loader.py          # NEW - Configuration abstraction
│   ├── main.py                   # MODIFIED - Uses ConfigLoader
│   ├── web_server.py             # MODIFIED - Uses ConfigLoader
│   ├── area_manager.py           # No changes needed
│   └── [other files unchanged]
│
├── Dockerfile                    # Existing - Supervisor add-on
├── Dockerfile.standalone         # NEW - Standalone Docker
├── run.sh                        # Existing - Supervisor startup
├── run-standalone.sh             # NEW - Standalone startup
├── build-standalone.sh           # NEW - Build script
├── docker-compose.yml            # NEW - Docker Compose config
├── .env.example                  # NEW - Environment template
├── DOCKER.md                     # NEW - Docker guide
├── README.md                     # MODIFIED - Added Docker section
└── DUAL_MODE_IMPLEMENTATION.md   # This file
```

## Code Complexity Added

**Total new code:** ~500 lines
- ConfigLoader: ~250 lines
- Modifications to existing files: ~50 lines
- Documentation: ~200 lines

**Complexity level:** Low
- Single abstraction point (ConfigLoader)
- No changes to business logic
- Backward compatible
- Well-documented

## Migration Path

### For Existing Add-on Users
**No action required** - Everything continues to work as before.

### For New Docker Users
1. Clone repository
2. Copy `.env.example` to `.env`
3. Configure HA_URL and HA_TOKEN
4. Update docker-compose.yml volume mount
5. Run `docker-compose up -d`

## Next Steps

1. **Test both modes** thoroughly
2. **Update version** in config.yaml
3. **Update CHANGELOG.md** with new features
4. **Create GitHub release** with both deployment options
5. **Update repository.yaml** if needed
6. **Consider CI/CD** for building standalone images

## Support Matrix

| Feature | Supervisor Add-on | Standalone Docker |
|---------|-------------------|-------------------|
| Auto-detection | ✅ | ✅ |
| Device discovery | ✅ | ✅ |
| Command learning | ✅ | ✅ |
| Entity generation | ✅ | ✅ |
| Area management | ✅ | ✅ |
| Web interface | ✅ | ✅ |
| Ingress support | ✅ | ❌ (not applicable) |
| Auto-updates | ✅ | ❌ (manual) |
| One-click install | ✅ | ❌ (manual setup) |

## Known Limitations

### Standalone Mode
- No Ingress support (not applicable outside Supervisor)
- Manual token management required
- Manual updates required
- Requires Docker knowledge

### Both Modes
- Requires Broadlink integration in Home Assistant
- Network access to Broadlink devices required

## Troubleshooting

### "Running in supervisor mode" but should be standalone
- Check that `SUPERVISOR_TOKEN` is not set in environment
- Verify you're using `run-standalone.sh` not `run.sh`

### "Running in standalone mode" but should be supervisor
- Verify `SUPERVISOR_TOKEN` is set by Supervisor
- Check add-on is running in Supervisor environment

### Configuration validation fails
- Check logs for specific error message
- Verify HA_TOKEN is set correctly
- Verify HA_URL is accessible
- Verify config path exists and is mounted

## Success Criteria

✅ Single codebase supports both modes
✅ Automatic environment detection
✅ Backward compatible with existing add-on
✅ Clear documentation for both modes
✅ Minimal code complexity added
✅ Easy to test and maintain

---

**Implementation Date:** 2025-10-09
**Status:** Complete and ready for testing
