# High Priority Issues

High priority issues represent significant performance problems, major architectural flaws, or serious maintainability concerns. These should be addressed in the next development cycle.

---

## HIGH-001: Monolithic web_server.py (3,400+ Lines)

### Description
The `web_server.py` file has grown to over 3,400 lines, violating the Single Responsibility Principle. It contains route definitions, business logic, Home Assistant integration, WebSocket handling, file watching, caching, and more.

### Location
- **File:** `app/web_server.py`
- **Lines:** 1-3423

### Impact
- **Maintainability:** Extremely difficult to navigate and modify
- **Testing:** Hard to unit test individual components
- **Code Reuse:** Difficult to reuse functionality
- **Cognitive Load:** High mental overhead for developers

### Evidence
```
File sizes:
- web_server.py: 157,403 bytes (3,400+ lines)
- api/commands.py: 71,780 bytes (1,800+ lines)
- api/smartir.py: 74,993 bytes (1,700+ lines)
```

### Recommendation
Refactor into separate modules:

```
app/
├── server/
│   ├── __init__.py
│   ├── app.py              # Flask app initialization
│   ├── middleware.py       # IngressMiddleware
│   └── routes.py           # Legacy route definitions (migrate to blueprints)
├── services/
│   ├── __init__.py
│   ├── ha_api.py           # _make_ha_request, HA API calls
│   ├── command_service.py  # _learn_command, _send_command, _delete_command
│   ├── storage_service.py  # _get_all_broadlink_commands, cache logic
│   └── notification_service.py  # WebSocket, notifications
├── background/
│   ├── __init__.py
│   ├── polling.py          # Command polling thread
│   └── file_watcher.py     # DevicesJsonWatcher
└── api/
    ├── __init__.py
    ├── commands.py
    ├── devices.py
    ├── smartir.py
    └── entities.py         # Move entity routes from web_server.py
```

### Effort Level
**Significant** - 2-3 sprints of work with careful testing

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## HIGH-002: Dual Storage System Confusion

### Description
The application uses two separate storage systems (`devices.json` via DeviceManager and `metadata.json` via StorageManager) for backward compatibility with v1, but there are no v1 users. This causes confusion and bugs where devices appear in one system but not the other.

### Location
- **Files:** 
  - `app/device_manager.py` - manages `devices.json`
  - `app/storage_manager.py` - manages `metadata.json`
  - `app/api/devices.py` - uses both

### Impact
- **Data Integrity:** Devices can exist in one file but not the other
- **Code Complexity:** Dual lookups and sync logic
- **Developer Confusion:** Which manager to use for what operation?

### Evidence
From memory/documentation:
> **Issue**: App uses both devices.json (DeviceManager) and metadata.json (StorageManager) for backward compatibility with v1, but there are no v1 users.

### Recommendation
1. Remove `storage_manager.py` entirely
2. Update all device operations to use only `DeviceManager`
3. Remove migration logic (`migration_manager.py`)
4. Update entity generation to work directly with `devices.json`

```python
# BEFORE (in api/devices.py)
storage = get_storage_manager()  # metadata.json
device_manager = get_device_manager()  # devices.json

# AFTER
device_manager = get_device_manager()  # Only devices.json
```

### Effort Level
**Significant** - Requires careful migration and testing

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## HIGH-003: Duplicate API Endpoints

### Description
Many API endpoints are defined both in `web_server.py` (inline) and in `api/*.py` (blueprints), leading to confusion about which endpoint is actually being called and potential for behavior divergence.

### Location
- **Files:** 
  - `app/web_server.py` - lines 305-500+ (inline routes)
  - `app/api/devices.py` - blueprint routes
  - `app/api/commands.py` - blueprint routes

### Impact
- **Maintenance:** Changes may need to be made in multiple places
- **Behavior:** Different endpoints might handle errors differently
- **Testing:** Which endpoint is being tested?

### Evidence
Duplicate endpoint examples:
```python
# In web_server.py:
@self.app.route("/api/devices")
def get_broadlink_devices():

# In api/devices.py:
@api_bp.route("/devices", methods=["GET"])
def get_devices():
```

### Recommendation
1. Audit all endpoints in `web_server.py`
2. Move unique functionality to appropriate blueprint
3. Remove duplicates from `web_server.py`
4. Ensure all routes are documented

### Effort Level
**Moderate** - 1 sprint with careful testing

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## HIGH-004: Event Loop Created Per Request

### Description
Each HTTP request that needs async functionality creates a new event loop, runs the async code, and destroys the loop. This is inefficient and can cause issues with shared resources.

