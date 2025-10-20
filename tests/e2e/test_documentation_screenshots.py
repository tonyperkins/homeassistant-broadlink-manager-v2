"""
E2E tests for capturing documentation screenshots

Run with: pytest tests/e2e/test_documentation_screenshots.py -v -m docs

Screenshots will be saved to: docs/images/screenshots/

Generated Screenshots (18 total):
- Light Mode: dashboard-overview, device-list, create-device-modal, 
  broadlink-device-form, smartir-device-form, settings-menu, smartir-status-card
- Dark Mode: dashboard-dark, device-list-dark, smartir-status-card-dark, settings-menu-dark
- Mobile: mobile-dashboard, mobile-device-list, mobile-dashboard-dark
- Tablet: tablet-dashboard, tablet-device-list
- Other: command-learning-wizard (conditional)
"""

import pytest
from playwright.sync_api import Page
from pathlib import Path


@pytest.fixture
def docs_screenshot_dir():
    """Directory for documentation screenshots"""
    screenshot_path = Path("docs/images/screenshots")
    screenshot_path.mkdir(parents=True, exist_ok=True)
    return screenshot_path


@pytest.mark.e2e
@pytest.mark.docs
class TestDocumentationScreenshots:
    """Capture screenshots for documentation"""
    
    def test_01_dashboard_overview(self, page: Page, base_url, docs_screenshot_dir):
        """Capture main dashboard view"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Wait for content to load
        page.wait_for_timeout(1000)
        
        # Full page screenshot
        page.screenshot(
            path=str(docs_screenshot_dir / "dashboard-overview.png"),
            full_page=True
        )
    
    def test_02_device_list(self, page: Page, base_url, docs_screenshot_dir):
        """Capture device list view"""
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        page.screenshot(
            path=str(docs_screenshot_dir / "device-list.png"),
            full_page=True
        )
    
    def test_03_create_device_modal(self, page: Page, base_url, docs_screenshot_dir):
        """Capture create device modal"""
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        
        # Click "New" button to add device
        page.click("button:has-text('New')")
        page.wait_for_timeout(500)
        
        # Screenshot of modal
        page.screenshot(
            path=str(docs_screenshot_dir / "create-device-modal.png")
        )
    
    def test_04_broadlink_device_form(self, page: Page, base_url, docs_screenshot_dir):
        """Capture Broadlink device creation form"""
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        
        # Open modal and select Broadlink device type
        page.click("button:has-text('New')")
        page.wait_for_timeout(500)
        
        # Select Broadlink device type from the specific dropdown in the modal
        page.select_option("select#device-type", value="broadlink")
        page.wait_for_timeout(500)
        
        page.screenshot(
            path=str(docs_screenshot_dir / "broadlink-device-form.png")
        )
    
    def test_05_smartir_device_form(self, page: Page, base_url, docs_screenshot_dir):
        """Capture SmartIR device creation form"""
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        
        # Open modal and select SmartIR device type
        page.click("button:has-text('New')")
        page.wait_for_timeout(500)
        
        # Select SmartIR device type from the specific dropdown
        # Try to select SmartIR if not disabled
        try:
            page.select_option("select#device-type", value="smartir")
            page.wait_for_timeout(500)
        except:
            # If disabled, just screenshot the modal as-is
            pass
        
        page.screenshot(
            path=str(docs_screenshot_dir / "smartir-device-form.png")
        )
    
    def test_06_command_learning_wizard(self, page: Page, base_url, docs_screenshot_dir):
        """Capture command learning wizard"""
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        
        # Assuming there's a device, click to edit
        # Adjust selector based on your actual UI
        device_card = page.locator(".device-card").first
        if device_card.is_visible():
            device_card.click()
            page.wait_for_timeout(500)
            
            # Click "Learn Command" button if visible
            learn_btn = page.locator("button:has-text('Learn Command')")
            if learn_btn.is_visible():
                learn_btn.click()
                page.wait_for_timeout(500)
                
                page.screenshot(
                    path=str(docs_screenshot_dir / "command-learning-wizard.png")
                )
    
    def test_07_settings_menu(self, page: Page, base_url, docs_screenshot_dir):
        """Capture settings menu"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Click settings button in header
        settings_btn = page.locator(".app-header button[title='Settings']")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(500)
            
            page.screenshot(
                path=str(docs_screenshot_dir / "settings-menu.png")
            )
    
    def test_08_smartir_status_card(self, page: Page, base_url, docs_screenshot_dir):
        """Capture SmartIR status card"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Find SmartIR status card
        smartir_card = page.locator(".smartir-status-card, [class*='smartir']").first
        if smartir_card.is_visible():
            smartir_card.screenshot(
                path=str(docs_screenshot_dir / "smartir-status-card.png")
            )
    
    def test_09_entity_generation_success(self, page: Page, base_url, docs_screenshot_dir):
        """Capture entity generation success message"""
        # This would require actually generating entities
        # For now, just a placeholder
        pass
    
    def test_10_mobile_view(self, page: Page, base_url, docs_screenshot_dir):
        """Capture mobile responsive view"""
        # Set mobile viewport - iPhone 12/13 Pro size
        page.set_viewport_size({"width": 390, "height": 844})
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Capture just the viewport (not full page)
        page.screenshot(
            path=str(docs_screenshot_dir / "mobile-dashboard.png"),
            full_page=False
        )
    
    def test_11_tablet_view(self, page: Page, base_url, docs_screenshot_dir):
        """Capture tablet responsive view"""
        # Set tablet viewport - iPad size
        page.set_viewport_size({"width": 768, "height": 1024})
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Capture just the viewport
        page.screenshot(
            path=str(docs_screenshot_dir / "tablet-dashboard.png"),
            full_page=False
        )
    
    def test_12_dashboard_dark_mode(self, page: Page, base_url, docs_screenshot_dir):
        """Capture dashboard in dark mode"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Switch to dark mode by cycling theme button
        # Click theme button until we get to dark mode (max 3 clicks)
        for _ in range(3):
            body_class = page.locator('body').get_attribute('class')
            if body_class and 'dark-mode' in body_class:
                break
            theme_btn = page.locator("button[title*='Theme']")
            if theme_btn.is_visible():
                theme_btn.click()
                page.wait_for_timeout(500)
        
        # Wait for theme to fully apply
        page.wait_for_timeout(500)
        
        # Capture dark mode dashboard
        page.screenshot(
            path=str(docs_screenshot_dir / "dashboard-dark.png"),
            full_page=True
        )
    
    def test_13_device_list_dark_mode(self, page: Page, base_url, docs_screenshot_dir):
        """Capture device list in dark mode"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        # Switch to dark mode by cycling theme button
        # Click theme button until we get to dark mode (max 3 clicks)
        for _ in range(3):
            body_class = page.locator('body').get_attribute('class')
            if body_class and 'dark-mode' in body_class:
                break
            theme_btn = page.locator("button[title*='Theme']")
            if theme_btn.is_visible():
                theme_btn.click()
                page.wait_for_timeout(800)
        
        # Navigate to devices page (theme should persist)
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        # Wait for dark theme to be applied after navigation
        page.wait_for_timeout(1500)
        
        # Capture dark mode device list
        page.screenshot(
            path=str(docs_screenshot_dir / "device-list-dark.png"),
            full_page=True
        )
    
    def test_14_smartir_status_dark_mode(self, page: Page, base_url, docs_screenshot_dir):
        """Capture SmartIR status card in dark mode"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Switch to dark mode by cycling theme button
        for _ in range(3):
            body_class = page.locator('body').get_attribute('class')
            if body_class and 'dark-mode' in body_class:
                break
            theme_btn = page.locator("button[title*='Theme']")
            if theme_btn.is_visible():
                theme_btn.click()
                page.wait_for_timeout(500)
        
        # Wait for theme to fully apply
        page.wait_for_timeout(1000)
        
        # Find SmartIR status card
        smartir_card = page.locator(".smartir-status-card, [class*='smartir']").first
        if smartir_card.is_visible():
            smartir_card.screenshot(
                path=str(docs_screenshot_dir / "smartir-status-card-dark.png")
            )
    
    def test_15_settings_menu_dark_mode(self, page: Page, base_url, docs_screenshot_dir):
        """Capture settings menu in dark mode"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Switch to dark mode by cycling theme button
        for _ in range(3):
            body_class = page.locator('body').get_attribute('class')
            if body_class and 'dark-mode' in body_class:
                break
            theme_btn = page.locator("button[title*='Theme']")
            if theme_btn.is_visible():
                theme_btn.click()
                page.wait_for_timeout(500)
        
        # Wait for theme to apply
        page.wait_for_timeout(500)
        
        # Open settings menu (in header)
        settings_btn = page.locator(".app-header button[title='Settings']")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(500)
            
            # Capture settings menu in dark mode
            page.screenshot(
                path=str(docs_screenshot_dir / "settings-menu-dark.png")
            )
    
    def test_16_mobile_device_list(self, page: Page, base_url, docs_screenshot_dir):
        """Capture device list on mobile view"""
        # Set mobile viewport - iPhone 12/13 Pro size
        page.set_viewport_size({"width": 390, "height": 844})
        
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Capture just the viewport (not full page)
        page.screenshot(
            path=str(docs_screenshot_dir / "mobile-device-list.png"),
            full_page=False
        )
    
    def test_17_mobile_dashboard_dark(self, page: Page, base_url, docs_screenshot_dir):
        """Capture mobile dashboard in dark mode"""
        # Set mobile viewport
        page.set_viewport_size({"width": 390, "height": 844})
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Switch to dark mode by cycling theme button
        for _ in range(3):
            body_class = page.locator('body').get_attribute('class')
            if body_class and 'dark-mode' in body_class:
                break
            theme_btn = page.locator("button[title*='Theme']")
            if theme_btn.is_visible():
                theme_btn.click()
                page.wait_for_timeout(500)
        
        # Wait for theme to apply
        page.wait_for_timeout(500)
        
        # Capture mobile dark mode
        page.screenshot(
            path=str(docs_screenshot_dir / "mobile-dashboard-dark.png"),
            full_page=False
        )
    
    def test_18_tablet_device_list(self, page: Page, base_url, docs_screenshot_dir):
        """Capture device list on tablet view"""
        # Set tablet viewport - iPad size
        page.set_viewport_size({"width": 768, "height": 1024})
        
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Capture just the viewport
        page.screenshot(
            path=str(docs_screenshot_dir / "tablet-device-list.png"),
            full_page=False
        )
