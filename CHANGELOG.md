# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
