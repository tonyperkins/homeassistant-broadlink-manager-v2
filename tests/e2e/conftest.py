"""
Playwright configuration and fixtures for E2E tests
"""

import pytest
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext
import tempfile
import shutil
from pathlib import Path


@pytest.fixture(scope="session")
def browser_type_launch_args():
    """Browser launch arguments"""
    return {
        "headless": True,  # Set to False to see browser during tests
        "slow_mo": 0,  # Milliseconds to slow down operations (useful for debugging)
    }


@pytest.fixture(scope="session")
def playwright_instance():
    """Create Playwright instance for the session"""
    with sync_playwright() as p:
        yield p


@pytest.fixture(scope="session")
def browser(playwright_instance, browser_type_launch_args):
    """Launch browser for the session"""
    browser = playwright_instance.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture
def context(browser):
    """Create a new browser context for each test"""
    context = browser.new_context(
        viewport={"width": 1280, "height": 720},
        locale="en-US",
        timezone_id="America/New_York",
    )
    yield context
    context.close()


@pytest.fixture
def page(context):
    """Create a new page for each test"""
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def mobile_context(browser):
    """Create a mobile browser context"""
    context = browser.new_context(
        **browser.devices["iPhone 12"],
        locale="en-US",
    )
    yield context
    context.close()


@pytest.fixture
def mobile_page(mobile_context):
    """Create a mobile page"""
    page = mobile_context.new_page()
    yield page
    page.close()


@pytest.fixture
def tablet_context(browser):
    """Create a tablet browser context"""
    context = browser.new_context(
        **browser.devices["iPad Pro"],
        locale="en-US",
    )
    yield context
    context.close()


@pytest.fixture
def tablet_page(tablet_context):
    """Create a tablet page"""
    page = tablet_context.new_page()
    yield page
    page.close()


@pytest.fixture
def base_url():
    """Base URL for the application"""
    return "http://localhost:8099"


@pytest.fixture
def authenticated_page(page, base_url):
    """Page with authentication if needed"""
    # If your app requires authentication, add it here
    # For now, just navigate to base URL
    page.goto(base_url)
    return page


@pytest.fixture
def screenshot_dir():
    """Directory for test screenshots"""
    screenshot_path = Path("test-results/screenshots")
    screenshot_path.mkdir(parents=True, exist_ok=True)
    return screenshot_path


@pytest.fixture(autouse=True)
def capture_screenshot_on_failure(request, page, screenshot_dir):
    """Automatically capture screenshot on test failure"""
    yield
    if request.node.rep_call.failed:
        screenshot_path = screenshot_dir / f"{request.node.name}.png"
        page.screenshot(path=str(screenshot_path))
        print(f"Screenshot saved: {screenshot_path}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for screenshot on failure"""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
