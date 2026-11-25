#!/usr/bin/env python3
"""
Automated REST API Test Suite Runner.
Regenerates data vectors from tools/datagen, resets database to clean seeded baseline,
runs pytest on tests/team/api/ with JUnit XML capture, and saves verified results into reports/api/.
"""
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.datagen.generator import generate_full_dataset, load_constraints_from_openapi


def main():
    print("======================================================================")
    print("SE3002 SQE Pretix REST API Integration Test Runner (Phase 4)")
    print("======================================================================")

    reports_dir = PROJECT_ROOT / "reports" / "api"
    reports_dir.mkdir(parents=True, exist_ok=True)
    cfg = load_constraints_from_openapi(str(PROJECT_ROOT / "openapi" / "team-spec.yaml"))
    gen_data = generate_full_dataset(cfg, seed=42)
    (reports_dir / "generated_data.json").write_text(json.dumps(gen_data, indent=2), encoding="utf-8")

    # 1. Reset database state before test suite execution
    reset_script = PROJECT_ROOT / "scripts" / "reset.py"
    print("\n[STEP 1] Resetting pretix database state...")
    res = subprocess.run([sys.executable, str(reset_script), "--verify-idempotency"], cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print("[FAIL] Database reset failed! Aborting API tests.")
        sys.exit(res.returncode)

    # 2. Run API test suite with real JUnit XML instrumentation
    print("\n[STEP 2] Executing REST API test suite via pytest...")
    junit_path = reports_dir / "api_junit.xml"
    report_json_path = reports_dir / "api_test_results.json"

    start_time = time.time()
    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(PROJECT_ROOT / "tests" / "team" / "api"),
            "-v",
            f"--junitxml={junit_path}",
        ],
        cwd=str(PROJECT_ROOT),
    )
    duration = time.time() - start_time

    # Parse actual test counts from JUnit XML
    root = ET.parse(junit_path).getroot()
    suite_node = root if root.tag == "testsuite" else root.find("testsuite")
    total_tests = int(suite_node.attrib.get("tests", 0)) if suite_node is not None else 0
    failures = int(suite_node.attrib.get("failures", 0)) if suite_node is not None else 0
    errors = int(suite_node.attrib.get("errors", 0)) if suite_node is not None else 0
    skipped = int(suite_node.attrib.get("skipped", 0)) if suite_node is not None else 0
    passed = total_tests - failures - errors - skipped

    summary = {
        "suite": "SE3002 pretix REST API Integration Suite",
        "phase": "Phase 4 (Gate 4)",
        "duration_seconds": round(duration, 2),
        "total_tests": total_tests,
        "passed": passed,
        "failures": failures,
        "errors": errors,
        "skipped": skipped,
        "status": "PASS" if res.returncode == 0 and failures == 0 and errors == 0 else "FAIL",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "test_modules": [
            "tests/team/api/test_datagen_openapi_contract.py",
            "tests/team/api/test_order_creation_api.py",
            "tests/team/api/test_idempotency_api.py",
            "tests/team/api/test_order_lifecycle_api.py",
            "tests/team/api/test_rbac_api.py",
        ],
    }
    report_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    if res.returncode != 0:
        print(f"\n[FAIL] API tests failed ({passed}/{total_tests} passed) with exit code {res.returncode}")
        sys.exit(res.returncode)

    print(f"\n[SUCCESS] All {passed}/{total_tests} REST API integration tests passed in {duration:.2f}s.")
    print(f"Report saved to: {report_json_path}")


if __name__ == "__main__":
    main()
