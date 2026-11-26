#!/usr/bin/env python3
"""
Comprehensive Performance and Recovery Execution Script.
Executes:
1. Setup 1 (1 VU, 60s): Run 1 and Run 2
2. Setup 2 (5 VUs, 60s): Run 1 and Run 2
3. Controlled failure-and-recovery test for state-changing order operation
4. Full metric comparison against SLA limits (p95 <= 500ms, unexpected failures < 1%)
"""
import sys
import os
import subprocess
import json
import time
import platform
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "perf"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

VENV_PYTHON = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if not VENV_PYTHON.exists():
    VENV_PYTHON = Path(sys.executable)

K6_BIN = "k6"
sys.path.insert(0, str(BASE_DIR))
from scripts.get_tokens import get_tokens

def runtime_env():
    """Pass the local API token to k6 without storing it in source or reports."""
    env = os.environ.copy()
    token = env.get("API_TOKEN") or get_tokens().get("SQE Test API Token")
    if not token:
        raise RuntimeError("No API token available. Set API_TOKEN or seed the local test token.")
    env["API_TOKEN"] = token
    return env

def reset_state():
    print("   [RESET] Restoring deterministic baseline (Quota=10, Orders=0)...")
    res = subprocess.run([str(VENV_PYTHON), str(BASE_DIR / "scripts" / "reset.py")],
                         capture_output=True, text=True)
    if res.returncode != 0:
        print(f"   [ERROR] Reset failed: {res.stderr}")
        sys.exit(1)

def run_k6(script_path, output_json, description, extra_env=None):
    print(f"\n>> Running {description} (60s steady-state)...")
    raw_output = output_json.with_name(output_json.stem + "_raw.json")
    cmd = [
        K6_BIN, "run",
        "--out", f"json={raw_output}",
        "--summary-export", str(output_json),
        str(script_path)
    ]
    env = runtime_env()
    if extra_env:
        env.update(extra_env)
    start = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    duration = time.time() - start
    print(f"   k6 finished in {duration:.2f}s. Exit code: {res.returncode}")
    if res.returncode not in (0, 99):
        raise RuntimeError(f"{description} failed (exit {res.returncode}): {res.stderr[-2000:]}")

    metrics = {}
    if output_json.exists():
        with open(output_json, "r", encoding="utf-8") as f:
            raw = json.load(f)
            m = raw.get("metrics", {})
            dur = m.get("http_req_duration", {})
            if "values" in dur: dur = dur["values"]
            failed = m.get("unexpected_failures", {})
            if "values" in failed: failed = failed["values"]
            reqs = m.get("http_reqs", {})
            if "values" in reqs: reqs = reqs["values"]

            metrics = {
                "p95_ms": round(dur.get("p(95)", 0), 2),
                "avg_ms": round(dur.get("avg", 0), 2),
                "med_ms": round(dur.get("med", 0), 2),
                "p90_ms": round(dur.get("p(90)", 0), 2),
                "rps": round(reqs.get("rate", 0), 2),
                "total_requests": reqs.get("count", 0),
                "unexpected_failure_rate": round(failed.get("rate", 0), 4),
                "unexpected_failure_percent": round(failed.get("rate", 0) * 100, 2),
            }
    return metrics

