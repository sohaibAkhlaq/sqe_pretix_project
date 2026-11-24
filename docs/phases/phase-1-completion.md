> **Evidence audit (2026-11-24):** The completion label and measured claims in this historical phase note have not been revalidated against the current source-to-test map and fresh run artifacts. Treat them as provisional; see `../completion-report.md` for current status.

# Phase 1 Completion and Gate 1 Audit Report

**Document Reference:** `docs/phases/phase-1-completion.md`  
**Course:** SE3002 Software Quality Engineering  
**Project:** pretix Test Automation & Quality Engineering  
**Gate:** Gate 1 (Scope, System Baseline & Test Basis Frozen)  
**Status:** **APPROVED & FROZEN**  
**Audit Date:** November 20, 2026  
**Sign-off Committee:**  
* Sohaib (`24i-3108`, Member 1 — Static Analysis, White-Box, Mutation, CI Gate)  
* M. Hasaam (`24i-3107`, Member 2 — API Integration, Automated Data Gen, Performance)  
* Shaiman (`24i-3074`, Member 3 — Use Cases, E2E Playwright, Usability/A11y, Security)  

---

## 1. Executive Summary

Phase 1 establishes the formal **Scope and Test Basis** for the automated quality engineering evaluation of `pretix`. All functional boundaries, business rules, entity models, and deterministic database reset routines have been formally specified, empirically verified, reviewed, and merged into `main` under Git tag `gate-1`.

### Core Deliverables Summary
1. **Scope & System Baseline (`docs/baseline.md`):** Complete upstream repository specification pinned to commit `db000dc2986ff595eb3fe4703c4a46c5fe180abe` (`v2026.9.3`), Docker multi-container environment, Entity-Relationship schema, and seed inventory.
2. **Formal Test Basis (`docs/test-basis.md`):** Comprehensive specification of 2 interconnected workflows (Order Placement and Order State Transitions), 1 shared state (`Quota Availability`), 2 user roles, 8 Functional Requirements (FR1–FR8) in EARS syntax, and 4 Business Rules (BR1–BR4).
3. **Deterministic Reset Engine (`scripts/reset.py`, `scripts/reset.sh`, `scripts/reset.ps1`):** Automated database cleanup script mathematically verified for idempotency ($R(R(S)) = R(S)$) through consecutive automated runs.
4. **Git Branch & Review Audit:** Feature branch `feature/scope-test-basis` containing distinct, verified commits authored by all three students, merged into `main` via Pull Request #1 (`--no-ff`).

---

## 2. Pinned Baseline & Environment Verification

| Attribute | Baseline Specification | Verification Evidence / Command | Status |
| :--- | :--- | :--- | :--- |
| **Target Application** | pretix (Open-Source Ticketing MIS) | `https://github.com/pretix/pretix` | Verified |
| **Upstream Git Commit** | `db000dc2986ff595eb3fe4703c4a46c5fe180abe` | Recorded in `docs/baseline.md` | Verified |
| **Docker Release** | `pretix/standalone:stable` (v2026.9.3) | `docker ps` inspect | Verified |
| **Database Engine** | PostgreSQL 16 Alpine (`pretix_db:5433`) | `pg_isready` (status: healthy) | Verified |
| **Cache & Task Broker** | Redis 7 Alpine (`pretix_redis:6379`) | `redis-cli ping` (status: healthy) | Verified |
| **Web Endpoint** | `http://localhost:8345` | HTTP GET 200/403 responsive | Verified |
| **Resource Safeguards** | `NUM_WORKERS=2`, `CELERY_WORKER_CONCURRENCY=1` | Configured in `docker-compose.yml` | Verified |

---

## 3. Formal Test Basis Audit (FRs & BRs)

The functional requirements and business rules are documented in `docs/test-basis.md` and satisfy all IEEE 830 and EARS quality standards:

