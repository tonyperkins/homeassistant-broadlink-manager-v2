# Critical Issues

Critical issues represent security vulnerabilities, data loss risks, or issues that could cause system failures. These must be addressed immediately.

---

## CRIT-001: Token Exposed via Debug Endpoint

### Description
The Home Assistant authentication token is exposed via an unauthenticated debug endpoint, allowing anyone with network access to obtain the token and gain full access to the Home Assistant instance.

### Location
- **File:** `app/web_server.py`
- **Lines:** 376-390

```python
@self.app.route("/api/debug/token")
def get_token():
    """Get supervisor token for WebSocket authentication"""
    try:
        # For add-on context, we need to check if supervisor token works
        # If not, we'll need to use alternative authentication
        logger.info(f"Providing token for WebSocket: {self.ha_token[:20]}...")
        return jsonify(
            {
                "token": self.ha_token,
            }
        )
    except Exception as e:
        logger.error(f"Error getting token: {e}")
        return jsonify({"error": str(e)}), 500
```

### Impact
- **Security Risk:** HIGH - Full Home Assistant access
- **Attack Vector:** Any user on the network can access this endpoint
- **Data at Risk:** Complete HA configuration, tokens, integrations

### Recommendation
**Option A (Recommended):** Remove the endpoint entirely
```python
# DELETE THIS ENDPOINT - Token should never be exposed
# @self.app.route("/api/debug/token")
# def get_token():
#     ...
```

**Option B:** If needed for debugging, add authentication and restrict to development mode only
```python
@self.app.route("/api/debug/token")
def get_token():
    if not self.app.debug:
        return jsonify({"error": "Debug endpoints disabled in production"}), 403
    # Require some form of local authentication
    ...
```

### Effort Level
**Quick Win** - Can be fixed by removing ~15 lines of code

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## CRIT-002: Global CORS Without Restrictions

### Description
CORS (Cross-Origin Resource Sharing) is enabled globally without any origin restrictions, allowing any website to make authenticated requests to the API when a user visits it.

### Location
- **File:** `app/web_server.py`
- **Line:** 121

```python
CORS(self.app)
```

### Impact
- **Security Risk:** HIGH - Cross-site request forgery (CSRF) attacks
- **Attack Vector:** Malicious websites can make API calls on behalf of users
- **Data at Risk:** Device configurations, commands, HA access

### Recommendation
Restrict CORS to specific origins:

```python
from flask_cors import CORS

# Only allow same-origin requests (default in add-on mode)
# In standalone mode, allow only the frontend origin
allowed_origins = [
    "http://localhost:8099",      # Development
    "http://127.0.0.1:8099",      # Local
    # Add HA ingress URLs if needed
]

CORS(self.app, origins=allowed_origins, supports_credentials=True)
```

Or for add-on mode where requests come through HA ingress:

```python
# In add-on mode, requests come from HA's ingress proxy
# which uses the same origin, so we can be more restrictive
if self.supervisor_mode:
    CORS(self.app, supports_credentials=True, origins=[])  # Same-origin only
else:
    # Standalone mode - allow configured frontend URL
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:8099")
    CORS(self.app, origins=[frontend_origin])
```

### Effort Level
**Quick Win** - Single line change with minimal testing

### Status
- [ ] Identified
- [ ] In Progress
- [ ] Fixed
- [ ] Verified

---

## Summary

| ID | Issue | Impact | Effort | Status |
|----|-------|--------|--------|--------|
| CRIT-001 | Token exposed via debug endpoint | Full HA access | Quick Win | Pending |
| CRIT-002 | Global CORS without restrictions | CSRF attacks | Quick Win | Pending |

**Total Critical Issues:** 2

Both critical issues can be fixed within a single development session. Prioritize CRIT-001 as it has the highest immediate risk.
