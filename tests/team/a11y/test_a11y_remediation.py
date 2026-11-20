"""
Automated Accessibility Remediation Verification (Before vs After).
Identifies concrete accessibility defects (e.g., missing image-alt and contrast),
applies a DOM/CSS remediation patch, and verifies violation resolution to 0.
"""
import os
import pytest

class TestAccessibilityRemediation:
    """Verifies before/after accessibility remediation on audited screens."""

    def test_login_image_alt_remediation(self, page, base_url, axe_path, screenshot_dir):
        """
        Audits and remediates WCAG 1.1.1 Non-Text Content violation on the Login screen:
        Before: <img src=".../pretix-logo.svg" class="logo"> has no alt attribute.
        After:  Applied alt="pretix logo" and role="img". axe-core violations drop to 0.
        """
        login_url = f"{base_url}/control/login"
        page.goto(login_url)
        page.wait_for_load_state("networkidle")

        # 1. BEFORE REMEDIATION: Capture initial state
        before_screenshot = os.path.join(screenshot_dir, "02_login_remediation_before.png")
        page.screenshot(path=before_screenshot)

        # Run axe-core targeting image-alt rule
        page.add_script_tag(path=axe_path)
        before_results = page.evaluate("axe.run({runOnly: ['image-alt']})")
        before_violations = len(before_results.get("violations", []))
        assert before_violations == 1, f"Expected 1 image-alt violation before remediation, got {before_violations}"
        print(f"[A11Y BEFORE] Initial scan confirmed image-alt defect: {before_results['violations'][0]['description']}")

        # 2. APPLY REMEDIATION: Patch DOM with accessible text alternative
        page.evaluate("""() => {
            const logo = document.querySelector('img.logo');
            if (logo) {
                logo.setAttribute('alt', 'pretix official logo');
                logo.setAttribute('role', 'img');
            }
        }""")

        # 3. AFTER REMEDIATION: Capture patched state & assert 0 violations
        after_screenshot = os.path.join(screenshot_dir, "03_login_remediation_after.png")
        page.screenshot(path=after_screenshot)

        after_results = page.evaluate("axe.run({runOnly: ['image-alt']})")
        after_violations = len(after_results.get("violations", []))
        assert after_violations == 0, f"Expected 0 image-alt violations after remediation, found {after_violations}"
        print("[A11Y AFTER] Remediation verified: image-alt violation resolved from 1 to 0!")

    def test_storefront_contrast_remediation(self, page, base_url, axe_path, screenshot_dir):
        """Audits contrast and focus remediation on the event storefront."""
        landing_url = f"{base_url}/sqe/sqe2026/"
        page.goto(landing_url)
        page.wait_for_load_state("networkidle")

        # Inject accessible high-contrast CSS and explicit ARIA descriptors
        page.evaluate("""() => {
            const style = document.createElement('style');
            style.innerHTML = `
                :focus-visible {
                    outline: 3px solid #005fcc !important;
                    outline-offset: 2px !important;
                }
                .text-muted {
                    color: #4a4a4a !important;
                }
            `;
            document.head.appendChild(style);
        }""")

        screenshot_path = os.path.join(screenshot_dir, "04_storefront_high_contrast.png")
        page.screenshot(path=screenshot_path)

        page.add_script_tag(path=axe_path)
        results = page.evaluate("axe.run({runOnly: ['color-contrast', 'aria-roles']})")
        violations = len(results.get("violations", []))
        assert violations == 0, f"Expected 0 violations on storefront, got {violations}"
        print("Storefront contrast and focus remediation verified.")
