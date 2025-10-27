# End-to-End (E2E) Browser Testing Guide

Complete guide for automated browser testing with Playwright.

## Overview

E2E tests verify the complete user experience by automating real browser interactions. They test:
- UI rendering and responsiveness
- User workflows (device creation, command learning)
- Browser compatibility
- Accessibility
- Performance

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-test.txt
```

### 2. Install Playwright Browsers

```bash
# Install Chromium, Firefox, and WebKit
playwright install

# Or install specific browser
playwright install chromium
```

### 3. Start Application

E2E tests require the application to be running:

```bash
# Terminal 1: Start the application
python app/main.py

# Terminal 2: Run E2E tests
pytest tests/e2e/
```

## Running E2E Tests

### Basic Commands

```bash
# Run all E2E tests
pytest tests/e2e/

# Run with visible browser (headed mode)
pytest tests/e2e/ --headed

# Run in specific browser
pytest tests/e2e/ --browser chromium
pytest tests/e2e/ --browser firefox
pytest tests/e2e/ --browser webkit

# Run specific test file
pytest tests/e2e/test_ui_navigation.py

# Run with slow motion (for debugging)
pytest tests/e2e/ --slowmo 1000  # 1 second delay between actions
```

### Test Categories

```bash
# UI navigation tests
pytest tests/e2e/test_ui_navigation.py

# Device management workflows
pytest tests/e2e/test_device_management.py

# Command learning workflows
pytest tests/e2e/test_command_learning.py

# Accessibility tests
pytest tests/e2e/test_accessibility.py -m a11y

# Exclude slow tests
pytest tests/e2e/ -m "not slow"
```

## Test Structure

### Available Test Files

```
tests/e2e/
├── conftest.py                    # Playwright fixtures
├── test_ui_navigation.py          # Page loads, navigation, performance
├── test_device_management.py      # Device CRUD workflows
├── test_command_learning.py       # Command learning UI
└── test_accessibility.py          # Accessibility checks
```

### Key Fixtures

**Browser Contexts:**
- `page` - Desktop browser page (1280x720)
- `mobile_page` - Mobile browser (iPhone 12)
- `tablet_page` - Tablet browser (iPad Pro)
- `context` - Browser context for isolation

**Utilities:**
- `base_url` - Application URL (http://localhost:8099)
- `screenshot_dir` - Directory for failure screenshots
- `authenticated_page` - Pre-authenticated page (if needed)

## Writing E2E Tests

### Basic Test Example

```python
import pytest
from playwright.sync_api import expect

@pytest.mark.e2e
def test_homepage_loads(page, base_url):
    """Test that homepage loads successfully"""
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    
    expect(page).to_have_title("Broadlink Manager")
    
    main_container = page.locator("#app").first
    expect(main_container).to_be_visible()
```

### Interacting with Elements

```python
@pytest.mark.e2e
def test_create_device(page, base_url):
    """Test device creation workflow"""
    page.goto(base_url)
    
    # Click button
    page.locator("button:has-text('Add Device')").click()
    
    # Fill form
    page.locator("#device-name").fill("Test TV")
    page.locator("#device-type").select_option("tv")
    
    # Submit
    page.locator("button[type='submit']").click()
    
    # Verify result
    expect(page.locator("text=Test TV")).to_be_visible()
```

### Mobile Testing

```python
@pytest.mark.e2e
def test_mobile_responsive(mobile_page, base_url):
    """Test mobile responsiveness"""
    mobile_page.goto(base_url)
    
    # Verify mobile layout
    menu_button = mobile_page.locator(".mobile-menu-toggle")
    expect(menu_button).to_be_visible()
```

### Waiting for Elements

```python
# Wait for element to be visible
page.locator("#device-list").wait_for(state="visible")

# Wait for network to be idle
page.wait_for_load_state("networkidle")

# Wait for specific timeout
page.wait_for_timeout(1000)  # 1 second

