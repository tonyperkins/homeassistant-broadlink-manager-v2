# Low Priority Issues

Low priority issues represent style inconsistencies, minor optimizations, or documentation improvements. These can be addressed opportunistically.

---

## LOW-001: Pinned Cryptography Version Constraint

### Description
The `cryptography` package has a strict version pin that may prevent security updates.

### Location
- **File:** `requirements.txt`
- **Line:** 2

### Evidence
```
cryptography>=42.0.0,<43.0.0  # Pin to version compatible with Rust 1.71.1 (Alpine 3.18)
```

### Impact
- **Security:** May miss security patches in newer versions
- **Maintenance:** Manual update required when upgrading Alpine

### Recommendation
Document the constraint reason and create a tracking issue:
```
# requirements.txt
# NOTE: cryptography pinned due to Rust compatibility in Alpine 3.18
# Review after Alpine upgrade - see issue #XXX
cryptography>=42.0.0,<43.0.0
```

### Effort Level
**Quick Win** - Add documentation

---

## LOW-002: Duplicate Watchdog in Requirements

### Description
`watchdog` is listed in both `requirements.txt` and `requirements-test.txt`.

### Location
- **Files:** `requirements.txt` (line 20), `requirements-test.txt` (line 32)

### Evidence
```
# requirements.txt
watchdog>=3.0.0

# requirements-test.txt
watchdog>=3.0.0
```

### Impact
- **Minor:** Redundant specification
- **Confusion:** Which is the authoritative version?

### Recommendation
Remove from `requirements-test.txt` (test requirements should only add to base requirements).

### Effort Level
**Quick Win** - Remove one line

---

## LOW-003: Missing Type Hints

### Description
Many Python files lack type hints, reducing IDE support and code clarity.

### Location
- Various files in `app/`

### Evidence
```python
# Current (no hints)
def _map_device_commands_to_entity_commands(self, device_commands, entity_type):

# With hints
def _map_device_commands_to_entity_commands(
    self, 
    device_commands: Dict[str, Any], 
    entity_type: str
) -> Dict[str, str]:
```

### Impact
- **IDE Support:** No autocomplete, type checking
- **Documentation:** Intent unclear
- **Errors:** Type-related bugs not caught early

### Recommendation
Add type hints incrementally, starting with public interfaces:
```python
from typing import Dict, List, Any, Optional

class DeviceManager:
    def create_device(self, device_id: str, device_data: Dict[str, Any]) -> bool:
        ...
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        ...
```

### Effort Level
**Significant** - Add to all files

---

## LOW-004: Redundant File Watcher + Polling

### Description
The system uses both a file watcher (for `devices.json`) and a polling thread, which may be redundant.

### Location
- **File:** `app/web_server.py`
- **Classes:** `DevicesJsonWatcher`, polling thread

### Evidence
```python
# File watcher
self._start_file_watcher()

# Also polling thread
self.poll_thread = threading.Thread(
    target=self._poll_pending_commands, daemon=True
)
```

### Impact
- **Resources:** Two mechanisms doing similar things
- **Complexity:** Both need to be understood and maintained

### Recommendation
Evaluate if both are necessary. Consider:
1. Using only file watcher with debounce
2. Using only polling at regular intervals
3. Document why both are needed if intentional

### Effort Level
**Moderate** - Requires analysis and testing

---

## LOW-005: Storage Cache TTL Inefficiency

### Description
The storage cache TTL is checked but never actually refreshes the cache proactively.

### Location
- **File:** `app/web_server.py`
- **Lines:** 156-157

### Evidence
```python
self.storage_cache_timestamp: float = 0
self.STORAGE_CACHE_TTL = 60  # Refresh cache every 60 seconds

# But no code actually uses storage_cache_timestamp to refresh
```

### Impact
- **Performance:** Cache may not be utilized optimally
- **Stale Data:** Cache strategy unclear

### Recommendation
Either implement the TTL refresh logic or remove the unused constants:
```python
async def _get_cached_commands(self):
    current_time = time.time()
    if current_time - self.storage_cache_timestamp > self.STORAGE_CACHE_TTL:
        self._storage_command_cache = await self._read_from_storage()
        self.storage_cache_timestamp = current_time
    return self._storage_command_cache
```

### Effort Level
**Quick Win** - Implement or remove

---

## LOW-006: Inline Comments Quality Varies

### Description
Some files have excellent comments explaining business logic, while others have minimal or outdated comments.

### Location
- Various files

### Evidence
```python
# Good example (entity_generator.py)
def sanitize_slug(name: str) -> str:
    """
    Sanitize a name to create a valid Home Assistant slug.
    Converts to lowercase, replaces spaces and invalid chars with underscores.
    """

# Could be better (web_server.py)
def _handle_change(self, event, action_label: str):
    # Debounce - only process if more than 0.1 second since last modification
    # (reduced from 1 second to handle rapid command learning)
    current_time = time.time()
```

### Impact
- **Maintenance:** Hard to understand intent
- **Onboarding:** New developers struggle

### Recommendation
Establish commenting guidelines:
1. All public methods have docstrings
2. Complex logic has inline comments
3. Non-obvious constants explained

### Effort Level
**Moderate** - Review and improve incrementally

---

## LOW-007: Architecture Decision Records Missing

### Description
No ADRs (Architecture Decision Records) exist to explain design choices.

### Location
- **Directory:** `docs/` (missing ADR folder)

### Impact
- **Knowledge Loss:** Why decisions were made is lost
- **Onboarding:** New developers question design
- **Consistency:** Similar decisions made differently

### Recommendation
Create ADR folder and document key decisions:
```
docs/
└── adr/
    ├── 0001-use-flask-over-fastapi.md
    ├── 0002-dual-storage-for-v1-compatibility.md
    ├── 0003-vue3-composition-api.md
    └── template.md
```

### Effort Level
**Moderate** - Write retrospective ADRs

---

## LOW-008: Test Coverage for Edge Cases

### Description
Some tests exist for happy paths but edge cases and error conditions are undertested.

### Location
- **Directory:** `tests/`

### Evidence
Regression tests exist but comprehensive edge case testing is limited:
- What if HA is offline during learning?
- What if storage file is corrupted?
- What if concurrent writes happen?

### Recommendation
Add edge case tests:
```python
class TestEdgeCases:
    def test_learn_command_ha_offline(self):
        """Test behavior when HA is unreachable"""
        
    def test_save_devices_concurrent_writes(self):
        """Test thread safety during concurrent saves"""
        
    def test_corrupted_storage_recovery(self):
        """Test recovery from corrupted devices.json"""
```

### Effort Level
**Moderate** - Identify and add tests incrementally

---

## Summary

| ID | Issue | Impact | Effort |
|----|-------|--------|--------|
| LOW-001 | Pinned cryptography version | Security updates | Quick Win |
| LOW-002 | Duplicate watchdog | Redundancy | Quick Win |
| LOW-003 | Missing type hints | IDE support | Significant |
| LOW-004 | Redundant watcher/polling | Resources | Moderate |
| LOW-005 | Unused cache TTL | Performance | Quick Win |
| LOW-006 | Comment quality varies | Maintenance | Moderate |
| LOW-007 | No ADRs | Knowledge loss | Moderate |
| LOW-008 | Edge case testing | Coverage | Moderate |

**Total Low Priority Issues:** 8
