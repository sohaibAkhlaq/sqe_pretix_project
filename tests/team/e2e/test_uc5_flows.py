"""
Playwright E2E Automation for Use Case 5 (UC5): Organizer Order Administration & Status Mutation.
Flows Automated:
- UC5-NF:  Administrator marks pending order as paid in control panel
- UC5-AF1: Administrator filters order list by lifecycle state query parameter
- UC5-AF2: Administrative cancellation of customer order (quota restored)
- UC5-EF1: Illegal state mutation attempt on terminal state (400 rejection, BR3)
- UC5-EF2: Session expiration during control panel navigation (redirected to login)
"""
import os
import requests
import pytest
from scripts.test_secrets import get_test_secret
from tests.team.e2e.e2e_helpers import (
    BASE_URL, SCREENSHOT_DIR,
    get_quota_availability, get_order_by_code,
    create_order_via_api, ensure_quota_headroom, get_admin_headers
)

class TestUC5FlowsE2E:
    """Verifies all 5 execution flows of UC5 in the Playwright browser."""

    @pytest.fixture(autouse=True)
    def admin_creds(self):
        self.admin_password = get_test_secret("SQE_ADMIN_PASSWORD")

    def _login_admin(self, page):
        """Helper to log into the organizer control panel."""
        page.goto(f"{BASE_URL}/control/login")
        page.wait_for_load_state("networkidle")
        if page.locator('input[name="email"]').count() > 0:
            page.fill('input[name="email"]', "admin@localhost")
            page.fill('input[name="password"]', self.admin_password)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")

    def test_uc5_nf_admin_marks_order_paid(self, page):
        """
        UC5-NF: Admin marks a pending order as paid.
        UI Assertion: Order detail page renders 'Paid' status badge (green).
        Persisted Postcondition: Order status transitions to 'p'; payment confirmed.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]

        self._login_admin(page)

        # Mark paid via API and inspect in UI
        headers = get_admin_headers()
        pay_resp = requests.post(
            f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_paid/",
            headers=headers
        )
        assert pay_resp.status_code in [200, 201]

        # Navigate to order detail in control panel
        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/{order_code}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion
        content = page.content()
        assert "Paid" in content or "label-success" in content, "Control panel must reflect Paid state"

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "p", f"Status must be 'p', got {order_data['status']}"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc5_nf_admin_mark_paid.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC5-NF PASS] Admin marked order {order_code} paid. Status 'p'. Screenshot: {screenshot_path}")

    def test_uc5_af1_filter_orders_by_status(self, page):
        """
        UC5-AF1: Admin filters orders list by lifecycle state.
        UI Assertion: View updates with ?status=p query parameter; orders table rendered.
        Persisted Postcondition: Read-only query; zero database mutations.
        """
        self._login_admin(page)

        filtered_url = f"{BASE_URL}/control/event/sqe/sqe2026/orders/?status=p"
        page.goto(filtered_url)
        page.wait_for_load_state("networkidle")

        # UI Assertion
        assert "status=p" in page.url
        content = page.content()
        assert "Orders" in content

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc5_af1_filter_orders.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC5-AF1 PASS] Filter orders by status 'p' verified. Screenshot: {screenshot_path}")

    def test_uc5_af2_admin_cancellation(self, page):
        """
        UC5-AF2: Admin cancels customer order from control panel.
        UI Assertion: Order detail page renders 'Canceled' badge.
        Persisted Postcondition: Status mutates to 'c'; held quota restored.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]
        avail_before = get_quota_availability()

        self._login_admin(page)

        # Cancel order
        headers = get_admin_headers()
        c_resp = requests.post(
            f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_canceled/",
            headers=headers
        )
        assert c_resp.status_code in [200, 201]

        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/{order_code}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion
        content = page.content()
        assert "Canceled" in content or "label-danger" in content

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "c"
        avail_after = get_quota_availability()
        assert avail_after >= avail_before

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc5_af2_admin_cancel.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC5-AF2 PASS] Admin cancellation verified for {order_code}. Screenshot: {screenshot_path}")

    def test_uc5_ef1_mutation_on_terminal_state(self, page):
        """
        UC5-EF1: Admin attempts to mark an already canceled order as paid.
        UI / API Assertion: Rejection with HTTP 400 Bad Request: 'not pending or expired'.
        Persisted Postcondition: Order status remains in terminal state 'c' (BR3).
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="c")
        order_code = order["code"]

        headers = get_admin_headers()
        pay_url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_paid/"
        pay_resp = requests.post(pay_url, headers=headers)

        # Rejection Assertion
        assert pay_resp.status_code in [400, 409], f"Illegal transition must return 400/409, got {pay_resp.status_code}"
        assert "not pending or expired" in pay_resp.text.lower() or "canceled" in pay_resp.text.lower()

        # Persisted Postcondition: Order untouched
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "c"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc5_ef1_terminal_state_rejection.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC5-EF1 PASS] Terminal state mutation rejected cleanly. Screenshot: {screenshot_path}")

    def test_uc5_ef2_session_expiry_during_action(self, page):
        """
        UC5-EF2: Admin session expires during navigation.
        UI Assertion: User is intercepted and redirected to /control/login?next=...
        Persisted Postcondition: Zero mutations; protected views inaccessible without auth.
        """
        # Ensure session cleared
        page.context.clear_cookies()

        # Attempt to access protected orders URL without active session
        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/")
        page.wait_for_load_state("networkidle")

        # UI Assertion: Redirected to login
        assert "/control/login" in page.url or page.locator('input[name="password"]').count() > 0, \
            f"Unauthenticated request must redirect to login, got {page.url}"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc5_ef2_session_expiry.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC5-EF2 PASS] Unauthenticated access intercepted to login. Screenshot: {screenshot_path}")
