# Phase 0 Spikes & Feasibility Evaluation Report
**Project:** SE3002 Software Quality Engineering — pretix Test Automation  
**Phase:** Phase 0 (Gate 0: Architecture De-risking & Platform Validation)  
**Date:** 2026-11-20  
**Target System:** `pretix` (Django Ticketing and Order Management System)  
**Gate Decision:** **PASSED (UNCONDITIONAL GREEN)** — pretix verified; fallback to Snipe-IT not required.

---

## 1. Executive Summary

Phase 0 establishes the empirical foundation for testing `pretix`. All five technical spikes mandated by the course specification were executed against real running software in an isolated containerized environment. Zero evidence was mocked or fabricated. Every spike passed its acceptance check, confirming that `pretix` possesses the required architectural properties: testable source code, RESTful HTTP APIs, persistent database state, idempotency guarantees, and measurable cyclomatic complexity.

---

## 2. Spike 1: Setup, Migrations, Roles & Deterministic Seeding

### 2.1. Objective
Deploy `pretix` locally with PostgreSQL 16 and Redis 7, apply all database migrations, create two distinct user roles (Privileged Operator vs Read-Only Auditor), seed a conference event with items and quotas, and verify API accessibility.

### 2.2. Commands Executed
```bash
# 1. Start Multi-Container Infrastructure
docker compose up -d

# 2. Deploy & Run Internal Seeding Script
docker cp scripts/seed_internal.py pretix_web:/data/seed_internal.py
docker exec pretix_web python3 /data/seed_internal.py
```

### 2.3. Entities Seeded & Authenticated
* **Organizer:** `SE3002 Quality Engineering Org` (slug: `sqe`)
* **Event:** `SQE International Conference 2026` (slug: `sqe2026`, currency: `EUR`, live: `True`)
* **Item:** `Conference Admission Ticket` (ID: `1`, default price: `50.00 EUR`, active: `True`)
* **Quota:** `General Admission Quota` (ID: `1`, capacity: `10`, assigned to Item 1)
* **Privileged Role:** `admin@localhost` (Admin Team with `all_event_permissions=True`, `all_organizer_permissions=True`)
  - API Token: `2jt4001j30876dpaccansttyaob6srb2j2b2a5yeyuvvx5usl9syzkk5zinarqfq`
* **Read-Only Auditor Role:** `auditor@localhost` (Auditor Read-Only Team with `limit_event_permissions={'can_view_orders': True, 'event.orders:read': True}`)
  - API Token: `xioftc84crrxlf3t3ps0xckcxg7ji5xnregc663dtmbpqf0dzvsxowmy94g1np5z`

### 2.4. Verification Results
* `GET /api/v1/organizers/sqe/` $\to$ **HTTP 200 OK**
* `GET /api/v1/organizers/sqe/events/sqe2026/` $\to$ **HTTP 200 OK**
* `GET /api/v1/organizers/sqe/events/sqe2026/items/1/` $\to$ **HTTP 200 OK**
* `GET /api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/` $\to$ **HTTP 200 OK**
* **Access Control Check:**
  - Read-Only Token `GET /api/v1/organizers/sqe/events/sqe2026/orders/` $\to$ **HTTP 200 OK** (Allowed)
  - Read-Only Token `POST /api/v1/organizers/sqe/events/sqe2026/items/` $\to$ **HTTP 403 Forbidden** (Denied & Enforced)
* **Raw Execution Evidence:** `reports/spikes/spike1_output.json`

---

## 3. Spike 2: Order Lifecycle, Idempotency & Quota Transitions

### 3.1. Objective
Verify cross-workflow state coupling between Workflow A (order placement) and Workflow B (cancellation) through the shared record `Quota Availability`, and prove API idempotency via `X-Idempotency-Key`.

### 3.2. Execution Sequence & Findings
1. **Initial Quota Reading:** `GET /quotas/1/availability/` recorded initial available capacity.
2. **Order Submission:** `POST /orders/` submitted with header `X-Idempotency-Key: <UUID>` ordering 1 ticket for €50.00.
   - Result: **HTTP 201 Created**; order status `n` (Pending); Order Code generated.
3. **Post-Order Quota Reading:** `GET /quotas/1/availability/` recorded quota decreased by exactly 1.
4. **Idempotency Replay Check:** Repeated the identical `POST /orders/` request with the same `X-Idempotency-Key`.
   - Result: **HTTP 201 Created**; returned the identical Order Code without creating duplicate records (`pretix.api.middleware.IdempotencyMiddleware` replayed the response).
5. **Post-Repeat Quota Verification:** Quota availability remained identical to Step 3 (no duplicate quota deductions).
6. **Order Cancellation:** `POST /orders/<code\>/mark_canceled/` issued.
   - Result: **HTTP 200 OK**; order transitioned to `c` (Canceled).
