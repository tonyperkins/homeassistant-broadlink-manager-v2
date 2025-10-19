# Ingress 502 Error - Root Cause and Fix

## Problem
After removing the `web_port` user configuration option, ingress stopped working with 502 Bad Gateway errors.

## Root Cause
The `webui` field was missing from `config.yaml`. This field is required for Home Assistant to properly configure the ingress proxy.

## Solution
Add the `webui` field to `config.yaml`:

```yaml
auth_api: true
webui: "http://[HOST]:[PORT:8099]"
ingress: true
```

## Complete Working Configuration

```yaml
name: Broadlink Manager v2 (Alpha)
version: "0.3.0-alpha.1-dev.5"
slug: broadlink-manager-v2
description: Next-generation Broadlink device manager with Vue 3 interface (Alpha)
arch:
  - amd64
  - aarch64
  - armv7
startup: application
boot: manual
init: false
auth_api: true
webui: "http://[HOST]:[PORT:8099]"
ingress: true
panel_icon: mdi:remote
options:
  log_level: info
  web_port: 8099
  auto_discover: true
schema:
  log_level: list(trace|debug|info|warning|error|fatal)?
  web_port: port
  auto_discover: bool?
ports:
  8099/tcp: 8099
ports_description:
  8099/tcp: Web interface for Broadlink device management
homeassistant_api: true
hassio_api: true
hassio_role: default
map:
  - config:rw
```

## Key Fields for Ingress

1. **`webui`**: Tells HA where the web interface is accessible
   - Format: `"http://[HOST]:[PORT:8099]"`
   - Required for ingress to work properly

2. **`ingress: true`**: Enables ingress support

3. **`auth_api: true`**: Enables authentication API access

4. **`ports: 8099/tcp: 8099`**: Port must be exposed (not null)

5. **`web_port` in options**: Must exist even though it's always 8099 for ingress

## What We Learned

- The `webui` field is **critical** for ingress functionality
- Even with ingress, the port must be **exposed** (`8099/tcp: 8099`, not `null`)
- The `web_port` option must exist in the schema, even if users shouldn't change it
- Removing `ingress_port: 0` doesn't break anything (it's optional)

## Testing
After applying this fix:
- ✅ Ingress works via sidebar
- ✅ "Show in sidebar" option appears
- ✅ No 502 errors
- ✅ Add-on accessible at ingress URL

## References
- Working V1 config: https://github.com/tonyperkins/homeassistant-broadlink-manager/blob/main/config.yaml
- Working V2 config: https://github.com/tonyperkins/homeassistant-broadlink-manager-v2/blob/main/config.yaml
