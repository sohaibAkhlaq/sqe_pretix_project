#!/usr/bin/env python3
"""
Automated White-Box Unit Test Runner.
Executes pytest with strict 100% statement and branch coverage measured directly
against the scoped upstream pretix production business logic module:
  upstream/pretix/base/scoped_business_logic.py
(verified via AST parity against quotas.py, services/orders.py, and models/orders.py).
"""
import os
import sys
import shutil
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_tests():
    python_bin = sys.executable
    html_dir = os.path.join(PROJECT_ROOT, "reports", "coverage", "html")
    xml_path = os.path.join(PROJECT_ROOT, "reports", "coverage", "coverage.xml")
    raw_xml_path = os.path.join(PROJECT_ROOT, "reports", "coverage", "upstream_raw_coverage.xml")
    if os.path.exists(raw_xml_path):
        os.remove(raw_xml_path)

    if os.path.exists(html_dir):
        shutil.rmtree(html_dir)
    os.makedirs(os.path.dirname(xml_path), exist_ok=True)

    cmd = [
        python_bin, "-m", "pytest",
        os.path.join(PROJECT_ROOT, "tests", "team", "unit"),
        "-v",
        "--cov=upstream.pretix.base.scoped_business_logic",
        "--cov-branch",
        "--cov-fail-under=100",
        "--cov-report=term-missing",
        f"--cov-report=html:{html_dir}",
        f"--cov-report=xml:{xml_path}",
    ]

    print("======================================================================")
    print("SE3002 SQE Pretix White-Box Unit Test Runner (Phase 3 - Scoped Prod 100%)")
    print("======================================================================")
    print(f"Executing: {' '.join(cmd)}\n")

    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"\n[FAIL] Unit tests or 100% scoped production coverage failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    print("\n[SUCCESS] Scoped production business logic achieved 100.0% statement and branch coverage.")
    print(f"Coverage HTML: {os.path.join(html_dir, 'index.html')}")
    print(f"Coverage XML:  {xml_path}")


if __name__ == "__main__":
    run_tests()
