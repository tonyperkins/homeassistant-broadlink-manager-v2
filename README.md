# Broadlink Manager v2 (Beta)

<p align="center">
  <img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/develop/images/broadlink-logo.png" alt="Broadlink Manager" width="120">
</p>

<h3 align="center">Transform Your Smart Home with Effortless IR/RF Control</h3>

<p align="center">
  <strong>The ultimate Home Assistant companion for Broadlink devices</strong><br>
  Learn, manage, and automate infrared and radio frequency commands with a beautiful, modern interface.
</p>

---

## 🎯 Why Broadlink Manager?

Tired of juggling multiple remotes? Want to control your TV, AC, fans, and legacy devices through Home Assistant? **Broadlink Manager v2** makes it effortless.

✨ **Point. Click. Control.** Learn any IR/RF command in seconds with our intuitive interface. No coding required.

🎨 **Beautiful by Design.** A completely rewritten Vue 3 interface that's as pleasant to use as it is powerful. Light, medium, and dark themes adapt to your preference.

🚀 **SmartIR Supercharged.** First-class SmartIR integration means instant access to thousands of pre-configured device profiles. Set up your AC, TV, or media player in minutes, not hours.

🧠 **Intelligent & Automatic.** Discovers existing commands, migrates your setup seamlessly, and auto-generates Home Assistant entities. It just works.

⚠️ **This is a beta version with a completely rewritten UI using Vue 3.**

## ✨ What's New in v2?

### 🎨 Modern Vue 3 Interface
- Complete UI rewrite with component-based architecture
- Responsive design that works beautifully on desktop, tablet, and mobile
- Three theme modes: Light, Medium (new!), and Dark
- Real-time command testing with visual feedback
- Intuitive device cards with logo badges

### 🔧 SmartIR Integration ✅ **NOW AVAILABLE**
- **Full SmartIR support** - Create and manage SmartIR devices directly
- **Profile builder** - Build custom climate profiles with guided wizard
- **Code browser** - Browse and preview 1000+ pre-made device codes
- **Command learning** - Learn missing commands for existing profiles
- **Dual device support** - Manage both Broadlink and SmartIR devices seamlessly
- **Automatic detection** - Discovers existing SmartIR devices on startup

### 🚀 Enhanced Features
- **Better Performance** - Lightning-fast, responsive user experience
- **Smart command management** - View, test, and organize all commands in one place
- **Logo integration** - Visual device identification with Broadlink and SmartIR logos
- **Improved entity generation** - Auto-create lights, fans, switches, and climate controls
- **Command testing** - Test any command directly from the interface
- **Area management** - Organize devices by room/area

## Should I Use This?

**Use v1 (stable)** if:
- ✅ You want a proven, stable version
- ✅ You don't want to deal with potential bugs
- ✅ You just need basic functionality
- 👉 Get v1 here: https://github.com/tonyperkins/homeassistant-broadlink-manager

**Use v2 (beta)** if:
- ✅ You want to help test new features
- ✅ You're comfortable reporting bugs
- ✅ You want **full SmartIR integration** (available now!)
- ✅ You like modern, beautiful UIs
- ✅ You want the latest features and improvements

## Screenshots

### 🌞 Light Mode

#### Dashboard Overview
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/dashboard-overview.png" alt="Dashboard Overview" width="700">

*Modern dashboard with SmartIR integration and device management*

#### Device Management
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/device-list.png" alt="Device List" width="700">

*Manage all your Broadlink and SmartIR devices in one place*

### 🌙 Dark Mode

#### Dashboard (Dark)
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/dashboard-dark.png" alt="Dashboard Dark Mode" width="700">

*Beautiful dark theme for comfortable nighttime use*

#### Device List (Dark)
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/device-list-dark.png" alt="Device List Dark Mode" width="700">

*All features look stunning in dark mode*

#### Settings Menu (Dark)
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/settings-menu-dark.png" alt="Settings Menu Dark Mode" width="500">

*Easy theme switching and configuration*

### 📱 Mobile & Tablet Views

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/mobile-dashboard.png" alt="Mobile Dashboard" width="300"><br>
      <em>Mobile Dashboard (Light)</em>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/mobile-dashboard-dark.png" alt="Mobile Dashboard Dark" width="300"><br>
      <em>Mobile Dashboard (Dark)</em>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/mobile-device-list.png" alt="Mobile Device List" width="300"><br>
      <em>Mobile Device List</em>
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/tablet-device-list.png" alt="Tablet View" width="400"><br>
      <em>Tablet View</em>
    </td>
  </tr>
</table>

*Fully responsive design works beautifully on all devices*

### 🎛️ Device Setup

#### Add New Device
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/create-device-modal.png" alt="Create Device Modal" width="500">

*Easy device creation with Broadlink or SmartIR support*

#### Broadlink Device Setup
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/broadlink-device-form.png" alt="Broadlink Device Form" width="500">

*Learn IR/RF commands from your remotes*

#### SmartIR Device Setup
<img src="https://raw.githubusercontent.com/tonyperkins/homeassistant-broadlink-manager-v2/main/docs/images/screenshots/smartir-device-form.png" alt="SmartIR Device Form" width="500">

