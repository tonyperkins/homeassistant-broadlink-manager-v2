# Contributing to Broadlink Manager

Thank you for your interest in contributing to the Broadlink Manager add-on! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check the [existing issues](https://github.com/yourusername/broadlink-manager-addon/issues) to avoid duplicates
2. Verify you're using the latest version
3. Check the troubleshooting section in the documentation

When reporting a bug, include:
- **Description**: Clear description of the issue
- **Steps to Reproduce**: Detailed steps to reproduce the behavior
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**: 
  - Home Assistant version
  - Add-on version
  - Architecture (amd64, aarch64, etc.)
  - Broadlink device model
- **Logs**: Relevant log excerpts (enable debug logging if needed)

### Suggesting Enhancements

Enhancement suggestions are welcome! Please include:
- **Use case**: Why this enhancement would be useful
- **Proposed solution**: How you envision it working
- **Alternatives**: Other approaches you've considered
- **Additional context**: Screenshots, mockups, or examples

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Make your changes**:
   - Follow the existing code style
   - Add comments for complex logic
   - Update documentation as needed
3. **Test your changes**:
   - Test on your Home Assistant installation
   - Verify all existing functionality still works
   - Test on multiple architectures if possible
4. **Commit your changes**:
   - Use clear, descriptive commit messages
   - Reference issue numbers if applicable
5. **Submit a pull request**:
   - Provide a clear description of the changes
   - Link to related issues
   - Include screenshots for UI changes

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Home Assistant OS or Supervised installation (for testing)
- Git
- Docker (for building images)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/broadlink-manager-addon.git
   cd broadlink-manager-addon
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally** (outside of Home Assistant):
   ```bash
   cd app
   python3 main.py
   ```

4. **Test in Home Assistant**:
   - Copy files to `/addons/local-addons/broadlink-manager/`
   - Install the add-on from the local repository
   - See DEPLOYMENT.md for detailed instructions

### Project Structure

```
broadlink_manager_addon/
├── app/                          # Application code
│   ├── main.py                   # Entry point
│   ├── web_server.py             # Flask web server
│   ├── storage_manager.py        # Entity metadata storage
│   ├── entity_detector.py        # Command pattern detection
│   ├── entity_generator.py       # YAML entity generation
│   ├── area_manager.py           # Area/room management
│   └── templates/                # HTML templates
├── config.yaml                   # Add-on configuration
├── Dockerfile                    # Docker image definition
├── run.sh                        # Startup script
├── requirements.txt              # Python dependencies
├── README.md                     # User documentation
├── CHANGELOG.md                  # Version history
├── DEPLOYMENT.md                 # Deployment guide
├── ENTITY_GENERATION.md          # Entity generation docs
└── API.md                        # API reference
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints where appropriate
- Maximum line length: 100 characters
- Use docstrings for all public functions and classes

Example:
```python
def detect_entity(command_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect entity type from command name.
    
    Args:
        command_name: The command name to analyze
        
    Returns:
        Tuple of (entity_type, command_role) or (None, None)
    """
    pass
```

### JavaScript/HTML Style

- Use consistent indentation (2 spaces)
- Use modern ES6+ syntax
- Add comments for complex logic
- Follow accessibility best practices

### Commit Messages

Use clear, descriptive commit messages:

```
Add fan reverse direction support

- Add reverse command detection in EntityDetector
- Update fan template generation
- Add UI controls for direction
- Update documentation

Fixes #123
```

## Testing

### Manual Testing Checklist

Before submitting a PR, test:

- [ ] Add-on starts successfully
- [ ] Web interface loads correctly
- [ ] Device discovery works
- [ ] Command learning functions
- [ ] Command testing works
- [ ] Entity detection is accurate
- [ ] Entity generation produces valid YAML
- [ ] Generated entities work in Home Assistant
- [ ] Configuration options are respected
- [ ] Logs are clear and helpful

### Test on Multiple Architectures

If possible, test on:
- amd64 (most common)
- aarch64 (Raspberry Pi 4, etc.)
- armv7 (older Raspberry Pi)

## Documentation

When making changes, update:

- **README.md** - User-facing features
- **CHANGELOG.md** - Version history
- **API.md** - API endpoint changes
- **ENTITY_GENERATION.md** - Entity generation features
- **Code comments** - Complex logic
- **Docstrings** - Function/class documentation

## Release Process

Maintainers will:

1. Update version in `config.yaml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Build and push Docker images
5. Create a GitHub release

## Getting Help

- **Documentation**: Check README.md and other docs
- **Issues**: Search existing issues or create a new one
- **Discussions**: Use GitHub Discussions for questions
- **Community**: Home Assistant community forums

## Recognition

Contributors will be:
- Listed in the repository contributors page
- Mentioned in release notes (for significant contributions)
- Credited in the README (for major features)

Thank you for contributing to make Broadlink Manager better! 🎉
