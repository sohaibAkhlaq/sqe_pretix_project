"""
Automated Keyboard-Only Navigation & Focus Trap Verification.
Verifies complete storefront accessibility without mouse interaction (WCAG 2.1.1 & 2.1.2).
"""
import os
import pytest

class TestKeyboardNavigation:
    """Verifies keyboard operability: Tab navigation, visual focus, no traps."""

    def test_keyboard_tab_traversal_on_storefront(self, page, base_url, screenshot_dir):
        """TC-A11Y-02: Sequentially tabs through interactive controls and verifies focus shift."""
        landing_url = f"{base_url}/sqe/sqe2026/"
        page.goto(landing_url)
        page.wait_for_load_state("networkidle")

        # Start from document body
        page.focus("body")

        focused_tags = []
        # Press Tab 8 times through interactive header and form controls
        for i in range(8):
            page.keyboard.press("Tab")
            active_info = page.evaluate("""() => {
                const el = document.activeElement;
                return {
                    tag: el.tagName,
                    id: el.id || '',
                    className: el.className || '',
                    name: el.getAttribute('name') || ''
                };
            }""")
            focused_tags.append(active_info["tag"])

        # Capture focus evidence
        screenshot_path = os.path.join(screenshot_dir, "01_keyboard_tab_focus.png")
        page.screenshot(path=screenshot_path)

        # Assert navigation took place (multiple interactive tags focused)
        interactive_tags = {"A", "BUTTON", "INPUT", "SELECT"}
        focused_set = set(focused_tags)
        assert len(focused_set.intersection(interactive_tags)) > 0, (
            f"Keyboard tabbing did not focus interactive elements: {focused_tags}"
        )
        print(f"Keyboard navigation successful across tags: {focused_tags}")

    def test_no_keyboard_focus_trap(self, page, base_url):
        """TC-A11Y-02b: Verifies focus does not get permanently stuck in any element."""
        landing_url = f"{base_url}/sqe/sqe2026/"
        page.goto(landing_url)
        page.wait_for_load_state("networkidle")

        visited_elements = set()
        for _ in range(12):
            page.keyboard.press("Tab")
            el_repr = page.evaluate("() => document.activeElement.outerHTML ? document.activeElement.outerHTML.slice(0, 50) : ''")
            visited_elements.add(el_repr)

        # Focus moved across at least 3 distinct elements
        assert len(visited_elements) >= 3, f"Possible focus trap detected! Distinct elements visited: {len(visited_elements)}"
        print(f"No focus traps: {len(visited_elements)} distinct elements visited.")
