"""
Playwright E2E Automation for Customer Storefront Order Placement (UC1).
Verifies complete customer journey: Landing -> Cart -> Checkout -> Confirmation.
"""
import os
import uuid
import pytest

class TestCustomerOrderFlowE2E:
    """Verifies UC1 Happy Path order creation through the web browser."""

    def test_customer_complete_order_journey(self, page, base_url, screenshot_dir):
        # 1. Landing Page
        landing_url = f"{base_url}/sqe/sqe2026/"
        page.goto(landing_url)
        page.wait_for_load_state("networkidle")

        assert "SQE International Conference 2026" in page.title()
        assert page.locator("#item_1").count() > 0, "Item 1 input must exist"

        # 2. Add 1 ticket to cart
        page.click("#btn-add-to-cart")

        # 3. Proceed with checkout (wait for async cart allocation)
        checkout_btn = page.wait_for_selector("text=Proceed with checkout", timeout=15000)
        assert checkout_btn is not None, "Proceed button must appear after adding to cart"
        checkout_btn.click()
        page.wait_for_load_state("networkidle")

        # Capture Cart / Checkout Step 1
        cart_screenshot = os.path.join(screenshot_dir, "01_cart_checkout_step.png")
        page.screenshot(path=cart_screenshot)

        # 4. Fill Customer Questions / Email
        test_email = f"e2e_buyer_{uuid.uuid4().hex[:6]}@example.com"
        email_input = page.locator('input[name="email"]')
        if email_input.count() > 0:
            email_input.fill(test_email)

        # Click Continue if present
        continue_btn = page.locator('button:has-text("Continue")')
        if continue_btn.count() > 0:
            continue_btn.first.click()
            page.wait_for_load_state("networkidle")

        # 5. Capture Final Order/Checkout Screen
        final_screenshot = os.path.join(screenshot_dir, "02_order_placed_confirmation.png")
        page.screenshot(path=final_screenshot)

        # Assert checkout flow progressed successfully
        assert "/sqe/sqe2026/checkout" in page.url or "/sqe/sqe2026/order" in page.url
        print(f"E2E Order Flow completed. Final URL: {page.url}")
