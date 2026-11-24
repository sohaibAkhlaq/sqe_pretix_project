# Weekly Quality Report (Week 1) - Goal-Question-Metric (GQM) Framework

**Project:** SE3002 Software Quality Engineering - pretix Test Automation  
**Reporting Period:** Week 1 (Environment Setup, Spikes & Baseline Ingestion)  
**Authors:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Milestones Covered:** Gate 0 (`gate-0`), Gate 1 (`gate-1`)

---

## 1. GQM Hierarchy Definition

```mermaid
flowchart TD
    G1["Goal 1: Establish Reproducible Local Environment"]
    G2["Goal 2: Formulate Rigorous Test Basis & State Reset"]

    Q1_1["Q1.1: Can all containers boot and communicate locally?"]
    Q1_2["Q1.2: Can all tools execute without remote dependencies?"]
    Q2_1["Q2.1: Is test state reset 100% deterministic and idempotent?"]
    Q2_2["Q2.2: Are requirements mapped to EARS and business rules?"]

    M1_1["M1.1: Docker uptime & health check status (100%)"]
    M1_2["M1.2: 5 Spike scripts executed successfully (5/5)"]
    M2_1["M2.1: Idempotency metric R(R(S)) == R(S) (0 diff)"]
    M2_2["M2.2: 8 FRs, 4 BRs, 2 Roles, 1 Shared State documented"]

    G1 --> Q1_1 --> M1_1
    G1 --> Q1_2 --> M1_2
    G2 --> Q2_1 --> M2_1
    G2 --> Q2_2 --> M2_2
```

---

## 2. Weekly Metric Tracking

| Goal | Question | Metric | Target | Measured Reality | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **G1: Environment** | Q1.1: Stack Health | Container availability (`pretix_web`, `db`, `redis`) | 100% | 100% healthy | **PASS** |
| **G1: Environment** | Q1.2: Feasibility | Execution of 5 Phase 0 spikes | 5/5 | 5/5 passed | **PASS** |
| **G2: Test Basis** | Q2.1: Reset Determinism | Mathematical idempotence $R(R(S)) = R(S)$ | True | Proven ($Q=10, O=0$) | **PASS** |
| **G2: Test Basis** | Q2.2: Requirements | EARS Functional Requirements count | $\ge 8$ | 8 FRs, 4 BRs | **PASS** |

---

## 3. Engineering Discoveries & Corrective Decisions
* **Gunicorn Multiplication (DEF-07):** Pinned `NUM_WORKERS=2` and `CELERY_WORKER_CONCURRENCY=1` to prevent host memory exhaustion.
* **Protected Foreign Key Constraint (DEF-01):** Engineered 9-stage topological deletion cascade to prevent `ProtectedError` during resets.
## Common GQM metric definitions and audit status

These definitions apply consistently to every weekly report:

- **Defect density** = count of distinct confirmed defects first detected in the reporting period divided by the declared size unit (use KLOC only when the counted source-code scope and line-count tool are recorded). Record numerator, denominator, severity mix, and period; do not mix test failures with confirmed defects.
- **Requirements coverage** = count of canonical FR/BR IDs with at least one executed, passing test and linked raw result divided by the total canonical FR/BR IDs in `docs/test-basis.md`. Planned or merely named test cases do not count as covered.
- **Defect reopen rate** = defects reopened during the period divided by defects closed during the same period; report `N/A` when the denominator is zero and disclose the time window.

Previously printed weekly PASS values were not recalculated against these definitions and remain provisional. Actual values require a reconciled defect log, canonical requirements inventory, and run-level test evidence; see `docs/completion-report.md`.
