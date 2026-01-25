# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
## [0.3.0-beta.3] - 2026-01-25

### Fixed
- Simplified CI workflow, fixed GitHub Actions tests, updated release documentation


## [0.3.0-alpha.34] - 2026-01-19

### Fixed
- SmartIR command merging and device edit support


## [0.3.0-alpha.33] - 2026-01-12

### Fixed
- Fixed SmartIR profile editing - commands now merge instead of overwrite, duplicate unique_id errors resolved


## [0.3.0-alpha.32] - 2026-01-12

### Fixed
- Fixed SmartIR media_player profile creation - commands now included in JSON file for all platforms (media_player, fan, light)



## [0.3.0-alpha.31] - 2025-12-26

### Fixed
- **SmartIR Command Learning** - Fixed SmartIR profile polling and command learning workflow
  - Fixed incorrect SmartIR path in polling (removed `..` directory traversal)
  - Added SmartIR metadata support to command learning system
  - Implemented profile scanning fallback to detect SmartIR devices without devices.json entries
  - Polling now correctly updates SmartIR profile JSON files when commands are learned
  - Fixed issue where learned commands stayed "pending" in SmartIR profiles
  - Removed duplicate device entries from climate.yaml to prevent unique_id conflicts

### Added
- Comprehensive command learning architecture documentation: `docs/development/COMMAND_LEARNING_ARCHITECTURE.md`
  - Explains API flow, storage file polling, and SmartIR vs Broadlink native handling
  - Documents the 3-60 second storage write lag and polling mechanism
  - Includes debugging guide with log examples and troubleshooting tips

### Changed
- `schedule_command_poll()` now accepts optional `smartir_metadata` parameter
- Command learning endpoint detects SmartIR devices via profile scanning when not in devices.json
- Polling thread handles both 5-element and 6-element tuple formats for backward compatibility

## [0.3.0-alpha.30] - 2024-12-23

### Fixed
- **Entity Generation: Brightness Range Conversion** - Fixed brightness values incorrectly mapped between Home Assistant's 0-255 scale and helper's 0-100 percentage scale
  - Added bidirectional conversion: helper 0-100% ↔ HA 0-255 brightness
  - Fixes "can't go above 100" error when setting brightness above 50%
  - Fixes 100% brightness displaying as "255%" instead of "100%"
  - Helper now correctly stores and displays 0-100 percentage values
  
- **Entity Generation: Custom Commands Support** - Custom commands with non-standard names now automatically generate as button entities
  - Detects commands that don't match standard patterns (turn_on, brightness_up, etc.)
  - Creates template button entities for each custom command (e.g., warm_tone, cool_tone, reading_mode)
  - Auto-generates friendly names (e.g., "Living Room Light Warm Tone")
  - Buttons appear alongside main entity in Home Assistant
  - Standard commands remain integrated in main entity (not duplicated as buttons)

### Added
- Complete entity generation fixes documentation: `docs/ENTITY_GENERATION_FIXES.md`
- Comprehensive testing guide: `docs/TESTING_ENTITY_FIXES.md`
- New method `_generate_custom_command_buttons()` in entity generator

### Changed
- Entity generator now includes `button` type in template entities
- Light entities now properly convert brightness between HA and helper scales

## [0.3.0-alpha.29] - 2024-12-10

### Fixed
- **CRITICAL: Modern Template Syntax** - Updated entity generator to use Home Assistant's modern template syntax (HA 2021.4+)
  - Fixed all template field names to match modern syntax standards
  - Changed `value_template:` → `state:` (all entity types)
  - Changed `level_template:` → `level:` (light brightness)
  - Changed `temperature_template:` → `temperature:` (light color temp)
  - Changed `percentage_template:` → `percentage:` (fan speed)
  - Changed `direction_template:` → `direction:` (fan direction)
  - Changed `position_template:` → `position:` (cover position)
  - Changed `friendly_name:` → `name:` (all entity types)
  - Updated `_build_entities_yaml()` to generate `template:` structure instead of `platform: template`
  - Updated setup instructions to use `template: !include` instead of individual platform includes
  - **Prevents Home Assistant deprecation warnings and ensures compatibility with HA 2026.6+**
  - **Minimum HA version now: 2021.4 or newer**

### Added
- Comprehensive migration guide: `docs/TEMPLATE_SYNTAX_MIGRATION.md`
- Complete field name reference: `docs/development/TEMPLATE_FIELD_NAMES.md`
- Updated README.md with HA 2021.4+ requirement in prerequisites

