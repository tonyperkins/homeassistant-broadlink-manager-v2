# Code Cleanup Recommendations

**Generated:** October 15, 2025  
**Purpose:** Identify unused code, outdated documentation, and areas for improvement

---

## 1. Unused/Incomplete Code

### API Endpoints (Stub Implementations)

**File:** `app/api/config.py`

- **Lines 16-42:** Three TODO endpoints that are not implemented:
  - `GET /api/config` - Returns placeholder "Coming soon"
  - `POST /api/config/reload` - Returns placeholder "Coming soon"  
  - `POST /api/config/generate-entities` - Returns placeholder "Coming soon"

**Recommendation:** 
- Remove these endpoints OR implement them
- If keeping, update documentation to mark as "planned features"

---

**File:** `app/api/areas.py`

- **Lines 39-46:** `GET /api/areas/<area_id>` - Returns placeholder "Coming soon"

**Recommendation:**
- Remove this endpoint (not used by frontend)
- Areas are fetched via Home Assistant WebSocket API, not this endpoint

---

### Incomplete TODO in Code

**File:** `app/web_server.py`

- **Lines 858-864:** TODO comment about command deletion from HA storage
  ```python
  # TODO: Implement command deletion from HA storage
  # This would require calling the /api/delete endpoint for each command
  # For now, just log it
  ```

**Status:** This has been implemented in `app/api/devices.py` (delete_managed_device)

**Recommendation:** Remove this TODO comment as it's now implemented

---

## 2. Potentially Unused Managers

### Migration Manager

**File:** `app/migration_manager.py`

**Usage:** Only used for initial migration from old metadata format

**Recommendation:**
- Keep for now (users may still need to migrate)
- Consider deprecating in v3.0 after sufficient adoption period
- Add deprecation notice in documentation

---

### Entity Detector

**File:** `app/entity_detector.py`

**Usage:** Auto-detects entity types from command names

**Status:** Actively used by SmartIR and device adoption features

**Recommendation:** Keep - actively used

---

## 3. Outdated Documentation

### API Documentation

**File:** `docs/API.md`

**Issues:**

1. **Lines 74-100:** Learn command endpoint documented as `POST /api/learn`
   - **Actual:** `POST /api/commands/learn`
   
2. **Lines 106-123:** Test command endpoint documented as `POST /api/test`
   - **Actual:** `POST /api/commands/test`

3. **Lines 26-41:** Device listing endpoint incomplete
   - Missing new managed devices endpoints
   - Missing device adoption endpoints

4. **Missing endpoints:**
   - `POST /api/devices/adopt` - Adopt untracked devices
   - `GET /api/devices/discover` - Discover untracked devices
   - `GET /api/devices/managed` - List managed devices
   - `PUT /api/devices/managed/<device_id>` - Update managed device
   - `DELETE /api/devices/managed/<device_id>` - Delete managed device
   - `POST /api/devices/managed/<device_id>/commands` - Add command to device
   - `DELETE /api/devices/managed/<device_id>/commands/<command_name>` - Delete command

**Recommendation:** Update API.md with complete endpoint documentation

---

### Architecture Documentation

**File:** `docs/ARCHITECTURE.md`

**Issues:**

1. **Lines 26-52:** Data model shows old metadata structure
   - Missing `device_type` field (broadlink vs smartir)
   - Missing `broadlink_entity` field for managed devices
   - Missing `created_at` timestamp

2. **Lines 123-158:** "How It Works" section outdated
   - Doesn't mention new Device Manager
   - Doesn't explain managed vs untracked devices
   - Doesn't cover device adoption workflow

**Recommendation:** Update with current data model and workflows

---

## 4. Development Documentation Cleanup

### Development Docs Folder

**Location:** `docs/development/`

**Files (23 total):** Many are progress snapshots from development

**Recommendations:**

#### Keep (Active Reference):
- `README.md` - Overview
- `E2E_QUICKSTART.md` - Testing guide
- `REFACTORING_ROADMAP.md` - Future plans

