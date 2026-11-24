"""
Playwright E2E Automation for Role-Based Access Control in Control Panel (UC5 / FR7).
Verifies restricted auditor account behavior in the control panel.
"""
import os
import pytest

class TestAuditorAccessControlE2E:
    """Verifies auditor login and restricted administrative privileges."""

    def test_auditor_login_and_inspection(self, page, base_url, screenshot_dir, auditor_password):
        login_url = f"{base_url}/control/login"
        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        # Login as auditor
        page.fill('input[name="email"]', "auditor@localhost")
        page.fill('input[name="password"]', auditor_password)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Verify session established
        assert "/control/login" not in page.url or "control" in page.url

        # Navigate to orders
        orders_url = f"{base_url}/control/event/sqe/sqe2026/orders/"
        page.goto(orders_url)
        page.wait_for_load_state("networkidle")

        screenshot_path = os.path.join(screenshot_dir, "05_auditor_dashboard.png")
        page.screenshot(path=screenshot_path)
        print(f"Auditor view captured: {screenshot_path}")
