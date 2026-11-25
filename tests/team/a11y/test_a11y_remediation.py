"""
Automated Accessibility Remediation Verification (Before vs After).
Verifies durable server-side template remediation of WCAG 1.1.1 (image-alt)
and stylesheet contrast remediation of WCAG 1.4.3 (color-contrast).
"""
import os
import pytest

class TestAccessibilityRemediation:
    """Verifies before/after accessibility remediation on audited screens."""

    def test_login_image_alt_remediation(self, page, base_url, axe_path, screenshot_dir):
        """
        Audits and verifies durable remediation of WCAG 1.1.1 Non-Text Content on the Login screen:
        Before: <img src=".../pretix-logo.svg" class="logo"> lacked an alt attribute (1 critical axe-core violation).
        Durable Fix: Applied to /pretix/src/pretix/control/templates/pretixcontrol/auth/base.html (alt="pretix official logo", role="img").
        After: Served page naturally contains the alt attribute, resolving violations from 1 to 0.
        """
        login_url = f"{base_url}/control/login"
        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        # 1. VERIFY DURABLE SERVER-SIDE REMEDIATION (lang, main landmark, h1, image alt)
        html_lang = page.locator("html").get_attribute("lang")
        assert html_lang == "en", f"Expected durable html lang='en', got: {html_lang}"
        assert page.locator("main#main-content").count() == 1, "Expected durable <main> landmark"
        assert page.locator("h1").count() >= 1, "Expected durable <h1> heading"

        logo = page.locator("img.logo")
        alt_attr = logo.get_attribute("alt")
        assert alt_attr == "pretix official logo", f"Expected durable server-rendered alt attribute, got: {alt_attr}"

        # 2. RUN AXE-CORE AGAINST DURABLE SCREEN (AFTER STATE: 0 VIOLATIONS)
        after_screenshot = os.path.join(screenshot_dir, "03_login_remediation_after.png")
        page.screenshot(path=after_screenshot)

        page.add_script_tag(path=axe_path)
        after_results = page.evaluate("axe.run()")
        after_violations = len(after_results.get("violations", []))
        assert after_violations == 0, f"Expected 0 total violations on durable screen, found {after_results.get('violations')}"
        print(f"[A11Y AFTER] Durable fix verified: 0 total axe-core violations on server-rendered page (lang='{html_lang}', alt='{alt_attr}')")

        # 3. VERIFY BEFORE STATE (DEMONSTRATE DETECTION WHEN DURABLE ATTRIBUTES REMOVED)
        page.evaluate("""() => {
            document.documentElement.removeAttribute('lang');
            const l = document.querySelector('img.logo');
            if (l) l.removeAttribute('alt');
        }""")
        before_screenshot = os.path.join(screenshot_dir, "02_login_remediation_before.png")
        page.screenshot(path=before_screenshot)

        before_results = page.evaluate("axe.run({runOnly: ['image-alt', 'html-has-lang']})")
        before_violations = len(before_results.get("violations", []))
        assert before_violations >= 2, f"Expected >=2 violations when alt and lang are removed, got {before_violations}"
        print(f"[A11Y BEFORE] Baseline violations confirmed when attributes absent: {[v['id'] for v in before_results['violations']]}")

    def test_storefront_contrast_remediation(self, page, base_url, axe_path, screenshot_dir):
        """Verifies durable server-rendered contrast & focus-visible CSS on storefront (no JS style injection)."""
        landing_url = f"{base_url}/sqe/sqe2026/"
        page.goto(landing_url)
        page.wait_for_load_state("networkidle")

        # Assert server HTML natively includes our durable contrast/focus patch
        server_style = page.locator("style#sqe-a11y-contrast-patch")
        assert server_style.count() == 1, "Expected durable server-rendered #sqe-a11y-contrast-patch in <head>"
        style_text = server_style.inner_text()
        assert "#4a4a4a" in style_text and ":focus-visible" in style_text

        screenshot_path = os.path.join(screenshot_dir, "04_storefront_high_contrast.png")
        page.screenshot(path=screenshot_path)

        page.add_script_tag(path=axe_path)
        results = page.evaluate("axe.run({runOnly: ['color-contrast', 'aria-roles']})")
        violations = len(results.get("violations", []))
        assert violations == 0, f"Expected 0 violations on storefront, got {violations}"
        print("[A11Y STOREFRONT] Durable server contrast and focus CSS verified (0 violations).")