### Changed
- Entity generation now produces modern `template:` YAML structure
- Configuration.yaml setup simplified to single `template:` include line
- All generated entities now use modern syntax by default

## [0.3.0-alpha.25] - 2025-11-18

### Fixed
- Fix entity type detection for speed_* commands - fresh installs now correctly detect fans


## [0.3.0-alpha.24] - 2025-11-17

### Fixed
- Fix medium speed not working - correctly handle non-sequential speed numbering from named speeds


## [0.3.0-alpha.23] - 2025-11-17

### Fixed
- Fix fan auto-on behavior - setting speed now automatically turns fan on/off, matching SmartIR


## [0.3.0-alpha.22] - 2025-11-17

### Fixed
- Fix fan helper generation for named speeds - input_select now includes all speed options


## [0.3.0-alpha.21] - 2025-11-16

### Fixed
- Fix RF fan entity generation with custom speed names (lowMedium, mediumHigh)



## [0.3.0-alpha.20] - 2025-11-15

### Fixed
- **SmartIR Profile Editing**: Fixed commands staying "pending" instead of saving actual IR/RF codes
  - Properly leverages backend polling mechanism (polls every 3s with 60s timeout)
  - `fetchLearnedCommandsForEdit()` now called at preview step to ensure codes are ready before save
  - Backend has fallback search across all device names to handle storage write lag
- **SmartIR "Off" Commands**: Fixed recognition of standalone "off" commands in existing profiles
  - Detects "off" commands that exist in JSON but not in `operationModes` array
  - Adds "Power Off (standalone command)" card in wizard for editing
  - Maintains backward compatibility with both command structures
- Documentation: Created comprehensive guide at `docs/development/SMARTIR_PROFILE_EDITING_FIXES.md`

## [0.3.0-alpha.11] - 2025-11-14

### Fixed
- Fix: Bind to 127.0.0.1 in supervisor mode to avoid permission denied errors


## [0.3.0-alpha.10] - 2025-11-14

### Fixed
- Add custom_codes directory support for SmartIR profiles - profiles now persist through HACS updates


## [0.3.0-alpha.9] - 2025-11-13

### Fixed
- Fix: Use pre-built GHCR images for faster updates


## [0.3.0-alpha.8] - 2025-11-13

### Fixed
- Docker fixes: standalone mode config defaults and Python 3.13 compatibility


## [0.3.0-alpha.7] - 2025-11-13

### Fixed
- Code quality: Fix all flake8 linting errors



## [0.3.0-alpha.6] - 2025-11-12

### Added
- **SmartIR Climate Profiles**: Added preset modes support for climate entities
  - New "Preset Modes" section in climate profile form with 6 common presets (none, eco, boost, sleep, away, comfort)
  - Command generation includes preset mode combinations
  - Generated JSON profiles include `presetModes` array
  - Command keys format: `cool_24_auto_eco` (includes preset at end)
  - Command labels show preset in brackets: `COOL 24°C auto [eco]`
  - Automatic inference of preset modes when loading existing profiles
  - Command count calculations updated to include preset mode multiplier
  - Fully compatible with SmartIR format specification

## [0.3.0-alpha.5] - 2025-11-06

### Fixed
- Fix area sync 404 error for newly created devices



## [0.3.0-alpha.4] - 2025-11-04

### Fixed
- **Entity Generator**: Fan entities with named speed commands (e.g., `speed_low`, `speed_medium`, `speed_high`) are now properly detected
  - Previously only numeric speed commands (e.g., `speed_1`, `speed_2`) were recognized
  - Added mapping system: `low→1`, `medium→2`, `high→3`
  - Supports both `speed_*` and `fan_speed_*` prefixes
  - Improved warning messages now show which commands were found for easier debugging
  - Fully backward compatible with existing numeric speed commands

### Changed
- **Test Suite**: Deprecated `test_command_storage_format.py` (StorageManager removed in favor of DeviceManager)
- **Documentation**: Added comprehensive bug fix documentation in `docs/development/BUG_FIX_ENTITY_GENERATOR_SPEED_COMMANDS.md`

### Added
- **Manual Test**: New speed command detection test suite (`tests/manual/test_speed_command_detection.py`)
  - Tests named speed commands
  - Tests numeric speed commands
  - Tests mixed speed configurations

## [0.3.0-alpha.4] - 2025-10-26

### Fixed
- **CRITICAL**: Fixed command learning polling system not detecting learned commands
  - Device IDs no longer include area prefix (area is metadata only)
  - Added `device` field to Broadlink devices for proper storage lookups
  - Fixed polling to use correct device name when checking Broadlink storage
  - Added automatic migration on startup to populate `device` field for existing devices
  - Commands now properly detected and updated from "pending" to actual code data

