#!/usr/bin/env python3
"""
Automated REST API Test Suite Runner.
Resets database to clean seeded baseline, runs pytest on tests/team/api/,
and records test execution results into reports/api/.
"""
import os
import sys
import subprocess
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("======================================================================")
    print("SE3002 SQE Pretix REST API Integration Test Runner (Phase 4)")
    print("======================================================================")

    # 1. Reset database state before test suite execution
    reset_script = os.path.join(PROJECT_ROOT, "scripts", "reset.py")
    print("\n[STEP 1] Resetting pretix database state...")
    res = subprocess.run([sys.executable, reset_script, "--verify-idempotency"], cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print("[FAIL] Database reset failed! Aborting API tests.")
        sys.exit(res.returncode)

    # 2. Run API test suite
    print("\n[STEP 2] Executing REST API test suite via pytest...")
    reports_dir = os.path.join(PROJECT_ROOT, "reports", "api")
    os.makedirs(reports_dir, exist_ok=True)
    report_json_path = os.path.join(reports_dir, "api_test_results.json")

    cmd = [
        sys.executable, "-m", "pytest",
        os.path.join(PROJECT_ROOT, "tests", "team", "api"),
        "-v",
        f"--json-report-file={report_json_path}"
    ]

    start_time = time.time()
    res = subprocess.run([
        sys.executable, "-m", "pytest",
        os.path.join(PROJECT_ROOT, "tests", "team", "api"),
        "-v"
    ], cwd=PROJECT_ROOT)
    duration = time.time() - start_time

    if res.returncode != 0:
        print(f"\n[FAIL] API tests failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    # 3. Save test result summary
    summary = {
        "suite": "SE3002 pretix REST API Integration Suite",
        "phase": "Phase 4 (Gate 4)",
        "duration_seconds": round(duration, 2),
        "status": "PASS",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_modules": [
            "tests/team/api/test_order_creation_api.py",
            "tests/team/api/test_idempotency_api.py",
            "tests/team/api/test_order_lifecycle_api.py",
            "tests/team/api/test_rbac_api.py"
        ]
    }
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n[SUCCESS] All REST API integration tests passed in {duration:.2f}s.")
    print(f"Report saved to: {report_json_path}")

if __name__ == "__main__":
    main()
