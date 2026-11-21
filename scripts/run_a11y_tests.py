#!/usr/bin/env python3
"""
Automated Usability & Accessibility Test Suite Runner (Phase 6).
Executes axe-core automated scans, keyboard navigation tests,
and before/after remediation checks, capturing screenshots.
"""
import os
import sys
import subprocess
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("======================================================================")
    print("SE3002 SQE Pretix Usability & Accessibility Test Runner (Phase 6)")
    print("======================================================================")

    reports_dir = os.path.join(PROJECT_ROOT, "reports", "a11y")
    screenshots_dir = os.path.join(reports_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    report_json_path = os.path.join(reports_dir, "a11y_test_results.json")

    cmd = [
        sys.executable, "-m", "pytest",
        os.path.join(PROJECT_ROOT, "tests", "team", "a11y"),
        "-v"
    ]

    print(f"Executing: {' '.join(cmd)}\n")
    start_time = time.time()
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    duration = time.time() - start_time

    if res.returncode != 0:
        print(f"\n[FAIL] Accessibility tests failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    screenshots = os.listdir(screenshots_dir) if os.path.exists(screenshots_dir) else []
    summary = {
        "suite": "SE3002 pretix Usability & Accessibility Suite",
        "phase": "Phase 6 (Gate 6)",
        "duration_seconds": round(duration, 2),
        "status": "PASS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "screenshots_captured": screenshots,
        "test_modules": [
            "tests/team/a11y/test_axe_accessibility.py",
            "tests/team/a11y/test_keyboard_navigation.py",
            "tests/team/a11y/test_a11y_remediation.py",
            "tests/team/a11y/test_usability_workflow_tasks.py"
        ]
    }
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[SUCCESS] All Usability & Accessibility tests passed in {duration:.2f}s.")
    print(f"Screenshots captured ({len(screenshots)}): {screenshots_dir}")
    print(f"Report saved to: {report_json_path}")

if __name__ == "__main__":
    main()
