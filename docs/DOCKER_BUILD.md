# Docker Build and Publish

This document explains how Docker images are built and published for the Broadlink Manager add-on.

## Automatic Builds

Docker images are automatically built and published to GitHub Container Registry (GHCR) when:

1. **A new release is published** on GitHub
2. **Manual workflow dispatch** is triggered

## Multi-Architecture Support

The workflow builds images for three architectures:
- **amd64** (x86_64) - Most desktop/server systems
- **aarch64** (ARM64) - Raspberry Pi 4/5, modern ARM servers
- **armv7** (ARM v7) - Raspberry Pi 3, older ARM devices

## Image Tags

Images are published with the following tags:

### Version-Specific Tags
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7` - Multi-arch manifest
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7-amd64` - AMD64 only
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7-aarch64` - ARM64 only
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7-armv7` - ARMv7 only

### Latest Tags (Stable Releases Only)
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:latest` - Multi-arch manifest (no alpha/beta)
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:latest-amd64` - AMD64 only
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:latest-aarch64` - ARM64 only
- `ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:latest-armv7` - ARMv7 only

**Note:** Alpha and beta releases do NOT get the `latest` tag.

## Manual Workflow Trigger

You can manually trigger a build for any tag:

1. Go to **Actions** → **Build and Publish Docker Images**
2. Click **Run workflow**
3. Enter the tag (e.g., `v0.3.0-alpha.7` or `0.3.0-alpha.7`)
4. Click **Run workflow**

The workflow will:
- Build images for all three architectures
- Push to GHCR with the specified version tag
- Create a multi-arch manifest

## Testing Locally

### Build for Your Architecture

```bash
# AMD64 (most common)
docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/amd64-base:3.18" \
  -t homeassistant-broadlink-manager-v2:test .

# ARM64 (Raspberry Pi 4/5)
docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/aarch64-base:3.18" \
  -t homeassistant-broadlink-manager-v2:test .

# ARMv7 (Raspberry Pi 3)
docker build --build-arg BUILD_FROM="ghcr.io/home-assistant/armv7-base:3.18" \
  -t homeassistant-broadlink-manager-v2:test .
```

### Run Locally

```bash
docker run -p 8099:8099 \
  -e HA_URL="http://homeassistant.local:8123" \
  -e HA_TOKEN="your_long_lived_access_token" \
  homeassistant-broadlink-manager-v2:test
```

Then visit: http://localhost:8099

## Pulling Images

Once published, users can pull images:

```bash
# Pull multi-arch image (Docker will select correct architecture)
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7

# Pull specific architecture
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7-amd64
```

## Troubleshooting

### Image Not Found

If `docker pull` fails with "denied" or "not found":

1. **Check if workflow ran successfully**
   - Go to Actions tab in GitHub
   - Look for "Build and Publish Docker Images" workflow
   - Check for errors in the logs

2. **Verify package exists**
   - Visit: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/pkgs/container/homeassistant-broadlink-manager-v2
   - Check if the version tag is listed

3. **Check package visibility**
   - Package must be public for unauthenticated pulls
   - Go to package settings → Change visibility to Public

### Build Failures

Common issues:

- **Missing dependencies**: Check `requirements.txt` is up to date
- **Base image issues**: Verify base images in `build.yaml` are accessible
- **Architecture mismatch**: Ensure platform matches base image architecture

## Release Process Integration

The Docker build workflow integrates with the release process:

1. **Create release** using `quick_release.py`:
   ```bash
   python scripts/quick_release.py patch -m "Fix description"
   ```

2. **Workflow automatically triggers** when release is published

3. **Images are built** for all architectures

4. **Multi-arch manifest created** and pushed to GHCR

5. **Users can pull** the new version immediately

## Workflow Configuration

The workflow uses:
- **QEMU** for cross-platform builds
- **Docker Buildx** for multi-arch support
- **GitHub Actions cache** for faster builds
- **GITHUB_TOKEN** for authentication (automatic)

No manual secrets configuration needed - the workflow uses the built-in `GITHUB_TOKEN`.

## Base Images

Base images are defined in `build.yaml`:

```yaml
build_from:
  aarch64: "ghcr.io/home-assistant/aarch64-base:3.18"
  amd64: "ghcr.io/home-assistant/amd64-base:3.18"
  armv7: "ghcr.io/home-assistant/armv7-base:3.18"
```

These are official Home Assistant base images with Alpine Linux 3.18.

## Build Time

Typical build times:
- **First build**: 10-15 minutes (no cache)
- **Subsequent builds**: 3-5 minutes (with cache)
- **All architectures**: ~15-20 minutes total (parallel builds)

## Package Visibility

To make images publicly accessible:

1. Go to package page: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/pkgs/container/homeassistant-broadlink-manager-v2
2. Click **Package settings**
3. Scroll to **Danger Zone**
4. Click **Change visibility**
5. Select **Public**
6. Confirm

This allows users to pull images without authentication.
