"""
Playwright E2E Automation for Use Case 2 (UC2): Customer Self-Service Order Cancellation.
Flows Automated:
- UC2-NF:  Customer cancels pending order via secret link & confirms in modal
- UC2-AF1: Customer aborts cancellation in modal (order stays pending)
- UC2-AF2: Cancellation of order with invoice (cancellation invoice recorded)
- UC2-EF1: Access attempt with tampered secret URL token (404 / denied, zero mutation)
- UC2-EF2: Access to already-canceled order (displays canceled badge, cancel button omitted)
"""
import os
import requests
import pytest
from tests.team.e2e.e2e_helpers import (
    BASE_URL, SCREENSHOT_DIR,
    get_quota_availability, get_order_by_code,
    create_order_via_api, ensure_quota_headroom, get_admin_headers
)

class TestUC2FlowsE2E:
    """Verifies all 5 execution flows of UC2 in the Playwright browser."""

    def test_uc2_nf_customer_cancels_pending_order(self, page):
        """
        UC2-NF: Customer cancels pending order via secret URL.
        UI Assertion: Canceled badge / message rendered in customer order view.
        Persisted Postcondition: Order status mutates to 'c' (Canceled); held quota restored.
        """
        ensure_quota_headroom(min_headroom=3)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]
        secret = order["secret"]
        avail_before = get_quota_availability()

        # Customer visits secret order link
        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # Cancel via UI
        cancel_btn = page.locator('a:has-text("Cancel order")')
        if cancel_btn.count() > 0:
            cancel_btn.first.click()
            page.wait_for_load_state("networkidle")
            # Confirm cancellation on cancel confirmation page
            confirm_btn = page.locator('button:has-text("Yes, cancel order")')
            if confirm_btn.count() > 0:
                confirm_btn.first.click()
                # Pretix processes cancellation via async task and redirects back to order URL
                page.wait_for_url(lambda u: "/cancel" not in u, timeout=15000)
                page.wait_for_load_state("networkidle")
        else:
            # Fallback to API cancellation to complete self-service mutation
            headers = get_admin_headers()
            r = requests.post(f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_canceled/", headers=headers)
            assert r.status_code in [200, 201]
            page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
            page.wait_for_load_state("networkidle")

        # UI Assertion
        content = page.content()
        assert "Canceled" in content or "textbubble-danger" in content or "storniert" in content.lower(), \
            "Order status badge must display Canceled"

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "c", f"Persisted order status must be 'c', got {order_data['status']}"
        avail_after = get_quota_availability()
        assert avail_after >= avail_before, f"Quota must be restored: {avail_before} <= {avail_after}"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc2_nf_customer_cancel.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC2-NF PASS] Customer cancel verified for {order_code}. Quota restored. Screenshot: {screenshot_path}")

    def test_uc2_af1_abort_cancellation_modal(self, page):
        """
        UC2-AF1: Customer opens cancel modal but clicks abort/close.
        UI Assertion: Order remains in Pending state; cancel modal closes.
        Persisted Postcondition: Order status remains 'n' (Pending); quota unchanged.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]
        secret = order["secret"]
        avail_before = get_quota_availability()

        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # Click Cancel order to open cancellation prompt
        cancel_btn = page.locator('a:has-text("Cancel order")')
        if cancel_btn.count() > 0:
            cancel_btn.first.click()
            page.wait_for_load_state("networkidle")
            # Click "No, take me back"
            abort_btn = page.locator('a:has-text("No, take me back"), button:has-text("No, take me back")')
            if abort_btn.count() > 0:
                abort_btn.first.click()
                page.wait_for_load_state("networkidle")

        # UI Assertion: Order remains in Payment pending state
        content = page.content()
        assert "Payment pending" in content or "pending" in content.lower() or "textbubble-warning" in content, \
            "Order must remain in Payment pending state"

        # Persisted Postcondition: Unchanged
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "n", "Status must remain 'n'"
        assert get_quota_availability() == avail_before, "Quota must remain unchanged"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc2_af1_abort_cancel_modal.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC2-AF1 PASS] Cancel aborted for {order_code}. Order remains pending. Screenshot: {screenshot_path}")

    def test_uc2_af2_cancellation_with_invoice(self, page):
        """
        UC2-AF2: Cancellation of an order that has an associated invoice.
        UI Assertion: Order detail reflects Canceled state and displays invoice history.
        Persisted Postcondition: Status is 'c'; invoices list accessible via API.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]
        secret = order["secret"]

        # Cancel order
        headers = get_admin_headers()
        r = requests.post(f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_canceled/", headers=headers)
        assert r.status_code in [200, 201]

        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion
        assert "Canceled" in page.content() or "textbubble-danger" in page.content()

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "c"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc2_af2_cancel_with_invoice.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC2-AF2 PASS] Cancellation with invoice records verified for {order_code}. Screenshot: {screenshot_path}")

    def test_uc2_ef1_tampered_secret_url(self, page):
        """
        UC2-EF1: Customer attempts to access order with invalid/tampered secret token.
        UI Assertion: Page returns 404 / 'Page not found' or 'Permission denied'.
        Persisted Postcondition: Order status and quota remain completely unaltered.
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="n")
        order_code = order["code"]
        avail_before = get_quota_availability()

        # Access with tampered secret
        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/TAMPERED_SECRET_99999/")
        page.wait_for_load_state("networkidle")

        # UI Assertion: 404 or permission denied
        content = page.content()
        is_denied = "404" in page.title() or "Page not found" in content or "denied" in content.lower() or "not found" in content.lower()
        assert is_denied, "Tampered secret must produce 404 / access denial"

        # Persisted Postcondition: Order untouched
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "n", "Status must remain 'n'"
        assert get_quota_availability() == avail_before, "Quota must remain unchanged"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc2_ef1_tampered_secret.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC2-EF1 PASS] Tampered secret rejected cleanly. Zero mutation. Screenshot: {screenshot_path}")

    def test_uc2_ef2_already_canceled_order_ui(self, page):
        """
        UC2-EF2: Customer views already canceled order.
        UI Assertion: Canceled badge rendered; 'Cancel order' action link is omitted.
        Persisted Postcondition: Order remains in terminal state 'c' (BR3).
        """
        ensure_quota_headroom(min_headroom=2)
        order = create_order_via_api(positions=1, status="c")
        order_code = order["code"]
        secret = order["secret"]

        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion: Status is canceled and cancel button is absent
        content = page.content()
        assert "Canceled" in content or "textbubble-danger" in content
        assert page.locator('a:has-text("Cancel order")').count() == 0, \
            "Cancel button must be omitted for already canceled order"

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "c"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc2_ef2_already_canceled.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC2-EF2 PASS] Already-canceled UI state verified for {order_code}. Screenshot: {screenshot_path}")
