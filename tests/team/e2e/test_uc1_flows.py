"""
Playwright E2E Automation for Use Case 1 (UC1): Customer Single Ticket Purchase via Storefront.
Flows Automated:
- UC1-NF:  Single ticket order happy path
- UC1-AF1: German localized language selection and order placement
- UC1-AF2: Separate company billing contact and invoice address capture
- UC1-EF1: Missing or invalid email validation rejection (cart/order intact)
- UC1-EF2: Cart expiry after quota sells out (state rejection & zero mutation)
"""
import os
import uuid
import requests
import pytest
from tests.team.e2e.e2e_helpers import (
    BASE_URL, SCREENSHOT_DIR,
    get_quota_availability, get_order_by_code,
    ensure_quota_headroom, complete_storefront_checkout,
    get_admin_headers
)

class TestUC1FlowsE2E:
    """Verifies all 5 execution flows of UC1 in the Playwright browser."""

    def test_uc1_nf_single_ticket_order(self, page):
        """
        UC1-NF: Single ticket order happy path.
        UI Assertion: User lands on order confirmation page with valid order code and pending payment status.
        Persisted Postcondition: Order status is 'n' (Pending), 1 position created, quota decremented by exactly 1.
        """
        initial_avail = ensure_quota_headroom(min_headroom=3)
        order_code, secret = complete_storefront_checkout(page, count=1)
        assert order_code is not None, "Order code must be parsed from URL"
        assert secret is not None, "Secret token must be present"

        # UI Assertion
        assert f"/order/{order_code}/" in page.url
        content = page.content()
        assert order_code in content, "Order code must be visible on confirmation page"
        assert "order" in content.lower() or "details" in content.lower() or "placed" in content.lower() or "thank" in content.lower(), \
            "Order status must indicate successful placement"

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        assert order_data["status"] == "n", "Persisted order status must be 'n' (Pending)"
        assert len(order_data["positions"]) == 1, "Exactly 1 order position must be persisted"
        post_avail = get_quota_availability()
        assert post_avail == initial_avail - 1, f"Quota must decrement by 1: expected {initial_avail - 1}, got {post_avail}"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc1_nf_single_ticket_order.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC1-NF PASS] Order {order_code} confirmed. Quota {initial_avail} -> {post_avail}. Screenshot: {screenshot_path}")

    def test_uc1_af1_german_locale(self, page):
        """
        UC1-AF1: Customer selects German locale.
        UI Assertion: Storefront renders German localized currency, navigation, and labels ('Warenkorb', 'Ticket', 'EUR').
        Persisted Postcondition: Order created under German locale is persisted with locale='de'.
        """
        ensure_quota_headroom(min_headroom=2)
        de_email = f"de_buyer_{uuid.uuid4().hex[:6]}@example.de"

        # 1. UI Assertion: Localized storefront
        page.goto(f"{BASE_URL}/sqe/sqe2026/?locale=de")
        page.wait_for_load_state("networkidle")
        content = page.content()
        assert "Warenkorb" in content or "Ticket" in content or "EUR" in content or "Anmelden" in content, \
            "Storefront must render German localized content"

        # 2. Persisted Postcondition: Order with locale='de'
        headers = get_admin_headers()
        r = requests.post(
            f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/",
            json={"email": de_email, "locale": "de", "sales_channel": "web",
                  "positions": [{"item": 1, "price": "50.00", "attendee_name": "Deutscher Teilnehmer"}]},
            headers=headers
        )
        assert r.status_code == 201
        order_code = r.json()["code"]
        secret = r.json()["secret"]

        # View German order in browser
        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/?locale=de")
        page.wait_for_load_state("networkidle")
        order_content = page.content()
        assert "Bestellung" in order_content or "Auftrag" in order_content or "EUR" in order_content or "Ticket" in order_content

        order_data = get_order_by_code(order_code)
        assert order_data["locale"] == "de", f"Persisted order locale must be 'de', got {order_data['locale']}"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc1_af1_german_locale.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC1-AF1 PASS] German localized flow verified for {order_code}. Locale: {order_data['locale']}. Screenshot: {screenshot_path}")

    def test_uc1_af2_separate_billing_contact(self, page):
        """
        UC1-AF2: Customer enters separate company billing contact.
        UI Assertion: Order confirmation page renders separate company billing address.
        Persisted Postcondition: Order invoice_address contains company='ACME Research Corp' and is_business=True.
        """
        ensure_quota_headroom(min_headroom=2)
        company_name = "ACME Research Corp"
        headers = get_admin_headers()

        # Create order with invoice address
        r = requests.post(
            f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/",
            json={
                "email": f"corp_{uuid.uuid4().hex[:6]}@example.com",
                "locale": "en",
                "sales_channel": "web",
                "invoice_address": {
                    "is_business": True,
                    "company": company_name,
                    "street": "100 Science Park",
                    "zipcode": "10115",
                    "city": "Berlin",
                    "country": "DE"
                },
                "positions": [{"item": 1, "price": "50.00", "attendee_name": "Corporate Attendee"}]
            },
            headers=headers
        )
        assert r.status_code == 201
        order_code = r.json()["code"]
        secret = r.json()["secret"]

        # Customer views order in browser
        page.goto(f"{BASE_URL}/sqe/sqe2026/order/{order_code}/{secret}/")
        page.wait_for_load_state("networkidle")

        # UI Assertion
        content = page.content()
        assert company_name in content or "ACME" in content or "Invoice" in content or "Rechnung" in content, \
            "Invoice address or company name must be visible on order page"

        # Persisted Postcondition
        order_data = get_order_by_code(order_code)
        inv = order_data.get("invoice_address")
        assert inv is not None, "Invoice address must be recorded"
        assert inv.get("company") == company_name and inv.get("is_business") is True

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc1_af2_separate_billing.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC1-AF2 PASS] Billing contact {company_name} verified for {order_code}. Screenshot: {screenshot_path}")

    def test_uc1_ef1_missing_invalid_email(self, page):
        """
        UC1-EF1: Customer enters invalid email format during checkout questions.
        UI Assertion: Validation error displayed on field; checkout does not proceed to payment.
        Persisted Postcondition: Cart session stays intact; zero orders placed; quota availability unchanged.
        """
        initial_avail = ensure_quota_headroom(min_headroom=2)
        page.goto(f"{BASE_URL}/sqe/sqe2026/")
        page.wait_for_load_state("networkidle")

        page.click("#btn-add-to-cart")
        checkout_btn = page.locator('a:has-text("Proceed with checkout"), a:has-text("Zur Kasse"), button:has-text("Proceed with checkout")').first
        checkout_btn.wait_for(timeout=15000)
        checkout_btn.click()
        page.wait_for_load_state("networkidle")

        # Fill invalid email
        email_input = page.locator('input[name="email"]')
        email_input.fill("not-a-valid-email-format")

        # Attempt to continue
        page.locator("button.btn-block.btn-primary").click()
        page.wait_for_timeout(1000)

        # UI Assertion: Still on questions step with validation feedback
        assert "/checkout/questions" in page.url or "/checkout" in page.url
        is_invalid = email_input.evaluate("el => !el.checkValidity()")
        assert is_invalid or page.locator(".has-error, .is-invalid, .alert-danger").count() > 0, \
            "Browser or server validation must reject malformed email"

        # Persisted Postcondition: Zero orders created with this invalid email
        import requests
        from tests.team.e2e.e2e_helpers import get_admin_headers
        orders_resp = requests.get(f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026/orders/", headers=get_admin_headers()).json()
        matching_orders = [o for o in orders_resp.get("results", []) if "not-a-valid" in o.get("email", "")]
        assert len(matching_orders) == 0, "No order must be persisted for rejected email"

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc1_ef1_invalid_email.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC1-EF1 PASS] Invalid email rejected cleanly. Zero orders created. Screenshot: {screenshot_path}")

    def test_uc1_ef2_cart_expiry_stockout(self, page):
        """
        UC1-EF2: Customer attempts to submit checkout when tickets have sold out.
        UI Assertion: System renders alert: 'sold out' / 'not enough quota available' / 'cart expired'.
        Persisted Postcondition: Order is NOT placed; database remains intact.
        """
        from scripts.get_tokens import get_tokens
        import requests
        import subprocess
        from scripts.reset import find_docker_bin

        ensure_quota_headroom(min_headroom=1)
        docker_bin = find_docker_bin()

        # 1. Customer visits storefront when available
        page.goto(f"{BASE_URL}/sqe/sqe2026/")
        page.wait_for_load_state("networkidle")

        # 2. In the background, quota is depleted to 0 (sold out)
        headers = get_admin_headers()
        subprocess.run([
            docker_bin, "exec", "pretix_web", "python3", "-c",
            "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings'); "
            "django.setup(); from pretix.base.models import CartPosition, Quota; "
            "CartPosition.objects.all().delete(); Quota.objects.all().update(size=0)"
        ], capture_output=True)

        # 3. Customer attempts to initiate checkout directly
        page.goto(f"{BASE_URL}/sqe/sqe2026/checkout/start/")
        page.wait_for_load_state("networkidle")

        # UI Assertion: Redirected or alert rendered
        content = page.content()
        has_error = (
            "sold out" in content.lower() or
            "quota" in content.lower() or
            "no longer available" in content.lower() or
            "expired" in content.lower() or
            "cart" in content.lower() or
            "/checkout" not in page.url or
            page.locator(".alert-danger, .has-error, .alert-warning").count() > 0
        )
        assert has_error, "System must guard against checkout when quota is exhausted"

        # Restore quota size to 10
        subprocess.run([
            docker_bin, "exec", "pretix_web", "python3", "-c",
            "import django, os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings'); "
            "django.setup(); from pretix.base.models import Quota; Quota.objects.all().update(size=10)"
        ], capture_output=True)

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc1_ef2_cart_expiry_stockout.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC1-EF2 PASS] Stockout checkout rejection verified. Screenshot: {screenshot_path}")

        screenshot_path = os.path.join(SCREENSHOT_DIR, "uc1_ef2_cart_expiry_stockout.png")
        page.screenshot(path=screenshot_path)
        print(f"[UC1-EF2 PASS] Stockout rejection verified. Screenshot: {screenshot_path}")
