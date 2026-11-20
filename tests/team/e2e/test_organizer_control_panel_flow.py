"""
Playwright E2E Automation for Organizer Control Panel (UC5).
Verifies privileged administrator login, dashboard navigation, and orders table view.
"""
import os
import pytest

class TestOrganizerControlPanelE2E:
    """Verifies UC5 Organizer administration in the backend control panel."""

    def test_admin_login_and_orders_view(self, page, base_url, screenshot_dir):
        # 1. Navigate to control login
        login_url = f"{base_url}/control/login"
        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        # 2. Enter admin credentials
        page.fill('input[name="email"]', "admin@localhost")
        page.fill('input[name="password"]', "admin_secure_password_2026")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # Assert successful authentication
        assert "/control/login" not in page.url or page.locator(".navbar-nav").count() > 0
        print(f"Admin logged in. Current URL: {page.url}")

        # 3. Navigate to Event Orders List
        orders_url = f"{base_url}/control/event/sqe/sqe2026/orders/"
        page.goto(orders_url)
        page.wait_for_load_state("networkidle")

        # 4. Verify orders management UI elements
        content = page.content()
        assert "Orders" in content
        # Under clean state "Nobody ordered a ticket yet" is displayed; under loaded state a table is displayed
        assert "Nobody ordered a ticket yet" in content or page.locator("table, .table, .table-responsive, .panel").count() > 0

        # Capture Control Panel Screenshot
        screenshot_path = os.path.join(screenshot_dir, "04_control_panel_orders.png")
        page.screenshot(path=screenshot_path)
        print(f"Control panel orders table verified. Screenshot: {screenshot_path}")
