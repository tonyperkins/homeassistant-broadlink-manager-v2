# Broadlink Manager Add-on


A Home Assistant add-on for managing Broadlink devices with a built-in web interface for easy IR/RF command learning and management.

## Screenshots

<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager/main/images/main-interface.png" alt="Main Interface - Command Management" width="600">

*Main interface showing currently active broadlink devices*

<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager/main/images/command-list.png" alt="Command List" width="600">

*Command list interface showing all learned commands and their associated devices and rooms*

<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager/main/images/command-learning.png" alt="Command Learning" width="600">

*Easy command learning with real-time feedback*

<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager/main/images/entity-management.png" alt="Entity Management" width="600">

*Auto-generate Home Assistant entities from learned commands*

<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager/main/images/command-management.png" alt="Command Management" width="600">

*Command management interface*

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

### Prerequisites

Before installing this add-on, ensure you have:
- Home Assistant OS or Supervised installation
- At least one Broadlink device configured in Home Assistant
- The official Broadlink integration installed and working

### Step 1: Add the Repository

1. Navigate to **Settings** → **Add-ons** in your Home Assistant interface
2. Click the **Add-on Store** button (bottom right)
3. Click the **⋮** menu (top right) and select **Repositories**
4. Add this repository URL:
   ```
   https://github.com/tonyperkins/homeassistant-broadlink-manager
   ```
5. Click **Add** and wait for the repository to load

### Step 2: Install the Add-on

1. Refresh the Add-on Store page
2. Find **Broadlink Manager** in the list (may be at the bottom)
3. Click on **Broadlink Manager**
4. Click the **Install** button
5. Wait for the installation to complete (this may take a few minutes)

### Step 3: Configure the Add-on

1. After installation, go to the **Configuration** tab
2. Adjust settings as needed (see Configuration section below)
3. Click **Save**

### Step 4: Start the Add-on

1. Go to the **Info** tab
2. Click **Start**
3. Optionally, enable:
   - **Start on boot** - Auto-start the add-on when Home Assistant starts
   - **Watchdog** - Automatically restart if the add-on crashes
   - **Show in sidebar** - Add a quick link to the sidebar (uses Ingress)

### Step 5: Access the Web Interface

Once started, access the interface in one of two ways:

**Option 1: Via Sidebar** (if enabled)
- Click **Broadlink Manager** in the Home Assistant sidebar

**Option 2: Direct URL**
- Navigate to: `http://homeassistant.local:8099`
- Or use your Home Assistant IP: `http://192.168.1.100:8099` (replace with your IP)

You should now see the Broadlink Manager interface with your devices listed!

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

- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

You could also [open an issue here][issue] on GitHub.

## Contributing

This is an active open-source project. We are always open to people who want to use the code or contribute to it.

We have set up a separate document containing our [contribution guidelines](CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Authors & contributors

The original setup of this repository is by [Tony Perkins](https://github.com/tonyperkins).

For a full list of all authors and contributors, check [the contributor's page][contributors].

## License

MIT License

Copyright (c) 2025 Tony Perkins

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

[aarch64-shield]: https://img.shields.io/badge/aarch64-yes-green.svg
[amd64-shield]: https://img.shields.io/badge/amd64-yes-green.svg
[armhf-shield]: https://img.shields.io/badge/armhf-yes-green.svg
[armv7-shield]: https://img.shields.io/badge/armv7-yes-green.svg
[i386-shield]: https://img.shields.io/badge/i386-yes-green.svg
[contributors]: https://github.com/tonyperkins/homeassistant-broadlink-manager/graphs/contributors
[discord-ha]: https://discord.gg/c5DvZ4e
[discord]: https://discord.me/hassioaddons
[forum]: https://community.home-assistant.io/t/repository-community-hass-io-add-ons/24705?u=frenck
[issue]: https://github.com/tonyperkins/homeassistant-broadlink-manager/issues
[reddit]: https://reddit.com/r/homeassistant
[repository]: https://github.com/tonyperkins/homeassistant-broadlink-manager
