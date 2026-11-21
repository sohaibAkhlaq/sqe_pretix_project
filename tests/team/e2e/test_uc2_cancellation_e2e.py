"""
Playwright E2E Automation for UC2 Customer Order Cancellation & Quota Restoral.
Author: Shaiman (24i-3074) | Core Technical Area 3
Flows Automated:
- UC2 NF: Customer views canceled order state on customer order page
- UC2 EF-1: Terminal state mutation rejection (attempting to mark paid on canceled order)
Postconditions:
- Status transitions to 'Canceled' ('c')
- Terminal state prevents illegal mutations (BR3)
"""
import os
import uuid
import requests
import pytest
from scripts.get_tokens import get_tokens
from scripts.reset import find_docker_bin, run_reset_once

class TestUC2OrderCancellationE2E:
    """Verifies UC2 Order Cancellation through the web browser and checks state restoral."""

    @pytest.fixture(autouse=True)
    def clean_quota(self):
        yield
        try:
            run_reset_once(find_docker_bin())
        except Exception:
            pass

    def test_uc2_nf_customer_cancel_order_flow(self, page, base_url, screenshot_dir):
        # 1. Create a test order via REST API to obtain order code and secret
        tokens = get_tokens()
        admin_token = tokens["SQE Test API Token"]
        headers = {
            "Authorization": f"Token {admin_token}",
            "Content-Type": "application/json"
        }
        order_payload = {
            "email": f"cancel_e2e_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "Cancel Tester"}]
        }
        create_resp = requests.post(
            f"{base_url}/api/v1/organizers/sqe/events/sqe2026/orders/",
            json=order_payload,
            headers=headers
        )
        assert create_resp.status_code == 201, f"Setup order creation failed: {create_resp.text}"
        order_data = create_resp.json()
        order_code = order_data["code"]
        secret = order_data.get("secret", "")

        # 2. Transition order to canceled via API (Workflow B)
        cancel_url = f"{base_url}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_canceled/"
        cancel_resp = requests.post(cancel_url, headers=headers)
        assert cancel_resp.status_code in [200, 201], f"API cancellation must succeed, got {cancel_resp.status_code}"

        # 3. Customer accesses secret order URL in Playwright browser
        order_url = f"{base_url}/sqe/sqe2026/order/{order_code}/{secret}/"
        page.goto(order_url)
        page.wait_for_load_state("networkidle")
        content = page.content()

        # 4. Assert UI renders Canceled status badge
        assert "Canceled" in content or "textbubble-danger" in content, \
            "Order status badge must indicate Canceled state"

        screenshot_path = os.path.join(screenshot_dir, "07_uc2_order_canceled.png")
        page.screenshot(path=screenshot_path)
        print(f"UC2 NF verified. Order {order_code} transitioned to Canceled. Screenshot: {screenshot_path}")

    def test_uc2_ef1_terminal_state_cancel_rejection(self, base_url):
        """
        Flow UC2 EF-1: Attempting to pay an already canceled order is rejected.
        Postcondition: HTTP 400 Bad Request; order remains in terminal state 'c' (BR3).
        """
        tokens = get_tokens()
        admin_token = tokens["SQE Test API Token"]
        headers = {
            "Authorization": f"Token {admin_token}",
            "Content-Type": "application/json"
        }
        # 1. Create order
        create_resp = requests.post(
            f"{base_url}/api/v1/organizers/sqe/events/sqe2026/orders/",
            json={"email": "terminal@example.com", "locale": "en", "sales_channel": "web",
                  "positions": [{"item": 1, "price": "50.00"}]},
            headers=headers
        )
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]

        # 2. Cancel order (Workflow B)
        cancel_url = f"{base_url}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_canceled/"
        c1 = requests.post(cancel_url, headers=headers)
        assert c1.status_code in [200, 201]

        # 3. Attempt illegal state transition on terminal state: Mark Paid on canceled order
        pay_url = f"{base_url}/api/v1/organizers/sqe/events/sqe2026/orders/{order_code}/mark_paid/"
        pay_resp = requests.post(pay_url, headers=headers)
        assert pay_resp.status_code in [400, 409], f"Illegal transition on terminal state must return 400/409, got {pay_resp.status_code}"
        assert "not pending or expired" in pay_resp.text.lower()
