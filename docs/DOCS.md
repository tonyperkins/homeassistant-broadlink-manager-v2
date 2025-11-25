# Broadlink Manager Documentation Index

Complete documentation for the Broadlink Manager Home Assistant add-on.

## 📚 Documentation Overview

### Getting Started

- **[README.md](../README.md)** - Start here! Main documentation with features, installation, and usage
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Detailed deployment and installation guide
  - Local add-on repository setup
  - GitHub repository deployment
  - Manual Docker builds
  - Post-installation configuration
- **[DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md)** - Windows-specific deployment guide
  - PowerShell deployment script
  - Network share setup
  - Troubleshooting Windows issues

### User Guides

- **[Architecture Overview](ARCHITECTURE.md)** - High-level system architecture
  - Key concepts (Broadlink devices, controlled devices, areas)
  - Data model and storage
  - How the system works
  - Best practices

- **[Automation Examples](AUTOMATION_EXAMPLES.md)** - Using commands in automations and dashboards
  - Basic automation examples
  - Dashboard card configurations
  - Time-based controls
  - Temperature-based controls
  - Finding device and command names
  - Troubleshooting automation issues

- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Solutions to common problems
  - Installation issues
  - Startup problems
  - Web interface issues
  - Device discovery problems
  - Command learning issues
  - Entity generation problems
  - Performance optimization

- **[YAML Validation](YAML_VALIDATION.md)** - SmartIR YAML validation system
  - Validation rules
  - Error messages
  - CLI validation tool
  - Troubleshooting safe mode issues

- **[Customization Guide](CUSTOMIZATION.md)** - Customizing entities and behavior
  - Entity customization
  - Configuration options
  - Advanced features

- **[Installation Scenarios](INSTALLATION_SCENARIOS.md)** - Different installation options
  - Add-on installation
  - Standalone Docker
  - Development setup

### Developer Resources

- **[API Reference](API.md)** - Complete REST API documentation
  - Device management endpoints
  - Command management endpoints
  - Area management endpoints
  - Entity management endpoints
  - Storage management endpoints
  - Request/response examples

- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute to the project
  - Code of conduct
  - Development setup
  - Coding standards
  - Testing guidelines
  - Pull request process

- **[Development Documentation](development/)** - For contributors and maintainers
  - [Development Workflow](development/DEVELOPMENT.md)
  - [Testing Guide](development/TESTING.md)
  - [Architecture Analysis](development/ARCHITECTURE_ANALYSIS.md)
  - [Implementation Details](development/)
  - See [development/README.md](development/README.md) for complete index

### Project Information

- **[Changelog](../CHANGELOG.md)** - Version history and release notes
- **[LICENSE](../LICENSE)** - MIT License terms

---

## 🚀 Quick Links by Task

### I want to...

