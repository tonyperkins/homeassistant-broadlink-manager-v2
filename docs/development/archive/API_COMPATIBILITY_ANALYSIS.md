# API Compatibility Analysis: Standalone vs Docker vs HA Add-on

## Overview

This document analyzes the Home Assistant API calls made by Broadlink Manager and verifies their availability across all deployment scenarios:
- **Standalone** - Running outside HA with network access
- **Docker** - Running in a Docker container with network access to HA
- **HA Add-on** - Running as a Supervisor add-on inside HA

## Deployment Mode Detection

The application automatically detects the deployment mode in `config_loader.py`:

```python
def _detect_supervisor_environment(self) -> bool:
    return os.environ.get("SUPERVISOR_TOKEN") is not None
```

### Mode-Specific Configuration

| Configuration | Standalone | Docker | HA Add-on |
|--------------|------------|--------|-----------|
| **HA URL** | `HA_URL` env var or `http://localhost:8123` | `HA_URL` env var | `http://supervisor/core` |
| **Auth Token** | `HA_TOKEN` (long-lived) | `HA_TOKEN` (long-lived) | `SUPERVISOR_TOKEN` (auto-provided) |
| **Config Path** | `HA_CONFIG_PATH` or `/config` | `/config` (mounted) | `/config` (auto-mounted) |

## API Endpoints Used

### 1. Core REST API Endpoints

#### ✅ `/api/states` - Get All States
**Usage**: Get all entity states, including Broadlink devices and notifications
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:417, 1976, 2126`

```python
states = await self._make_ha_request("GET", "states")
```

#### ✅ `/api/states/{entity_id}` - Get Specific State
**Usage**: Get status of specific Broadlink device
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:1244, 1285, 1884`

```python
entity_state = await self._make_ha_request("GET", f"states/{entity_id}")
```

#### ✅ `/api/services` - Get Available Services
**Usage**: Check what services are available
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:1850`

```python
services_result = await self._make_ha_request("GET", "services")
```

---

### 2. Service Call Endpoints

#### ✅ `/api/services/remote/learn_command` - Learn IR/RF Command
**Usage**: Trigger Broadlink device to learn a command
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:1924, 1946`

```python
result = await self._make_ha_request(
    "POST", "services/remote/learn_command", service_payload
)
```

**Formats Supported**:
- Modern format: `{"target": {"entity_id": "..."}, "data": {...}}`
- Legacy format: `{"entity_id": "...", "device": "...", "command": "..."}`

#### ✅ `/api/services/remote/delete_command` - Delete Command
**Usage**: Delete a learned command from Broadlink storage
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:2043, 2545`

```python
result = await self._make_ha_request(
    "POST", "services/remote/delete_command", service_data
)
```

#### ✅ `/api/services/remote/send_command` - Send Command
**Usage**: Send a learned command to a device
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:2329, 2346, 2366`

```python
result = await self._make_ha_request(
    "POST", "services/remote/send_command", payload
)
```

---

### 3. Notification Endpoints

#### ✅ `/api/persistent_notification` - Get Notifications
**Usage**: Get persistent notifications (for learning status)
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `web_server.py:2060`

```python
pn_notifications = await self._make_ha_request("GET", "persistent_notification")
```

**Fallback**: If this endpoint fails, falls back to filtering `/api/states` for `persistent_notification.*` entities.

---

### 4. Configuration Endpoints

#### ⚠️ `/api/config/config_entries/entry` - Get Config Entries
**Usage**: Get list of integration config entries (for reloading Broadlink)
**Availability**: ⚠️ **RESTRICTED in Add-on mode**
**Restrictions**: **May require additional permissions in Supervisor**
**Code**: `web_server.py:2491`

```python
result = await self._make_ha_request("GET", "config/config_entries/entry")
```

**Issue**: This endpoint accesses internal configuration which may be restricted when running as an add-on.

#### ⚠️ `/api/config/config_entries/entry/{entry_id}/reload` - Reload Config Entry
**Usage**: Reload Broadlink integration after changes
**Availability**: ⚠️ **RESTRICTED in Add-on mode**
**Restrictions**: **May require additional permissions in Supervisor**
**Code**: `web_server.py:2504`

```python
reload_result = await self._make_ha_request(
    "POST", f"config/config_entries/entry/{entry_id}/reload"
)
```

**Issue**: Config entry manipulation may be restricted in add-on mode.

---

### 5. WebSocket API (Area Manager)

#### ✅ `config/area_registry/list` - List Areas
**Usage**: Get all areas for device assignment
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `area_manager.py:103`

```python
areas = await self._send_ws_command("config/area_registry/list")
```

#### ✅ `config/area_registry/create` - Create Area
**Usage**: Create new area
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `area_manager.py:118`

```python
new_area = await self._send_ws_command(
    "config/area_registry/create", name=area_name
)
```

#### ✅ `config/entity_registry/update` - Update Entity
**Usage**: Assign entity to area
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `area_manager.py:147`

```python
result = await self._send_ws_command(
    "config/entity_registry/update",
    entity_id=entity_id,
    area_id=area_id
)
```

#### ✅ `config/entity_registry/get` - Get Entity Info
**Usage**: Check if entity exists
**Availability**: ✅ All modes
**Restrictions**: None
**Code**: `area_manager.py:175`

```python
entity_info = await self._send_ws_command(
    "config/entity_registry/get",
    entity_id=entity_id
)
```

---

## Potential Issues by Deployment Mode

### Standalone Mode ✅
**Status**: All APIs work
**Requirements**:
- `HA_TOKEN` environment variable (long-lived access token)
- `HA_URL` environment variable
- Network access to Home Assistant

