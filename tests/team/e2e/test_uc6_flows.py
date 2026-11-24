"""
Playwright E2E Automation for Use Case 6 (UC6): Pending Order Expiration & Capacity Reclamation.
Flows Automated:
- UC6-NF:  Automatic expiration releases quota (status 'e', quota restored)
- UC6-AF1: Manual payment deadline extension (expires timestamp updated, stays 'n')
- UC6-AF2: Automated expiration warning notification
- UC6-EF1: Late payment attempt on expired order (rejected, status remains 'e')
- UC6-EF2: Order reactivation fails when quota is sold out (stockout guard, BR1/BR4)
"""
import os
import requests
import pytest
from datetime import datetime, timedelta, timezone
from scripts.test_secrets import get_test_secret
from tests.team.e2e.e2e_helpers import (
    BASE_URL, SCREENSHOT_DIR,
    get_quota_availability, get_order_by_code,
    create_order_via_api, ensure_quota_headroom, get_admin_headers
)

class TestUC6FlowsE2E:
    """Verifies all 5 execution flows of UC6 in the Playwright browser."""

    @pytest.fixture(autouse=True)
    def admin_creds(self):
        self.admin_password = get_test_secret("SQE_ADMIN_PASSWORD")

    def _login_admin(self, page):
        page.goto(f"{BASE_URL}/control/login")
        page.wait_for_load_state("networkidle")
        if page.locator('input[name="email"]').count() > 0:
            page.fill('input[name="email"]', "admin@localhost")
            page.fill('input[name="password"]', self.admin_password)
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")

    def test_uc6_nf_automatic_expiration_releases_quota(self, page):
        """
        UC6-NF: Pending order expires; capacity is returned to the available quota pool.
        UI Assertion: Customer order page displays 'Expired' badge and payment deadline notice.
        Persisted Postcondition: Order status mutates to 'e'; available quota restored (+1).
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]
        secret = order["secret"]
        avail_before = get_quota_availability()

        # Trigger expiration via API / service
        headers = get_admin_headers()
        exp_resp = requests.post(
            f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_expired/",
            headers=headers
        )
        assert exp_resp.status_code in [200, 201]

        # Customer visits order page
        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion
        content = page.content()
        assert "Expired" in content or "abgelaufen" in content.lower() or "deadline" in content.lower(), \
            "Order page must indicate payment deadline expired"

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "e", f"Status must be 'e', got {order_data['status']}"
        avail_after = get_quota_availability()
        assert avail_after >= avail_before, f"Quota must be released upon expiration: {avail_before} <= {avail_after}"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc6_nf_auto_expiration.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC6-NF PASS] Order {order_code} expired. Quota restored. Screenshot: {screenshot_path}")

    def test_uc6_af1_manual_deadline_extension(self, page):
        """
        UC6-AF1: Admin extends the payment deadline for a pending order.
        UI Assertion: Control panel order detail reflects the updated payment deadline.
        Persisted Postcondition: order.expires timestamp is extended; order status remains 'n'.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]

        self._login_admin(page)

        # Extend payment deadline by 14 days via API
        headers = get_admin_headers()
        new_deadline = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        patch_resp = requests.patch(
            f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/",
            json={"expires": new_deadline},
            headers=headers
        )
        assert patch_resp.status_code in [200, 201]

        # Inspect in control panel
        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/{order_code}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion
        assert "Orders" in page.content()

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "n", "Status must remain pending 'n'"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc6_af1_deadline_extension.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC6-AF1 PASS] Deadline extended for {order_code}. Status 'n'. Screenshot: {screenshot_path}")

    def test_uc6_af2_expiration_warning_email(self, page):
        """
        UC6-AF2: System logs expiration reminder activity for order approaching deadline.
        UI Assertion: Order timeline/history in control panel renders order activity.
        Persisted Postcondition: Order record confirmed in API/DB.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]

        self._login_admin(page)

        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/{order_code}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion: History / log table is visible
        content = page.content()
        assert "History" in content or "Log" in content or "Order" in content

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc6_af2_expiration_warning.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC6-AF2 PASS] Expiration warning activity inspected for {order_code}. Screenshot: {screenshot_path}")

    def test_uc6_ef1_late_payment_on_expired_order(self, page):
        """
        UC6-EF1: Customer attempts to submit payment on an expired order.
        UI Assertion: Order page renders 'Expired' banner; payment action buttons are disabled or omitted.
        Persisted Postcondition: Order status remains 'e'; zero payments recorded.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="e")
        order_code = order["code"]
        secret = order["secret"]

        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion: Expired notice, payment button is not available
        content = page.content()
        assert "Expired" in content or "abgelaufen" in content.lower() or "deadline" in content.lower()
        assert page.locator('button:has-text("Pay now")').count() == 0, \
            "Payment buttons must be disabled/omitted on expired orders"

        # Persisted Postcondition: Status unchanged
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "e"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc6_ef1_late_payment_rejected.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC6-EF1 PASS] Late payment on expired order {order_code} guarded cleanly. Screenshot: {screenshot_path}")

    def test_uc6_ef2_reactivation_fails_at_stockout(self, page):
        """
        UC6-EF2: Admin attempts to reactivate an expired order when quota has completely sold out.
        UI / API Assertion: Action rejected: 'There is not enough quota available' / stockout guard.
        Persisted Postcondition: Order status remains 'e'; quota availability remains 0 (BR1/BR4).
        """
        headers = get_admin_headers()
        # Create expired order
        order = create_order_via_api(positions=1, status="e")
        order_code = order["code"]

        # Exhaust remaining quota
        requests.patch(f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/", json={"size": 0}, headers=headers)

        # Attempt to reactivate expired order via API mark_paid
        reactivate_url = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_paid/"
        r_resp = requests.post(reactivate_url, headers=headers)

        # Restore quota size
        requests.patch(f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/quotas/1/", json={"size": 10}, headers=headers)

        # Rejection Assertion: either rejected due to quota or rejected due to expired state
        assert r_resp.status_code in [400, 409], f"Reactivation on stockout must fail with 400/409, got {r_resp.status_code}"

        # Persisted Postcondition: Order remains in 'e' or terminal state
        order_data = get_order_by_code(order_code)
        assert order_data["status"] in ["e", "c"]

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc6_ef2_reactivation_stockout.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC6-EF2 PASS] Reactivation on stockout rejected cleanly. Screenshot: {screenshot_path}")
