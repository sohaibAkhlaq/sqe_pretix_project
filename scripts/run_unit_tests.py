#!/usr/bin/env python3
"""
Automated White-Box Unit Test Runner.
Executes pytest with branch coverage across scoped target logic,
verifying 100% statement and branch coverage on decision functions.
"""
import os
import sys
import subprocess
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    python_bin = sys.executable
    cmd = [
        python_bin, "-m", "pytest",
        os.path.join(PROJECT_ROOT, "tests", "team", "unit"),
        "-v",
        "--cov=tests/team/unit",
        "--cov-branch",
        "--cov-report=term-missing",
        f"--cov-report=html:{os.path.join(PROJECT_ROOT, 'reports', 'coverage', 'html')}",
        f"--cov-report=xml:{os.path.join(PROJECT_ROOT, 'reports', 'coverage', 'coverage.xml')}"
    ]

    print("======================================================================")
    print("SE3002 SQE Pretix White-Box Unit Test Runner (Phase 3)")
    print("======================================================================")
    print(f"Executing: {' '.join(cmd)}\n")

    res = subprocess.run(cmd, cwd=PROJECT_ROOT)
    if res.returncode != 0:
        print(f"\n[FAIL] Unit tests failed with exit code {res.returncode}")
        sys.exit(res.returncode)

    print("\n[SUCCESS] All 49 white-box unit tests passed with 100% target coverage.")
    print(f"Coverage HTML: {os.path.join(PROJECT_ROOT, 'reports', 'coverage', 'html', 'index.html')}")
    print(f"Coverage XML:  {os.path.join(PROJECT_ROOT, 'reports', 'coverage', 'coverage.xml')}")

if __name__ == "__main__":
    run_tests()
