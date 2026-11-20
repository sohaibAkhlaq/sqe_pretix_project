"""
Playwright E2E Automation for Storefront Inventory & Quota UI Controls (UC4).
Verifies that item quantity limits, pricing display, and cart buttons conform to BR1.
"""
import os
import pytest

class TestStorefrontInventoryE2E:
    """Verifies UC4 inventory visibility and capacity guards on storefront."""

    def test_storefront_item_and_pricing_elements(self, page, base_url, screenshot_dir):
        landing_url = f"{base_url}/sqe/sqe2026/"
        page.goto(landing_url)
        page.wait_for_load_state("networkidle")

        # 1. Assert Conference details
        content = page.content()
        assert "Conference Admission Ticket" in content
        assert "50.00" in content

        # 2. Assert Quantity input and bounds
        item_input = page.locator("#item_1")
        assert item_input.count() > 0
        min_val = item_input.get_attribute("min")
        assert min_val == "0"

        # 3. Assert Add to Cart button is present
        add_btn = page.locator("#btn-add-to-cart")
        assert add_btn.count() > 0
        assert add_btn.is_visible()

        # Capture Screenshot
        screenshot_path = os.path.join(screenshot_dir, "03_storefront_inventory.png")
        page.screenshot(path=screenshot_path)
        print(f"Storefront inventory verified. Screenshot: {screenshot_path}")
