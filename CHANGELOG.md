# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.0-alpha.1] - 2025-10-18

### Changed
- **Version numbering**: Switched from 2.0.x to 0.x.x to properly reflect alpha/pre-release status
- **Status**: Changed from Beta to Alpha to set proper expectations

### Added
- **SmartIR Profile Browser**: Advanced browsing and management system for SmartIR device profiles
  - Browse 4000+ device profiles from SmartIR Code Aggregator
  - Filter by platform, manufacturer, model, and source
  - Pagination support (50 profiles per page)
  - Clone index profiles to custom codes for customization
  - Search across all platforms
  - Lazy loading for performance
- **SmartIR Code Tester**: Comprehensive testing interface for SmartIR device codes
  - Test individual commands with visual feedback
  - Climate control testing (temperature, modes, fan speeds)
  - Real-time command execution via Broadlink devices
  - Test results tracking and validation
- **Command Learning Wizard**: Enhanced command learning interface
  - Step-by-step wizard for learning IR/RF commands
  - Visual progress tracking
  - Command type detection (IR/RF)
  - Test learned commands immediately
- **Git Workflow Documentation**: Added comprehensive Git workflow guide (`docs/GIT_WORKFLOW.md`)
  - Feature branch strategy
  - Release branch process
  - Version tagging guidelines
  - Common commands reference
- **Fan direction support**: All fan entities now include direction control by default
- **Automatic config reload**: Generate Entities button now automatically reloads both Broadlink and YAML configurations
- **Enhanced command sync**: Fan-specific commands (`fan_off`, `fan_reverse`, etc.) now properly sync to metadata
- **Unit tests**: Added comprehensive tests for entity generator to prevent regressions

### Fixed
- **CRITICAL**: Fixed media_player generation to use universal platform instead of unsupported template platform
  - Resolves "ModuleNotFoundError: No module named 'homeassistant.components.template.media_player'" error
  - Media players now generate as `platform: universal` with companion switches for power control
  - Supports volume control, play/pause, source selection, and other media commands
- **CRITICAL**: Removed climate entity type - template.climate platform removed from Home Assistant
  - Climate entity type no longer available in UI
  - Users should use SmartIR custom integration for AC/Heater control
  - Added documentation link to SmartIR in the UI
- **CRITICAL**: Fixed template platform configuration generating multiple platform entries instead of grouping entities together
  - Multiple entities of same type now correctly grouped under single `platform: template` entry
  - Applies to light, fan, switch, and cover entity types
- Fixed entity generation to include `fan_off` command in turn_off action instead of lowest speed
- Fixed entity generation to include `fan_off` in set_percentage when percentage is 0
- Fixed command mapping to include all `fan_*` prefixed commands during metadata sync
- Fixed direction control not appearing in Mushroom Fan Card due to missing remote command in set_direction action

### Changed
- Fan entities always include direction support (even if no reverse command learned yet)
- Entity generation now calls both `reload_broadlink_config` and `reload_core_config` for complete reload
- Entity generator now groups all entities of the same type under a single platform entry (correct HA syntax)

## [1.10.24] - 2025-10-09

### Fixed
- Fixed washed out header title "Broadlink" - now uses primary text color
- Fixed washed out command names - now uses primary text color
- Both now properly adapt to light/dark mode

## [1.10.23] - 2025-10-09

### Fixed
- Improved text contrast in light mode
- Secondary text color changed from `#5f6368` to `#424242` (darker, more readable)
- Section headers now use theme variable and are bolder (600 weight)

## [1.10.22] - 2025-10-09

### Fixed
- **Removed ALL auto-detection** - manual toggle only, no exceptions
- **Fixed all hardcoded dark colors** in light mode:
  - Device card backgrounds now white
  - Command group backgrounds now light
  - Hover effects now subtle light gray
  - Device icons now use primary color
  - All text colors use theme variables
  - Log area uses theme colors
- Default is light mode, persists in localStorage
- No automatic theme switching whatsoever

