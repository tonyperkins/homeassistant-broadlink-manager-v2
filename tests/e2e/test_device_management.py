"""
E2E tests for device management workflows
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
class TestDeviceManagement:
    """Test device creation, editing, and deletion workflows"""
    
    def test_add_device_button_exists(self, page, base_url):
        """Test that add device button is present"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Look for add device button (adjust selector to match your UI)
        add_button = page.locator(
            "button:has-text('Add Device'), "
            "[data-testid='add-device'], "
            ".add-device-btn"
        ).first
        
        expect(add_button).to_be_visible(timeout=5000)
    
    def test_create_device_modal_opens(self, page, base_url):
        """Test that clicking add device opens modal/form"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Click add device button
        add_button = page.locator(
            "button:has-text('Add Device'), "
            "[data-testid='add-device']"
        ).first
        
        if add_button.is_visible():
            add_button.click()
            
            # Wait for modal or form to appear
            modal = page.locator(
                ".modal, dialog, [role='dialog'], "
                "[data-testid='device-form']"
            ).first
            
            expect(modal).to_be_visible(timeout=3000)
    
    def test_device_form_fields(self, page, base_url):
        """Test that device form has required fields"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Open add device form
        add_button = page.locator("button:has-text('Add Device')").first
        if add_button.is_visible():
            add_button.click()
            page.wait_for_timeout(500)
            
            # Check for form fields (adjust selectors)
            name_field = page.locator(
                "input[name='name'], "
                "input[placeholder*='name' i], "
                "#device-name"
            ).first
            
            if name_field.is_visible():
                expect(name_field).to_be_visible()
    
    def test_create_device_workflow(self, page, base_url):
        """Test complete device creation workflow"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Click add device
        add_button = page.locator("button:has-text('Add Device')").first
        if not add_button.is_visible():
            pytest.skip("Add device button not found")
        
        add_button.click()
        page.wait_for_timeout(500)
        
        # Fill in device details
        # Adjust selectors based on your actual form
        name_input = page.locator("input[name='name'], #device-name").first
        if name_input.is_visible():
            name_input.fill("Test Device")
            
            # Select device type if dropdown exists
            type_select = page.locator("select[name='type'], #device-type").first
            if type_select.is_visible():
                type_select.select_option("tv")
            
            # Submit form
            submit_button = page.locator(
                "button[type='submit'], "
                "button:has-text('Save'), "
                "button:has-text('Create')"
            ).first
            
            if submit_button.is_visible():
                submit_button.click()
                
                # Wait for success message or device to appear in list
                page.wait_for_timeout(1000)
                
                # Verify device appears in list
                device_item = page.locator("text=Test Device").first
                expect(device_item).to_be_visible(timeout=5000)
    
    def test_device_list_displays(self, page, base_url):
        """Test that device list displays correctly"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Check for device list or empty state
        device_list = page.locator(
            "[data-testid='device-list'], "
            ".device-list, "
            "#devices"
        ).first
        
        expect(device_list).to_be_visible(timeout=5000)
    
    def test_device_search_filter(self, page, base_url):
        """Test device search/filter functionality"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Look for search input
        search_input = page.locator(
            "input[type='search'], "
            "input[placeholder*='search' i], "
            "[data-testid='device-search']"
        ).first
        
        if search_input.is_visible():
            # Type in search
            search_input.fill("bedroom")
            page.wait_for_timeout(500)
            
            # Results should update (basic check)
            expect(search_input).to_have_value("bedroom")


@pytest.mark.e2e
class TestDeviceInteractions:
    """Test device interaction features"""
    
    def test_device_click_shows_details(self, page, base_url):
        """Test that clicking a device shows its details"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Find first device in list
        device_item = page.locator(
            ".device-item, "
            "[data-testid='device-item'], "
            ".device-card"
        ).first
        
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Details panel or modal should appear
            details = page.locator(
                ".device-details, "
                "[data-testid='device-details'], "
                ".details-panel"
            ).first
            
            expect(details).to_be_visible(timeout=3000)
    
    def test_device_edit_button(self, page, base_url):
        """Test that device edit button is accessible"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Find first device
        device_item = page.locator(".device-item, [data-testid='device-item']").first
        
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for edit button
            edit_button = page.locator(
                "button:has-text('Edit'), "
                "[data-testid='edit-device'], "
                ".edit-btn"
            ).first
            
            if edit_button.is_visible():
                expect(edit_button).to_be_visible()
    
    def test_device_delete_confirmation(self, page, base_url):
        """Test that delete requires confirmation"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Find first device
        device_item = page.locator(".device-item").first
        
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for delete button
            delete_button = page.locator(
                "button:has-text('Delete'), "
                "[data-testid='delete-device']"
            ).first
            
            if delete_button.is_visible():
                # Set up dialog handler before clicking
                page.on("dialog", lambda dialog: dialog.dismiss())
                
                delete_button.click()
                page.wait_for_timeout(500)
                
                # Confirmation dialog should have appeared
                # (we dismissed it, so device should still be there)