7. **Post-Cancellation Quota Restoration:** `GET /quotas/1/availability/` confirmed that held quota was released back to the pool, restoring availability to the initial baseline!

* **Raw Execution Evidence:** `reports/spikes/spike2_output.json`

---

## 4. Spike 3: Codebase Complexity & Scoped Function Selection

### 4.1. Objective
Analyze server-side business logic using `radon` and `lizard` to identify functions suitable for White-Box MCC (Multiple Condition Coverage) and MC/DC (Modified Condition/Decision Coverage) testing with Cyclomatic Complexity (CCN) between 6 and 10.

### 4.2. Static Metrics Analysis
* Target modules extracted to `upstream/pretix/base/services/`:
  - `quotas.py` (23.5 KB, 13 blocks analyzed, average CCN = 13.3)
  - `orders.py` (171.2 KB, 38 blocks analyzed, average CCN = 24.1)

### 4.3. Shortlisted Functions (6 to 10 Decision Paths)
1. **Function 1:** `OrderChangeManager._check_quotas`
   - *Module:* `pretix/base/services/orders.py` (Line 2285)
   - *Cyclomatic Complexity (CCN):* **8** (Rank B)
   - *Role in Workflows:* Evaluates quota availability for order positions during state mutations and changes.
2. **Function 2:** `QuotaAvailability._compute_early_outs`
   - *Module:* `pretix/base/services/quotas.py` (Line 493)
   - *Cyclomatic Complexity (CCN):* **6** (Rank B)
   - *Role in Workflows:* Enforces early-exit boundary conditions for quota availability calculations.

---

## 5. Spike 4: Mutation Tooling & Static Analysis Platform

### 5.1. Mutation Testing Evaluation (`mutmut`)
* **Tool Tested:** `mutmut` v3.8.1.
* **Finding:** When executed natively on Windows host Python, mutmut emitted:
  > *"To run mutmut on Windows, please use the WSL. Native windows support is tracked in issue boxed/mutmut#397"*
* **Mitigation Strategy (Project Risk PR-1 Resolved):**
  - mutmut was installed and validated inside the Linux container (`pretix_web`) where it executed cleanly (`python3 -m mutmut, version 3.8.1`).
  - In GitHub Actions CI, tests and mutation analysis run on Ubuntu runners (`ubuntu-latest`), bypassing host OS limitations completely.
* **Configuration:** Dedicated `setup.cfg` initialized pointing to `upstream/pretix/base/services/quotas.py`.

### 5.2. Static Analysis Platform (`SonarCloud`)
* Configuration file **[sonar-project.properties](file:///c:/Users/USER/Desktop/sqe_project/sonar-project.properties)** created.
* Integrated to measure: Cyclomatic Complexity, Code Smells, Bugs, Vulnerabilities, Coverage %, Technical Debt.

---

## 6. Spike 5: End-to-End UI & Performance Benchmarking

### 6.1. Playwright Browser Authentication Spike
* **Script:** `tests/team/e2e/spike_login.py` executed via Playwright Chromium.
* **Result:** Successfully loaded `/control/login`, filled credentials, submitted form, and asserted transition to `/control/` dashboard.
* **Evidence:** Screen capture saved at `reports/spikes/spike5_login_success.png`.

### 6.2. k6 Performance Baseline Run
* **Script:** `tests/team/perf/spike_load.js` executed with Grafana k6 OSS (1 VU, 60-second duration).
* **Target:** `GET /api/v1/organizers/sqe/events/sqe2026/quotas/1/availability/`
* **Results:** Target p95 response time and error rate verified against thresholds. Raw output exported to `reports/spikes/spike5_k6_summary.json`.

---

## 7. Gate 0 Evaluation & Sign-Off

| Gate 0 Requirement | Target Condition | Observed Outcome | Status |
| :--- | :--- | :--- | :---: |
| **Spike 1** | Local install, migrations, roles, seeded API records | PostgreSQL 16 migrated; 2 roles verified; records created. | **PASS** |
| **Spike 2** | Idempotent order creation, cancellation, quota readback | `X-Idempotency-Key` replayed; quota $8 \to 7 \to 8$. | **PASS** |
| **Spike 3** | Code measurement; 2 functions with CCN 6–10 | `_check_quotas` (8) & `_compute_early_outs` (6). | **PASS** |
| **Spike 4** | mutmut operational; Sonar configured | mutmut 3.8.1 verified in container; Sonar properties created. | **PASS** |
| **Spike 5** | Playwright login passes; k6 60s benchmark passes | Browser login verified; k6 run completed. | **PASS** |
| **Governance** | Repository initialized; AI prompt log started | Git `main` branch active; `docs/ai-use-record.md` started. | **PASS** |

**Final Gate 0 Decision:** **APPROVED TO PROCEED ON PRETEX.**  
Tag `gate-0` applied to Git repository.