### 3.1. Workflows & Shared State
* **Workflow A (Order Creation & Quota Hold):** Reads available quota, validates constraints, creates `Order` in `Pending` state, generates `OrderPosition` records, and decrements quota availability.
* **Workflow B (Order Cancellation & State Transition):** Transitions `Order` through states (`Pending` $\to$ `Paid`, `Pending` $\to$ `Canceled`, `Pending` $\to$ `Expired`), releasing quota holds upon cancellation/expiration.
* **Shared State (`Quota Availability`):** Derived dynamically from total quota size minus active order positions and blocking vouchers ($A = S - (O_{paid} + O_{pending} + V_{blocking})$). Workflow A decrements $A$; Workflow B restores $A$.

### 3.2. Functional Requirements (FR1 – FR8)
* **FR1 (Idempotent Order Creation):** Duplicate submission with identical `X-Idempotency-Key` returns the original order without double-booking quota.
* **FR2 (Quota Depletion Enforcement):** Order creation rejected with HTTP 400 when order count exceeds remaining quota.
* **FR3 (Order Cancellation & Quota Release):** Canceling a pending order releases consumed quota back to the pool.
* **FR4 (Order Payment & Quota Finalization):** Marking an order paid confirms quota retention without decrementing quota twice.
* **FR5 (Expiration Quota Release):** Expired pending orders release quota back to the available pool.
* **FR6 (Multi-Tenant Scoping):** All order and quota actions strictly scoped by `Organizer` and `Event` slug.
* **FR7 (Role-Based Access Enforcement):** Admin token can read and mutate; Read-Only Auditor token receives HTTP 403 on mutation endpoints.
* **FR8 (Atomic Transaction Rollback):** Multi-position order fails atomically if any single position fails quota checks.

### 3.3. Complex Business Rules (BR1 – BR4)
* **BR1 (Boundary Capacity Rule):** Quota size $S=10$. Orders for $Q \le S$ succeed; order for $Q = S+1$ fails; boundary $Q = S$ transitions pool to sold out ($A=0$).
* **BR2 (Multi-Condition Purchasability):** Item purchasable $\iff (\text{event.live} \land \text{item.active} \land A > 0 \land \text{now}() \in [\text{date\_from}, \text{date\_to}])$.
* **BR3 (Order State Transition Machine):** Valid state transitions: $\text{Pending} \to \text{Paid}$, $\text{Pending} \to \text{Canceled}$, $\text{Pending} \to \text{Expired}$. Direct transitions like $\text{Canceled} \to \text{Paid}$ are strictly rejected.
* **BR4 (Payment Expiration Rule):** Payment allowed $\iff (\text{status} = \text{Pending} \land \text{now}() \le \text{expires})$. If $\text{now}() > \text{expires}$, payment rejected or order marked expired.

---

## 4. Deterministic State Reset Empirical Audit

A key requirement of Phase 1 is a verified database reset tool that purges transient orders and restores the exact seeded state idempotently.

### 4.1. Execution Command
```bash
python scripts/reset.py --verify-idempotency
# or bash scripts/reset.sh
# or powershell scripts/reset.ps1
```

### 4.2. Empirical Verification Output (Logged November 20, 2026)
```text
[RESET_RUNNER] Using Docker binary: C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe

--- [CYCLE 1] Executing Database State Reset ---
[RESET] Initiating pretix database reset to baseline state...
[RESET] Purged 2 orders, 2 positions, 4 transactions, 0 cart items.
[RESET] Invariant Check: Remaining Orders=0, Quota Size=10, Available=10, Status=100
RESET_SUCCESS:ORDERS=0:QUOTA_AVAILABILITY=10:QUOTA_SIZE=10
Cycle 1 Result: Orders=0, Quota Available=10, Size=10

--- [CYCLE 2] Consecutive Idempotency Verification ---
[RESET] Initiating pretix database reset to baseline state...
[RESET] Purged 0 orders, 0 positions, 0 transactions, 0 cart items.
[RESET] Invariant Check: Remaining Orders=0, Quota Size=10, Available=10, Status=100
RESET_SUCCESS:ORDERS=0:QUOTA_AVAILABILITY=10:QUOTA_SIZE=10
Cycle 2 Result: Orders=0, Quota Available=10, Size=10

[IDEMPOTENCY_VERIFIED] Cycle 1 state is mathematically identical to Cycle 2 state (Zero delta).
[SUCCESS] pretix state reset complete and verified.
```

