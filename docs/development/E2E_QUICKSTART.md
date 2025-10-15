# E2E Testing Quick Start

Get started with browser automation testing in 5 minutes.

## Installation

```bash
# 1. Install dependencies
pip install -r requirements-test.txt

# 2. Install browsers
playwright install chromium
```

## Running E2E Tests

```bash
# Start your application first
python app/main.py

# In another terminal, run E2E tests
pytest tests/e2e/

# Run with visible browser (for debugging)
pytest tests/e2e/ --headed

# Run specific test
pytest tests/e2e/test_ui_navigation.py
```

## Quick Examples

### Test Page Load

```python
@pytest.mark.e2e
def test_homepage(page, base_url):
    page.goto(base_url)
    expect(page).to_have_title("Broadlink Manager")
```

### Test Button Click

```python
@pytest.mark.e2e
def test_add_device_button(page, base_url):
    page.goto(base_url)
    page.locator("button:has-text('Add Device')").click()
    expect(page.locator(".modal")).to_be_visible()
```

### Test Form Submission

```python
@pytest.mark.e2e
def test_create_device(page, base_url):
    page.goto(base_url)
    page.locator("#device-name").fill("Test TV")
    page.locator("button[type='submit']").click()
    expect(page.locator("text=Test TV")).to_be_visible()
```

### Test Mobile View

```python
@pytest.mark.e2e
def test_mobile(mobile_page, base_url):
    mobile_page.goto(base_url)
    expect(mobile_page).to_have_title("Broadlink Manager")
```

## Common Commands

```bash
# All E2E tests
pytest tests/e2e/

# Specific browser
pytest tests/e2e/ --browser firefox

# Slow motion (debugging)
pytest tests/e2e/ --slowmo 1000

# Exclude slow tests
pytest tests/e2e/ -m "not slow"

# Accessibility tests only
pytest tests/e2e/ -m a11y

# With screenshots on failure (automatic)
pytest tests/e2e/
# See: test-results/screenshots/
```

## Debugging

```bash
# Run with visible browser
pytest tests/e2e/ --headed

# Stop on first failure
pytest tests/e2e/ -x

# Verbose output
pytest tests/e2e/ -v

# Drop into debugger
pytest tests/e2e/ --pdb
```

## Test Structure

```
tests/e2e/
├── conftest.py                 # Fixtures (page, mobile_page, etc.)
├── test_ui_navigation.py       # Page loads, navigation
├── test_device_management.py   # Device CRUD
├── test_command_learning.py    # Command learning UI
└── test_accessibility.py       # Keyboard, ARIA, etc.
```

## Available Fixtures

- `page` - Desktop browser (1280x720)
- `mobile_page` - Mobile browser (iPhone 12)
- `tablet_page` - Tablet browser (iPad Pro)
- `base_url` - App URL (http://localhost:8099)
- `screenshot_dir` - Screenshot directory

## Best Practices

1. **Use data-testid attributes** for stable selectors
   ```html
   <button data-testid="add-device">Add Device</button>
   ```

2. **Wait for network idle**
   ```python
   page.goto(base_url)
   page.wait_for_load_state("networkidle")
   ```

3. **Use explicit waits**
   ```python
   page.locator("#element").wait_for(state="visible")
   ```

4. **One assertion per test** (when possible)

5. **Test user behavior, not implementation**

## Adding Test IDs to Your HTML

```html
<!-- Before -->
<button class="btn btn-primary">Add Device</button>

<!-- After -->
<button class="btn btn-primary" data-testid="add-device">
  Add Device
</button>
```

Then in tests:
```python
page.locator("[data-testid='add-device']").click()
```

## Selectors Priority

1. ✅ `data-testid` - Most stable
2. ✅ Text content - Good for buttons/links
3. ⚠️ CSS classes - Can change
4. ❌ XPath - Brittle, avoid

```python
# Best
page.locator("[data-testid='add-device']")

# Good
page.locator("button:has-text('Add Device')")

# OK
page.locator("#add-device-btn")

# Avoid
page.locator("div > div > button.btn-primary")
```

## Common Patterns

### Click and Wait
```python
page.locator("button").click()
page.locator(".modal").wait_for(state="visible")
```

### Fill Form
```python
page.locator("#name").fill("Test")
page.locator("#type").select_option("tv")
page.locator("button[type='submit']").click()
```

### Check Element Exists
```python
if page.locator("#optional-element").count() > 0:
    page.locator("#optional-element").click()
```

### Handle Dialogs
```python
page.on("dialog", lambda dialog: dialog.accept())
page.locator(".delete-btn").click()
```

## Next Steps

- **Full Guide**: See `docs/E2E_TESTING.md`
- **Add test IDs**: Add `data-testid` to your HTML
- **Write tests**: Start with critical user flows
- **CI/CD**: Integrate into GitHub Actions

## Resources

- [Playwright Docs](https://playwright.dev/python/)
- [Selectors Guide](https://playwright.dev/python/docs/selectors)
- [Best Practices](https://playwright.dev/python/docs/best-practices)

---

**Quick Tip**: Run with `--headed` to see what's happening!

```bash
pytest tests/e2e/test_ui_navigation.py --headed
```
