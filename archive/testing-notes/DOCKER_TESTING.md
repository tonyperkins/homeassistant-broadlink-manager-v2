# Docker Testing Guide

## ✅ Local Build Successful!

Your Docker image has been built locally:
- **Image:** `homeassistant-broadlink-manager-v2:0.3.0-alpha.7-test`
- **Size:** 1.58GB
- **Status:** Ready to test

## Test the Local Image

### Option 1: Run Standalone (Minimal)
```powershell
docker run -p 8099:8099 `
  -e HA_URL="http://homeassistant.local:8123" `
  -e HA_TOKEN="your_long_lived_access_token" `
  -v ${PWD}/test-config:/config `
  homeassistant-broadlink-manager-v2:0.3.0-alpha.7-test
```

**Required:**
- `HA_URL` - Your Home Assistant URL
- `HA_TOKEN` - Long-lived access token from HA
- Volume mount `/config` - For storing devices.json

Then visit: http://localhost:8099

### Option 2: Run with All Options
```powershell
docker run -p 8099:8099 `
  -e HA_URL="http://homeassistant.local:8123" `
  -e HA_TOKEN="your_long_lived_access_token" `
  -e LOG_LEVEL="debug" `
  -e WEB_PORT="8099" `
  -e AUTO_DISCOVER="true" `
  -v ${PWD}/test-config:/config `
  homeassistant-broadlink-manager-v2:0.3.0-alpha.7-test
```

### Create Test Config Directory
```powershell
New-Item -ItemType Directory -Force -Path test-config
```

## Publish to GitHub Container Registry

### Step 1: Trigger the Workflow

Go to: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/actions/workflows/docker-publish.yml

1. Click **Run workflow**
2. Enter tag: `v0.3.0-alpha.7` (or `0.3.0-alpha.7`)
3. Click **Run workflow**

The workflow will:
- Build for amd64, aarch64, and armv7
- Push to GHCR
- Create multi-arch manifest
- Take ~15-20 minutes

### Step 2: Make Package Public

After the workflow completes:

1. Go to: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/pkgs/container/homeassistant-broadlink-manager-v2
2. Click **Package settings**
3. Scroll to **Danger Zone**
4. Click **Change visibility** → **Public**
5. Confirm

### Step 3: Test Pull

```powershell
docker pull ghcr.io/tonyperkins/homeassistant-broadlink-manager-v2:0.3.0-alpha.7
```

## Future Releases

The workflow will automatically run when you publish a release:

```powershell
python scripts/quick_release.py patch -m "Your changes"
```

This will:
1. Create and push the release
2. Trigger Docker build workflow
3. Publish images to GHCR

## Cleanup Local Test Image

When done testing:
```powershell
docker rmi homeassistant-broadlink-manager-v2:0.3.0-alpha.7-test
```

## Troubleshooting

### Workflow Fails
- Check Actions tab for error logs
- Verify base images are accessible
- Check requirements.txt for invalid packages

### Pull Denied
- Ensure package is public (see Step 2 above)
- Check workflow completed successfully
- Verify tag exists in package versions

### Image Too Large
- Current size: 1.58GB (includes Python, dependencies, Node.js build)
- This is normal for Home Assistant add-ons
- Size is compressed when pushed to registry

## Next Steps

1. **Test locally** using the commands above
2. **Trigger workflow** to publish to GHCR
3. **Make package public** for users to pull
4. **Update add-on repository** to use GHCR images