### Changed
- Device ID generation simplified - now uses only normalized device name
- Area field is now purely metadata and doesn't affect device identification
- Broadlink storage lookups use new `device` field instead of device_id

## [0.3.0-alpha.3] - 2025-10-26

### ⚠️ BREAKING CHANGES
- **Independent Command Storage**: Commands are now stored in `devices.json` instead of relying solely on Broadlink integration storage
  - Existing commands will be automatically migrated on first run
  - Provides better reliability and independence from integration storage
  - **Note**: If you downgrade to alpha.2 or earlier, you may need to re-learn commands

### Added
- **Independent Command Storage System**: Commands stored directly in app's `devices.json`
  - Three storage modes: `manager_only`, `integration_only`, `both` (default)
  - Background polling automatically fetches command codes from integration storage
  - Commands persist even if integration storage is cleared
  - Automatic migration from integration-only storage on startup
- **Manual Refresh Button**: Added refresh button (🔄) in command learner dialog
  - Manually triggers polling check for pending commands
  - Useful if automatic file watching misses updates
- **Improved File Watching**: Reduced debounce from 1s to 0.1s for faster command detection
- **API Endpoint**: `POST /api/commands/check-pending` to manually trigger polling

### Changed
- **Command Learning Flow**: Commands now saved to `devices.json` with "pending" status
  - Background thread polls for actual command codes
  - Updates automatically when codes are available (typically 3-5 seconds)
  - Timeout after 60 seconds with error status
- **Storage Architecture**: Moved from integration-dependent to app-managed storage
  - Better reliability and control
  - Reduced dependency on Home Assistant storage timing
  - Optimistic UI updates for better UX

### Fixed
- **Polling Reliability**: File watcher now more responsive to rapid command learning
- **Command Persistence**: Commands no longer lost if integration storage is cleared
- **Storage Lag Issues**: Background polling handles HA storage write delays

### Technical Details
- Background polling thread monitors pending commands
- Automatic code fetching from integration storage
- File watcher triggers on `devices.json` changes
- Configurable save destinations per command

## [0.3.0-alpha.2] - 2025-10-20

### Added
- **Collapsible Filters**: Filter sections now collapse/expand with icon button
  - Filter icon button with active filter count badge
  - Filters collapsed by default for cleaner interface
  - Badge shows number of active filters
- **Auto-Expand on Settings**: Clicking settings cog automatically expands section if collapsed
- **Mobile Improvements**: Enhanced mobile layout for device discovery components
  - Discovery banner stacks vertically on mobile
  - Full-width buttons for better touch targets
  - Modal improvements with proper spacing
- **Release Process Documentation**: Added comprehensive release process guide and version bump script
  - `docs/RELEASE_PROCESS.md` - Complete release workflow
  - `scripts/bump_version.py` - Automated version bumping tool

### Changed
- **Filter UI Redesign**: Replaced filter header with compact icon button next to search
  - Filter icon positioned left of search box
  - Search box takes full width with icon inside
  - Cleaner, more modern layout matching Home Assistant design patterns
- **Welcome Banner**: Hidden on mobile devices, dismissable on desktop
  - Dismiss button in top-right corner
  - State persists in localStorage
- **Mobile Headers**: Icon and text now properly aligned side-by-side
  - Fixed text alignment in search boxes
  - Improved header layout on small screens

### Fixed
- Search box text alignment with icon
- Mobile header layout (icon and text side-by-side)
- UTF-8 encoding issues in version bump script for Windows compatibility



## [0.3.0-alpha.1] - 2025-10-19

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
- **Enhanced Diagnostics System**: Added 8 new diagnostic sections for better troubleshooting
  - Python dependencies tracking with version numbers
  - Recent log entries (last 20 errors and warnings)
  - Home Assistant connection testing with version detection
  - Broadlink device discovery information
  - Environment variables (sanitized, no secrets)
  - File system permissions checking
  - Backup file status with age tracking
  - SmartIR profile statistics
  - Enhanced ZIP bundle now includes recent_logs.txt
  - Improved markdown report with all new sections

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
- **Fixed SmartIR device config API payload structure** - "Missing platform or device_config" error when saving profiles
  - Frontend now correctly wraps device fields in device_config object
  - Profiles now save AND add to YAML config file without "Partial Success" warnings
- **Fixed missing yaml import** in SmartIR API causing "name 'yaml' is not defined" error

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
