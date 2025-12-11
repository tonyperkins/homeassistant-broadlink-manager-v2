# Medium Priority Issues

Medium priority issues represent code quality issues, minor security concerns, or moderate technical debt. These should be addressed as part of regular maintenance.

---

## MED-001: Flake8 Exceptions for web_server.py

### Description
The `.flake8` configuration file has specific exceptions for `web_server.py`, suggesting known code quality issues that have been suppressed rather than fixed.

### Location
- **File:** `.flake8`
- **Lines:** 4-5

### Evidence
```ini
per-file-ignores =
    web_server.py:E501,F811,E722,F841
```

Ignored errors:
- **E501:** Line too long (>127 characters)
- **F811:** Redefinition of unused name
- **E722:** Bare `except:` clause
- **F841:** Local variable assigned but never used

### Impact
- **Code Quality:** Suppresses legitimate warnings
- **Technical Debt:** Problems accumulate over time
- **Maintenance:** Makes it harder to spot real issues

### Recommendation
1. Fix the underlying issues in `web_server.py`
2. Remove the per-file ignores
3. Or, if specific ignores are needed, use inline comments with explanations:

```python
# noqa: E501 - Complex URL construction requires long line
url = f"{self.ha_url}/api/services/remote/learn_command?..."
```

### Effort Level
**Moderate** - Fix issues as part of HIGH-001 refactoring

---

## MED-002: Bare Except Clauses

### Description
Several places use bare `except:` clauses which catch all exceptions including `KeyboardInterrupt` and `SystemExit`, making debugging difficult and potentially hiding serious errors.

### Location
- **File:** `app/web_server.py`
- **Multiple locations**

### Evidence
```python
# Line 1314
try:
    return await response.json() if response_text else {}
except:
    logger.info(
        "POST response was successful but not JSON, returning empty dict"
    )
    return {}
```

### Impact
- **Debugging:** Hides actual exception types and messages
- **Reliability:** May catch exceptions that should propagate
- **Logging:** Lost exception details

### Recommendation
Catch specific exceptions:

```python
try:
    return await response.json() if response_text else {}
except json.JSONDecodeError:
    logger.info("POST response was successful but not valid JSON")
    return {}
except Exception as e:
    logger.warning(f"Unexpected error parsing response: {e}")
    return {}
```

### Effort Level
**Quick Win** - Fix each occurrence individually

---

## MED-003: Inconsistent Error Response Format

### Description
API endpoints return errors in inconsistent formats, making it difficult for frontend code to handle errors uniformly.

### Location
- Various API endpoints across `app/api/*.py` and `app/web_server.py`

### Evidence
```python
# Format 1: {"error": "message"}
return jsonify({"error": "Device not found"}), 404

# Format 2: {"success": False, "error": "message"}
return jsonify({"success": False, "error": "Failed"}), 400

# Format 3: {"success": False, "message": "error message"}
return jsonify({"success": False, "message": "Error occurred"}), 500
```

### Impact
- **Frontend Complexity:** Must handle multiple error formats
- **User Experience:** Inconsistent error display
- **API Documentation:** Hard to document error responses

### Recommendation
Standardize error response format:

```python
def error_response(message, status_code=400, details=None):
    """Create a standardized error response"""
    response = {
        "success": False,
        "error": {
            "message": message,
            "code": status_code
        }
    }
    if details:
        response["error"]["details"] = details
    return jsonify(response), status_code

# Usage:
return error_response("Device not found", 404)
return error_response("Validation failed", 400, {"field": "name", "issue": "required"})
```

### Effort Level
**Moderate** - Requires updating all endpoints

---

## MED-004: No Rate Limiting

### Description
API endpoints have no rate limiting, making them vulnerable to abuse and denial of service attacks.

### Location
- All API endpoints

### Impact
- **Security:** DoS vulnerability
- **Resources:** Unconstrained resource usage
- **HA Integration:** Could overwhelm Home Assistant API

### Recommendation
Add Flask-Limiter:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=self.app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Apply to sensitive endpoints
@self.app.route("/api/learn", methods=["POST"])
@limiter.limit("10 per minute")
def learn_command():
    ...
```

### Effort Level
**Moderate** - Add limiter with sensible defaults

---

## MED-005: No HTTP Connection Pooling

### Description
Each async HTTP request to Home Assistant creates a new `aiohttp.ClientSession`, which is inefficient and doesn't take advantage of connection reuse.

### Location
- **File:** `app/web_server.py`
- **Method:** `_make_ha_request`

### Evidence
```python
async def _make_ha_request(self, method: str, endpoint: str, data=None):
    async with aiohttp.ClientSession() as session:  # New session every time
        ...
