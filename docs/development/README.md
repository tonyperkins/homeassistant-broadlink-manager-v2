# Development Documentation

**Last Updated:** January 2025

This folder contains **development-focused documentation** for contributors and maintainers. End-user documentation is in the parent [docs](../) folder.

---

## 📋 Table of Contents

- [Development Workflow](#development-workflow)
- [Architecture & Design](#architecture--design)
- [Testing](#testing)
- [Implementation Details](#implementation-details)
- [Project Management](#project-management)
- [Archived Documentation](#archived-documentation)

---

## Development Workflow

### Setup & Process
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development workflow, branch strategy, testing workflows
- **[RELEASE_PROCESS.md](RELEASE_PROCESS.md)** - Release workflow and version management

---

## Architecture & Design

### System Architecture
- **[ARCHITECTURE_ANALYSIS.md](ARCHITECTURE_ANALYSIS.md)** - Deep analysis of decoupling from Broadlink storage
- **[REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md)** - Long-term refactoring plans and technical debt

### Implementation Guides
- **[DIRECT_LEARNING_IMPLEMENTATION.md](DIRECT_LEARNING_IMPLEMENTATION.md)** - Direct command learning implementation
- **[ENTITY_GENERATION.md](ENTITY_GENERATION.md)** - Entity generation system details
- **[V1_STYLE_ENTITY_GENERATION.md](V1_STYLE_ENTITY_GENERATION.md)** - v1 compatibility entity generation
- **[AUTO_MIGRATION.md](AUTO_MIGRATION.md)** - Automatic migration system implementation

---

## Testing

### Testing Guides
- **[TESTING.md](TESTING.md)** - Comprehensive testing guide (unit, integration, e2e)
- **[TESTING_QUICKSTART.md](TESTING_QUICKSTART.md)** - Quick start guide for running tests
- **[E2E_TESTING.md](E2E_TESTING.md)** - End-to-end browser testing with Playwright

### Test Results
- **[RAW_BASE64_TEST_RESULTS.md](RAW_BASE64_TEST_RESULTS.md)** - Base64 command testing results

---

## Implementation Details

### Completed Features
- **[PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)** - Phase 1 backend foundation completion
- **[PHASE2_COMPLETE.md](PHASE2_COMPLETE.md)** - Phase 2 completion summary

### Bug Fixes & Issues
- **[MIGRATION_FIX.md](MIGRATION_FIX.md)** - Migration bug fix documentation
- **[ISSUE_LIST_VIEW_COMMANDS.md](ISSUE_LIST_VIEW_COMMANDS.md)** - List view commands issue tracking

---

## Project Management

### Updates & Communication
- **[REDDIT_UPDATES.md](REDDIT_UPDATES.md)** - Reddit community update tracking
- **[SCREENSHOT_REFERENCE.md](SCREENSHOT_REFERENCE.md)** - Screenshot documentation reference

---

## Archived Documentation

Historical development documentation has been moved to the **[archive/](archive/)** folder. This includes:
- API implementation milestones
- Component creation summaries
- SmartIR implementation plans
- Historical bug fixes
- Phase completion summaries

See **[archive/README.md](archive/README.md)** for a complete list of archived documents.

---

## User-Facing Documentation

For **end-user documentation** (installation, usage, troubleshooting, API reference), see the main **[docs](../)** folder:

- Installation & Setup
- User Guides
- API Reference
- Troubleshooting
- Architecture Overview (high-level)

---

## Document Lifecycle

### Active Documents
Documents currently being used for ongoing development work. These should be kept up-to-date as implementation progresses.

### Completion Summaries
Historical records of completed work (PHASE*_COMPLETE.md). These are kept for reference but are not actively updated.

### Archived Documents
When a development phase is complete and the document is no longer needed for active reference, it should be moved to the `archive/` subfolder.

---

## Contributing

When creating new development documents:

1. **Filename**: Use descriptive, ALL_CAPS filenames with underscores
2. **Structure**: Include overview, goals, implementation phases
3. **Metadata**: Add status, date, and version information
4. **Links**: Link to related documents
5. **Update**: Update this README with a reference to the new document
6. **Location**: Place in appropriate section above

---

## Quick Links

### User Documentation (../docs/)
- [Installation Scenarios](../INSTALLATION_SCENARIOS.md)
- [Troubleshooting](../TROUBLESHOOTING.md)
- [API Reference](../API.md)
- [Architecture Overview](../ARCHITECTURE.md)

### Development Documentation (this folder)
- [Development Workflow](DEVELOPMENT.md)
- [Testing Guide](TESTING.md)
- [Architecture Analysis](ARCHITECTURE_ANALYSIS.md)
- [Refactoring Roadmap](REFACTORING_ROADMAP.md)
