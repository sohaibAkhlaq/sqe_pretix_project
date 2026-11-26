"""
Playwright Usability & Accessibility Workflow Tests.
Implements:
1. Workflow A Test: Opens storefront, attempts invalid checkout (business rule rejection),
   verifies error message explains what to correct, corrects value, navigates via genuine
   keyboard Tab order through required fields to the submit button, submits via Enter,
   and completes checkout through to the final order confirmation page (/order/{code}/{secret}/).
2. Workflow B Test: Opens organizer control panel, authenticates as admin, navigates to
   Orders ledger and order detail view, executes Control Panel order cancellation, and
   asserts the Canceled confirmation state.
3. Generates structured Playwright usability report -> reports/a11y/playwright_usability_report.json.
"""
import json
import time
from pathlib import Path

from tests.team.e2e.e2e_helpers import create_order_via_api, ensure_quota_headroom, get_order_by_code

BASE_URL = "http://localhost:8345"
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "a11y"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


class TestUsabilityWorkflows:
    """Automated browser tests verifying usability, validation recovery, and keyboard navigation."""

    def test_workflow_a_storefront_rejection_recovery_and_keyboard_nav(self, page):
        """
        Workflow A (Ticket Purchase):
        - Open task screen (/sqe/sqe2026/).
        - Attempt checkout with invalid email violating validation rule.
        - Verify validation error explains what to correct.
        - Correct value and traverse form strictly via Tab order to submit button, pressing Enter.
        - Complete payment & binding order confirmation, asserting final /order/{code}/{secret}/ screen.
        """
        ensure_quota_headroom(min_headroom=2)
        results = {}

        # 1. Open task screen
        page.goto(f"{BASE_URL}/sqe/sqe2026/")
        page.wait_for_load_state("networkidle")
        assert "SQE International Conference 2026" in page.title()

        # 2. Submit value rejected by domain business rule (BR1: Q = 11 > Quota 10)
        page.fill("input#item_1", "11")
        page.click("#btn-add-to-cart")
        alert_loc = page.locator(".alert-danger, .alert").first
        alert_loc.wait_for(timeout=15000)
        br_error = alert_loc.inner_text().strip()
        print(f"[REJECTION] Business rule validation error: {br_error}")
        assert any(k in br_error.lower() for k in ("more than 10", "not enough", "quota", "available")), (
            f"Business-rule error does not explain what to correct: {br_error}"
        )
        page.screenshot(path=str(SCREENSHOTS_DIR / "workflow_a_01_validation_rejected.png"))

        # 3. Correct value to Q = 1 and proceed to checkout
        page.fill("input#item_1", "1")
        page.click("#btn-add-to-cart")
        page.wait_for_selector("text=Proceed with checkout", timeout=15000)
        page.click("text=Proceed with checkout")
        page.wait_for_load_state("networkidle")

        # 4. Fill required email via keyboard and traverse strictly via Tab to submit button
        email_field = page.locator("input#id_email")
        email_field.focus()
        valid_email = f"usability_buyer_{int(time.time())}@sqe.local"
        page.keyboard.type(valid_email)

        validation_after = email_field.evaluate("el => el.validationMessage")
        assert validation_after == "", "Validation error present on valid email!"

        tab_sequence = ["input#id_email"]
        reached_submit = False
        for _ in range(25):
            page.keyboard.press("Tab")
            active = page.evaluate("""() => {
                const el = document.activeElement;
                return {
                    tag: el ? el.tagName : '',
                    id: el ? (el.id || '') : '',
                    name: el ? (el.getAttribute('name') || '') : '',
                    type: el ? (el.getAttribute('type') || '') : '',
                    text: el ? (el.innerText || '').trim() : ''
                };
            }""")
            label = f"{active['tag']}#{active['id'] or active['name'] or active['text']}"
            tab_sequence.append(label)
            if active["tag"] == "BUTTON" and "Continue" in active["text"]:
                reached_submit = True
                break

        assert reached_submit, f"Genuine Tab traversal did not reach Continue submit button: {tab_sequence}"
        print(f"[KEYBOARD NAV] Ordered Tab sequence to submit: {tab_sequence}")

        # Submit form strictly via keyboard Enter
        page.keyboard.press("Enter")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)

        # 4. Complete Payment & Confirm steps to reach final order confirmation
        if "payment" in page.url:
            radios = page.locator('input[name="payment"]')
            if radios.count() > 0:
                radios.first.check(force=True)
            page.locator("button.btn-block.btn-primary").click()
            page.wait_for_load_state("networkidle")

        if "confirm" in page.url:
            bind_btn = page.locator('button:has-text("Place binding order")').first
            if bind_btn.count() > 0 and bind_btn.is_visible():
                bind_btn.click()
            else:
                page.locator("button.btn-block.btn-primary").click()
            page.wait_for_url(lambda u: "/order/" in u, timeout=15000)
            page.wait_for_load_state("networkidle")

        assert "/order/" in page.url, f"Expected final order confirmation URL, got {page.url}"
        parts = [p for p in page.url.split("/") if p]
        order_idx = parts.index("order")
        order_code = parts[order_idx + 1]
        assert order_code in page.content(), f"Order confirmation page missing order code {order_code}"

        page.screenshot(path=str(SCREENSHOTS_DIR / "workflow_a_02_checkout_progressed.png"))
        print(f"[WORKFLOW A SUCCESS] Final order confirmation reached for {order_code} at: {page.url}")

        results["workflow_a"] = {
            "task": "Storefront Ticket Purchase with BR1 Rejection (Q=11>10), Keyboard Tab Order & Final Confirmation",
            "business_rule_violated": "BR1: Over-quota quantity Q=11 > max 10",
            "validation_message_observed": br_error,
            "corrected_value_submitted": f"quantity=1, email={valid_email}",
            "keyboard_operable": True,
            "keyboard_tab_sequence": tab_sequence,
            "order_code_confirmed": order_code,
            "confirmation_displayed": True,
            "final_url": page.url,
            "status": "PASSED",
        }

        report_path = REPORTS_DIR / "playwright_usability_report.json"
        existing = {}
        if report_path.exists():
            existing = json.loads(report_path.read_text(encoding="utf-8"))
        existing.update(results)
        report_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    def test_workflow_b_control_panel_order_management(self, page, admin_password):
        """
        Workflow B (Order Management & Cancellation in Control Panel):
        - Seed a fresh pending order via API helper.
        - Log into Control Panel (/control/login) as admin@localhost.
        - Open Orders Ledger (/control/event/sqe/sqe2026/orders/), navigate to the order,
          execute Cancel Order in the UI, and assert the Canceled confirmation badge.
        """
        ensure_quota_headroom(min_headroom=2)
        seeded_order = create_order_via_api(positions=1, status="n")
        order_code = seeded_order["code"]

        # 1. Authenticate in Control Panel
        page.goto(f"{BASE_URL}/control/login")
        page.wait_for_load_state("networkidle")
        page.fill('input[name="email"]', "admin@localhost")
        page.fill('input[name="password"]', admin_password)
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

        # 2. Verify order appears in Orders Ledger
        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/")
        page.wait_for_load_state("networkidle")
        assert "Orders" in page.title() or "Orders" in page.content()
        assert order_code in page.content(), f"Order {order_code} not visible in Control Panel Orders ledger"

        # 3. Open Order Detail and complete Cancel Order transition in Control Panel UI
        page.goto(f"{BASE_URL}/control/event/sqe/sqe2026/orders/{order_code}/")
        page.wait_for_load_state("networkidle")
        cancel_link = page.locator(f'a[href*="/orders/{order_code}/transition?status=c"]').first
        cancel_link.click()
        page.wait_for_load_state("networkidle")

        confirm_btn = page.locator('main button[type="submit"], .btn-danger[type="submit"], button:has-text("Cancel order"), button:has-text("Yes")').first
        confirm_btn.click()
        page.wait_for_load_state("networkidle")

        detail_content = page.content()
        assert "Canceled" in detail_content or "canceled" in detail_content.lower(), (
            f"Canceled confirmation not displayed for {order_code}"
        )
        persisted = get_order_by_code(order_code)
        assert persisted["status"] == "c", f"Expected persisted status 'c', got {persisted['status']}"

        page.screenshot(path=str(SCREENSHOTS_DIR / "workflow_b_01_orders_ledger_confirmed.png"))
        print(f"[WORKFLOW B SUCCESS] Order {order_code} canceled & confirmed in Control Panel at: {page.url}")

        report_path = REPORTS_DIR / "playwright_usability_report.json"
        data = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        data["workflow_b"] = {
            "task": "Control Panel Order Management & Cancellation",
            "auth_user": "admin@localhost",
            "order_code_canceled": order_code,
            "route_verified": f"/control/event/sqe/sqe2026/orders/{order_code}/",
            "confirmation_displayed": True,
            "status": "PASSED",
        }
        report_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
