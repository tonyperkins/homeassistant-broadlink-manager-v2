# Remediation Roadmap

This document provides a prioritized action plan for addressing the issues identified in the code review.

---

## Phase 1: Immediate Security Fixes (Week 1)

**Goal:** Address critical security vulnerabilities

### Sprint 1.1: Security Hardening

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Remove debug token endpoint | CRIT-001 | Critical | 15 min | - |
| Restrict CORS configuration | CRIT-002 | Critical | 30 min | - |
| Remove debug print statements | HIGH-006 | High | 1 hour | - |

**Acceptance Criteria:**
- [ ] `/api/debug/token` endpoint removed or secured
- [ ] CORS only allows appropriate origins
- [ ] No `print()` statements in production code
- [ ] All changes tested in both add-on and standalone modes

**Estimated Total Effort:** 2 hours

---

## Phase 2: Quick Wins (Week 2)

**Goal:** Address easy fixes that improve code quality

### Sprint 2.1: Code Quality Quick Wins

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Fix bare except clauses | MED-002 | Medium | 2 hours | - |
| Fix duplicate test fixture | MED-007 | Medium | 30 min | - |
| Remove duplicate watchdog | LOW-002 | Low | 5 min | - |
| Fix cache TTL usage | LOW-005 | Low | 30 min | - |
| Add silent failure logging | MED-006 | Medium | 1 hour | - |

**Acceptance Criteria:**
- [ ] All `except:` clauses replaced with specific exceptions
- [ ] Only one `mock_ha_api` fixture in conftest.py
- [ ] watchdog only in requirements.txt
- [ ] Storage cache TTL implemented or removed
- [ ] Background threads log errors with context

**Estimated Total Effort:** 4-5 hours

---

## Phase 3: Architecture - Storage Consolidation (Sprint 3-4)

**Goal:** Eliminate dual storage system confusion

### Sprint 3.1: Analysis & Planning

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Audit all storage_manager usage | HIGH-002 | High | 4 hours | - |
| Document migration plan | HIGH-002 | High | 2 hours | - |
| Create feature flag for gradual migration | HIGH-002 | High | 2 hours | - |

### Sprint 3.2: Implementation

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Migrate entity generation to devices.json | HIGH-002 | High | 8 hours | - |
| Remove storage_manager.py | HIGH-002 | High | 4 hours | - |
| Remove migration_manager.py | HIGH-002 | High | 2 hours | - |
| Update all API endpoints | HIGH-002 | High | 4 hours | - |

**Acceptance Criteria:**
- [ ] All device data stored only in `devices.json`
- [ ] `storage_manager.py` deleted
- [ ] `migration_manager.py` deleted
- [ ] Entity generation works with single storage
- [ ] All tests pass
- [ ] No data loss during migration

**Estimated Total Effort:** 3-4 days

---

## Phase 4: Architecture - web_server.py Refactoring (Sprint 5-7)

**Goal:** Break monolithic file into maintainable modules

### Sprint 5.1: Extract Services

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Create `services/ha_api.py` | HIGH-001 | High | 4 hours | - |
| Create `services/command_service.py` | HIGH-001 | High | 4 hours | - |
| Create `services/storage_service.py` | HIGH-001 | High | 4 hours | - |

### Sprint 5.2: Extract Background Tasks

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Create `background/polling.py` | HIGH-001 | High | 4 hours | - |
| Create `background/file_watcher.py` | HIGH-001 | High | 2 hours | - |

### Sprint 6.1: Move Routes to Blueprints

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Move entity routes to `api/entities.py` | HIGH-003 | High | 4 hours | - |
| Move migration routes to `api/migration.py` | HIGH-003 | High | 2 hours | - |
| Move debug routes to `api/debug.py` | HIGH-003 | High | 2 hours | - |
| Remove duplicate routes | HIGH-003 | High | 4 hours | - |

### Sprint 7.1: Final Cleanup

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Clean up web_server.py | HIGH-001 | High | 4 hours | - |
| Remove flake8 exceptions | MED-001 | Medium | 2 hours | - |
| Update imports across codebase | HIGH-001 | High | 4 hours | - |
| Update tests | HIGH-001 | High | 8 hours | - |

**Acceptance Criteria:**
- [ ] `web_server.py` < 500 lines
- [ ] All services in separate modules
- [ ] No duplicate routes
- [ ] All flake8 checks pass without exceptions
- [ ] All tests pass
- [ ] Documentation updated

**Target File Structure:**
```
app/
├── __init__.py
├── main.py
├── config_loader.py
├── server/
│   ├── __init__.py
│   ├── app.py              # Flask app initialization (~200 lines)
│   └── middleware.py       # IngressMiddleware
├── services/
│   ├── __init__.py
│   ├── ha_api.py           # HA API communication
│   ├── command_service.py  # Command learning/sending
│   └── storage_service.py  # Broadlink storage operations
├── background/
│   ├── __init__.py
│   ├── polling.py          # Command polling thread
│   └── file_watcher.py     # File change detection
├── api/
│   ├── __init__.py
│   ├── commands.py
│   ├── devices.py
│   ├── entities.py         # (new)
│   ├── smartir.py
│   └── debug.py            # (new, dev-only)
└── managers/
    ├── __init__.py
    ├── device_manager.py
    └── area_manager.py
```

**Estimated Total Effort:** 2-3 weeks

---

## Phase 5: Performance & Reliability (Sprint 8-9)

**Goal:** Improve system performance and reliability

### Sprint 8.1: Async Optimization

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Implement shared event loop | HIGH-004 | High | 8 hours | - |
| Add HTTP connection pooling | MED-005 | Medium | 4 hours | - |

