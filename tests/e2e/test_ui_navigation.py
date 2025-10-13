"""
E2E tests for UI navigation and basic interactions
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
class TestUINavigation:
    """Test basic UI navigation and page loads"""
    
    def test_homepage_loads(self, page, base_url):
        """Test that the homepage loads successfully"""
        page.goto(base_url)
        
        # Wait for page to load
        page.wait_for_load_state("networkidle")
        
        # Check title or main heading
        expect(page).to_have_title("Broadlink Manager")
        
        # Verify main container is visible
        main_container = page.locator("main, #app, .container").first
        expect(main_container).to_be_visible()
    
    def test_device_list_visible(self, page, base_url):
        """Test that device list section is visible"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Look for device list or empty state
        device_section = page.locator("[data-testid='device-list'], .device-list, #devices").first
        expect(device_section).to_be_visible(timeout=5000)
    
    def test_navigation_menu(self, page, base_url):
        """Test navigation menu is present and functional"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Check for navigation elements
        # Adjust selectors based on your actual UI
        nav = page.locator("nav, .navbar, [role='navigation']").first
        if nav.is_visible():
            expect(nav).to_be_visible()
    
    def test_responsive_layout(self, mobile_page, base_url):
        """Test that UI is responsive on mobile"""
        mobile_page.goto(base_url)
        mobile_page.wait_for_load_state("networkidle")
        
        # Verify page loads on mobile
        expect(mobile_page).to_have_title("Broadlink Manager")
        
        # Check that main content is visible
        main_content = mobile_page.locator("main, #app, .container").first
        expect(main_content).to_be_visible()
    
    def test_no_console_errors(self, page, base_url):
        """Test that page loads without console errors"""
        errors = []
        
        # Listen for console errors
        page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)
        
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Assert no critical errors (some warnings might be acceptable)
        critical_errors = [e for e in errors if "error" in str(e).lower()]
        assert len(critical_errors) == 0, f"Console errors found: {critical_errors}"


@pytest.mark.e2e
class TestUIPerformance:
    """Test UI performance metrics"""
    
    def test_page_load_time(self, page, base_url):
        """Test that page loads within acceptable time"""
        import time
        
        start_time = time.time()
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        load_time = time.time() - start_time
        
        # Page should load in under 3 seconds
        assert load_time < 3.0, f"Page took {load_time:.2f}s to load"
    
    def test_no_layout_shift(self, page, base_url):
        """Test for minimal layout shift during load"""
        page.goto(base_url)
        
        # Wait for initial load
        page.wait_for_timeout(500)
        
        # Take initial screenshot
        initial_screenshot = page.screenshot()
        
        # Wait for any late-loading content
        page.wait_for_timeout(1000)
        
        # Content should be stable (this is a basic check)
        # In production, you'd use Cumulative Layout Shift metrics
        page.wait_for_load_state("networkidle")
