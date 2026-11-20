#!/usr/bin/env python3
"""
Automated Playwright End-to-End Test Suite Runner.
Executes browser tests across customer storefront, cart, checkout,
and organizer control panel, capturing screenshot artifacts.
"""
import os
import sys
import subprocess
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("======================================================================")
    print("SE3002 SQE Pretix Playwright E2E Test Suite Runner (Phase 5)")
    print("======================================================================")

    # 1. Reset database state before E2E execution
    reset_script = os.path.join(PROJECT_ROOT, "scripts", "reset.py")
    print("\n[STEP 1] Resetting pretix database state to clean seed...")
    res = subprocess.run([sys.executable, reset_script, "--verify-idempotency"], cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print("[FAIL] Database reset failed! Aborting E2E tests.")
        sys.exit(res.returncode)

    reports_dir = os.path.join(PROJECT_ROOT, "reports", "e2e")
    screenshots_dir = os.path.join(reports_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    report_json_path = os.path.join(reports_dir, "e2e_test_results.json")

    cmd = [
        sys.executable, "-m", "pytest",
        os.path.join(PROJECT_ROOT, "tests", "team", "e2e"),
        "-v",
        "-k", "not spike"
    ]

    print(f"\n[STEP 2] Executing Playwright E2E tests: {' '.join(cmd)}\n")
    start_time = time.time()
    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    duration = time.time() - start_time

    if res.returncode != 0:
        print(f"\n[FAIL] E2E Playwright tests failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    # Save summary
    screenshots = os.listdir(screenshots_dir) if os.path.exists(screenshots_dir) else []
    summary = {
        "suite": "SE3002 pretix Playwright E2E Suite",
        "phase": "Phase 5 (Gate 5)",
        "duration_seconds": round(duration, 2),
        "status": "PASS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "screenshots_captured": screenshots,
        "test_modules": [
            "tests/team/e2e/test_customer_order_flow.py",
            "tests/team/e2e/test_sold_out_ui_flow.py",
            "tests/team/e2e/test_organizer_control_panel_flow.py",
            "tests/team/e2e/test_auditor_access_control_ui.py"
        ]
    }
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[SUCCESS] All Playwright E2E tests passed in {duration:.2f}s.")
    print(f"Screenshots captured ({len(screenshots)}): {screenshots_dir}")
    print(f"Report saved to: {report_json_path}")

if __name__ == "__main__":
    main()
