# Troubleshooting Guide

This guide helps you diagnose and fix common issues with the Broadlink Manager add-on.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Add-on Won't Start](#add-on-wont-start)
- [Web Interface Issues](#web-interface-issues)
- [Device Discovery Issues](#device-discovery-issues)
- [Command Learning Issues](#command-learning-issues)
- [Entity Generation Issues](#entity-generation-issues)
- [Performance Issues](#performance-issues)
- [Getting Help](#getting-help)

---

## Installation Issues

### Add-on Not Appearing in Store

**Symptoms:**
- Broadlink Manager doesn't appear in the add-on store after adding the repository

**Solutions:**
1. **Verify repository URL** is correct
2. **Refresh the add-on store**:
   - Click the three dots (⋮) in the top right
   - Select "Reload"
3. **Check repository.yaml** format:
   ```yaml
   name: "Broadlink Manager Add-ons"
   url: "https://github.com/tonyperkins/homeassistant-broadlink-manager"
   maintainer: "Tony Perkins"
   ```
4. **Check Home Assistant logs** for repository errors
5. **Try local installation** method (see DEPLOYMENT.md)

### Installation Fails

**Symptoms:**
- Installation starts but fails with an error

**Solutions:**
1. **Check architecture compatibility**:
   - Supported: amd64, aarch64, armv7
   - Check your system: Settings → System → Hardware
2. **Check available disk space**:
   - Need at least 500MB free
3. **Check Docker status**:
   ```bash
   docker ps
   docker images
   ```
4. **Review installation logs** in the add-on page
5. **Try rebuilding** if using local installation

---

## Add-on Won't Start

### Startup Fails Immediately

**Symptoms:**
- Add-on shows as "stopped" immediately after starting
- Red error indicator in add-on card

**Solutions:**

1. **Check the logs** (most important!):
   - Go to the add-on page
   - Click "Log" tab
   - Look for error messages

2. **Common log errors and fixes**:

   **Error: "Port 8099 already in use"**
   ```
   Solution: Change web_port in configuration
   ```

   **Error: "Cannot access /config"**
   ```
   Solution: Check add-on has config:rw permission in config.yaml
   ```

   **Error: "SUPERVISOR_TOKEN not found"**
   ```
   Solution: Restart Home Assistant, then restart add-on
   ```

   **Error: "Python module not found"**
   ```
   Solution: Rebuild the add-on or reinstall
   ```

3. **Verify configuration**:
   ```yaml
   log_level: info
   web_port: 8099
   auto_discover: true
   ```

4. **Check system resources**:
   - CPU usage < 90%
   - Memory available > 100MB
   - Disk space available

5. **Restart Home Assistant** and try again

### Add-on Starts Then Crashes

**Symptoms:**
- Add-on starts successfully but stops after a few seconds/minutes

**Solutions:**

1. **Enable debug logging**:
   ```yaml
   log_level: debug
   ```

2. **Check for memory issues**:
   - Monitor memory usage in System → Hardware
   - Increase swap if needed

3. **Check for network issues**:
   - Verify network connectivity
   - Check firewall rules

4. **Review crash logs**:
   - Look for Python tracebacks
   - Note the last action before crash

---

## Web Interface Issues

### Cannot Access Web Interface

**Symptoms:**
- Browser shows "Connection refused" or "Cannot connect"
- URL: `http://homeassistant.local:8099`

**Solutions:**

1. **Verify add-on is running**:
   - Check add-on status is "Started"
   - Green indicator on add-on card

2. **Check port configuration**:
   - Verify `web_port` in add-on config
   - Default is 8099

3. **Try different URLs**:
   ```
   http://homeassistant.local:8099
   http://192.168.1.100:8099  (use your HA IP)
   http://localhost:8099  (if on same machine)
   ```

4. **Check firewall**:
   - Ensure port 8099 is not blocked
   - Check router/firewall settings

5. **Check browser console** (F12):
   - Look for JavaScript errors
   - Check network tab for failed requests

6. **Try different browser**:
   - Clear cache and cookies
   - Try incognito/private mode

### Web Interface Loads But Shows Errors

**Symptoms:**
- Page loads but shows error messages
- Features don't work

**Solutions:**

1. **Refresh the page** (Ctrl+F5 / Cmd+Shift+R)

2. **Check browser console** for errors

3. **Verify API connectivity**:
   ```bash
   curl http://homeassistant.local:8099/api/devices
   ```

4. **Check add-on logs** for backend errors

5. **Clear browser cache**

---

## Device Discovery Issues

### No Devices Found

**Symptoms:**
- Device dropdown is empty
- "No devices found" message

**Solutions:**

1. **Verify Broadlink integration is installed**:
   - Settings → Devices & Services
   - Look for "Broadlink" integration
   - Devices should show as `remote.*` entities

2. **Check device status**:
   - Devices should be "Available" in Home Assistant
   - Test device with Home Assistant's remote service

3. **Enable auto-discovery**:
   ```yaml
   auto_discover: true
   ```

4. **Restart the add-on** after adding devices

5. **Check network connectivity**:
   - Devices must be on same network
   - Check device IP addresses are reachable

6. **Manually add device** if auto-discovery fails

### Device Shows But Can't Connect

**Symptoms:**
- Device appears in dropdown
- Learning/testing commands fails

**Solutions:**

1. **Test device in Home Assistant**:
   - Developer Tools → Services
   - Service: `remote.send_command`
   - Test with a known command

2. **Check device is online**:
   - Ping device IP address
   - Check device LED/status

3. **Verify device type**:
   - Only RM series support learning
   - Check device model compatibility

4. **Restart device**:
   - Unplug for 10 seconds
   - Plug back in and wait for connection

---

## Command Learning Issues

### Learning Times Out

**Symptoms:**
- "Learning timeout" error
- No signal received message

**Solutions:**

1. **Check device is in learning mode**:
   - LED should indicate learning state
   - Verify in add-on logs

2. **Position remote correctly**:
   - Point directly at Broadlink device
   - Distance: 10-30cm (4-12 inches)
   - No obstacles between remote and device

3. **Press button firmly**:
   - Hold for 1-2 seconds
   - Use fresh batteries in remote

4. **Try multiple times**:
   - Some remotes need multiple attempts
   - Try different buttons

5. **Check device compatibility**:
   - Verify device supports IR/RF learning
   - Some frequencies may not be supported

### Learned Command Doesn't Work

**Symptoms:**
- Command learns successfully
- Testing the command does nothing

**Solutions:**

1. **Re-learn the command**:
   - Delete existing command
   - Learn again with better positioning

2. **Test immediately after learning**:
   - Verify command works right away
   - If not, re-learn

3. **Check target device**:
   - Ensure target device is on
   - Check target device is in range
   - Verify line of sight

4. **Try learning multiple times**:
   - Learn same command 3-5 times
   - Use the one that works best

5. **Check for interference**:
   - Turn off other IR devices
   - Avoid direct sunlight
   - Remove obstacles

---

## Entity Generation Issues

### Auto-Detection Finds No Entities

**Symptoms:**
- Detection returns 0 entities
- Commands exist but not detected

**Solutions:**

1. **Check command naming**:
   - Use standard patterns: `light_on`, `fan_speed_1`
   - See [Command Naming Conventions](API.md#command-naming-conventions)

2. **Review learned commands**:
   - Ensure commands are saved
   - Check command names are correct

3. **Manual entity creation**:
   - Create entities manually via API
   - Specify entity type and commands

4. **Check logs** for detection errors

### Generated YAML Has Errors

**Symptoms:**
- Home Assistant configuration check fails
- YAML syntax errors

**Solutions:**

1. **Check configuration**:
   - Developer Tools → YAML
   - Look for specific error messages

2. **Verify include paths**:
   ```yaml
   light: !include broadlink_manager/entities.yaml
   ```

3. **Check file permissions**:
   ```bash
   ls -la /config/broadlink_manager/
   ```

4. **Regenerate files**:
   - Delete existing files
   - Generate again

5. **Manual YAML review**:
   - Open `/config/broadlink_manager/entities.yaml`
   - Check for syntax errors
   - Verify indentation (2 spaces)

### Entities Don't Appear in Home Assistant

**Symptoms:**
- Configuration check passes
- Entities don't show up after restart

**Solutions:**

1. **Verify includes in configuration.yaml**:
   ```yaml
   light: !include broadlink_manager/entities.yaml
   fan: !include broadlink_manager/entities.yaml
   switch: !include broadlink_manager/entities.yaml
   input_boolean: !include broadlink_manager/helpers.yaml
   input_select: !include broadlink_manager/helpers.yaml
   ```

2. **Check for duplicate includes**:
   - Only include each file once
   - Remove old includes if updating

3. **Restart Home Assistant** (full restart, not just reload)

4. **Check entity registry**:
   - Settings → Devices & Services → Entities
   - Search for entity names

5. **Check logs** for entity loading errors

### Entities Don't Control Devices

**Symptoms:**
- Entities appear in Home Assistant
- Turning on/off does nothing

**Solutions:**

1. **Test commands directly**:
   - Use add-on web interface
   - Test each command individually

2. **Check device_id**:
   - Verify device_id in entity configuration
   - Must match Broadlink device ID

3. **Check command names**:
   - Verify command names match learned commands
   - Case-sensitive

4. **Check helper entities**:
   - Ensure input_boolean helpers exist
   - Check input_select for fans

5. **Review entity YAML**:
   - Check service calls are correct
   - Verify target device_id

---

## Performance Issues

### Web Interface is Slow

**Solutions:**

1. **Check system resources**:
   - CPU usage
   - Memory usage
   - Disk I/O

2. **Reduce log level**:
   ```yaml
   log_level: warning
   ```

3. **Clear browser cache**

4. **Restart add-on**

### Command Execution is Slow

**Solutions:**

1. **Check network latency**:
   - Ping Broadlink device
   - Check Wi-Fi signal strength

2. **Reduce command complexity**:
   - Use simpler automations
   - Avoid rapid command sequences

3. **Check device firmware**:
   - Update Broadlink device firmware
   - Check for device issues

---

## Debug Mode

Enable detailed logging for troubleshooting:

```yaml
log_level: debug
```

This will show:
- API requests and responses
- Command detection logic
- Entity generation steps
- Device communication details

**Note:** Debug mode generates large log files. Use only for troubleshooting.

---

## Collecting Diagnostic Information

When reporting issues, include:

1. **Add-on version**: Check config.yaml
2. **Home Assistant version**: Settings → About
3. **Architecture**: Settings → System → Hardware
4. **Device model**: Broadlink device model
5. **Configuration**: Your add-on configuration (remove sensitive data)
6. **Broadlink commands file**: Located in /config/.storage/broadlink_remote_***_codes (if you are comfortable with the file contents)
7. **Logs**: Relevant log excerpts (enable debug mode)
8. **Steps to reproduce**: Detailed steps
9. **Expected vs actual behavior**

---

## Getting Help

### Before Asking for Help

1. **Read this guide** thoroughly
2. **Check existing issues** on GitHub
3. **Enable debug logging** and review logs
4. **Try basic troubleshooting** steps

### Where to Get Help

1. **GitHub Issues**: [Report a bug](https://github.com/tonyperkins/homeassistant-broadlink-manager/issues)
2. **Home Assistant Community**: [Community Forums](https://community.home-assistant.io/)
3. **Discord**: Home Assistant Discord server
4. **Documentation**: Review all documentation files

### Creating a Good Issue Report

Include:
- Clear title describing the issue
- Detailed description
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment information
- Relevant logs
- Screenshots (if applicable)

---

## Common Error Messages

### "Device not found"
- Device not configured in Home Assistant
- Device offline
- Wrong device name

### "Command not found"
- Command not learned
- Wrong command name
- Device name mismatch

### "Learning timeout"
- Remote too far away
- Weak remote batteries
- Device not in learning mode

### "Invalid entity configuration"
- Missing required commands
- Wrong entity type
- Invalid command mapping

### "File permission denied"
- Add-on lacks write access
- Check config:rw in config.yaml

### "Port already in use"
- Another service using port 8099
- Change web_port in configuration

---

## Reset and Recovery

### Reset Entity Configuration

```bash
# Backup first
cp /config/broadlink_manager/metadata.json /config/metadata.json.backup

# Delete metadata
rm /config/broadlink_manager/metadata.json

# Restart add-on
```

### Complete Reset

```bash
# Backup entire directory
cp -r /config/broadlink_manager /config/broadlink_manager.backup

# Remove directory
rm -rf /config/broadlink_manager

# Restart add-on (will recreate directory)
```

### Restore from Backup

```bash
# Restore directory
cp -r /config/broadlink_manager.backup /config/broadlink_manager

# Restart add-on
```

---

## Still Having Issues?

If you've tried everything in this guide and still have problems:

1. **Create a detailed issue report** on GitHub
2. **Include all diagnostic information**
3. **Be patient** - maintainers are volunteers
4. **Consider contributing** a fix if you find the solution

Thank you for using Broadlink Manager! 🎉
