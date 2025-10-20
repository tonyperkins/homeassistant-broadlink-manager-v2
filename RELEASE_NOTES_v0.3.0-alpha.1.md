# Broadlink Manager v0.3.0-alpha.1

## 🎉 Major Release - Enhanced Diagnostics & SmartIR Fixes

This release brings significant improvements to the diagnostics system and fixes critical SmartIR profile creation bugs.

---

## ⚠️ Breaking Changes

- **Version numbering**: Switched from 2.0.x to 0.x.x to properly reflect alpha/pre-release status
- **Status**: Changed from Beta to Alpha to set proper expectations

---

## ✨ New Features

### Enhanced Diagnostics System
Added 8 new diagnostic sections for comprehensive troubleshooting:

- **Python Dependencies** - Track package versions (broadlink, flask, aiohttp, pyyaml, etc.)
- **Recent Log Entries** - Capture last 20 errors and warnings from log files
- **Home Assistant Connection** - Test connection, report HA version and WebSocket status
- **Broadlink Device Info** - List discovered devices with types and command counts
- **Environment Variables** - Safe env vars only (no secrets)
- **File System Permissions** - Check read/write access to critical paths
- **Backup File Status** - Report backup existence, size, and age
- **SmartIR Profile Statistics** - Custom profile counts and index status

**Enhanced ZIP Bundle:**
- Now includes `recent_logs.txt` with error and warning entries
- Improved markdown report with all new sections
- All data remains sanitized (no tokens, passwords, or IR/RF codes)

### SmartIR Features
- **Profile Browser** - Advanced browsing system for 4000+ device profiles
- **Code Tester** - Comprehensive testing interface for SmartIR device codes
- **Command Learning Wizard** - Enhanced step-by-step command learning interface

### Other Enhancements
- **Fan direction support** - All fan entities include direction control by default
- **Automatic config reload** - Generate Entities button reloads both Broadlink and YAML configs
- **Enhanced command sync** - Fan-specific commands properly sync to metadata
- **Unit tests** - Comprehensive tests for entity generator

---

## 🐛 Bug Fixes

### Critical Fixes
- **Fixed SmartIR device config API payload structure** - Resolved "Missing platform or device_config" error when saving profiles
  - Frontend now correctly wraps device fields in device_config object
  - Profiles now save AND add to YAML config file without "Partial Success" warnings
- **Fixed missing yaml import** in SmartIR API causing "name 'yaml' is not defined" error
- **Fixed media_player generation** - Now uses universal platform instead of unsupported template platform
- **Removed climate entity type** - template.climate platform removed from Home Assistant
- **Fixed template platform configuration** - Multiple entities now correctly grouped under single platform entry

### Other Fixes
- Fixed entity generation to include `fan_off` command in turn_off action
- Fixed command mapping to include all `fan_*` prefixed commands during metadata sync
- Fixed direction control not appearing in Mushroom Fan Card

---

## 📦 Installation

### For Home Assistant Add-on Store Users:
1. Go to Settings → Add-ons → Add-on Store
2. Click the three dots (⋮) in the top right
3. Select "Repositories"
4. Add: `https://github.com/tonyperkins/homeassistant-broadlink-manager-v2`
5. Find "Broadlink Manager v2 (Alpha)" and click Install

### For Existing Users:
Simply update the add-on from the Add-on Store. Your data and configuration will be preserved.

---

## 📚 Documentation

- [Complete Documentation](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/tree/main/docs)
- [Diagnostics Guide](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/docs/DIAGNOSTICS_ENHANCEMENTS.md)
- [SmartIR Profile Browser](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/docs/SMARTIR_PROFILE_BROWSER.md)
- [YAML Validation](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/docs/YAML_VALIDATION.md)

---

## 🙏 Acknowledgments

- **SmartIR** - Thanks to the SmartIR team for the excellent integration
- **Community** - Thanks to all users who reported issues and provided feedback

---

## ⚠️ Alpha Release Notice

This is an **alpha release**. While extensively tested, you may encounter bugs. Please report any issues on GitHub.

**Backup your data** before upgrading, especially if you have many devices configured.

---

## 🔗 Links

- [GitHub Repository](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2)
- [Report Issues](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/issues)
- [Full Changelog](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/CHANGELOG.md)