**No restrictions** - Full API access with proper authentication.

---

### Docker Mode ✅
**Status**: All APIs work
**Requirements**:
- `HA_TOKEN` environment variable (long-lived access token)
- `HA_URL` environment variable
- `/config` volume mounted to HA config directory
- Network access to Home Assistant

**No restrictions** - Same as standalone, just containerized.

---

### HA Add-on Mode ⚠️
**Status**: Most APIs work, some may be restricted
**Requirements**:
- `SUPERVISOR_TOKEN` (automatically provided)
- Uses `http://supervisor/core` for API access
- `/config` automatically mounted

**Potential Restrictions**:

1. **Config Entry Endpoints** ⚠️
   - `/api/config/config_entries/entry` - May be restricted
   - `/api/config/config_entries/entry/{entry_id}/reload` - May be restricted
   
   **Impact**: The "Reload Broadlink Integration" feature may not work in add-on mode.
   
   **Workaround**: Users can manually reload the Broadlink integration from HA UI.

2. **File System Access** ✅
   - Reading Broadlink storage files: ✅ Works (same filesystem)
   - Writing entity YAML files: ✅ Works (same filesystem)

3. **Service Calls** ✅
   - All `remote.*` services: ✅ Work normally
   - Area management: ✅ Works normally

---

## Recommendations

### 1. Add Permission Checks

Add runtime checks for restricted endpoints:

```python
async def _check_api_permissions(self) -> Dict[str, bool]:
    """Check which API endpoints are available"""
    permissions = {
        "config_entries": False,
        "config_reload": False,
    }
    
    try:
        # Try to access config entries
        result = await self._make_ha_request("GET", "config/config_entries/entry")
        permissions["config_entries"] = result is not None
    except Exception as e:
        logger.warning(f"Config entries API not available: {e}")
    
    return permissions
```

### 2. Graceful Degradation

Modify the reload function to handle restrictions:

```python
async def _reload_broadlink_integration(self):
    """Reload Broadlink integration (may not work in add-on mode)"""
    if self.config_loader.is_supervisor:
        logger.warning(
            "Config entry reload may not be available in add-on mode. "
            "Please reload the Broadlink integration manually from HA UI if needed."
        )
        return {"success": False, "reason": "restricted_in_addon_mode"}
    
    # Proceed with reload for standalone/docker modes
    try:
        result = await self._make_ha_request("GET", "config/config_entries/entry")
        # ... rest of reload logic
    except Exception as e:
        logger.error(f"Failed to reload integration: {e}")
        return {"success": False, "error": str(e)}
```

### 3. Update Documentation

Add a note in the UI and documentation:

```markdown
**Note for Add-on Users**: The "Reload Broadlink Integration" button may not work 
when running as a Home Assistant add-on due to security restrictions. If you need 
to reload the Broadlink integration, please do so manually from:
Settings → Devices & Services → Broadlink → ⋮ → Reload
```

### 4. Update Mock for Testing

The test mocks should handle both modes:

```python
@pytest.fixture
def mock_ha_api_addon_mode():
    """Mock HA API with add-on restrictions"""
    api = MockHAAPI()
    
    # Simulate restricted endpoints
    def restricted_request(method, endpoint, data=None):
        if "config/config_entries" in endpoint:
            raise PermissionError("Access denied in add-on mode")
        return api.make_request(method, endpoint, data)
    
    api.make_request = restricted_request
    return api
```

---

## Summary

### ✅ Fully Compatible (All Modes)
- ✅ Get states
- ✅ Get specific entity state
- ✅ Learn commands
- ✅ Delete commands
- ✅ Send commands
- ✅ Get notifications
- ✅ Area management (WebSocket)
- ✅ Entity registry operations
- ✅ File system access (Broadlink storage, entity YAML)

### ⚠️ Potentially Restricted (Add-on Mode Only)
- ⚠️ Get config entries
- ⚠️ Reload config entries

### 📊 Compatibility Score
- **Standalone**: 100% (12/12 endpoints)
- **Docker**: 100% (12/12 endpoints)
- **HA Add-on**: 83% (10/12 endpoints - 2 may be restricted)

---

## Testing Recommendations

### 1. Test in All Modes
Create tests for each deployment mode:

```python
@pytest.mark.parametrize("mode", ["standalone", "docker", "addon"])
async def test_api_compatibility(mode):
    # Test all API endpoints in each mode
    pass
```

### 2. Mock Supervisor Restrictions
Create mocks that simulate add-on restrictions:

```python
@pytest.fixture
def mock_supervisor_restrictions():
    """Mock API with supervisor restrictions"""
    # Return 403 for restricted endpoints
    pass
```

### 3. Integration Tests
Test actual deployment in each mode:
- Standalone: Test with real HA instance
- Docker: Test in Docker container
- Add-on: Test as actual HA add-on

---

## Action Items

1. ✅ **Document API compatibility** (this document)
2. ⏳ **Add permission checks** to `web_server.py`
3. ⏳ **Implement graceful degradation** for restricted endpoints
4. ⏳ **Update UI** to show warnings in add-on mode
5. ⏳ **Add tests** for add-on mode restrictions
6. ⏳ **Update user documentation** about limitations

---

## Conclusion

The Broadlink Manager is **highly compatible** across all deployment modes:
- **Core functionality** (learning, deleting, sending commands) works in all modes
- **Area management** works in all modes
- **File operations** work in all modes
- **Only limitation**: Config entry reload may not work in add-on mode (minor feature)

**Recommendation**: The current implementation is safe for all deployment modes. The config entry reload feature should be wrapped with proper error handling and user messaging for add-on mode.
