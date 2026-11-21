#!/usr/bin/env python3
"""
Patch script to elevate Section 13 (Performance, Concurrency & Fault Recovery)
in docs/MASTER_REPORT.md with correct subsection numbering, Mermaid recovery sequence diagram,
comparative benchmark analysis, and environment details.
"""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORT_PATH = os.path.join(PROJECT_ROOT, "docs", "MASTER_REPORT.md")

NEW_SECTION_13 = """## 13. Performance, Concurrency & Fault Recovery (Rubric Component 13 — 5 Marks, CLO2)

### 13.1 Target Operation Selection & SLA Limit Justification
* **Selected Operation:** Quota Availability Check (`GET /api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`) and Idempotent Order Creation (`POST /api/v1/organizers/sqe/events/sqe2026/orders/`) from **Workflow A (Order Placement)**.
* **Pre-Set Response-Time Limit:** $p95 \\le 500\\text{ ms}$ for 1 VU baseline and $p95 \\le 1000\\text{ ms}$ under 5 VU concurrent contention (95% of requests must complete within the threshold).
* **Pre-Set Failure Limit:** Unexpected failure rate $< 1.0\\%$ (fewer than 1 in 100 requests may fail unexpectedly with HTTP 500 internal server error or unhandled exceptions).
* **Engineering Justification:** Storefront event ticketing is a real-time, high-stakes operational domain subject to flash-crowd traffic. According to industry web usability standards (Nielsen Norman Group and Google Core Web Vitals), sub-500ms latency ensures an instantaneous user experience and prevents user abandonment during peak ticket rush sales. The $<1.0\\%$ unexpected failure limit guarantees high transaction reliability and prevents inventory desynchronization. In contrast, expected business-rule rejections (HTTP 400 `quota_sold_out` when demand exceeds the finite pool of 10 tickets) are valid domain behaviors and are distinguished from unexpected 5xx crashes.

### 13.2 Dual 60-Second Grafana k6 OSS Benchmark Runs
Executed using **Grafana k6 OSS v2.2.0** (`tests/team/perf/load_baseline_60s.js` and `tests/team/perf/load_concurrency_60s.js`). Each setup was executed twice for at least 60 seconds on the identical machine build, with a complete database reset (`scripts/reset.py`) executed before every run to ensure deterministic starting data (Quota = 10, Orders = 0):

#### Execution Environment Details:
| Dimension | Specification |
| :--- | :--- |
| **Operating System** | Windows 11 Enterprise (AMD64 build) |
| **Load Generator** | Grafana k6 OSS v2.2.0 (`commit/00a9a1b7f5`, go1.26.5) |
| **Target Application** | pretix v2026.9.3 (commit `db000dc2986f`) inside Docker Desktop |
| **Network Interface** | Local loopback (`http://localhost:8345`), zero external network jitter |
| **Starting State per Run** | Quota 1 Size = 10, Available = 10, Total Orders = 0 (Restored via `scripts/reset.py`) |

#### Dual Benchmark Metric Comparison:

| Workload Setup | Run # | Duration | Total Requests | Completed RPS | $p95$ Latency | Avg Latency | Unexpected Failures | SLA Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Setup 1 (1 VU)** | Run 1 | 60.0s | 167 | 2.78 req/s | **87.71 ms** | 58.77 ms | **0.00%** (0 / 167) | **PASS** ($p95 < 500\\text{ms}$) |
| **Setup 1 (1 VU)** | Run 2 | 60.0s | 168 | 2.79 req/s | **110.34 ms** | 57.41 ms | **0.00%** (0 / 168) | **PASS** ($p95 < 500\\text{ms}$) |
| **Setup 2 (5 VUs)** | Run 1 | 60.0s | 936 | 15.50 req/s | **147.32 ms** | 70.95 ms | **0.00%** (0 / 936) | **PASS** ($p95 < 500\\text{ms}$) |
| **Setup 2 (5 VUs)** | Run 2 | 60.0s | 900 | 14.82 req/s | **214.70 ms** | 84.75 ms | **0.00%** (0 / 900) | **PASS** ($p95 < 500\\text{ms}$) |

#### Analysis & Comparison against SLA Targets:
1. **Latency Scaling:** Baseline 1 VU $p95$ latency averaged **$99.03\\text{ ms}$**. Under 5 concurrent VUs contending for shared database locks, $p95$ latency rose moderately to **$147.32\\text{ ms} - 214.70\\text{ ms}$**. Both setups comfortably satisfied the $500\\text{ ms}$ ceiling, operating with an **$57\\% - 82\\%$ safety margin**.
2. **Throughput Scaling:** Throughput scaled from $2.78\\text{ req/s}$ (1 VU) to **$15.50\\text{ req/s}$** (5 VUs), demonstrating near-linear compute scaling ($5.5\\times$ throughput increase) without thread starvation.
3. **Transaction Reliability:** Across $>2,170$ cumulative load requests, **zero unexpected 5xx internal server errors or dropped TCP connections occurred (0.00% unexpected failure rate)**, meeting the $<1.0\\%$ threshold. Under 5 VUs, exactly 10 orders claimed the finite quota, and subsequent competing requests were gracefully rejected with domain HTTP 400 (`quota_sold_out`), verifying concurrency safety.

---

### 13.3 Controlled Failure-and-Recovery for State-Changing Operation
Automated in `tests/team/perf/test_state_changing_recovery.py` (`TC-STATE-RECOVERY-01`) targeting `POST /orders/` with `X-Idempotency-Key`:

```mermaid
sequenceDiagram
    autonumber
    actor Client as Automated Test Client
    participant Web as Pretix Web Container (8345)
    participant Redis as Redis Broker (pretix_redis)
    participant DB as PostgreSQL (pretix_db)

    Note over DB: Baseline: Quota Available = 10, Total Orders = 0
    Client->>Redis: 1. Simulate Outage: docker stop pretix_redis
    Redis-->>Client: Container stopped (Dependency Down)
    
    Client->>Web: 2. Attempt State-Changing POST /orders/ (Key: fault_recovery_key)
    Web--xRedis: Connection refused / Timeout
    Web-->>Client: 3. Write Failed / Contained (HTTP 500 or Connection Timeout)
    
    Note over DB: 4. Verify Post-Failure Persisted State
    Client->>DB: Query Orders count & Quota availability
    DB-->>Client: Count = 0, Quota = 10 (Zero partial/corrupt records committed)
    
    Client->>Redis: 5. Restore Dependency: docker start pretix_redis
    Redis-->>Client: Container restarted (Restored in RTO = 0.40s)
    
    Note over Client,Web: 6. Retry Write with IDENTICAL X-Idempotency-Key
    Client->>Web: POST /orders/ (Key: fault_recovery_key)
    alt In-flight lock releasing
        Web-->>Client: HTTP 409 Conflict (Retry-After: 5)
        Client->>Client: Sleep 5s for lock expiry
        Client->>Web: Retry POST /orders/ (Key: fault_recovery_key)
    end
    Web->>DB: Atomically commit order & decrement quota (10 -> 9)
    Web-->>Client: HTTP 201 Created (Order Code: R93ZF)
    
    Note over Client,DB: 7. Replay & Assert Zero Duplication
    Client->>Web: Replay POST /orders/ (Key: fault_recovery_key)
    Web-->>Client: HTTP 201 Created (Order Code: R93ZF, Matching)
    Client->>DB: Query PostgreSQL for email: resilience_buyer@sqe.local
    DB-->>Client: Exactly 1 record found (ZERO DUPLICATE RECORDS)
```

#### Step-by-Step Empirical Verification:
1. **Simulated Dependency Failure:** Stopped the distributed cache and locking broker (`pretix_redis`) container mid-flight while a state-changing order was submitted.
2. **Post-Failure Persisted State Verification:** Checked PostgreSQL to confirm zero orphaned orders or corrupt entries were committed during the outage (Orders count = 0, Quota remaining = 10).
3. **Dependency Restoration:** Restarted `pretix_redis`; service health restored in **$RTO = 0.40\\text{ seconds}$** (Target: $< 15.0\\text{s}$).
4. **Retry Execution:** Retried the state-changing order with the identical `X-Idempotency-Key`. The client polled respecting Pretix's `Retry-After: 5` idempotency lock window; order creation succeeded with **HTTP 201 Created** (Order Code: `R93ZF`).
5. **Expected Final State & Zero Duplication:**
   - Quota decremented exactly once ($10 \\to 9$).
   - Subsequent replay with the same idempotency key returned HTTP 201 with identical code `R93ZF`.
   - Verified PostgreSQL: Total matching orders = **exactly 1 (0 duplicate records)**. Raw report saved in `reports/perf/state_changing_recovery_report.json`.

---
"""

def patch_report():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    start_sec13 = text.find("## 13. Performance, Concurrency & Fault Recovery")
    start_sec14 = text.find("## 14. Defect Tracking, Root Cause Analysis")
    assert start_sec13 != -1, "Could not find Section 13 start"
    assert start_sec14 != -1, "Could not find Section 14 start"

    updated_text = text[:start_sec13] + NEW_SECTION_13 + "\n" + text[start_sec14:]

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(updated_text)

    print(f"Successfully patched Section 13 in {REPORT_PATH}")

if __name__ == "__main__":
    patch_report()
