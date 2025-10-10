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

- **[Entity Generation Guide](ENTITY_GENERATION.md)** - Complete guide to auto-generating Home Assistant entities
  - Architecture overview
  - Command naming conventions
  - Entity types (lights, fans, switches, media players)
  - API endpoints
  - Testing procedures

- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Solutions to common problems
  - Installation issues
  - Startup problems
  - Web interface issues
  - Device discovery problems
  - Command learning issues
  - Entity generation problems
  - Performance optimization

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

#### Auto-Generate Entities
1. Read [README.md](../README.md) - Auto-Generating Entities section
2. Read [ENTITY_GENERATION.md](ENTITY_GENERATION.md) - Complete guide
3. Check [API.md](API.md) - Entity Management endpoints
4. If issues: [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Entity Generation Issues

#### Use the API
1. Read [API.md](API.md) - Complete API reference
2. Check [ENTITY_GENERATION.md](ENTITY_GENERATION.md) - API examples

#### Contribute Code
1. Read [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
2. Check [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow
3. Check [API.md](API.md) - API structure
4. Review [DUAL_MODE_IMPLEMENTATION.md](DUAL_MODE_IMPLEMENTATION.md) - Architecture

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
- [ENTITY_GENERATION.md](ENTITY_GENERATION.md) - Advanced entity configuration
- [API.md](API.md) - API usage for automation
- [DOCKER.md](DOCKER.md) - Standalone Docker deployment

### For Developers

**Essential Reading:**
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development setup and standards
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow and testing
- [DUAL_MODE_IMPLEMENTATION.md](DUAL_MODE_IMPLEMENTATION.md) - Architecture and components
- [API.md](API.md) - API reference

**Optional Reading:**
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
- [ENTITY_GENERATION.md](ENTITY_GENERATION.md) - Storage and file structure

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
- [ENTITY_GENERATION.md](ENTITY_GENERATION.md) - Complete technical guide
- [API.md](API.md) - Entity management endpoints
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Entity generation issues

### API Integration
- [API.md](API.md) - Complete API reference
- [ENTITY_GENERATION.md](ENTITY_GENERATION.md) - API examples
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - API troubleshooting

### Development
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development workflow
- [DUAL_MODE_IMPLEMENTATION.md](DUAL_MODE_IMPLEMENTATION.md) - Architecture
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
    ├── DOCS.md                  # Documentation index
    ├── DEPLOYMENT.md            # Installation and deployment
    ├── DEPLOYMENT_WINDOWS.md    # Windows deployment guide
    ├── DEVELOPMENT.md           # Development workflow
    ├── DOCKER.md                # Standalone Docker guide
    ├── DUAL_MODE_IMPLEMENTATION.md  # Architecture details
    ├── ENTITY_GENERATION.md     # Entity generation guide
    ├── API.md                   # REST API reference
    ├── TROUBLESHOOTING.md       # Problem solving guide
    └── CONTRIBUTING.md          # Contribution guidelines
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

- **Total Documentation Files**: 9
- **Lines of Documentation**: ~3,500+
- **Topics Covered**: Installation, Usage, API, Troubleshooting, Development
- **Last Updated**: 2025-10-08

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
