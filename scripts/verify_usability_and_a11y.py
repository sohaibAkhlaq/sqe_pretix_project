#!/usr/bin/env python3
"""
SE3002 Component 11 Audit: Usability & Accessibility Verification Script.
Cross-checks reports/a11y/lighthouse_*.html, axe_*.json, playwright_usability_report.json,
and lighthouse_axe_unified_report.json so zero hardcoded/stale scores can pass.
"""
import json
import os
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _extract_lh_a11y(html_path: Path) -> int:
    text = html_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"window\.__LIGHTHOUSE_JSON__\s*=\s*(\{.*?\});</script>", text, re.DOTALL)
    assert m, f"Missing Lighthouse JSON inside {html_path}"
    data = json.loads(m.group(1))
    return round(data["categories"]["accessibility"]["score"] * 100)


def audit_usability_and_a11y():
    print("======================================================================")
    print("SE3002 Component 11: Usability & Accessibility Audit (5 Marks, CLO3)")
    print("======================================================================")

    reports_dir = PROJECT_ROOT / "reports" / "a11y"
    unified_json = reports_dir / "lighthouse_axe_unified_report.json"
    assert unified_json.exists(), "Missing reports/a11y/lighthouse_axe_unified_report.json"
    data = json.loads(unified_json.read_text(encoding="utf-8"))

    # 1. Inspect Unified Lighthouse & axe-core Register
    print("\n--- [CHECK 1] Auditing Lighthouse & axe-core Deduplicated Register ---")
    issues = data["issue_register"]
    print(f"  Total Unique Deduplicated Issues: {len(issues)}")
    assert len(issues) == 3, f"Expected 3 deduplicated issues, found {len(issues)}"

    severities = {"Critical": 0, "High": 0, "Minor": 0}
    for issue in issues:
        sev = issue["severity"]
        severities[sev] = severities.get(sev, 0) + 1
        print(f"  [ISSUE] {issue['issue_id']}: {issue['wcag_criterion']} | Severity: {sev} | Status: {issue['remediation_status']}")
        assert len(issue["user_impact"]) > 10
        assert len(issue["proposed_fix"]) > 10

    assert severities["Critical"] == 1
    assert severities["High"] == 1
    assert severities["Minor"] == 1

    # 2. Cross-Verify Before vs After Scores Against Real HTML & JSON Artifacts
    print("\n--- [CHECK 2] Cross-Verifying Before vs. After Against Raw HTML/JSON ---")
    bva = data["before_after_comparison"]
    before = bva["before_remediation"]
    after = bva["after_remediation"]

    raw_before_a11y = _extract_lh_a11y(reports_dir / "lighthouse_before.html")
    raw_after_a11y = _extract_lh_a11y(reports_dir / "lighthouse_after.html")
    raw_store_a11y = _extract_lh_a11y(reports_dir / "lighthouse_storefront.html")

    assert before["lighthouse_accessibility_score"] == raw_before_a11y, (
        f"Before score mismatch: JSON={before['lighthouse_accessibility_score']} vs HTML={raw_before_a11y}"
    )
    assert after["lighthouse_accessibility_score"] == raw_after_a11y, (
        f"After score mismatch: JSON={after['lighthouse_accessibility_score']} vs HTML={raw_after_a11y}"
    )
    assert data["lighthouse_category_scores"]["storefront_landing"]["accessibility"] == raw_store_a11y

    axe_login = json.loads((reports_dir / "axe_login_report.json").read_text(encoding="utf-8"))
    assert axe_login["violations_count"] == after["axe_core_violations"] == 0
    assert before["axe_core_violations"] >= 1
    assert raw_after_a11y > raw_before_a11y

    delta = raw_after_a11y - raw_before_a11y
    print(f"  Remediated Screen: {bva['remediated_screen']}")
    print(f"  axe-core Violations: {before['axe_core_violations']} -> {after['axe_core_violations']} (RESOLVED)")
    print(f"  Lighthouse A11y Score: {raw_before_a11y} -> {raw_after_a11y} (+{delta} points verified from HTML)")
    print(f"  Storefront Lighthouse A11y: {raw_store_a11y} (verified from HTML)")

    # 3. Inspect Automated Usability Workflow Tasks Report
    print("\n--- [CHECK 3] Auditing Automated Playwright Usability Workflow Tasks ---")
    usability_json = reports_dir / "playwright_usability_report.json"
    assert usability_json.exists(), "Missing reports/a11y/playwright_usability_report.json"
    u_data = json.loads(usability_json.read_text(encoding="utf-8"))

    wf_a = u_data["workflow_a"]
    print(f"  [PASS] Workflow A: {wf_a['task']} -> {wf_a['status']}")
    assert wf_a["status"] == "PASSED"

    wf_b = u_data["workflow_b"]
    print(f"  [PASS] Workflow B: {wf_b['task']} -> {wf_b['status']}")
    assert wf_b["status"] == "PASSED"

    # 4. Inspect Real Captured Screenshot Artifacts
    print("\n--- [CHECK 4] Inspecting Real Usability & A11y Screenshot Artifacts ---")
    screenshots_dir = reports_dir / "screenshots"
    expected_shots = [
        "01_keyboard_tab_focus.png",
        "02_login_remediation_before.png",
        "03_login_remediation_after.png",
        "04_storefront_high_contrast.png",
        "workflow_a_01_validation_rejected.png",
        "workflow_a_02_checkout_progressed.png",
        "workflow_b_01_orders_ledger_confirmed.png",
    ]
    for shot in expected_shots:
        shot_path = screenshots_dir / shot
        assert shot_path.exists(), f"Missing screenshot: {shot}"
        size = shot_path.stat().st_size
        assert size > 10000, f"Screenshot {shot} too small ({size} bytes)"
        print(f"  [PASS] Verified screenshot: {shot:40} ({size:,} bytes)")

    print("\n======================================================================")
    print("[SUCCESS] ALL USABILITY & ACCESSIBILITY CRITERIA MET (5/5 MARKS)")
    print("======================================================================")
    return True


if __name__ == "__main__":
    audit_usability_and_a11y()
