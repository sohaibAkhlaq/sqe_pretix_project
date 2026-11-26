"""
Playwright E2E Test Configuration.
Manages browser lifecycle, context, viewport, and screenshot artifacts.
"""
import os
import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
from playwright.sync_api import sync_playwright
from scripts.test_secrets import get_test_secret

BASE_URL = "http://localhost:8345"
SCREENSHOT_DIR = os.path.join("reports", "e2e", "screenshots")

@pytest.fixture(scope="session")
def browser_instance():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    zap_proxy = os.environ.get("ZAP_PROXY")
    launch_kwargs = {"headless": True}
    if zap_proxy:
        launch_kwargs["proxy"] = {"server": zap_proxy}
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch_kwargs)
        yield browser
        browser.close()

@pytest.fixture(scope="function")
def page(browser_instance):
    context = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        locale="en",
        ignore_https_errors=True,
    )
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture(scope="session")
def base_url():
    return BASE_URL

@pytest.fixture(scope="session")
def screenshot_dir():
    return SCREENSHOT_DIR

@pytest.fixture(scope="session")
def admin_password():
    return get_test_secret("SQE_ADMIN_PASSWORD")

@pytest.fixture(scope="session")
def auditor_password():
    return get_test_secret("SQE_AUDITOR_PASSWORD")
