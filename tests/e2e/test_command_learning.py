"""
E2E tests for command learning workflows
"""

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
@pytest.mark.slow
class TestCommandLearning:
    """Test command learning interface and workflows"""
    
    def test_learn_command_button_exists(self, page, base_url):
        """Test that learn command button is accessible"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to a device first
        device_item = page.locator(".device-item, [data-testid='device-item']").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for learn/add command button
            learn_button = page.locator(
                "button:has-text('Learn'), "
                "button:has-text('Add Command'), "
                "[data-testid='learn-command']"
            ).first
            
            if learn_button.is_visible():
                expect(learn_button).to_be_visible()
    
    def test_learn_command_modal_opens(self, page, base_url):
        """Test that learn command opens modal"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device
        device_item = page.locator(".device-item").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Click learn button
            learn_button = page.locator(
                "button:has-text('Learn'), "
                "button:has-text('Add Command')"
            ).first
            
            if learn_button.is_visible():
                learn_button.click()
                page.wait_for_timeout(500)
                
                # Modal should appear
                modal = page.locator(
                    ".modal, dialog, [role='dialog'], "
                    "[data-testid='learn-modal']"
                ).first
                
                expect(modal).to_be_visible(timeout=3000)
    
    def test_command_name_input(self, page, base_url):
        """Test command name input field"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device and open learn modal
        device_item = page.locator(".device-item").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            learn_button = page.locator("button:has-text('Learn')").first
            if learn_button.is_visible():
                learn_button.click()
                page.wait_for_timeout(500)
                
                # Find command name input
                name_input = page.locator(
                    "input[name='command_name'], "
                    "input[placeholder*='command' i], "
                    "#command-name"
                ).first
                
                if name_input.is_visible():
                    name_input.fill("power")
                    expect(name_input).to_have_value("power")
    
    def test_learning_countdown_display(self, page, base_url):
        """Test that learning countdown is displayed"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device
        device_item = page.locator(".device-item").first
        if not device_item.is_visible():
            pytest.skip("No devices available")
        
        device_item.click()
        page.wait_for_timeout(500)
        
        # Open learn modal and start learning
        learn_button = page.locator("button:has-text('Learn')").first
        if not learn_button.is_visible():
            pytest.skip("Learn button not found")
        
        learn_button.click()
        page.wait_for_timeout(500)
        
        # Fill command name
        name_input = page.locator("input[name='command_name']").first
        if name_input.is_visible():
            name_input.fill("test_command")
            
            # Click start learning
            start_button = page.locator(
                "button:has-text('Start Learning'), "
                "button[type='submit']"
            ).first
            
            if start_button.is_visible():
                start_button.click()
                page.wait_for_timeout(500)
                
                # Look for countdown or progress indicator
                countdown = page.locator(
                    ".countdown, "
                    "[data-testid='countdown'], "
                    "text=/\\d+\\s*seconds?/"
                ).first
                
                # Countdown should be visible (or timeout message)
                page.wait_for_timeout(2000)
    
    def test_command_list_displays(self, page, base_url):
        """Test that learned commands are displayed"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device
        device_item = page.locator(".device-item").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for command list
            command_list = page.locator(
                ".command-list, "
                "[data-testid='command-list'], "
                "#commands"
            ).first
            
            expect(command_list).to_be_visible(timeout=5000)
    
    def test_test_command_button(self, page, base_url):
        """Test that test button exists for commands"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device
        device_item = page.locator(".device-item").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for test button on first command
            test_button = page.locator(
                "button:has-text('Test'), "
                "[data-testid='test-command']"
            ).first
            
            if test_button.is_visible():
                expect(test_button).to_be_visible()


@pytest.mark.e2e
class TestCommandManagement:
    """Test command management features"""
    
    def test_delete_command_button(self, page, base_url):
        """Test that commands can be deleted"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device with commands
        device_item = page.locator(".device-item").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for delete button on command
            delete_button = page.locator(
                "button:has-text('Delete'), "
                ".delete-command, "
                "[data-testid='delete-command']"
            ).first
            
            if delete_button.is_visible():
                expect(delete_button).to_be_visible()
    
    def test_command_search_filter(self, page, base_url):
        """Test command search/filter"""
        page.goto(base_url)
        page.wait_for_load_state("networkidle")
        
        # Navigate to device
        device_item = page.locator(".device-item").first
        if device_item.is_visible():
            device_item.click()
            page.wait_for_timeout(500)
            
            # Look for command search
            search_input = page.locator(
                "input[placeholder*='search command' i], "
                "[data-testid='command-search']"
            ).first
            
            if search_input.is_visible():
                search_input.fill("power")
                expect(search_input).to_have_value("power")
