# Phase 9 Completion & Compliance Report: Performance, Concurrency & Fault Recovery

**Milestone Tag:** `gate-9`  
**Git Branch:** `feature/performance-recovery` (merged into `main` via `--no-ff`)  
**Lead Author:** M. Hasaam (`24i-3107`, Git: `M-Hasaam <m.hasaam.official@gmail.com>`)  
**Target Services:** pretix v2026.9.3 container stack (Nginx, Gunicorn, PostgreSQL 15, Redis 7)  
**Verification Date:** November 25, 2026  
**Execution Status:** **100% VERIFIED — ALL DUAL 60-SECOND BENCHMARKS & FAULT RECOVERY SLAS MET**

---

## 1. Executive Summary

Phase 9 of the SE3002 Software Quality Engineering Final Project establishes the **Empirical Performance Baseline, High-Concurrency Stress Testing, and State-Changing Fault Injection / Recovery Analysis** for the pretix ticketing system.

All deliverables mandated by the Course Project Guidelines and the Professor Audit Deduction #9 have been authored, executed against the live multi-container environment, verified, and committed under proper author attribution (`M-Hasaam <m.hasaam.official@gmail.com>`).

### Key Deliverables Produced:
1. **Baseline 60-Second Load Script:** [`tests/team/perf/load_baseline_60s.js`](file:///c:/Users/USER/Desktop/sqe_project/tests/team/perf/load_baseline_60s.js) testing steady-state read capacity (1 VU, 60s steady state) against availability endpoint.
2. **Concurrency 60-Second Stress Script:** [`tests/team/perf/load_concurrency_60s.js`](file:///c:/Users/USER/Desktop/sqe_project/tests/team/perf/load_concurrency_60s.js) executing 5 concurrent VUs placing orders with unique idempotency keys against a finite quota of 10 items for 60s steady state.
3. **Controlled State-Changing Fault Recovery Suite:** [`tests/team/perf/test_state_changing_recovery.py`](file:///c:/Users/USER/Desktop/sqe_project/tests/team/perf/test_state_changing_recovery.py) testing container termination (`pretix_redis`) during in-flight `POST /orders/`, database persisted state verification, service restoral, retry/replay idempotency, and proof of zero duplicate records (`PR4, PR5`).
4. **Master Benchmark Runner:** [`scripts/run_perf_dual_benchmarks.py`](file:///c:/Users/USER/Desktop/sqe_project/scripts/run_perf_dual_benchmarks.py) automating pre-run deterministic resets, executing dual runs of both workloads, running the state-changing recovery test, and compiling master SLA reports.
5. **Raw Metrics & Reports:**
   - [`reports/perf/k6_1vu_run1.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/perf/k6_1vu_run1.json)
   - [`reports/perf/k6_1vu_run2.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/perf/k6_1vu_run2.json)
   - [`reports/perf/k6_5vu_run1.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/perf/k6_5vu_run1.json)
   - [`reports/perf/k6_5vu_run2.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/perf/k6_5vu_run2.json)
   - [`reports/perf/state_changing_recovery_report.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/perf/state_changing_recovery_report.json)
   - [`reports/perf/perf_comprehensive_benchmark_report.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/perf/perf_comprehensive_benchmark_report.json)
6. **Detailed Academic Report:** [`docs/performance-recovery.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/performance-recovery.md).

---

## 2. Empirical Execution Results

Execution of `scripts/run_perf_dual_benchmarks.py`:

```text
================================================================================
  SE3002: Grafana k6 OSS Performance & Recovery Benchmark Suite
  Operation: Quota Availability & Order Creation (Workflow A)
  Limits: p95 <= 500 ms, Unexpected Failure Rate < 1.0%
================================================================================
   [RESET] Restoring deterministic baseline (Quota=10, Orders=0)...

>> Running Setup 1 (1 VU, 60s) - Run 1 (60s duration)...
   k6 finished in 72.87s. Exit code: 0
   [RESET] Restoring deterministic baseline (Quota=10, Orders=0)...

>> Running Setup 1 (1 VU, 60s) - Run 2 (60s duration)...
   k6 finished in 73.90s. Exit code: 0
   [RESET] Restoring deterministic baseline (Quota=10, Orders=0)...

>> Running Setup 2 (5 VUs, 60s) - Run 1 (60s duration)...
   k6 finished in 82.57s. Exit code: 0
   [RESET] Restoring deterministic baseline (Quota=10, Orders=0)...

>> Running Setup 2 (5 VUs, 60s) - Run 2 (60s duration)...
   k6 finished in 82.96s. Exit code: 0

>> Running Controlled State-Changing Failure-and-Recovery Test...
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0 -- C:\Users\USER\Desktop\sqe_project\.venv\Scripts\python.exe
rootdir: C:\Users\USER\Desktop\sqe_project
plugins: platformdirs-4.14.8, cov-7.1.0
collected 1 item

tests/team/perf/test_state_changing_recovery.py::test_state_changing_order_recovers_without_partial_or_duplicate_records PASSED

============================= 1 passed in 15.94s ==============================

================================================================================
  FINAL PERFORMANCE & RECOVERY RESULTS SUMMARY
================================================================================
  1 VU Run 1: p95 = 183.98 ms | RPS = 2.38  | Total Reqs =  167 | Unexpected Failures = 0%
  1 VU Run 2: p95 = 186.16 ms | RPS = 2.44  | Total Reqs =  171 | Unexpected Failures = 0%
  5 VU Run 1: p95 = 354.47 ms | RPS = 11.49 | Total Reqs =  922 | Unexpected Failures = 0%
  5 VU Run 2: p95 = 212.14 ms | RPS = 13.64 | Total Reqs = 1092 | Unexpected Failures = 0%
  Controlled Recovery: RTO = 0.28s | Order = PSELH | Duplicates = 0 | Status = PASSED
================================================================================
```

---

## 3. SLA Compliance Summary

| Test Profile | Run # | SLA Target | Measured Reality | Compliance Margin | Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Setup 1 (1 VU)** | Run 1 | $p95 \le 500.0\text{ ms}$ | **$183.98\text{ ms}$** | $+316.02\text{ ms}$ buffer (63.2% margin) | **PASS** |
| **Setup 1 (1 VU)** | Run 2 | $p95 \le 500.0\text{ ms}$ | **$186.16\text{ ms}$** | $+313.84\text{ ms}$ buffer (62.8% margin) | **PASS** |
| **Setup 2 (5 VUs)**| Run 1 | $p95 \le 500.0\text{ ms}$ | **$354.47\text{ ms}$** | $+145.53\text{ ms}$ buffer (29.1% margin) | **PASS** |
| **Setup 2 (5 VUs)**| Run 2 | $p95 \le 500.0\text{ ms}$ | **$212.14\text{ ms}$** | $+287.86\text{ ms}$ buffer (57.6% margin) | **PASS** |
| **Unexpected Failures** | All Runs | $< 1.00\%$ | **$0.00\%$ (0 / 2,352)** | Zero unexpected errors | **PASS** |
| **State-Changing RTO** | Outage | $\le 15.0\text{ seconds}$ | **$0.28\text{ seconds}$** | $+14.72\text{ seconds}$ buffer (98.1% margin) | **PASS** |
| **Post-Outage Duplicates** | Retries | 0 Duplicates | **0 Duplicates (1 record)** | Zero duplicate orders (`PSELH`) | **PASS** |
| **Post-Outage Quota** | Final | Exactly 9 | **9 available** | Single decrement verified | **PASS** |

---

## 4. Concurrency Invariant & Fault Recovery Integrity

* **Deterministic Resets:** Restored Quota 1 = 10 and Orders = 0 before every single benchmark run.
* **Concurrency Protection:** Under 5 concurrent virtual users firing asynchronous order placements (`461` + `546` POST attempts), strictly `10` orders claimed capacity per run (`451` + `536` returned HTTP 400 `quota_sold_out`). Zero capacity leakage or negative quotas occurred ($Q_{\text{final}} \ge 0$).
* **State-Changing Fault Recovery (`PR4, PR5`):** When Redis was terminated mid-flight during `POST /orders/`, zero partial or orphaned orders were committed to PostgreSQL. Following service restoral (`0.28s`), retrying with the same `X-Idempotency-Key` completed successfully (`HTTP 201`, `PSELH`), replaying identical code `PSELH` and proving zero duplicate records in PostgreSQL.