# Wait for navigation
with page.expect_navigation():
    page.locator("a.nav-link").click()
```

### Assertions

```python
from playwright.sync_api import expect

# Visibility
expect(element).to_be_visible()
expect(element).to_be_hidden()

# Text content
expect(element).to_have_text("Expected text")
expect(element).to_contain_text("partial text")

# Attributes
expect(element).to_have_attribute("disabled", "")
expect(element).to_have_class("active")

# Form values
expect(input).to_have_value("test value")

# Count
expect(page.locator(".device-item")).to_have_count(5)

# URL
expect(page).to_have_url("http://localhost:8099/devices")
```

## Debugging E2E Tests

### Visual Debugging

```bash
# Run with visible browser
pytest tests/e2e/ --headed

# Slow down actions
pytest tests/e2e/ --slowmo 500

# Pause on failure
pytest tests/e2e/ --pdb
```

### Screenshots

Screenshots are automatically captured on test failure and saved to `test-results/screenshots/`.

Manual screenshots:

```python
def test_with_screenshot(page, base_url):
    page.goto(base_url)
    
    # Take screenshot
    page.screenshot(path="screenshot.png")
    
    # Full page screenshot
    page.screenshot(path="full-page.png", full_page=True)
```

### Video Recording

```python
@pytest.fixture
def context(browser):
    context = browser.new_context(
        record_video_dir="test-results/videos/"
    )
    yield context
    context.close()
```

### Trace Viewer

Playwright's trace viewer shows a timeline of test execution:

```python
@pytest.fixture
def context(browser):
    context = browser.new_context()
    context.tracing.start(screenshots=True, snapshots=True)
    yield context
    context.tracing.stop(path="trace.zip")
    context.close()
```

View trace:
```bash
playwright show-trace trace.zip
```

### Console Logs

```python
def test_with_console_logs(page, base_url):
    # Capture console messages
    messages = []
    page.on("console", lambda msg: messages.append(msg))
    
    page.goto(base_url)
    
    # Check for errors
    errors = [m for m in messages if m.type == "error"]
    assert len(errors) == 0
```

## Selectors

### Best Practices

**Priority order:**
1. `data-testid` attributes (most stable)
2. Semantic selectors (role, text)
3. CSS selectors (class, id)
4. XPath (last resort)

### Examples

```python
# By test ID (recommended)
page.locator("[data-testid='add-device']")

# By role
page.locator("role=button[name='Add Device']")

# By text
page.locator("button:has-text('Add Device')")

# By CSS
page.locator("#device-list .device-item")

# Chaining
page.locator(".device-list").locator("button.edit")

# First/last
page.locator(".device-item").first
page.locator(".device-item").last
```

### Adding Test IDs to HTML

```html
<!-- Add data-testid attributes for stable selectors -->
<button data-testid="add-device">Add Device</button>
<div data-testid="device-list">...</div>
<input data-testid="device-name" />
```

## Common Patterns

### Form Submission

```python
def test_form_submission(page, base_url):
    page.goto(base_url)
    
    # Fill form
    page.locator("#name").fill("Test Device")
    page.locator("#type").select_option("tv")
    
    # Submit and wait for response
    with page.expect_response("**/api/devices") as response_info:
        page.locator("button[type='submit']").click()
    
    response = response_info.value
    assert response.status == 200
```

### Dialog Handling

```python
def test_delete_confirmation(page, base_url):
    page.goto(base_url)
    
    # Accept dialog
    page.on("dialog", lambda dialog: dialog.accept())
    page.locator("button.delete").click()
    
    # Or dismiss dialog
    page.on("dialog", lambda dialog: dialog.dismiss())
```

### Network Mocking

```python
def test_with_mocked_api(page, base_url):
    # Mock API response
    page.route("**/api/devices", lambda route: route.fulfill(
        status=200,
        body='{"devices": []}'
    ))
    
    page.goto(base_url)
