# Manual Test Scripts

This directory contains manual test scripts for development and troubleshooting.

## Critical Tests

### test_raw_base64_send.py

**Purpose:** Determine if Home Assistant's Broadlink integration accepts raw base64 data in `remote.send_command`.

**Why This Matters:** This test determines our entire architectural approach for decoupling from Broadlink storage:
- ✅ **If raw base64 works:** We can use simple template entities with embedded data
- ❌ **If raw base64 doesn't work:** We need REST API entities or custom integration

**Setup:**

1. Get a long-lived access token from Home Assistant:
   - Go to your HA profile (click your name in bottom left)
   - Scroll to "Long-Lived Access Tokens"
   - Click "Create Token"
   - Copy the token

2. Edit the script and set your configuration:
   ```python
   HA_URL = "http://homeassistant.local:8123"  # Your HA URL
   HA_TOKEN = "your_token_here"                # Your token
   BROADLINK_ENTITY_ID = "remote.bedroom_rm4"  # Your device
   TEST_COMMAND_NAME = "power"                 # A command you've learned
   ```

3. Make sure you have at least one command learned in Broadlink integration

**Usage:**

```bash
python tests/manual/test_raw_base64_send.py
```

**What It Tests:**

1. ✅ Baseline: Send using command name (should work)
2. ❓ Send using `b64:` prefix
3. ❓ Send using raw base64 without prefix
4. ❓ Send using `base64:` prefix

**Expected Output:**

The script will:
1. Find your Broadlink storage file
2. Read the command data
3. Attempt to send using different formats
4. Report which methods work
5. Provide architectural recommendation

**⚠️ Warning:** This test will actually send IR/RF signals! Make sure your device is ready.

---

## Other Test Scripts

### test_api_debug.py
Debug API endpoint responses and data structures.

### test_config_path.py
Verify configuration file paths and permissions.

### test_discovery_logic.py
Test device discovery and tracking logic.

### test_rf_detect.py
Test RF command detection and classification.

### test_storage.py
Test storage file operations and backup/recovery.

### test_tracked.py
Check which devices are tracked in devices.json vs metadata.json.

---

## Running Tests

All tests assume you're running from the project root:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# Run a test
python tests/manual/test_name.py
```

---

## Adding New Tests

When adding new manual tests:

1. Create descriptive filename: `test_feature_name.py`
2. Add docstring explaining purpose and usage
3. Include configuration section at top
4. Add error handling and clear output
5. Update this README with test description
