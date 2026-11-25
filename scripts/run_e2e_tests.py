#!/usr/bin/env python3
"""
Automated Playwright End-to-End Test Suite Runner.
Executes browser tests across customer storefront, cart, checkout,
and organizer control panel, generating JUnit XML, HTML report, and JSON summary.
"""
import html
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _parse_junit_and_write_html(junit_path: Path, html_path: Path, screenshots: list, duration: float) -> dict:
    root = ET.parse(junit_path).getroot()
    suite_node = root if root.tag == "testsuite" else root.find("testsuite")
    total = int(suite_node.attrib.get("tests", 0)) if suite_node is not None else 0
    failures = int(suite_node.attrib.get("failures", 0)) if suite_node is not None else 0
    errors = int(suite_node.attrib.get("errors", 0)) if suite_node is not None else 0
    skipped = int(suite_node.attrib.get("skipped", 0)) if suite_node is not None else 0
    passed = total - failures - errors - skipped

    rows_html = []
    for tc in root.iter("testcase"):
        cls = tc.attrib.get("classname", "")
        name = tc.attrib.get("name", "")
        t = tc.attrib.get("time", "0")
        fail_el = tc.find("failure") or tc.find("error")
        skip_el = tc.find("skipped")
        if fail_el is not None:
            status = "FAIL"
            color = "#b91c1c"
        elif skip_el is not None:
            status = "SKIP"
            color = "#b45309"
        else:
            status = "PASS"
            color = "#15803d"
        rows_html.append(
            f"<tr><td>{html.escape(cls)}</td><td>{html.escape(name)}</td>"
            f"<td style='color:{color};font-weight:bold'>{status}</td><td>{html.escape(t)}s</td></tr>"
        )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SE3002 Playwright E2E Test Report</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; margin: 24px; color: #111827; }}
  h1 {{ margin-bottom: 4px; }}
  .summary {{ display: flex; gap: 16px; margin: 16px 0; }}
  .card {{ padding: 12px 18px; border: 1px solid #d1d5db; border-radius: 6px; background: #f9fafb; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 14px; }}
  th, td {{ border: 1px solid #d1d5db; padding: 8px 10px; text-align: left; }}
  th {{ background: #f3f4f6; }}
</style>
</head>
<body>
  <h1>SE3002 Pretix Playwright E2E Test Execution Report</h1>
  <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())} | Duration: {duration:.2f}s | Screenshots: {len(screenshots)}</p>
  <div class="summary">
    <div class="card"><strong>Total Tests:</strong> {total}</div>
    <div class="card"><strong>Passed:</strong> {passed}</div>
    <div class="card"><strong>Failed:</strong> {failures + errors}</div>
    <div class="card"><strong>Skipped:</strong> {skipped}</div>
  </div>
  <table>
    <thead><tr><th>Module / Class</th><th>Test Function</th><th>Status</th><th>Duration</th></tr></thead>
    <tbody>
      {''.join(rows_html)}
    </tbody>
  </table>
</body>
</html>
"""
    html_path.write_text(doc, encoding="utf-8")
    return {"total": total, "passed": passed, "failures": failures, "errors": errors, "skipped": skipped}


def main():
    print("======================================================================")
    print("SE3002 SQE Pretix Playwright E2E Test Suite Runner (Phase 5)")
    print("======================================================================")

    reset_script = PROJECT_ROOT / "scripts" / "reset.py"
    print("\n[STEP 1] Resetting pretix database state to clean seed...")
    res = subprocess.run([sys.executable, str(reset_script), "--verify-idempotency"], cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print("[FAIL] Database reset failed! Aborting E2E tests.")
        sys.exit(res.returncode)

    reports_dir = PROJECT_ROOT / "reports" / "e2e"
    screenshots_dir = reports_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)
    junit_path = reports_dir / "e2e_junit.xml"
    html_path = reports_dir / "e2e_report.html"
    report_json_path = reports_dir / "e2e_test_results.json"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        str(PROJECT_ROOT / "tests" / "team" / "e2e"),
        "-v",
        "-k",
        "not spike",
        f"--junitxml={junit_path}",
    ]

    print(f"\n[STEP 2] Executing Playwright E2E tests: {' '.join(cmd)}\n")
    start_time = time.time()
    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    duration = time.time() - start_time

    screenshots = sorted(os.listdir(screenshots_dir)) if screenshots_dir.exists() else []
    counts = _parse_junit_and_write_html(junit_path, html_path, screenshots, duration) if junit_path.exists() else {}

    passed_all = res.returncode == 0 and counts.get("failures", 1) == 0 and counts.get("errors", 1) == 0
    summary = {
        "suite": "SE3002 pretix Playwright E2E Suite (30-Flow Automation)",
        "phase": "Phase 5 (Gate 5) / Remediation Phase 3",
        "duration_seconds": round(duration, 2),
        "status": "PASS" if passed_all else "FAIL",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_pytest_cases": counts.get("total", 0),
        "passed_pytest_cases": counts.get("passed", 0),
        "failed_pytest_cases": counts.get("failures", 0) + counts.get("errors", 0),
        "skipped_pytest_cases": counts.get("skipped", 0),
        "html_report": "reports/e2e/e2e_report.html",
        "junit_xml": "reports/e2e/e2e_junit.xml",
        "screenshots_captured": screenshots,
        "total_flows_automated": 30,
        "flows_passed": 30 if passed_all else 0,
        "test_modules": [
            "tests/team/e2e/test_customer_order_flow.py",
            "tests/team/e2e/test_sold_out_ui_flow.py",
            "tests/team/e2e/test_organizer_control_panel_flow.py",
            "tests/team/e2e/test_auditor_access_control_ui.py",
            "tests/team/e2e/test_uc1_flows.py",
            "tests/team/e2e/test_uc2_flows.py",
            "tests/team/e2e/test_uc3_flows.py",
            "tests/team/e2e/test_uc4_flows.py",
            "tests/team/e2e/test_uc5_flows.py",
            "tests/team/e2e/test_uc6_flows.py",
        ],
    }
    report_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if not passed_all:
        print(f"\n[FAIL] E2E Playwright tests failed with exit code {res.returncode}")
        sys.exit(res.returncode or 1)

    print(f"\n[SUCCESS] All {counts.get('passed')}/{counts.get('total')} Playwright E2E tests passed in {duration:.2f}s.")
    print(f"HTML report: {html_path}")
    print(f"JSON summary: {report_json_path}")


if __name__ == "__main__":
    main()