```

### Impact
- **Performance:** Connection overhead for each request
- **Resources:** More socket/memory usage
- **Latency:** No TCP connection reuse

### Recommendation
Create a shared session:

```python
class BroadlinkWebServer:
    def __init__(self, ...):
        ...
        self._session = None
    
    async def _get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {self.ha_token}"},
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self._session
    
    async def _make_ha_request(self, method: str, endpoint: str, data=None):
        session = await self._get_session()
        url = f"{self.ha_url}/api/{endpoint}"
        ...
```

### Effort Level
**Moderate** - Refactor session management

---

## MED-006: Silent Failures in Background Threads

### Description
Background threads (polling, file watching) catch exceptions but may not adequately report them, leading to silent failures that are hard to diagnose.

### Location
- **File:** `app/web_server.py`
- **Methods:** `_poll_pending_commands`, `DevicesJsonWatcher`

### Evidence
```python
def _poll_pending_commands(self):
    while True:
        try:
            # ... polling logic
        except Exception as e:
            logger.error(f"Error in polling thread: {e}")
            time.sleep(5)  # Continue silently after error
```

### Impact
- **Observability:** Hard to know when background tasks fail
- **Reliability:** Issues may go unnoticed
- **Debugging:** Limited context on failures

### Recommendation
1. Add health check endpoint for background tasks
2. Add retry count limits with exponential backoff
3. Consider using a task queue (Celery) for robust background processing

```python
def _poll_pending_commands(self):
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    while True:
        try:
            # ... polling logic
            consecutive_errors = 0  # Reset on success
        except Exception as e:
            consecutive_errors += 1
            logger.error(
                f"Error in polling thread (attempt {consecutive_errors}): {e}",
                exc_info=True  # Include stack trace
            )
            
            if consecutive_errors >= max_consecutive_errors:
                logger.critical(
                    f"Polling thread failed {max_consecutive_errors} times, stopping"
                )
                self.poll_thread_running = False
                break
                
            backoff = min(60, 5 * (2 ** consecutive_errors))  # Exponential backoff
            time.sleep(backoff)
```

### Effort Level
**Quick Win** - Add logging and error counting

---

## MED-007: Duplicate Fixture in conftest.py

### Description
The `mock_ha_api` fixture is defined twice in `tests/conftest.py`, which could lead to unexpected behavior.

### Location
- **File:** `tests/conftest.py`
- **Lines:** 83-103 and 174-198

### Evidence
```python
@pytest.fixture
def mock_ha_api():
    """Mock Home Assistant API responses"""
    mock = Mock()
    # ... first definition

# Later in the file...

@pytest.fixture
def mock_ha_api():
    """Mock Home Assistant REST API"""
    api = MockHAAPI()
    # ... second definition (overrides first)
```

### Impact
- **Test Reliability:** First definition is never used
- **Confusion:** Which mock is being used in tests?

### Recommendation
Remove the duplicate or rename to be more specific:

```python
@pytest.fixture
def mock_ha_api_simple():
    """Simple mock for basic tests"""
    mock = Mock()
    ...

@pytest.fixture
def mock_ha_api_full():
    """Full mock with devices and areas"""
    api = MockHAAPI()
    ...
```

### Effort Level
**Quick Win** - Rename or remove duplicate

---

## MED-008: Magic Numbers Throughout Codebase

### Description
Numeric constants are used directly in code without named constants, making their purpose unclear and maintenance difficult.

### Location
- Various files throughout the codebase

### Evidence
```python
# In web_server.py
self.DELETION_CACHE_TTL = 30  # Good - named constant
self.POLL_TIMEOUT = 60        # Good - named constant

# But elsewhere:
time.sleep(5)  # What does 5 mean?
if elapsed < 10:  # Why 10?
await asyncio.sleep(0.5)  # What's special about 0.5?
```

### Impact
- **Readability:** Purpose of numbers unclear
- **Maintenance:** Hard to change consistently
- **Documentation:** No explanation of business rules

### Recommendation
Create a constants module:

```python
# app/constants.py
class TimeoutSeconds:
    POLL_INTERVAL = 3
    POLL_TIMEOUT = 60
    WEBSOCKET_RECONNECT = 5
    CACHE_TTL = 60
    DELETION_CACHE_TTL = 30
    HTTP_REQUEST_TIMEOUT = 30
    
class Limits:
    MAX_RETRIES = 10
    MAX_CONSECUTIVE_ERRORS = 10
    DEBOUNCE_INTERVAL = 0.1
