# Broadlink Manager Add-on

![Supports aarch64 Architecture][aarch64-shield] ![Supports amd64 Architecture][amd64-shield] ![Supports armhf Architecture][armhf-shield] ![Supports armv7 Architecture][armv7-shield] ![Supports i386 Architecture][i386-shield]

A Home Assistant add-on for managing Broadlink devices with a built-in web interface for easy IR/RF command learning and management.

## About

This add-on provides a comprehensive solution for managing Broadlink devices in your Home Assistant installation. It features:

- **Web Interface**: Modern, responsive web UI for device management
- **Command Learning**: Easy IR/RF command learning with real-time feedback
- **Command Management**: View, test, and organize learned commands
- **Entity Auto-Generation**: Automatically create Home Assistant entities (lights, fans, switches) from learned commands
- **Storage Integration**: Direct access to Home Assistant's command storage
- **Multi-Device Support**: Manage multiple Broadlink devices from one interface
- **No External Dependencies**: Works entirely within Home Assistant

## Installation

1. Add this repository to your Home Assistant Supervisor add-on store
2. Install the "Broadlink Manager" add-on
3. Configure the add-on options (see Configuration section)
4. Start the add-on

## Configuration

### Add-on Configuration

```yaml
log_level: info
web_port: 8099
auto_discover: true
```

### Option: `log_level`

The `log_level` option controls the level of log output by the addon and can be changed to be more or less verbose, which might be useful when you are dealing with an unknown issue.

Possible values are:

- `trace`: Show every detail, like all called internal functions.
- `debug`: Shows detailed debug information.
- `info`: Normal (usually) interesting events.
- `warning`: Exceptional occurrences that are not errors.
- `error`: Runtime errors that do not require immediate action.
- `fatal`: Something went terribly wrong. Add-on becomes unusable.

Please note that each level automatically includes log messages from a more severe level, e.g., `debug` also shows `info` messages. By default, the `log_level` is set to `info`, which is the recommended setting unless you are troubleshooting.

### Option: `web_port`

Sets the port for the web interface. Default is 8099. The web interface will be available at `http://homeassistant.local:8099` (replace with your Home Assistant URL).

### Option: `auto_discover`

Enables automatic discovery of Broadlink devices on your network. Default is true.

## Usage

### Learning Commands

1. **Access the Web Interface**: After starting the add-on, navigate to `http://homeassistant.local:8099` in your web browser
2. **Select Device**: Choose your Broadlink device from the dropdown
3. **Choose Room and Device**: Select the room and device name for organizing commands
4. **Learn Commands**: 
   - Add command names using the "Add Command" field
   - Click "Learn" next to each command
   - Follow the on-screen instructions to press your remote buttons
5. **Test Commands**: Use the "Test" button to verify learned commands work correctly
6. **Manage Commands**: View all learned commands and organize them by device

### Auto-Generating Home Assistant Entities

The add-on can automatically create Home Assistant entities from your learned commands:

1. **Learn your commands** with descriptive names (e.g., `light_on`, `light_off`, `fan_speed_1`, etc.)
2. **Configure entities** via the web interface:
   - The add-on will auto-detect entity types based on command names
   - You can manually adjust entity types and command roles
3. **Generate entity files** by clicking the "Generate Entities" button
4. **Add to configuration.yaml**:
   ```yaml
   light: !include broadlink_manager/entities.yaml
   fan: !include broadlink_manager/entities.yaml
   switch: !include broadlink_manager/entities.yaml
   input_boolean: !include broadlink_manager/helpers.yaml
   input_select: !include broadlink_manager/helpers.yaml
   ```
5. **Restart Home Assistant** and your entities will appear!

#### Supported Entity Types

- **Light**: Requires `light_on` and `light_off` commands (or `light_toggle`)
- **Fan**: Requires `fan_speed_X` commands and optionally `fan_off`, `fan_reverse`
- **Switch**: Requires `on` and `off` commands (or `toggle`)
- **Media Player**: Coming soon

#### Command Naming Conventions

For best auto-detection results, use these naming patterns:

- **Lights**: `light_on`, `light_off`, `light_toggle`
- **Fans**: `fan_speed_1`, `fan_speed_2`, `fan_speed_3`, `fan_off`, `fan_reverse`
- **Switches**: `on`, `off`, `toggle`, `power`

## Documentation

- **[API Reference](API.md)** - Complete REST API documentation
- **[Entity Generation Guide](ENTITY_GENERATION.md)** - Technical details on entity auto-generation
- **[Deployment Guide](DEPLOYMENT.md)** - Installation and deployment instructions
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[Contributing](CONTRIBUTING.md)** - How to contribute to this project

## Support

Got questions?

You have several options to get them answered:

- The [Home Assistant Community Add-ons Discord chat server][discord] for add-on support and feature requests.
- The [Home Assistant Discord chat server][discord-ha] for general Home Assistant discussions and questions.
- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

You could also [open an issue here][issue] on GitHub.

## Contributing

This is an active open-source project. We are always open to people who want to use the code or contribute to it.

We have set up a separate document containing our [contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Authors & contributors

The original setup of this repository is by [Your Name][yourname].

For a full list of all authors and contributors, check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2023 [Your Name]

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[contributors]: https://github.com/yourusername/broadlink-manager-addon/graphs/contributors
[discord-ha]: https://discord.gg/c5DvZ4e
[discord]: https://discord.me/hassioaddons
[forum]: https://community.home-assistant.io/t/repository-community-hass-io-add-ons/24705?u=frenck
[yourname]: https://github.com/yourusername
[issue]: https://github.com/yourusername/broadlink-manager-addon/issues
[reddit]: https://reddit.com/r/homeassistant
[repository]: https://github.com/yourusername/broadlink-manager-addon