### Location
- **File:** `app/web_server.py`
- **Pattern appears:** 40+ times

### Evidence
```python
@self.app.route("/api/areas")
def get_areas():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        areas = loop.run_until_complete(self._get_ha_areas("GET /api/areas"))
        loop.close()
        return jsonify(areas)
```

### Impact
- **Performance:** Event loop creation is expensive
- **Resources:** Potential resource leaks if exception occurs before `loop.close()`
- **Scalability:** Limits concurrent request handling

### Recommendation
Use a proper async framework or maintain a single event loop:

**Option A:** Use Flask with async support (Flask 2.0+)
```python
@self.app.route("/api/areas")
async def get_areas():
    areas = await self._get_ha_areas("GET /api/areas")
    return jsonify(areas)
```

**Option B:** Use a shared event loop with thread-safe execution
```python
# In __init__
self._loop = asyncio.new_event_loop()
self._executor = ThreadPoolExecutor(max_workers=4)

def _run_async(self, coro):
    """Run coroutine in the shared event loop"""
    return asyncio.run_coroutine_threadsafe(coro, self._loop).result()
```

**Option C:** Switch to an async framework (Quart, FastAPI)
- Better long-term solution but significant refactoring

### Effort Level
**Moderate** - 1-2 sprints depending on approach

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## HIGH-005: No Input Validation on Many Endpoints

### Description
Many API endpoints accept user input without validation, potentially allowing injection attacks or causing unexpected errors.

### Location
- **Files:** 
  - `app/web_server.py`
  - `app/api/commands.py`
  - `app/api/devices.py`

### Evidence
```python
@self.app.route("/api/devices/managed", methods=["POST"])
def create_managed_device():
    try:
        data = request.get_json()
        device_name = data.get("device_name")  # No validation
        storage_name = data.get("device")       # No validation
        # ... used directly
```

### Impact
- **Security:** Potential for injection attacks
- **Stability:** Malformed input can crash the application
- **Data Integrity:** Invalid data can corrupt storage

### Recommendation
Add input validation using a schema validation library:

```python
from marshmallow import Schema, fields, validate, ValidationError

class DeviceCreateSchema(Schema):
    device_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    device = fields.Str(allow_none=True)
    entity_type = fields.Str(required=True, validate=validate.OneOf(
        ['light', 'fan', 'switch', 'media_player', 'cover', 'climate']
    ))
    broadlink_entity = fields.Str(required=True, validate=validate.Regexp(r'^remote\..+$'))
    icon = fields.Str(allow_none=True)

@self.app.route("/api/devices/managed", methods=["POST"])
def create_managed_device():
    try:
        schema = DeviceCreateSchema()
        data = schema.load(request.get_json())
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
```

### Effort Level
**Moderate** - Add validation incrementally to each endpoint

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## HIGH-006: Debug Print Statements in Production

### Description
Debug print statements are left in production code, which is unprofessional and can leak sensitive information to stdout.

### Location
- **File:** `app/web_server.py`
- **Lines:** 1006-1008

### Evidence
```python
@self.app.route("/api/devices/managed", methods=["POST"])
def create_managed_device():
    print("=" * 80)
    print("🔵 POST /api/devices/managed endpoint hit!")
    print("=" * 80)
```

### Impact
- **Professionalism:** Looks unprofessional in container logs
- **Performance:** Minor overhead
- **Security:** Could leak sensitive data if print statements expand

### Recommendation
Remove print statements and use logging instead:

```python
@self.app.route("/api/devices/managed", methods=["POST"])
def create_managed_device():
    logger.info("POST /api/devices/managed endpoint hit")
```

Or use a debug flag:
```python
if logger.isEnabledFor(logging.DEBUG):
    logger.debug("POST /api/devices/managed endpoint hit")
```

### Effort Level
**Quick Win** - Global search and replace

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## Summary

| ID | Issue | Impact | Effort | Status |
|----|-------|--------|--------|--------|
| HIGH-001 | Monolithic web_server.py | Maintainability | Significant | Pending |
| HIGH-002 | Dual storage system | Data integrity | Significant | Pending |
| HIGH-003 | Duplicate API endpoints | Maintenance | Moderate | Pending |
| HIGH-004 | Event loop per request | Performance | Moderate | Pending |
| HIGH-005 | No input validation | Security | Moderate | Pending |
| HIGH-006 | Debug print statements | Professionalism | Quick Win | Pending |

**Total High Priority Issues:** 6

Start with HIGH-006 (Quick Win), then address HIGH-001 and HIGH-002 together as they are related architectural issues.
