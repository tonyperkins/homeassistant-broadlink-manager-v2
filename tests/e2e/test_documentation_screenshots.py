"""
E2E tests for capturing documentation screenshots

Run with: pytest tests/e2e/test_documentation_screenshots.py -v

Screenshots will be saved to: docs/images/screenshots/
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
        
        # Click "Add Device" button
        page.click("button:has-text('Add Device')")
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
        page.click("button:has-text('Add Device')")
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
        page.click("button:has-text('Add Device')")
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
        
        # Click settings icon (adjust selector as needed)
        settings_btn = page.locator("button[aria-label='Settings'], .settings-icon, i.mdi-cog")
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
        
        # Click settings to open menu
        settings_btn = page.locator("button[aria-label='Settings'], .settings-icon, i.mdi-cog")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(500)
            
            # Click dark theme option
            dark_theme_btn = page.locator("button:has-text('Dark'), [data-theme='dark']")
            if dark_theme_btn.is_visible():
                dark_theme_btn.click()
                page.wait_for_timeout(1000)
                
                # Close settings menu
                page.keyboard.press("Escape")
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
        
        # Switch to dark mode
        settings_btn = page.locator("button[aria-label='Settings'], .settings-icon, i.mdi-cog")
        if settings_btn.is_visible():
            settings_btn.click()
            page.wait_for_timeout(500)
            
            dark_theme_btn = page.locator("button:has-text('Dark'), [data-theme='dark']")
            if dark_theme_btn.is_visible():
                dark_theme_btn.click()
                page.wait_for_timeout(1000)
                
                # Close settings and navigate to devices
                page.keyboard.press("Escape")
                page.wait_for_timeout(500)
        
        # Navigate to devices page
        page.goto(f"{base_url}/#/devices")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        
        # Capture dark mode device list
        page.screenshot(
            path=str(docs_screenshot_dir / "device-list-dark.png"),
            full_page=True
        )
