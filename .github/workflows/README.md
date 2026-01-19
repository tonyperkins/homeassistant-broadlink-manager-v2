# GitHub Actions Workflows

This directory contains automated workflows for the Broadlink Manager project.

## Workflows

### docker-publish.yml
Builds and publishes the **Home Assistant add-on** Docker images for multiple architectures.

**Triggers:**
- Automatically on release publish
- Manually via workflow dispatch

**Images Published:**
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:latest`
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:X.X.X`

### docker-publish-standalone.yml
Builds and publishes the **standalone Docker** images for non-Supervisor installations.

**Triggers:**
- Automatically on release publish
- Manually via workflow dispatch

**Images Published:**
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone`
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone-latest`
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:standalone-X.X.X`

**Manual Trigger:**
```bash
# Navigate to Actions tab on GitHub
# Select "Build and Publish Standalone Docker Images"
# Click "Run workflow"
# Enter tag (e.g., v0.3.0-alpha.29)
```

### tests.yml
Runs automated tests on push and pull requests.

### update-smartir-index.yml
Monthly automated update of the SmartIR device index.

## Triggering Manual Builds

To manually trigger a Docker build:

1. Go to the [Actions tab](https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/actions)
2. Select the workflow you want to run
3. Click "Run workflow"
4. Enter the version tag (e.g., `v0.3.0-alpha.29`)
5. Click the green "Run workflow" button

## First-Time Setup

After merging this workflow, you need to trigger the first build manually:

1. Ensure you have a recent release tag (e.g., `v0.3.0-alpha.29`)
2. Go to Actions → "Build and Publish Standalone Docker Images"
3. Run workflow with the current version tag
4. Wait for the build to complete (~10-15 minutes)
5. Verify images are published: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/pkgs/container/homeassistant-broadlink-manager-v2

The workflow will automatically run for all future releases.