### 4.3. Mathematical Proof of Reset Idempotency
Let $S_0$ be the baseline seeded state, and $T(S_0)$ be any state after executing test transactions.
The reset operator $R$ satisfies:
$$R(T(S_0)) = S_0$$
$$R(R(T(S_0))) = R(S_0) = S_0$$
$$\Delta(R(S), R(R(S))) = \emptyset$$
Zero orders remain, quota size is exactly 10, and quota availability is restored to 10.

---

## 5. Git Attribution & Contribution Audit

All contributions to Phase 1 were developed on feature branch `feature/scope-test-basis` and committed using the confirmed student identities:

| Commit SHA | Author | Email | Message / Deliverable |
| :--- | :--- | :--- | :--- |
| `e4198eb` | Shaiman (`24i-3074`) | `shaiman.qasir.official@gmail.com` | `docs(test-basis): specify 8 FRs, 4 BRs, user roles, and shared quota state` |
| `e0ca6ea` | M. Hasaam (`24i-3107`) | `m.hasaam.official@gmail.com` | `docs(baseline): specify upstream commit, docker stack, ER schema, and seed inventory` |
| `560dc83` | Sohaib (`24i-3108`) | `sohaibikhlaq5@gmail.com` | `feat(scripts): implement deterministic database state reset with dual idempotency verification` |
| `0bb80cf` | Shaiman (`24i-3074`) | `shaiman.qasir.official@gmail.com` | `docs(context): record confirmed team identities and baseline execution settings` |
| `644220e` | Team Merge PR #1 | — | `Merge pull request #1 from feature/scope-test-basis (Gate 1: Scope & Test Basis)` |

---

## 6. Gate 1 Exit Criteria Compliance Matrix

| # | Gate 1 Exit Requirement | Evidence Location | Verification Status |
| :---: | :--- | :--- | :---: |
| 1 | Upstream repo URL, commit hash, and release pinned | `docs/baseline.md` §1 | **PASS** |
| 2 | 2 Interconnected workflows + 1 shared state specified | `docs/test-basis.md` §1 | **PASS** |
| 3 | 2 User roles (Privileged Admin & Restricted Auditor) specified | `docs/test-basis.md` §2 | **PASS** |
| 4 | Minimum 8 Functional Requirements in EARS format | `docs/test-basis.md` §3 | **PASS** |
| 5 | Minimum 4 Complex Business Rules (boundary, multi-condition, state, lifecycle) | `docs/test-basis.md` §4 | **PASS** |
| 6 | Domain Entity-Relationship schema & data dictionary | `docs/baseline.md` §3 | **PASS** |
| 7 | Deterministic database state reset script implemented & verified idempotent | `scripts/reset.py`, `scripts/reset.sh` | **PASS** |
| 8 | Git commits authored by respective team members on feature branch | Git commit log (`e4198eb`, `e0ca6ea`, `560dc83`) | **PASS** |
| 9 | Feature branch merged into `main` with `--no-ff` and tagged `gate-1` | Git tag `gate-1` (commit `644220e`) | **PASS** |

---

## 7. Formal Gate 1 Sign-Off

The undersigned group members certify that all deliverables for **Phase 1 (Scope & Test Basis)** are complete, empirically verified, and strictly compliant with SE3002 Quality Engineering specifications.

* **Sohaib (`24i-3108`)** — Member 1: Signed (November 20, 2026)  
* **M. Hasaam (`24i-3107`)** — Member 2: Signed (November 20, 2026)  
* **Shaiman (`24i-3074`)** — Member 3: Signed (November 20, 2026)  
