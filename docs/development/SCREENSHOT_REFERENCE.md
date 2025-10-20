# Screenshot Reference

This document tracks all automatically generated screenshots and their usage in documentation.

## Overview

Screenshots are automatically generated using Playwright E2E tests and are used throughout the README and documentation.

**Script Location**: `tests/e2e/test_documentation_screenshots.py`  
**Output Directory**: `docs/images/screenshots/`  
**Total Screenshots**: 18

## Update Screenshots

### PowerShell (Windows)
```powershell
.\update-docs-screenshots.ps1
```

### Bash (Linux/Mac)
```bash
./update-docs-screenshots.sh
```

## Screenshot Inventory

### Light Mode Screenshots (7)

| Filename | Test | Used In | Description |
|----------|------|---------|-------------|
| `dashboard-overview.png` | test_01 | README.md | Main dashboard with SmartIR integration |
| `device-list.png` | test_02 | README.md | Device management page |
| `create-device-modal.png` | test_03 | README.md | Add device modal dialog |
| `broadlink-device-form.png` | test_04 | README.md | Broadlink device creation form |
| `smartir-device-form.png` | test_05 | README.md | SmartIR device creation form |
| `settings-menu.png` | test_07 | - | Settings dropdown menu (light) |
| `smartir-status-card.png` | test_08 | - | SmartIR status card component |

### Dark Mode Screenshots (4)

| Filename | Test | Used In | Description |
|----------|------|---------|-------------|
| `dashboard-dark.png` | test_12 | README.md | Dashboard in dark theme |
| `device-list-dark.png` | test_13 | README.md | Device list in dark theme |
| `smartir-status-card-dark.png` | test_14 | - | SmartIR card in dark theme |
| `settings-menu-dark.png` | test_15 | README.md | Settings menu in dark theme |

### Mobile Screenshots (3)

| Filename | Test | Used In | Description |
|----------|------|---------|-------------|
| `mobile-dashboard.png` | test_10 | README.md | Dashboard on iPhone 12/13 Pro (390x844) |
| `mobile-device-list.png` | test_16 | README.md | Device list on mobile |
| `mobile-dashboard-dark.png` | test_17 | README.md | Mobile dashboard in dark mode |

### Tablet Screenshots (2)

| Filename | Test | Used In | Description |
|----------|------|---------|-------------|
| `tablet-dashboard.png` | test_11 | - | Dashboard on iPad (768x1024) |
| `tablet-device-list.png` | test_18 | README.md | Device list on tablet |

### Conditional Screenshots (2)

| Filename | Test | Used In | Description |
|----------|------|---------|-------------|
| `command-learning-wizard.png` | test_06 | - | Command learning dialog (if device exists) |
| `entity-generation-success.png` | test_09 | - | Placeholder for future implementation |

## README.md Screenshot Organization

The README organizes screenshots into themed sections:

### 🌞 Light Mode
- Dashboard Overview
- Device Management

### 🌙 Dark Mode
- Dashboard (Dark)
- Device List (Dark)
- Settings Menu (Dark)

### 📱 Mobile & Tablet Views
- 2x2 table layout showing:
  - Mobile Dashboard (Light)
  - Mobile Dashboard (Dark)
  - Mobile Device List
  - Tablet View

### 🎛️ Device Setup
- Add New Device
- Broadlink Device Setup
- SmartIR Device Setup

## Viewport Sizes

| Device Type | Width | Height | Test Cases |
|-------------|-------|--------|------------|
| Desktop | 1280 | 720 | Most tests (default) |
| Mobile (iPhone 12/13 Pro) | 390 | 844 | test_10, test_16, test_17 |
| Tablet (iPad) | 768 | 1024 | test_11, test_18 |

## Screenshot Capture Strategy

### Full Page vs Viewport
- **Full Page** (`full_page=True`): Desktop views that may scroll
- **Viewport Only** (`full_page=False`): Mobile/tablet views to show exact device size

### Dark Mode Activation
All dark mode tests follow this pattern:
1. Navigate to page
2. Click settings button
3. Click dark theme option
4. Wait for theme to apply (1000ms)
5. Close settings menu (if needed)
6. Capture screenshot

### Mobile/Tablet Views
1. Set viewport size using `page.set_viewport_size()`
2. Navigate to page
3. Wait for content to load
4. Capture viewport only (not full page)

## Adding New Screenshots

To add a new screenshot:

1. **Add test method** in `test_documentation_screenshots.py`:
   ```python
   def test_XX_your_screenshot(self, page: Page, base_url, docs_screenshot_dir):
       """Capture your new view"""
       page.goto(f"{base_url}/#/your-route")
       page.wait_for_load_state("networkidle")
       page.wait_for_timeout(1000)
       
       page.screenshot(
           path=str(docs_screenshot_dir / "your-screenshot.png"),
           full_page=True  # or False for viewport only
       )
   ```

2. **Update this reference** with the new screenshot details

3. **Add to README.md** in the appropriate section

4. **Run the script** to generate all screenshots:
   ```powershell
   .\update-docs-screenshots.ps1
   ```

## Maintenance Notes

- Screenshots are committed to git (not in .gitignore)
- Run before each release to ensure docs are current
- All tests use `@pytest.mark.docs` marker
- Tests run sequentially (not in parallel) to avoid conflicts
- Each test is independent and can run standalone

## CI/CD Integration

Screenshots can be automatically updated in CI/CD:

```yaml
- name: Update Documentation Screenshots
  run: |
    python app/main.py &
    sleep 5
    pytest tests/e2e/test_documentation_screenshots.py -v -m docs
    kill %1
```

## Troubleshooting

### Screenshots are blank
- Increase wait timeouts (`page.wait_for_timeout()`)
- Check if app is fully loaded (`page.wait_for_load_state("networkidle")`)

### Dark mode not applying
- Increase wait after clicking dark theme button
- Verify dark theme selector is correct

### Mobile screenshots too large/small
- Verify viewport size matches device dimensions
- Use `full_page=False` for mobile/tablet views

### Settings menu not visible
- Check selector: `button[aria-label='Settings'], .settings-icon, i.mdi-cog`
- Verify element is visible before clicking
