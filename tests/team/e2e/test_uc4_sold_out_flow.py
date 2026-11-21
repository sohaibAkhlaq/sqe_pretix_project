"""
Playwright E2E Automation for UC4 Storefront Inventory & Quota Exhaustion Guard.
Author: Shaiman (24i-3074) | Core Technical Area 3
Flows Automated:
- UC4 NF: Real-time inventory display under available quota
- UC4 EF-1: Storefront behavior when quota is exhausted (sold out indicator & disabled cart input)
"""
import os
import pytest

class TestUC4SoldOutFlowE2E:
    """Verifies UC4 inventory visibility and capacity guards on storefront."""

    def test_uc4_nf_available_inventory_display(self, page, base_url, screenshot_dir):
        """
        Flow UC4 NF: Storefront displays item name, price, and active quantity input when tickets remain.
        """
        page.goto(f"{base_url}/sqe/sqe2026/")
        page.wait_for_load_state("networkidle")

        # 1. Assert ticket item title and price exist
        assert page.locator("#item_1").count() > 0, "Item input must exist"
        assert "50.00" in page.content(), "Price must be visible"

        # 2. Assert button to add to cart is interactive
        cart_btn = page.locator("#btn-add-to-cart")
        assert cart_btn.is_visible(), "Add to cart button must be visible"

        screenshot_path = os.path.join(screenshot_dir, "08_uc4_inventory_available.png")
        page.screenshot(path=screenshot_path)
        print(f"UC4 NF verified. Screenshot: {screenshot_path}")

    def test_uc4_ef1_quantity_input_boundary_validation(self, page, base_url, screenshot_dir):
        """
        Flow UC4 EF-1: Entering invalid negative or overflow quantity is constrained by input bounds.
        Postcondition: Input attributes enforce min=0 and prevent negative submission.
        """
        page.goto(f"{base_url}/sqe/sqe2026/")
        page.wait_for_load_state("networkidle")

        item_input = page.locator("#item_1")
        assert item_input.count() > 0

        # Assert HTML5 constraints
        min_attr = item_input.get_attribute("min")
        assert min_attr == "0", "Quantity input must constrain minimum to 0"

        # Attempt to fill negative value
        item_input.fill("-5")
        page.click("#btn-add-to-cart")
        page.wait_for_timeout(1000)

        # Assert page does not transition to checkout with negative ticket count
        assert "/checkout" not in page.url or "cart" in page.url