## [1.10.21] - 2025-10-09

### Fixed
- Improved light mode colors for better contrast and readability
- Added one-time HA theme detection on initial load (no polling/watching)
- If no manual preference saved, detects if HA is in dark/light mode and matches it
- Once user manually toggles, their preference is saved and used instead
- Better color scheme: lighter backgrounds, darker text for light mode

## [1.10.20] - 2025-10-09

### Fixed
- **Completely removed all HA theme auto-detection** - was causing constant switching
- **Simplified to manual toggle only** - exactly like Everything Presence add-on
- Removed theme watcher that was overriding manual selection
- Removed parent window theme detection
- Removed API theme polling
- Default is now light mode, toggle to dark mode manually
- Theme preference persists in localStorage

## [1.10.19] - 2025-10-09

### Added
- **Manual theme toggle button** in header (🌙/☀️)
- Three-way toggle: Auto (follows HA) → Light → Dark → Auto
- Theme preference saved in localStorage
- Visual feedback with icon changes (🌙 for dark, ☀️ for light)
- Manual override disables automatic HA theme detection

## [1.10.18] - 2025-10-09

### Fixed
- Changed default theme to proper light theme with good contrast
- Added CSS `@media (prefers-color-scheme: dark)` for automatic dark mode
- Improved theme detection logic with better validation
- Light mode now has appropriate colors (light backgrounds, dark text)
- Dark mode automatically applies based on system/HA preference
- Removed non-functional inline script that was causing CORS issues

## [1.10.17] - 2025-10-09

### Fixed
- Eliminated theme flash on page load by detecting HA theme in `<head>` before rendering
- Theme now applies immediately, preventing light-to-dark flash
- Inline script runs synchronously before CSS loads

## [1.10.16] - 2025-10-09

### Fixed
- Implemented client-side theme detection from parent window (ingress mode)
- Add-on now reads HA theme colors directly from parent window's CSS variables
- Works around missing theme API endpoints in some HA versions
- Properly inherits all HA theme colors including dark/light mode detection

## [1.10.15] - 2025-10-09

### Fixed
- Added detailed logging for theme API endpoint debugging
- Try multiple API endpoints (/api/frontend/themes and /api/themes) for theme detection
- Better error handling and reporting when theme APIs fail

## [1.10.14] - 2025-10-09

### Fixed
- Enhanced theme detection to use Home Assistant API for better theme support
- Added comprehensive logging for theme detection debugging
- Improved fallback to storage files when API is unavailable
- Better detection of dark vs light themes

### Added
- **Entity Auto-Generation Feature**: Automatically create Home Assistant entities from learned commands
  - Storage manager for entity metadata in `/config/broadlink_manager/`
  - Entity detector with pattern matching for lights, fans, switches, and media players
  - YAML entity generator for template lights, fans, and switches
  - Auto-generated helper entities (input_boolean, input_select)
  - REST API endpoints for entity management:
    - `GET /api/entities` - List all configured entities
    - `POST /api/entities` - Save/update entity configuration
    - `DELETE /api/entities/<id>` - Delete entity
    - `POST /api/entities/detect` - Auto-detect entities from commands
    - `POST /api/entities/generate` - Generate YAML files
    - `GET /api/entities/types` - Get supported entity types
  - Automatic README generation in `/config/broadlink_manager/`
  - Command naming convention detection (e.g., `light_on`, `fan_speed_1`)

### Changed
- Updated documentation with entity auto-generation usage guide
- Added entity management section to README

## [1.0.0] - 2025-09-22

### Added
- Initial release of Broadlink Manager Add-on
- Automatic Broadlink device discovery
- Device configuration and management
- Home Assistant integration
- Configurable logging levels
- Configurable discovery and device timeouts
- Multi-architecture support (armhf, armv7, aarch64, amd64, i386)

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

[Unreleased]: https://github.com/tonyperkins/homeassistant-broadlink-manager/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/tonyperkins/homeassistant-broadlink-manager/releases/tag/v1.0.0