def main():
    print("=" * 80)
    print("  SE3002: Grafana k6 OSS Performance & Recovery Benchmark Suite")
    print("  Operation: Quota Availability & Order Creation (Workflow A)")
    print("  Limits: p95 <= 500 ms, Unexpected Failure Rate < 1.0%")
    print("=" * 80)

    unified_script = BASE_DIR / "tests" / "team" / "perf" / "load_unified_60s.js"

    # 1. Setup 1: 1 VU, 60 seconds (Run 1)
    reset_state()
    run1_1vu_json = REPORTS_DIR / "k6_1vu_run1.json"
    m_1vu_run1 = run_k6(unified_script, run1_1vu_json, "Setup 1 (1 VU, 60s) - Run 1", {"VUS": "1", "RAMP": "5s"})

    # 2. Setup 1: 1 VU, 60 seconds (Run 2)
    reset_state()
    run2_1vu_json = REPORTS_DIR / "k6_1vu_run2.json"
    m_1vu_run2 = run_k6(unified_script, run2_1vu_json, "Setup 1 (1 VU, 60s) - Run 2", {"VUS": "1", "RAMP": "5s"})

    # 3. Setup 2: 5 VUs, 60 seconds (Run 1)
    reset_state()
    run1_5vu_json = REPORTS_DIR / "k6_5vu_run1.json"
    m_5vu_run1 = run_k6(unified_script, run1_5vu_json, "Setup 2 (5 VUs, 60s) - Run 1", {"VUS": "5", "RAMP": "10s"})

    # 4. Setup 2: 5 VUs, 60 seconds (Run 2)
    reset_state()
    run2_5vu_json = REPORTS_DIR / "k6_5vu_run2.json"
    m_5vu_run2 = run_k6(unified_script, run2_5vu_json, "Setup 2 (5 VUs, 60s) - Run 2", {"VUS": "5", "RAMP": "10s"})

    # 5. Controlled Failure and Recovery Test
    print("\n>> Running Controlled State-Changing Failure-and-Recovery Test...")
    res_rec = subprocess.run([
        str(VENV_PYTHON), "-m", "pytest",
        str(BASE_DIR / "tests" / "team" / "perf" / "test_state_changing_recovery.py"),
        "-v", "-s"
    ], capture_output=True, text=True)
    print(res_rec.stdout)
    if res_rec.returncode != 0:
        raise RuntimeError(f"Recovery test failed (exit {res_rec.returncode}): {res_rec.stderr[-2000:]}")

    recovery_data = {}
    rec_report_path = REPORTS_DIR / "state_changing_recovery_report.json"
    if rec_report_path.exists():
        with open(rec_report_path, "r", encoding="utf-8") as f:
            recovery_data = json.load(f)
    else:
        raise RuntimeError("Recovery test returned success but did not produce its required JSON report.")

    # 6. Master Summary & SLA Evaluation
    master_report = {
        "operation_tested": "Quota Availability Check (GET) & Order Creation (POST)",
        "workflow": "Workflow A (Order Placement)",
        "environment": {
            "os": platform.platform(),
            "python": platform.python_version(),
            "build_commit": subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=BASE_DIR, capture_output=True, text=True
            ).stdout.strip(),
            "starting_data": "reset.py before each run; expected quota=10 and orders=0",
            "steady_state_seconds": 60,
            "ramp_up_seconds": {"1_vu": 5, "5_vu": 10},
            "http_400": "Expected quota-exhaustion rejection; excluded from unexpected failures.",
        },
        "sla_limits": {
            "p95_limit_ms": 500,
            "max_unexpected_failure_percent": 1.0,
            "justification": "Storefront ticketing checkout requires p95 < 500ms to preserve user conversion and avoid drop-off during ticket rushes; unexpected failure rate < 1% ensures zero lost orders and database integrity."
        },
        "benchmarks": {
            "1_vu_run1": m_1vu_run1,
            "1_vu_run2": m_1vu_run2,
            "5_vu_run1": m_5vu_run1,
            "5_vu_run2": m_5vu_run2
        },
        "state_changing_recovery": recovery_data,
        "compliance_verdict": {
            "all_runs_within_p95_limit": (
                m_1vu_run1.get("p95_ms", 9999) <= 500 and
                m_1vu_run2.get("p95_ms", 9999) <= 500 and
                m_5vu_run1.get("p95_ms", 9999) <= 500 and
                m_5vu_run2.get("p95_ms", 9999) <= 500
            ),
            "all_runs_unexpected_failure_under_1_percent": (
                m_1vu_run1.get("unexpected_failure_percent", 100) < 1.0 and
                m_1vu_run2.get("unexpected_failure_percent", 100) < 1.0 and
                m_5vu_run1.get("unexpected_failure_percent", 100) < 1.0 and
                m_5vu_run2.get("unexpected_failure_percent", 100) < 1.0
            ),
            "recovery_without_duplicates": recovery_data.get("status") == "PASSED" and recovery_data.get("total_duplicate_records") == 0
        }
    }
    master_report["compliance_verdict"]["all_required_criteria_pass"] = all(
        master_report["compliance_verdict"].values()
    )

    master_path = REPORTS_DIR / "perf_comprehensive_benchmark_report.json"
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master_report, f, indent=2)

    print("\n" + "=" * 80)
    print("  FINAL PERFORMANCE & RECOVERY RESULTS SUMMARY")
    print("=" * 80)
    print(f"  1 VU Run 1: p95 = {m_1vu_run1.get('p95_ms')} ms | RPS = {m_1vu_run1.get('rps')} | Failures = {m_1vu_run1.get('unexpected_failure_percent')}%")
    print(f"  1 VU Run 2: p95 = {m_1vu_run2.get('p95_ms')} ms | RPS = {m_1vu_run2.get('rps')} | Failures = {m_1vu_run2.get('unexpected_failure_percent')}%")
    print(f"  5 VU Run 1: p95 = {m_5vu_run1.get('p95_ms')} ms | RPS = {m_5vu_run1.get('rps')} | Failures = {m_5vu_run1.get('unexpected_failure_percent')}%")
    print(f"  5 VU Run 2: p95 = {m_5vu_run2.get('p95_ms')} ms | RPS = {m_5vu_run2.get('rps')} | Failures = {m_5vu_run2.get('unexpected_failure_percent')}%")
    print(f"  Controlled Recovery: RTO = {recovery_data.get('recovery_time_seconds')}s | Duplicates = {recovery_data.get('total_duplicate_records')} | Status = {recovery_data.get('status')}")
    print("=" * 80)

if __name__ == "__main__":
    main()