### Sprint 9.1: Input Validation

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Add marshmallow schemas | HIGH-005 | High | 8 hours | - |
| Validate all endpoints | HIGH-005 | High | 8 hours | - |

### Sprint 9.2: Rate Limiting

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Add Flask-Limiter | MED-004 | Medium | 4 hours | - |
| Configure appropriate limits | MED-004 | Medium | 2 hours | - |

**Acceptance Criteria:**
- [ ] Single event loop for async operations
- [ ] HTTP session reuse for HA API calls
- [ ] All endpoints have input validation
- [ ] Rate limiting on sensitive endpoints

**Estimated Total Effort:** 1-2 weeks

---

## Phase 6: Error Handling & Observability (Sprint 10)

**Goal:** Standardize error handling and improve observability

### Sprint 10.1: Error Standardization

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Create error response utilities | MED-003 | Medium | 4 hours | - |
| Update all endpoints | MED-003 | Medium | 8 hours | - |
| Update frontend error handling | MED-003 | Medium | 4 hours | - |

### Sprint 10.2: Constants & Cleanup

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Create constants module | MED-008 | Medium | 4 hours | - |
| Replace magic numbers | MED-008 | Medium | 4 hours | - |

**Acceptance Criteria:**
- [ ] Consistent error response format
- [ ] All magic numbers replaced with named constants
- [ ] Frontend handles errors uniformly

**Estimated Total Effort:** 1 week

---

## Phase 7: Testing & Documentation (Sprint 11-12)

**Goal:** Improve test coverage and documentation

### Sprint 11.1: Frontend Testing

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Set up Vitest | MED-009 | Medium | 4 hours | - |
| Add component tests | MED-009 | Medium | 16 hours | - |

### Sprint 11.2: API Documentation

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Add OpenAPI/Swagger | MED-010 | Medium | 8 hours | - |
| Document all endpoints | MED-010 | Medium | 8 hours | - |

### Sprint 12.1: Type Hints & ADRs

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Add type hints to core modules | LOW-003 | Low | 16 hours | - |
| Create ADR folder and templates | LOW-007 | Low | 4 hours | - |
| Write retrospective ADRs | LOW-007 | Low | 8 hours | - |

**Acceptance Criteria:**
- [ ] Frontend test coverage > 50%
- [ ] All API endpoints documented with Swagger
- [ ] Core modules have type hints
- [ ] Key decisions documented in ADRs

**Estimated Total Effort:** 2-3 weeks

---

## Phase 8: Long-term Improvements (Quarterly)

**Goal:** Address remaining technical debt

### Ongoing Tasks

| Task | Issue | Priority | Effort | Owner |
|------|-------|----------|--------|-------|
| Edge case testing | LOW-008 | Low | Ongoing | - |
| Comment quality improvement | LOW-006 | Low | Ongoing | - |
| Dependency updates | LOW-001 | Low | Monthly | - |
| Evaluate watcher vs polling | LOW-004 | Low | 8 hours | - |

---

## Progress Tracking

### Overall Status

| Phase | Status | Start Date | Target Date | Completion |
|-------|--------|------------|-------------|------------|
| Phase 1: Security | Not Started | - | - | 0% |
| Phase 2: Quick Wins | Not Started | - | - | 0% |
| Phase 3: Storage | Not Started | - | - | 0% |
| Phase 4: Refactoring | Not Started | - | - | 0% |
| Phase 5: Performance | Not Started | - | - | 0% |
| Phase 6: Error Handling | Not Started | - | - | 0% |
| Phase 7: Testing/Docs | Not Started | - | - | 0% |
| Phase 8: Long-term | Not Started | - | - | 0% |

### Issue Resolution Summary

| Severity | Total | Resolved | Remaining |
|----------|-------|----------|-----------|
| Critical | 2 | 0 | 2 |
| High | 6 | 0 | 6 |
| Medium | 12 | 0 | 12 |
| Low | 8 | 0 | 8 |
| **Total** | **28** | **0** | **28** |

---

## Risk Assessment

### High Risk Items
1. **Phase 3 (Storage):** Data migration could cause issues if not carefully tested
2. **Phase 4 (Refactoring):** Large refactor could introduce regressions

### Mitigation Strategies
1. Always create backups before major changes
2. Feature flags for gradual rollout
3. Comprehensive testing at each phase
4. User communication about breaking changes

---

## Resource Estimates

| Phase | Developer Days | Testing Days | Total Days |
|-------|---------------|--------------|------------|
| Phase 1 | 0.25 | 0.25 | 0.5 |
| Phase 2 | 0.5 | 0.25 | 0.75 |
| Phase 3 | 3 | 1 | 4 |
| Phase 4 | 8 | 2 | 10 |
| Phase 5 | 4 | 1 | 5 |
| Phase 6 | 2 | 0.5 | 2.5 |
| Phase 7 | 6 | 1 | 7 |
| **Total** | **23.75** | **6** | **29.75** |

**Estimated Calendar Time:** ~3 months at 50% capacity

---

## Version Milestones

| Version | Phases | Target | Key Deliverables |
|---------|--------|--------|------------------|
| 0.3.1 | 1, 2 | Week 2 | Security fixes, quick wins |
| 0.4.0 | 3 | Week 6 | Single storage system |
| 0.5.0 | 4 | Week 12 | Refactored architecture |
| 0.6.0 | 5, 6 | Week 16 | Performance, error handling |
| 1.0.0 | 7 | Week 20 | Production ready |