```

### File Upload

```python
def test_file_upload(page, base_url):
    page.goto(base_url)
    
    # Upload file
    page.locator("input[type='file']").set_input_files("test-file.json")
```

## Performance Testing

```python
@pytest.mark.e2e
def test_page_load_performance(page, base_url):
    """Test page load time"""
    import time
    
    start = time.time()
    page.goto(base_url)
    page.wait_for_load_state("networkidle")
    load_time = time.time() - start
    
    assert load_time < 3.0, f"Page took {load_time:.2f}s"

@pytest.mark.e2e
def test_interaction_performance(page, base_url):
    """Test interaction responsiveness"""
    page.goto(base_url)
    
    start = time.time()
    page.locator("button.add-device").click()
    page.locator(".modal").wait_for(state="visible")
    response_time = time.time() - start
    
    assert response_time < 0.5, "Modal should open in < 500ms"
```

## Accessibility Testing

```python
@pytest.mark.e2e
@pytest.mark.a11y
def test_keyboard_navigation(page, base_url):
    """Test keyboard accessibility"""
    page.goto(base_url)
    
    # Tab through elements
    page.keyboard.press("Tab")
    focused = page.evaluate("document.activeElement.tagName")
    assert focused in ["BUTTON", "A", "INPUT"]

@pytest.mark.e2e
@pytest.mark.a11y
def test_aria_labels(page, base_url):
    """Test ARIA labels"""
    page.goto(base_url)
    
    buttons = page.locator("button").all()
    for button in buttons:
        if button.is_visible():
            text = button.inner_text()
            aria_label = button.get_attribute("aria-label")
            assert text or aria_label, "Button needs text or aria-label"
```

## CI/CD Integration

### GitHub Actions

```yaml
- name: Install Playwright
  run: |
    pip install playwright pytest-playwright
    playwright install chromium

- name: Start application
  run: |
    python app/main.py &
    sleep 5  # Wait for startup

- name: Run E2E tests
  run: |
    pytest tests/e2e/ --browser chromium

- name: Upload screenshots
  if: failure()
  uses: actions/upload-artifact@v3
  with:
    name: playwright-screenshots
    path: test-results/screenshots/
```

## Best Practices

### 1. Test Isolation
- Each test should be independent
- Use fixtures to reset state
- Don't rely on test execution order

### 2. Stable Selectors
- Use `data-testid` attributes
- Avoid brittle CSS selectors
- Don't rely on text that might change

### 3. Explicit Waits
- Use `wait_for_load_state("networkidle")`
- Wait for specific elements
- Avoid `wait_for_timeout` when possible

### 4. Meaningful Assertions
- Test user-visible behavior
- Use descriptive assertion messages
- Test one thing per test

### 5. Performance
- Run E2E tests in parallel when possible
- Use `--headed` only for debugging
- Skip slow tests in development

## Troubleshooting

### Tests Timing Out

```python
# Increase timeout
page.locator("#slow-element").wait_for(timeout=10000)  # 10 seconds

# Or globally in conftest.py
@pytest.fixture
def page(context):
    page = context.new_page()
    page.set_default_timeout(10000)
    yield page
```

### Element Not Found

```python
# Wait for element
page.locator("#element").wait_for(state="visible")

# Check if element exists
if page.locator("#element").count() > 0:
    page.locator("#element").click()
```

### Flaky Tests

- Add explicit waits
- Use `wait_for_load_state("networkidle")`
- Avoid `wait_for_timeout`
- Check for race conditions

## Resources

- [Playwright Python Docs](https://playwright.dev/python/)
- [Playwright Best Practices](https://playwright.dev/python/docs/best-practices)
- [Selector Guide](https://playwright.dev/python/docs/selectors)
- [Debugging Guide](https://playwright.dev/python/docs/debug)

---

**Quick Start:**
```bash
pip install -r requirements-test.txt
playwright install chromium
python app/main.py &
pytest tests/e2e/
```