#### Archive (Historical):
Move to `docs/development/archive/`:
- `API_IMPLEMENTATION_COMPLETE.md`
- `API_SETUP_COMPLETE.md`
- `BROWSER_TESTING_SUMMARY.md`
- `BUGFIX_MEDIA_PLAYER.md`
- `COMMAND_LEARNING_COMPLETE.md`
- `COMPONENTS_CREATED.md`
- `DUAL_MODE_IMPLEMENTATION.md`
- `IMPLEMENTATION_SUMMARY.md`
- `PHASE_3_1_COMPLETE.md`
- `RECENT_UPDATES.md`
- `SMARTIR_DEVICE_TYPE_IMPLEMENTATION.md`
- `SMARTIR_DEVICE_TYPE_PROGRESS.md`
- `SMARTIR_IMPLEMENTATION_PLAN.md`
- `SMARTIR_INTEGRATION_ROADMAP.md`
- `SMARTIR_PROGRESS.md`
- `SMARTIR_STATUS.md`
- `SMARTIR_TESTING_PLAN.md`
- `TESTING_COMPLETE.md`
- `TESTING_PROGRESS.md`
- `UI_IMPLEMENTATION_COMPLETE.md`

---

## 5. Unused Frontend Components

### Check for Unused Vue Components

**Recommendation:** Run analysis to find:
- Components imported but never used
- Composables defined but not imported
- Unused CSS classes

**Command:**
```bash
cd frontend
npm run analyze  # If available
```

---

## 6. Code Duplication

### Command Learning Logic

**Locations:**
- `app/web_server.py` - `_learn_command()` method
- `app/api/commands.py` - `/api/commands/learn` endpoint

**Issue:** Some logic duplication between these

**Recommendation:** Keep as-is (separation of concerns is appropriate)

---

### Device Fetching

**Locations:**
- Multiple places fetch Broadlink devices from HA
- Some use WebSocket, some use REST API

**Recommendation:** Standardize on WebSocket API where possible

---

## 7. Test Coverage

### Missing Tests

**Areas needing tests:**
- Device adoption workflow
- Command deletion with storage lag handling
- SmartIR profile management
- Area assignment

**Recommendation:** Add integration tests for these workflows

---

## 8. Configuration Files

### Unused Config Options

**File:** `config.yaml`

**Check:** Are all options actually used?

**Recommendation:** Review and remove unused options

---

## 9. Static Assets

### Frontend Build Artifacts

**Location:** `app/static/assets/`

**Files:** Vendor bundles, CSS, JS

**Recommendation:** 
- Ensure these are gitignored
- Document build process
- Consider CDN for vendor libraries

---

## 10. Logging

### Excessive Logging

**Issue:** Some endpoints log every request at INFO level

**Example:** `GET /api/broadlink/devices` logs 6+ lines per request

**Recommendation:**
- Move verbose logs to DEBUG level
- Keep only essential INFO logs
- Add log level configuration

---

## Summary

### High Priority
1. ✅ Update API.md with current endpoints (COMPLETED - Full rewrite with all endpoints)
2. ✅ Update ARCHITECTURE.md with current data model (COMPLETED - Added Device Manager, device types)
3. ✅ Remove or implement stub API endpoints (COMPLETED - 4 endpoints removed)
4. ✅ Remove completed TODO comments (COMPLETED - All TODOs cleaned)

### Medium Priority
5. ✅ Archive old development docs (COMPLETED - 14 files archived)
6. Reduce logging verbosity
7. Add missing integration tests

### Low Priority
8. Analyze unused frontend code
9. Review configuration options
10. Consider migration manager deprecation timeline

---

## Action Plan

### Phase 1: Documentation (1-2 hours)
- [ ] Update API.md
- [ ] Update ARCHITECTURE.md  
- [ ] Create DATA_MODEL.md (see separate document)

### Phase 2: Code Cleanup (1 hour)
- [ ] Remove stub endpoints or implement them
- [ ] Remove completed TODOs
- [ ] Archive development docs

### Phase 3: Optimization (2-3 hours)
- [ ] Reduce logging verbosity
- [ ] Add log level configuration
- [ ] Standardize HA API calls

### Phase 4: Testing (3-4 hours)
- [ ] Add device adoption tests
- [ ] Add command deletion tests
- [ ] Add SmartIR integration tests
