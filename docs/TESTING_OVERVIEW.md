# Testing Overview
## Broadlink Manager v2

**Version**: 0.3.0-alpha.1  
**Last Updated**: 2025-01-19

---

## Testing Strategy

Broadlink Manager v2 uses a multi-layered testing approach:

```
┌─────────────────────────────────────────┐
│   Manual Testing (User Perspective)    │  ← You are here
├─────────────────────────────────────────┤
│   E2E Tests (Playwright)                │  ← Automated UI testing
├─────────────────────────────────────────┤
│   Integration Tests (pytest)            │  ← API endpoint testing
├─────────────────────────────────────────┤
│   Unit Tests (pytest)                   │  ← Module testing (24% coverage)
└─────────────────────────────────────────┘
```

---

## Test Documents

### 1. **MANUAL_TEST_CHECKLIST.md** (This Document)
**Purpose**: Quick, user-friendly manual testing checklist  
**Audience**: QA testers, beta users, release verification  
**Time**: 45-60 minutes for full test, 15 minutes for smoke test  
**Format**: Simple checkboxes with pass/fail tracking

**Use When**:
- ✅ Before each release
- ✅ After major feature additions
- ✅ Verifying bug fixes
- ✅ Beta testing with users
- ✅ Quick smoke tests

**Key Features**:
- Priority levels (P0/P1/P2)
- Regression test section
- Quick smoke test option
- Simple pass/fail tracking
- Notes sections for issues

---

### 2. **TEST_PLAN.md** (Comprehensive)
**Purpose**: Detailed test plan with 150+ test cases  
**Audience**: QA team, developers, project managers  
**Time**: 2-3 hours for full execution  
**Format**: Detailed tables with test IDs and tracking

**Use When**:
- ✅ Major release testing
- ✅ Certification/compliance
- ✅ Comprehensive QA cycles
- ✅ Documenting test coverage

**Key Features**:
- 150+ test cases
- Test IDs for tracking
- Detailed steps and expected results
- Performance benchmarks
- Browser compatibility matrix

---

### 3. **Unit Tests** (Automated)
**Location**: `tests/unit/`  
**Coverage**: 24% (299 tests)  
**Run**: `pytest tests/unit/ -v`

**Modules Tested**:
- ✅ config_loader.py (99%)
- ✅ smartir_detector.py (95%)
- ✅ diagnostics.py (92%)
- ✅ yaml_validator.py (82%)
- ✅ storage_manager.py (77%)
- ✅ device_manager.py (57%)
- ✅ entity_generator.py (55%)
- ✅ api/commands.py (45%)

**Not Yet Tested**:
- ❌ api/smartir.py (0%)
- ❌ api/devices.py (7%)
- ❌ entity_detector.py (0%)
- ❌ smartir_code_service.py (0%)

---

### 4. **Integration Tests** (Automated)
**Location**: `tests/integration/`  
**Purpose**: Test API endpoints and workflows  
**Run**: `pytest tests/integration/ -v`

**Coverage**:
- API endpoint testing
- Database operations
- File system operations
- Home Assistant integration

---

### 5. **E2E Tests** (Automated)
**Location**: `tests/e2e/`  
**Tool**: Playwright  
**Purpose**: Browser-based UI testing  
**Run**: `pytest tests/e2e/ -v`

**Coverage**:
- User workflows
- UI interactions
- Screenshot generation
- Cross-browser testing

---

## Test Execution Guide

### Quick Smoke Test (15 min)
**When**: After every code change, before commits

```bash
# Run unit tests
pytest tests/unit/ -v -x

# Manual smoke test
# Follow "Smoke Test" section in MANUAL_TEST_CHECKLIST.md
```

---

### Pre-Release Testing (2-3 hours)
**When**: Before alpha/beta/production releases

```bash
# 1. Run all automated tests
pytest tests/ -v --cov=app

# 2. Run manual test checklist
# Complete MANUAL_TEST_CHECKLIST.md

# 3. Verify regression tests
# Focus on Section 9 of checklist

# 4. Browser compatibility
# Test on Chrome, Firefox, Safari
```

---

### Bug Fix Verification (30 min)
**When**: After fixing a reported bug

```bash
# 1. Run related unit tests
pytest tests/unit/test_<module>.py -v

# 2. Run regression test
# Check specific regression test in checklist

# 3. Manual verification
# Reproduce original bug scenario
# Verify fix works as expected
```

---

### Feature Testing (1-2 hours)
**When**: After adding new feature

```bash
# 1. Write unit tests for new code
# Add to tests/unit/test_<feature>.py

# 2. Run all tests
pytest tests/ -v

# 3. Manual feature testing
# Add new test cases to checklist if needed
# Test feature thoroughly

# 4. Update documentation
# Update TEST_PLAN.md with new test cases
```

---

## Test Priority Levels

### ✅ P0 (Critical) - Must Pass
**Blocks Release**: Yes  
**Examples**:
- App launches without errors
- Core CRUD operations work
- Command learning works
- Entity generation works
- Data persists after restart
- No regression of fixed bugs

**Failure Impact**: Cannot release

---

### 🔶 P1 (High) - Should Pass
**Blocks Release**: Usually  
**Examples**:
- SmartIR integration works
- Edit/delete operations work
- Error handling graceful
- Network error recovery
- Backup files created

**Failure Impact**: Delay release for fixes

---

### 🔵 P2 (Medium) - Nice to Have
**Blocks Release**: No  
**Examples**:
- UI polish (dark mode, responsive)
- View mode toggles
- Search and filter
- Toast notifications
- Loading states

**Failure Impact**: Document as known issue