```

### Effort Level
**Moderate** - Extract constants and update references

---

## MED-009: Missing Frontend Unit Tests

### Description
The frontend Vue.js code has no unit tests, making it risky to refactor components.

### Location
- **Directory:** `frontend/src/`

### Evidence
- No `__tests__` or `*.spec.js` files in frontend
- `package.json` has no test dependencies (Vitest, Jest, etc.)

### Impact
- **Regression Risk:** Changes may break existing functionality
- **Confidence:** Can't verify components work correctly
- **Refactoring:** Risky to improve code without tests

### Recommendation
1. Add Vitest for unit testing
2. Add Vue Test Utils for component testing
3. Start with critical components (DeviceList, CommandLearner)

```json
// package.json
{
  "devDependencies": {
    "@vue/test-utils": "^2.4.0",
    "vitest": "^1.0.0",
    "@vitest/coverage-v8": "^1.0.0"
  },
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest --coverage"
  }
}
```

### Effort Level
**Significant** - Add testing infrastructure and write initial tests

---

## MED-010: API Documentation Incomplete

### Description
API endpoints are not fully documented, making it difficult for developers to understand available functionality.

### Location
- **File:** `docs/API.md` (if exists)

### Impact
- **Developer Experience:** Hard to understand API
- **Integration:** Difficult for others to integrate
- **Maintenance:** API contract unclear

### Recommendation
Add OpenAPI/Swagger documentation:

```python
# Using Flask-RESTX or flasgger
from flask_restx import Api, Resource, fields

api = Api(self.app, 
    title='Broadlink Manager API',
    version='2.0',
    description='API for managing Broadlink devices'
)

device_model = api.model('Device', {
    'id': fields.String(required=True, description='Device ID'),
    'name': fields.String(required=True, description='Device name'),
    'entity_type': fields.String(enum=['light', 'fan', 'switch']),
})

@api.route('/devices/managed')
class DeviceList(Resource):
    @api.doc('list_devices')
    @api.marshal_list_with(device_model)
    def get(self):
        """List all managed devices"""
        ...
```

### Effort Level
**Moderate** - Add documentation incrementally

---

## MED-011: Tight Coupling Between Components

### Description
Components have direct dependencies on each other rather than through interfaces, making testing and modification difficult.

### Location
- Various files in `app/`

### Evidence
```python
# web_server.py directly instantiates dependencies
self.device_manager = DeviceManager(...)
self.smartir_detector = SmartIRDetector(...)
self.smartir_code_service = SmartIRCodeService(...)

# API routes access these through app.config
device_manager = current_app.config.get("device_manager")
```

### Impact
- **Testing:** Hard to substitute mocks
- **Flexibility:** Can't easily swap implementations
- **Coupling:** Changes ripple through codebase

### Recommendation
Implement dependency injection:

```python
# container.py
class Container:
    def __init__(self, config_loader):
        self.config_loader = config_loader
        self._device_manager = None
        
    @property
    def device_manager(self):
        if self._device_manager is None:
            self._device_manager = DeviceManager(
                str(self.config_loader.get_broadlink_manager_path())
            )
        return self._device_manager

# In web_server.py
def __init__(self, container: Container):
    self.container = container
    self.device_manager = container.device_manager
```

### Effort Level
**Significant** - Architecture change

---

## MED-012: Inconsistent Async/Sync Pattern

### Description
The codebase mixes synchronous Flask routes with async operations in an inconsistent pattern, creating complexity and potential race conditions.

### Location
- **File:** `app/web_server.py`

### Evidence
```python
# Sync route calling async code
@self.app.route("/api/areas")
def get_areas():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    areas = loop.run_until_complete(self._get_ha_areas(...))
    loop.close()
    return jsonify(areas)
```

### Impact
- **Complexity:** Hard to reason about execution
- **Performance:** Event loop overhead (see HIGH-004)
- **Maintenance:** Two paradigms to maintain

### Recommendation
Choose one pattern:
1. Convert to fully async (Flask 2.0+ async routes or switch to Quart/FastAPI)
2. Make HA operations synchronous using `requests` library

### Effort Level
**Significant** - Architectural decision and refactoring

---

## Summary

| ID | Issue | Impact | Effort |
|----|-------|--------|--------|
| MED-001 | Flake8 exceptions | Code quality | Moderate |
| MED-002 | Bare except clauses | Debugging | Quick Win |
| MED-003 | Inconsistent error format | Frontend complexity | Moderate |
| MED-004 | No rate limiting | Security | Moderate |
| MED-005 | No connection pooling | Performance | Moderate |
| MED-006 | Silent thread failures | Observability | Quick Win |
| MED-007 | Duplicate fixture | Test reliability | Quick Win |
| MED-008 | Magic numbers | Readability | Moderate |
| MED-009 | No frontend tests | Regression risk | Significant |
| MED-010 | Incomplete API docs | Developer experience | Moderate |
| MED-011 | Tight coupling | Testability | Significant |
| MED-012 | Inconsistent async/sync | Complexity | Significant |

**Total Medium Priority Issues:** 12
