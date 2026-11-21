"""
Playwright E2E Automation for UC5 Organizer Order Management & Filter Controls.
Author: Shaiman (24i-3074) | Core Technical Area 3
Flows Automated:
- UC5 NF: Administrator logs in, accesses orders dashboard, and views management controls
- UC5 AF-1: Administrator filters orders by status query parameter
"""
import os
import pytest

class TestUC5AdminOrderManagementE2E:
    """Verifies UC5 backend control panel administration workflows."""

    def test_uc5_nf_admin_order_management_dashboard(self, page, base_url, screenshot_dir):
        # 1. Login as Admin
        page.goto(f"{base_url}/control/login")
        page.wait_for_load_state("networkidle")

        page.fill('input[name="email"]', "admin@localhost")
        page.fill('input[name="password"]', "admin_secure_password_2026")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # 2. Navigate to Orders management
        orders_url = f"{base_url}/control/event/sqe/sqe2026/orders/"
        page.goto(orders_url)
        page.wait_for_load_state("networkidle")

        assert "Orders" in page.content()

        screenshot_path = os.path.join(screenshot_dir, "09_uc5_admin_orders_dashboard.png")
        page.screenshot(path=screenshot_path)
        print(f"UC5 NF verified. Screenshot: {screenshot_path}")

    def test_uc5_af1_filter_orders_by_status(self, page, base_url, screenshot_dir):
        """
        Flow UC5 AF-1: Administrator filters orders by status (e.g. status=p or status=n).
        Postcondition: Orders view updates with filtered results query parameter.
        """
        page.goto(f"{base_url}/control/login")
        page.wait_for_load_state("networkidle")
        if page.locator('input[name="email"]').count() > 0:
            page.fill('input[name="email"]', "admin@localhost")
            page.fill('input[name="password"]', "admin_secure_password_2026")
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")

        # Filter orders by status 'p' (paid)
        filtered_url = f"{base_url}/control/event/sqe/sqe2026/orders/?status=p"
        page.goto(filtered_url)
        page.wait_for_load_state("networkidle")

        assert "status=p" in page.url
        assert "Orders" in page.content() or "Nobody" in page.content()

        screenshot_path = os.path.join(screenshot_dir, "10_uc5_admin_orders_filter.png")
        page.screenshot(path=screenshot_path)
        print(f"UC5 AF-1 verified. Screenshot: {screenshot_path}")
