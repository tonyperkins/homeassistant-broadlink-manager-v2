# Ingress 502 Error Troubleshooting

## Current Status
- ✅ Add-on starts successfully on port 8099
- ✅ App is listening on `http://172.30.33.9:8099`
- ❌ Ingress returns 502 Bad Gateway
- ❌ Supervisor trying to connect to wrong port (63722 instead of 8099)

## Configuration (Correct)
```yaml
ingress: true
ingress_port: 0  # Default 8099
ports:
  8099/tcp: 8099  # Port must be exposed for ingress
options:
  web_port: 8099
```

## What We've Tried
1. ✅ Removed and restored web_port option
2. ✅ Changed ingress_port from 0 to 8099 and back
3. ✅ Enabled port mapping (8099/tcp: 8099)
4. ✅ Restarted Supervisor
5. ✅ Uninstalled and reinstalled add-on
6. ✅ Compared with working V1 config

## Current Issues
1. **Supervisor connecting to wrong port**: Ingress proxy tries port 63722 instead of 8099
2. **Add-on getting 502 from HA Core**: Add-on can't reach `http://supervisor/core/api`

## Things to Check

### 1. Wait for Home Assistant Core to Fully Start
The 502 errors from the add-on to HA Core suggest Core is still restarting. Wait 2-3 minutes after Supervisor restart.

### 2. Check Supervisor Logs
Settings → System → Logs → Supervisor
Look for:
- Port assignment errors
- Ingress configuration errors
- Network errors

### 3. Check Home Assistant Core Logs  
Settings → System → Logs → Home Assistant Core
Look for:
- Startup errors
- API errors

### 4. Verify Add-on Network Configuration
In Supervisor logs, look for lines like:
```
INFO (SyncWorker_X) [supervisor.docker.addon] Starting Docker add-on local_broadlink-manager-v2
```
Check if it mentions the correct port.

### 5. Compare with Working V1
V1 add-on (slug: `broadlink-manager`) works with ingress. Compare:
- Docker container name
- Port mapping
- Network mode

### 6. Check Docker Container
Via SSH/Terminal:
```bash
docker ps | grep broadlink
docker inspect addon_local_broadlink-manager-v2 | grep -A 20 NetworkSettings
```

### 7. Try Direct IP Access
Test if app is accessible directly:
```
http://172.30.33.9:8099
```
If this works, it's purely an ingress proxy issue.

### 8. Check for Port Conflicts
```bash
netstat -tulpn | grep 8099
```

## Possible Root Causes

### Theory 1: Supervisor Port Cache
Supervisor cached wrong port mapping from when we had `ports: null`. 
- **Fix**: Full system reboot (not just Supervisor restart)

### Theory 2: Docker Network Issue
Add-on container not on correct Docker network for ingress.
- **Fix**: Check network mode in Docker inspect

### Theory 3: Ingress Session Issue
Ingress proxy session corrupted.
- **Fix**: Clear browser cache, try incognito mode

### Theory 4: Add-on Slug Conflict
Local add-on slug might conflict with something.
- **Fix**: Try changing slug to `broadlink_manager_v2_test`

### Theory 5: Home Assistant Core Not Ready
Core is still starting up when add-on tries to connect.
- **Fix**: Wait longer, check Core logs

## Next Steps

1. **Wait 5 minutes** for everything to fully stabilize
2. **Check if HA Core is fully started** (no errors in Core logs)
3. **Try accessing add-on via ingress** again
4. **If still 502**, try accessing `http://172.30.33.9:8099` directly
5. **If direct access works**, it's definitely an ingress proxy issue
6. **Check Supervisor logs** for the exact error when accessing ingress
7. **Try full system reboot** (Settings → System → Restart → Restart System)

## Working Configuration (V1 for Reference)
```yaml
name: Broadlink Manager
slug: broadlink-manager
ingress: true
ingress_port: 0
ports:
  8099/tcp: 8099
options:
  web_port: 8099
```

## Files to Check
- `/data/options.json` - Add-on configuration
- Supervisor logs - Ingress errors
- Docker inspect - Network configuration