*Use pre-configured device profiles for instant setup*

## 🎯 Key Features

### 🎮 Device Management
- **Dual Platform Support**: Manage both Broadlink and SmartIR devices from one interface
- **Automatic Discovery**: Detects existing devices and commands on first startup
- **Smart Migration**: Seamlessly migrates from v1 or vanilla Broadlink integration
- **Multi-Device Support**: Control unlimited Broadlink remotes and devices
- **Area Organization**: Group devices by room for easy management

### 📡 Command Learning & Testing
- **Intuitive Learning**: Point, click, and press your remote - it's that simple
- **Real-Time Feedback**: Visual confirmation when commands are learned
- **Instant Testing**: Test any command with a single click
- **Command Browser**: View all learned commands organized by device
- **Import/Export**: Backup and restore your command library

### 🌟 SmartIR Integration (Optional)

Broadlink Manager integrates with [SmartIR](https://github.com/smartHomeHub/SmartIR), a Home Assistant integration for managing climate devices, media players, fans, and lights using IR/RF controllers. SmartIR is a separate project developed by Vassilis Panos and contributors.

- **1000+ Device Profiles**: Access pre-configured codes for popular devices
- **Profile Builder**: Create custom climate profiles with step-by-step wizard
- **Code Browser**: Preview and select from extensive device database
- **Command Learning**: Fill in missing commands for existing profiles
- **Climate Control**: Full support for AC units with temperature, modes, and fan speeds
- **Media Players**: Control TVs, receivers, and media devices
- **Optional Feature**: SmartIR integration can be enabled/disabled in settings

### 🏠 Home Assistant Integration
- **Entity Auto-Generation**: Create lights, fans, switches, and climate entities automatically
- **Helper Generation**: Auto-create input helpers for advanced control
- **Template Support**: Generate ready-to-use entity templates
- **Configuration Integration**: Seamless YAML configuration generation
- **No External Dependencies**: Works entirely within Home Assistant

### 🎨 Modern Interface
- **Vue 3 Architecture**: Fast, responsive, component-based UI
- **Three Theme Modes**: Light, Medium, and Dark themes
- **Mobile Optimized**: Works perfectly on phones and tablets
- **Visual Feedback**: Real-time status updates and notifications
- **Logo Integration**: Device identification with brand logos

### 🎉 Intelligent Startup System

Broadlink Manager automatically detects your installation type and adapts accordingly:

- **👋 First-time users**: Welcome guide and getting started instructions
- **📋 Existing BL Manager users**: Configuration preserved, continues normally  
- **🎉 Existing Broadlink users**: Automatic migration - all commands discovered and entities created instantly!

No matter your situation, setup is automatic and seamless. See [Installation Scenarios Guide](docs/INSTALLATION_SCENARIOS.md) for details.

## Installation

**Choose your installation method based on your Home Assistant setup:**

- **[Home Assistant OS / Supervised](#supervisor-add-on-installation)** - Use the add-on (recommended)
- **[Home Assistant Container / Docker](#standalone-docker-installation)** - Use standalone Docker

---

### Supervisor Add-on Installation

For Home Assistant OS and Supervised installations.

#### Prerequisites

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
   https://github.com/tonyperkins/homeassistant-broadlink-manager-v2
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

---

### Standalone Docker Installation

For Home Assistant installations that don't support add-ons (Container, Core, or any non-Supervisor setup).

#### Prerequisites

- **Home Assistant** (any installation type: Container, Core, etc.)
- **Docker and Docker Compose** installed on your host
- **Network access** to Home Assistant
- **Access to Home Assistant's config folder** (for reading/writing command storage)
- **Long-lived access token** from Home Assistant
- At least one **Broadlink device** configured in Home Assistant

#### Quick Start

```bash
# Clone the repository
git clone https://github.com/tonyperkins/homeassistant-broadlink-manager.git
cd homeassistant-broadlink-manager

# Copy environment template
cp .env.example .env

# Edit .env and set your HA_URL and HA_TOKEN
nano .env

# Update docker-compose.yml with your HA config path
nano docker-compose.yml

# Start the container
docker-compose up -d
```

Access the web interface at `http://your-host-ip:8099`

#### Creating a Long-Lived Access Token

1. Open Home Assistant and click your **profile** (your name in the sidebar)
2. Scroll to **"Long-Lived Access Tokens"**
3. Click **"Create Token"**
4. Name it `Broadlink Manager` and copy the token
5. Add it to your `.env` file as `HA_TOKEN`

#### Configuration

Edit `.env` with your settings:

```env
HA_URL=http://192.168.1.100:8123  # Your Home Assistant URL
HA_TOKEN=your_long_lived_token_here
LOG_LEVEL=info
WEB_PORT=8099
AUTO_DISCOVER=true
```

Update `docker-compose.yml` volume mount:

```yaml
volumes:
  - /path/to/homeassistant/config:/config  # Update this path!
```

**📖 For detailed Docker installation instructions, see [DOCKER.md](docs/DOCKER.md)**

---

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
4. **Add to configuration.yaml** (if not already using the package method):

   **Option A: Using Package (Recommended)** - If you added this during setup, you're done!
   ```yaml
   homeassistant:
     packages:
       broadlink_manager: !include broadlink_manager/package.yaml
   ```

   **Option B: Individual Includes** - Only if you prefer manual control:
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
  - Automatic percentage-based speed control
  - Direction control (forward/reverse) included by default
  - Supports 1-6 speed levels
- **Switch**: Requires `on` and `off` commands (or `toggle`)
- **Media Player**: Coming soon

#### Command Naming Conventions

For best auto-detection results, use these naming patterns:

- **Lights**: `light_on`, `light_off`, `light_toggle`
- **Fans**: `fan_speed_1`, `fan_speed_2`, ..., `fan_speed_6`, `fan_off`, `fan_reverse`
  - Speed commands are required (at least one)
  - `fan_off` is optional (will use lowest speed if not provided)
  - `fan_reverse` is optional (direction control will still appear in UI)
- **Switches**: `on`, `off`, `toggle`, `power`

## Documentation

### 📘 User Guides
- **[Installation Scenarios Guide](docs/INSTALLATION_SCENARIOS.md)** - Complete guide for all user types (first-time, existing, migration)
- **[Automation Examples Guide](docs/AUTOMATION_EXAMPLES.md)** - Using learned commands in automations and dashboards
- **[Automatic Migration Guide](docs/AUTO_MIGRATION.md)** - How automatic command discovery and migration works
- **[Entity Customization Guide](docs/CUSTOMIZATION.md)** - Customize entity names, icons, and more
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Installation and deployment instructions
- **[Windows Deployment](docs/DEPLOYMENT_WINDOWS.md)** - Windows-specific deployment guide
- **[Standalone Docker Guide](docs/DOCKER.md)** - Complete guide for Docker/Container installations
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Entity Generation Guide](docs/ENTITY_GENERATION.md)** - Technical details on entity auto-generation

### 🔧 Developer Resources
- **[Architecture Guide](docs/ARCHITECTURE.md)** - Understanding Broadlink devices, areas, and entity relationships
- **[API Reference](docs/API.md)** - Complete REST API documentation
- **[Development Guide](docs/DEVELOPMENT.md)** - Development workflow and testing
- **[Testing Guide](docs/TESTING.md)** - Comprehensive testing documentation with automated and manual test plans
- **[Testing Quick Start](docs/development/TESTING_QUICKSTART.md)** - Get started with testing in 5 minutes
- **[E2E Testing Guide](docs/E2E_TESTING.md)** - Browser automation testing with Playwright
- **[Contributing Guidelines](docs/CONTRIBUTING.md)** - How to contribute to this project

### 📚 Additional Resources
- **[Documentation Index](docs/DOCS.md)** - Complete documentation overview
- **[Changelog](CHANGELOG.md)** - Version history and changes
- **[Reddit Updates Guide](docs/REDDIT_UPDATES.md)** - Automate Reddit post updates with project info

## Support

Got questions?

You have several options to get them answered:

- The Home Assistant [Community Forum][forum].
- Join the [Reddit subreddit][reddit] in [/r/homeassistant][reddit]

You could also [open an issue here][issue] on GitHub.

## 💬 Community & Support

<p align="center">
  <a href="https://www.reddit.com/r/homeassistant/comments/1o1q3kf/release_broadlink_manager_addon_a_modern_web_ui/">
    <img src="https://img.shields.io/badge/Reddit-Announcement-FF4500?style=for-the-badge&logo=reddit&logoColor=white" alt="Reddit Announcement">
  </a>
  <a href="https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/discussions/1">
    <img src="https://img.shields.io/badge/GitHub-Discussions-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub Discussions">
  </a>
</p>

<p align="center">
  Join the conversation! Share your experience, ask questions, or get help from the community.
</p>

---

## Contributing

This is an active open-source project. We are always open to people who want to use the code or contribute to it.

We have set up a separate document containing our [contribution guidelines](docs/CONTRIBUTING.md).

Thank you for being involved! :heart_eyes:

## Authors & contributors

The original setup of this repository is by [Tony Perkins](https://github.com/tonyperkins).

For a full list of all authors and contributors, check [the contributor's page][contributors].

## Third-Party Integrations

### SmartIR

This project integrates with [SmartIR](https://github.com/smartHomeHub/SmartIR), a Home Assistant custom integration for controlling IR/RF devices. SmartIR is an independent project and is not included with Broadlink Manager.

**SmartIR License**: MIT License  
**Copyright**: (c) 2019 Vassilis Panos  
**Repository**: https://github.com/smartHomeHub/SmartIR

Broadlink Manager provides optional integration features to work alongside SmartIR, including profile creation, command learning, and YAML configuration generation. SmartIR must be installed separately via HACS or manually.

**Device Code Database**: Broadlink Manager uses the [SmartIR Code Aggregator](https://github.com/tonyperkins/smartir-code-aggregator), which combines device codes from SmartIR, IRDB, and other sources in a standardized SmartIR format. This provides a comprehensive database with thousands of pre-configured devices while maintaining compatibility with the SmartIR integration.

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
