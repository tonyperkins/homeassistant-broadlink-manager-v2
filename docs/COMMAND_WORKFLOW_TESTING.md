# Command Workflow Testing Strategy

## Overview

This document describes the testing strategy for ensuring command learn/test/delete functionality remains working for both Broadlink and SmartIR device types.

## Why This Matters

The command workflows are critical to the app's functionality:
- **Learn**: Users must be able to learn IR/RF commands
- **Test**: Users must be able to test commands immediately after learning
- **Delete**: Users must be able to remove unwanted commands
- **Storage Separation**: Broadlink and SmartIR must use separate storage

Breaking any of these workflows renders the app unusable for affected device types.

## Test Coverage

### 1. Broadlink Device Workflows (`TestBroadlinkCommandWorkflow`)

**Learn Command**
- ✅ Returns actual IR code, not "pending"
- ✅ Code is stored in Broadlink storage files
- ✅ Code is immediately available for testing

**Test Command**
- ✅ Can test immediately after learning
- ✅ Rejects "pending" placeholder commands
- ✅ Sends correct IR code to device

**Delete Command**
- ✅ Removes command from Broadlink storage
- ✅ Preserves other commands in storage
- ✅ Updates storage file correctly

### 2. SmartIR Device Workflows (`TestSmartIRCommandWorkflow`)

**Learn Command**
- ✅ Returns actual IR code, not "pending"
- ✅ Code is stored in SmartIR JSON file
- ✅ Code is immediately available for testing

**Test Command**
- ✅ Reads from SmartIR JSON file
- ✅ Rejects "pending" placeholder commands
- ✅ Sends correct IR code to device

**Delete Profile**
- ✅ Blocked when profile is in use by devices
- ✅ Returns list of devices using the profile
- ✅ Allowed when no devices reference it

### 3. Storage Separation (`TestStorageSeparation`)

**Independence**
- ✅ SmartIR doesn't read from Broadlink storage files
- ✅ Broadlink doesn't write to SmartIR JSON files
- ✅ Each system maintains its own data

**Code Numbering**
- ✅ SmartIR codes increment correctly (10000, 10001, 10002...)
- ✅ Deleted codes don't get reused
- ✅ Next code = max(existing codes) + 1

## Running Tests

### Locally

```bash
# Run all command workflow tests
pytest tests/integration/test_command_workflows.py -v

# Run specific test class
pytest tests/integration/test_command_workflows.py::TestBroadlinkCommandWorkflow -v

# Run specific test
pytest tests/integration/test_command_workflows.py::TestBroadlinkCommandWorkflow::test_learn_command_returns_actual_code -v
```

### In CI/CD

Tests run automatically on:
- Push to `main`, `develop`, or `release/**` branches
- Pull requests to `main` or `develop`
- Changes to command-related files

See `.github/workflows/test-command-workflows.yml`

### Pre-commit Hook

Install the pre-commit hook to run tests before committing:

```bash
# On Linux/Mac
ln -s ../../.githooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# On Windows (PowerShell as Admin)
New-Item -ItemType SymbolicLink -Path .git\hooks\pre-commit -Target ..\..\githooks\pre-commit
```

## Test Fixtures

### `broadlink_device`
Creates a test Broadlink device for testing native Broadlink workflows.

### `smartir_device`
Creates a test SmartIR device with profile code 10000.

### `mock_ha_api`
Mocks Home Assistant API responses for learning commands.

### `mock_smartir_installed`
Mocks SmartIR installation detection.

## Key Test Scenarios

### Scenario 1: Learn → Test Workflow (Broadlink)
```python
# Learn a command
response = client.post("/api/commands/learn", json={...})
code = response.json["code"]

# Test immediately (should work)
response = client.post("/api/commands/send-raw", json={
    "command": code  # Actual code, not "pending"
})
assert response.status_code == 200
```

### Scenario 2: Learn → Test Workflow (SmartIR)
```python
# Learn a command
response = client.post("/api/commands/learn", json={...})
code = response.json["code"]

# Code is saved to SmartIR JSON
# Test immediately (should work)
response = client.post("/api/commands/test", json={...})
assert response.status_code == 200
```

### Scenario 3: Reject Pending Commands
```python
# Try to test a pending command
response = client.post("/api/commands/send-raw", json={
    "command": "pending"
})
assert response.status_code == 400
assert "not been learned yet" in response.json["error"]
```

### Scenario 4: Profile Deletion Protection
```python
# Try to delete profile in use
response = client.delete("/api/smartir/profiles/10000")
assert response.status_code == 400
assert "currently in use" in response.json["error"]
assert "Test AC" in response.json["devices"]
```

## Debugging Failed Tests

### Test fails: "Returns 'pending' instead of actual code"
**Cause**: Learn endpoint not fetching code from storage
**Fix**: Check `_get_all_broadlink_commands()` is called after learning

### Test fails: "Cannot test immediately after learning"
**Cause**: Code not available in storage yet
**Fix**: Ensure 0.5s delay and proper storage fetch in learn endpoint

### Test fails: "Pending command not rejected"
**Cause**: Missing validation in test/send-raw endpoints
**Fix**: Add validation to check for placeholder values

### Test fails: "SmartIR reads from Broadlink storage"
**Cause**: Incorrect storage path resolution
**Fix**: Ensure SmartIR always uses JSON files, never Broadlink storage

## Maintenance

### Adding New Command Types
When adding support for new command types:
1. Add test cases to `test_command_workflows.py`
2. Test learn → test → delete workflow
3. Test storage separation
4. Update this documentation

### Modifying Storage Logic
When changing how commands are stored:
1. Update relevant test fixtures
2. Verify all workflow tests still pass
3. Add new tests for new storage behavior
4. Update documentation

### Refactoring Endpoints
When refactoring command endpoints:
1. Run tests before changes (baseline)
2. Make changes
3. Run tests after changes
4. Fix any failures
5. Add new tests for new functionality

## Best Practices

1. **Always test both device types**: Changes that work for Broadlink might break SmartIR
2. **Test the full workflow**: Don't just test individual endpoints
3. **Use realistic data**: Use actual IR codes, not dummy strings
4. **Mock external dependencies**: Mock HA API, file system, etc.
5. **Test error cases**: Test what happens when things go wrong
6. **Keep tests fast**: Use mocks to avoid slow I/O operations

## Related Documentation

- [Testing Guide](../tests/TESTING_GUIDE.md) - General testing information
- [SmartIR Integration](SMARTIR_INTEGRATION.md) - SmartIR-specific details
- [API Documentation](API.md) - Command endpoint specifications
