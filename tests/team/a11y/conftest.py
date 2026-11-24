"""
Playwright configuration for Usability & Accessibility Testing (Phase 6).
Provides axe-core injection fixtures and screenshot directories.
"""
import os
import pytest
from playwright.sync_api import sync_playwright
from scripts.test_secrets import get_test_secret

BASE_URL = "http://localhost:8345"
AXE_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "axe.min.js")
REPORTS_DIR = os.path.join("reports", "a11y")
SCREENSHOT_DIR = os.path.join(REPORTS_DIR, "screenshots")

@pytest.fixture(scope="session")
def browser_instance():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        locale="en",
        bypass_csp=True
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def axe_path():
    return AXE_SCRIPT_PATH

@pytest.fixture(scope="session")
def reports_dir():
    return REPORTS_DIR

@pytest.fixture(scope="session")
def screenshot_dir():
    return SCREENSHOT_DIR

@pytest.fixture(scope="session")
def admin_password():
    return get_test_secret("SQE_ADMIN_PASSWORD")