---

## Regression Testing

### Critical Bug Fixes (Must Not Regress)

#### 1. Entity ID Format
**Bug**: Entity IDs included domain prefix (`light.bedroom_light`)  
**Fix**: Remove domain prefix (`bedroom_light`)  
**Test**: Section 9.1 in checklist  
**Verification**: Check generated entities.yaml

#### 2. Fan Direction Helper
**Bug**: Direction helper not created, causing validation errors  
**Fix**: Always create direction helper for fans  
**Test**: Section 9.2 in checklist  
**Verification**: Check helpers.yaml for `{entity_id}_direction`

#### 3. SmartIR Config Persistence
**Bug**: SmartIR device edits didn't save to devices.json  
**Fix**: Ensure device_code saved on create/edit  
**Test**: Section 9.3 in checklist  
**Verification**: Edit device, refresh, verify changes persist

#### 4. SmartIR Controller Format
**Bug**: Used IP address instead of entity ID in YAML  
**Fix**: Use entity ID (e.g., `remote.bedroom_rm4`)  
**Test**: Section 9.4 in checklist  
**Verification**: Check generated YAML controller_data field

---

## Test Data Management

### Setup Test Environment
```bash
# 1. Backup existing data
cp -r /config/broadlink_manager /config/broadlink_manager.backup

# 2. Clear test data (optional)
rm -rf /config/broadlink_manager/*

# 3. Restart add-on
# Home Assistant → Settings → Add-ons → Broadlink Manager → Restart
```

### Cleanup After Testing
```bash
# 1. Remove test devices
# Use UI to delete test devices

# 2. Restore backup (if needed)
cp -r /config/broadlink_manager.backup/* /config/broadlink_manager/

# 3. Restart add-on
```

---

## Test Reporting

### Bug Report Template
```markdown
**Bug Title**: [Short description]

**Priority**: P0 / P1 / P2

**Environment**:
- HA Version: 
- Broadlink Manager: 0.3.0-alpha.1
- Browser: 
- Device: 

**Steps to Reproduce**:
1. 
2. 
3. 

**Expected Result**:


**Actual Result**:


**Screenshots/Logs**:


**Workaround** (if any):


**Test Case**: [Reference to test checklist section]
```

### Test Session Report Template
```markdown
**Test Session Report**

**Date**: 
**Tester**: 
**Version**: 0.3.0-alpha.1
**Duration**: 

**Summary**:
- Total Tests: 
- Passed: 
- Failed: 
- Skipped: 

**Critical Issues** (P0):
1. 

**High Priority Issues** (P1):
1. 

**Medium Priority Issues** (P2):
1. 

**Regression Status**:
- Entity ID Format: PASS / FAIL
- Fan Direction Helper: PASS / FAIL
- SmartIR Persistence: PASS / FAIL
- SmartIR Controller: PASS / FAIL

**Release Recommendation**:
☐ Ready for Release
☐ Ready with Known Issues
☐ Not Ready - Fixes Required
☐ Blocked - Critical Issues

**Notes**:

```

---

## Continuous Improvement

### Adding New Tests

#### When to Add Unit Tests
- New module created
- New function added
- Bug fixed (add regression test)
- Coverage below 70% for module

#### When to Add Manual Tests
- New user-facing feature
- New workflow
- Complex user interaction
- Visual/UI changes

#### When to Add E2E Tests
- Critical user workflows
- Multi-step processes
- Cross-component interactions
- Screenshot documentation needed

---

## Test Metrics

### Current Status (v0.3.0-alpha.1)
```
Unit Test Coverage:    24% (299 tests)
Integration Tests:     ~15 tests
E2E Tests:            ~10 tests
Manual Test Cases:    ~60 test cases
Regression Tests:     4 critical tests

Total Test Coverage:  ~370 test cases
```

### Goals for v0.3.0 Release
```
Unit Test Coverage:    35% target
Integration Tests:     25 tests
E2E Tests:            15 tests
Manual Test Pass:     100% P0, 95% P1
Regression Tests:     All passing
```

---

## Quick Reference

### Run All Tests
```bash
# Unit tests only
pytest tests/unit/ -v

# Unit tests with coverage
pytest tests/unit/ --cov=app --cov-report=term-missing

# All automated tests
pytest tests/ -v

# E2E tests
pytest tests/e2e/ -v --headed

# Specific test file
pytest tests/unit/test_config_loader.py -v
```

### Test Markers
```bash
# Run only smoke tests
pytest -m smoke

# Run only docs tests (screenshots)
pytest -m docs

# Skip slow tests
pytest -m "not slow"
```

### Coverage Reports
```bash
# Terminal report
pytest --cov=app --cov-report=term-missing

# HTML report
pytest --cov=app --cov-report=html
# Open htmlcov/index.html

# XML report (for CI)
pytest --cov=app --cov-report=xml
```

---

## Resources

- **Unit Tests**: `tests/unit/`
- **Integration Tests**: `tests/integration/`
- **E2E Tests**: `tests/e2e/`
- **Test Plan**: `docs/TEST_PLAN.md`
- **Manual Checklist**: `docs/MANUAL_TEST_CHECKLIST.md`
- **Testing Guide**: `tests/TESTING_GUIDE.md`

---

## Next Steps

1. **Complete Manual Testing**: Use MANUAL_TEST_CHECKLIST.md
2. **Increase Unit Coverage**: Target 35% coverage
3. **Add E2E Tests**: Cover critical workflows
4. **Automate Regression**: Convert manual regression tests to automated
5. **CI/CD Integration**: Run tests on every commit

---

**Happy Testing! 🧪**
