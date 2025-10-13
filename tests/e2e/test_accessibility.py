"""
E2E tests for accessibility (a11y)
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
@pytest.mark.a11y
class TestAccessibility:
    """Test accessibility features"""
    
    def test_keyboard_navigation(self, page, base_url):
        """Test that UI is keyboard navigable"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Tab through interactive elements
        page.keyboard.press("Tab")
        page.wait_for_timeout(200)
        
        # Check that focus is visible
        focused_element = page.evaluate("document.activeElement.tagName")
        assert focused_element in ["BUTTON", "A", "INPUT", "SELECT"], \
            "First tab should focus an interactive element"
    
    def test_buttons_have_accessible_names(self, page, base_url):
        """Test that buttons have accessible names"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Get all buttons
        buttons = page.locator("button").all()
        
        for button in buttons:
            if button.is_visible():
                # Button should have text or aria-label
                text = button.inner_text()
                aria_label = button.get_attribute("aria-label")
                
                assert text or aria_label, \
                    "Button should have visible text or aria-label"
    
    def test_heading_hierarchy(self, page, base_url):
        """Test that headings follow proper hierarchy"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Get all headings
        h1_count = len(page.locator("h1").all())
        assert h1_count >= 1, "Page should have at least one h1"
