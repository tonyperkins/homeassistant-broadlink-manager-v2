# Testing Quick Start Guide

Get started with testing Broadlink Manager in 5 minutes.

## Installation

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

## Run Tests

```bash
# Run all tests (unit + integration)
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run only unit tests (fast)
pytest -m unit

# Run only integration tests
pytest -m integration

# Run E2E browser tests (requires app running)
pytest -m e2e

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring real devices
pytest -m "not requires_device"
```

## Quick Test Examples

### Run Specific Test File

```bash
pytest tests/unit/test_device_manager.py
```

### Run Specific Test

```bash
pytest tests/unit/test_device_manager.py::TestDeviceManager::test_create_device
```

### Verbose Output

```bash
pytest -v
```

### Stop on First Failure

```bash
pytest -x
```

## View Coverage Report

```bash
# Generate HTML report
pytest --cov=app --cov-report=html

# Open in browser
# Windows
start htmlcov/index.html

# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html
```

## Common Test Patterns

### Testing Device Creation

```python
def test_create_device(device_manager, sample_device_data):
    result = device_manager.create_device('test_device', sample_device_data)
    assert result is True
    
    device = device_manager.get_device('test_device')
    assert device is not None
```

### Testing API Endpoints

```python
def test_api_endpoint(client):
    response = client.get('/api/devices')
    assert response.status_code == 200
```

### Using Fixtures

```python
def test_with_populated_data(populated_device_manager):
    # Device manager already has test data
    devices = populated_device_manager.get_all_devices()
    assert len(devices) > 0
```

## Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit
def test_unit_functionality():
    pass

@pytest.mark.integration
def test_api_integration():
    pass

@pytest.mark.slow
def test_long_running_operation():
    pass

@pytest.mark.requires_device
def test_with_real_broadlink():
    pass
```

## Debugging Tests

### Run with Print Statements

```bash
pytest -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Local Variables on Failure

```bash
pytest -l
```

## Pre-Commit Checklist

Before committing code:

```bash
# 1. Run all tests
pytest

# 2. Check coverage (should be > 80%)
pytest --cov=app --cov-report=term-missing

# 3. Run linting
flake8 app/

# 4. Format code
black app/
```

## CI/CD Integration

Tests run automatically on:
- Every push to main branch
- Every pull request
- Before releases

## E2E Browser Testing

For automated browser testing with Playwright:

```bash
# Install Playwright browsers
playwright install chromium

# Start your app
python app/main.py

# Run E2E tests (in another terminal)
pytest tests/e2e/

# Run with visible browser
pytest tests/e2e/ --headed
```

See **`E2E_QUICKSTART.md`** for browser testing guide.

## Need Help?

- **Unit/Integration Tests**: See `docs/TESTING.md`
- **Browser Tests**: See `E2E_QUICKSTART.md` and `docs/E2E_TESTING.md`
- **Browser Testing Summary**: See `BROWSER_TESTING_SUMMARY.md`
- **Fixtures Reference**: See `tests/conftest.py` and `tests/e2e/conftest.py`
- **Example Tests**: Browse `tests/unit/`, `tests/integration/`, and `tests/e2e/`

## Manual Testing

For features requiring human verification (UI, hardware interaction):

See the comprehensive manual test plan in `docs/TESTING.md`

Key manual test areas:
- Command learning with real remotes
- Entity generation and Home Assistant integration
- Web UI responsiveness
- Browser compatibility
- Mobile device testing

---

**Quick Tips**: 
- Start with unit tests (`pytest -m unit`) for fast feedback during development!
- Use E2E tests (`pytest -m e2e --headed`) to verify UI workflows!
