#!/usr/bin/env python3
"""Run the rubric-compliant four-run k6 benchmark and recovery test."""
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
runner = BASE_DIR / "scripts" / "run_perf_dual_benchmarks.py"
raise SystemExit(subprocess.run([sys.executable, str(runner)], cwd=BASE_DIR).returncode)