#### Install the Add-on
1. Read [README.md](../README.md) - Installation section
2. Follow [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed instructions
3. Windows users: [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md) - Windows guide
4. If issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Installation Issues

#### Learn IR/RF Commands
1. Read [README.md](../README.md) - Learning Commands section
2. If issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Command Learning Issues

#### Use Commands in Automations
1. Read [AUTOMATION_EXAMPLES.md](AUTOMATION_EXAMPLES.md) - Complete automation guide
2. Check automation examples for your use case
3. Learn dashboard card configurations
4. If issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Automation troubleshooting

#### Auto-Generate Entities
1. Read [README.md](../README.md) - Auto-Generating Entities section
2. Check [API.md](API.md) - Entity Management endpoints
3. If issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Entity Generation Issues
4. Advanced: [development/ENTITY_GENERATION.md](development/ENTITY_GENERATION.md) - Technical implementation

#### Use the API
1. Read [API.md](API.md) - Complete API reference
2. Check examples in [development/](development/) folder

#### Contribute Code
1. Read [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
2. Check [development/DEVELOPMENT.md](development/DEVELOPMENT.md) - Development workflow
3. Check [development/TESTING.md](development/TESTING.md) - Testing guide
4. Review [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
5. See [development/README.md](development/README.md) - Complete development docs

#### Fix a Problem
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
2. Enable debug logging (see Troubleshooting guide)
3. Open an issue on GitHub with logs

---

## 📖 Documentation by Audience

### For End Users

**Essential Reading:**
- [README.md](../README.md) - Features and basic usage
- [DEPLOYMENT.md](DEPLOYMENT.md) - Installation
- [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md) - Windows deployment
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problem solving

**Optional Reading:**
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [API.md](API.md) - API usage for automation
- [DOCKER.md](DOCKER.md) - Standalone Docker deployment
- [YAML_VALIDATION.md](YAML_VALIDATION.md) - SmartIR YAML validation
- [CUSTOMIZATION.md](CUSTOMIZATION.md) - Entity customization

### For Developers

**Essential Reading:**
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development setup and standards
- [development/DEVELOPMENT.md](development/DEVELOPMENT.md) - Development workflow
- [development/TESTING.md](development/TESTING.md) - Testing framework and guidelines
- [ARCHITECTURE.md](ARCHITECTURE.md) - High-level system architecture
- [API.md](API.md) - API reference

**Optional Reading:**
- [development/ARCHITECTURE_ANALYSIS.md](development/ARCHITECTURE_ANALYSIS.md) - Deep architecture analysis
- [development/E2E_TESTING.md](development/E2E_TESTING.md) - Browser automation testing
- [development/README.md](development/README.md) - Complete development docs index
- [DEPLOYMENT.md](DEPLOYMENT.md) - Build and deployment process
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and debugging

### For System Administrators

**Essential Reading:**
- [DEPLOYMENT.md](DEPLOYMENT.md) - Installation and configuration
- [DOCKER.md](DOCKER.md) - Docker deployment
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - System issues
- [README.md](../README.md) - Configuration options

**Optional Reading:**
- [API.md](API.md) - API for monitoring and automation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Storage and file structure
- [INSTALLATION_SCENARIOS.md](INSTALLATION_SCENARIOS.md) - Different deployment options

---

## 🔍 Documentation by Topic

### Installation & Setup
- [README.md](../README.md) - Installation section
- [DEPLOYMENT.md](DEPLOYMENT.md) - Complete deployment guide
- [DEPLOYMENT_WINDOWS.md](DEPLOYMENT_WINDOWS.md) - Windows deployment
- [DOCKER.md](DOCKER.md) - Standalone Docker deployment
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Installation issues

### Configuration
- [README.md](../README.md) - Configuration section
- [DEPLOYMENT.md](DEPLOYMENT.md) - Configuration options
- [config.yaml](../config.yaml) - Add-on configuration file

### Device Management
- [README.md](../README.md) - Usage section
- [API.md](API.md) - Device management endpoints
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Device discovery issues

### Command Learning
- [README.md](../README.md) - Learning commands section
- [API.md](API.md) - Command management endpoints
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Command learning issues

### Entity Generation
- [README.md](../README.md) - Auto-generating entities section
- [API.md](API.md) - Entity management endpoints
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Entity generation issues
- [development/ENTITY_GENERATION.md](development/ENTITY_GENERATION.md) - Technical implementation details

### API Integration
- [API.md](API.md) - Complete API reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - API troubleshooting

### Development
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [development/README.md](development/README.md) - Development documentation index
- [development/DEVELOPMENT.md](development/DEVELOPMENT.md) - Development workflow
- [development/TESTING.md](development/TESTING.md) - Testing documentation
- [development/E2E_TESTING.md](development/E2E_TESTING.md) - Browser automation testing
- [development/TESTING_QUICKSTART.md](development/TESTING_QUICKSTART.md) - Quick start guide
- [development/ARCHITECTURE_ANALYSIS.md](development/ARCHITECTURE_ANALYSIS.md) - Architecture deep dive
- [development/RELEASE_PROCESS.md](development/RELEASE_PROCESS.md) - Release workflow
- [ARCHITECTURE.md](ARCHITECTURE.md) - High-level system architecture
- [TEST_PLAN.md](TEST_PLAN.md) - Comprehensive test plan
- [../CHANGELOG.md](../CHANGELOG.md) - Version history

---

## 📝 File Structure Reference

```
broadlink_manager_addon/
├── README.md                    # Main documentation
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT License
├── config.yaml                  # Add-on configuration
├── Dockerfile                   # Docker image definition (add-on)
├── Dockerfile.standalone        # Docker image (standalone)
├── run.sh                       # Startup script (add-on)
├── run-standalone.sh            # Startup script (standalone)
├── requirements.txt             # Python dependencies
├── build.yaml                   # Build configuration
├── repository.yaml              # Repository metadata
├── deploy-to-haos.ps1           # Windows deployment script
├── docker-compose.yml           # Standalone Docker compose
├── .env.example                 # Environment template
├── app/                         # Application source code
│   ├── main.py                  # Entry point
│   ├── web_server.py            # Flask web server
│   ├── config_loader.py         # Configuration abstraction
│   ├── storage_manager.py       # Entity metadata storage
│   ├── entity_detector.py       # Command pattern detection
│   ├── entity_generator.py      # YAML entity generation
│   ├── area_manager.py          # Area/room management
│   └── templates/               # HTML templates
│       └── index.html           # Web interface
└── docs/                        # Documentation
    ├── DOCS.md                  # Documentation index (this file)
    ├── API.md                   # REST API reference
    ├── ARCHITECTURE.md          # High-level system architecture
    ├── CONTRIBUTING.md          # Contribution guidelines
    ├── CUSTOMIZATION.md         # Entity customization
    ├── DEPLOYMENT.md            # Installation and deployment
    ├── DEPLOYMENT_WINDOWS.md    # Windows deployment guide
    ├── DOCKER.md                # Standalone Docker guide
    ├── INSTALLATION_SCENARIOS.md # Installation scenarios
    ├── TEST_PLAN.md             # Comprehensive test plan
    ├── TROUBLESHOOTING.md       # Problem solving guide
    ├── YAML_VALIDATION.md       # YAML validation system
    └── development/             # Development documentation
        ├── README.md            # Development docs index
        ├── ARCHITECTURE_ANALYSIS.md # Deep architecture analysis
        ├── AUTO_MIGRATION.md    # Migration implementation
        ├── DEVELOPMENT.md       # Development workflow
        ├── DIRECT_LEARNING_IMPLEMENTATION.md # Learning implementation
        ├── E2E_TESTING.md       # Browser automation testing
        ├── ENTITY_GENERATION.md # Entity generation implementation
        ├── MIGRATION_FIX.md     # Migration bug fixes
        ├── PHASE1_COMPLETE.md   # Phase 1 completion
        ├── PHASE2_COMPLETE.md   # Phase 2 completion
        ├── RAW_BASE64_TEST_RESULTS.md # Test results
        ├── REDDIT_UPDATES.md    # Reddit automation
        ├── REFACTORING_ROADMAP.md # Future planning
        ├── RELEASE_PROCESS.md   # Release workflow
        ├── TESTING.md           # Testing documentation
        ├── TESTING_QUICKSTART.md # Testing quick start
        ├── V1_STYLE_ENTITY_GENERATION.md # v1 compatibility
        └── archive/             # Historical documentation
```

---

## 🆘 Getting Help

### Before Asking for Help

1. **Search the documentation** - Use Ctrl+F to search within docs
2. **Check troubleshooting guide** - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. **Review existing issues** - GitHub issues page
4. **Enable debug logging** - See troubleshooting guide

### Where to Get Help

1. **GitHub Issues** - For bugs and feature requests
2. **Home Assistant Community** - For general questions
3. **Discord** - For real-time chat support
4. **Documentation** - Most answers are here!

### Reporting Issues

When reporting issues, include:
- Add-on version
- Home Assistant version
- Architecture (amd64, aarch64, etc.)
- Device model
- Configuration (remove sensitive data)
- Logs (enable debug mode)
- Steps to reproduce

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🔄 Keeping Documentation Updated

This documentation is maintained by the community. If you find:
- Outdated information
- Missing details
- Errors or typos
- Unclear explanations

Please:
1. Open an issue on GitHub
2. Submit a pull request with fixes
3. Suggest improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

---

## 📊 Documentation Statistics

- **User-Facing Documentation**: 12 files in main docs/ folder
- **Development Documentation**: 19 files in docs/development/ folder
- **Archived Documentation**: 42+ files in docs/development/archive/
- **Lines of Documentation**: ~5,000+
- **Topics Covered**: Installation, Usage, API, Testing, Troubleshooting, Development, SmartIR
- **Last Updated**: January 2025
- **Organization**: Separated user-facing and development documentation

---

## 🎯 Documentation Roadmap

### Planned Documentation

- [ ] Video tutorials
- [ ] Architecture diagrams
- [ ] API client examples (Python, JavaScript)
- [ ] Advanced automation examples
- [ ] Performance tuning guide
- [ ] Security best practices guide
- [ ] Multi-language support

### Recent Additions

- ✅ API Reference (API.md)
- ✅ Troubleshooting Guide (TROUBLESHOOTING.md)
- ✅ Contributing Guidelines (CONTRIBUTING.md)
- ✅ Documentation Index (DOCS.md)

---

Thank you for using Broadlink Manager! 🎉

For the latest documentation, visit the [GitHub repository](https://github.com/tonyperkins/homeassistant-broadlink-manager).
