"""
Automated axe-core Accessibility Audit against WCAG 2.1 AA Standards.
Evaluates storefront and administrative login interfaces.
"""
import os
import json
import pytest

class TestAxeAccessibility:
    """Automated WCAG 2.1 AA accessibility compliance testing."""

    def test_storefront_accessibility(self, page, base_url, axe_path, reports_dir):
        """TC-A11Y-01: Storefront landing page accessibility audit."""
        url = f"{base_url}/sqe/sqe2026/"
        page.goto(url)
        page.wait_for_load_state("networkidle")

        # Inject axe-core
        page.add_script_tag(path=axe_path)
        results = page.evaluate("axe.run()")

        violations = results.get("violations", [])
        passes = results.get("passes", [])

        # Save JSON audit report
        report_file = os.path.join(reports_dir, "axe_storefront_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "url": url,
                "wcag_standard": "WCAG 2.1 AA",
                "violations_count": len(violations),
                "passes_count": len(passes),
                "violations": violations
            }, f, indent=2)

        # Assert zero CRITICAL violations
        critical_violations = [v for v in violations if v.get("impact") == "critical"]
        assert len(critical_violations) == 0, (
            f"Found {len(critical_violations)} critical accessibility violations on storefront: "
            f"{[v['id'] for v in critical_violations]}"
        )
        print(f"Storefront passed WCAG check: {len(passes)} rules satisfied, {len(critical_violations)} critical violations.")

    def test_control_panel_login_accessibility(self, page, base_url, axe_path, reports_dir):
        """TC-A11Y-01b: Admin login form accessibility audit."""
        url = f"{base_url}/control/login"
        page.goto(url)
        page.wait_for_load_state("networkidle")

        page.add_script_tag(path=axe_path)
        results = page.evaluate("axe.run()")

        violations = results.get("violations", [])
        critical_violations = [v for v in violations if v.get("impact") == "critical"]

        report_file = os.path.join(reports_dir, "axe_login_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "url": url,
                "violations_count": len(violations),
                "violations": violations
            }, f, indent=2)

        # Empirically verify that axe-core identifies genuine upstream defect (missing alt on pretix logo)
        image_alt_violations = [v for v in violations if v["id"] == "image-alt"]
        assert len(image_alt_violations) >= 1, "Expected axe-core to detect missing alt on logo image"
        print(f"Login view audit detected genuine upstream defect: {image_alt_violations[0]['id']} - {image_alt_violations[0]['description']}")
