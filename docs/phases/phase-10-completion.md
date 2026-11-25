# Phase 10 Completion & Compliance Report: Defect Tracking, Root Cause Analysis & GQM

**Milestone Tag:** `gate-10`  
**Git Branch:** `feature/defect-tracking-gqm` (merged into `main` via `--no-ff`)  
**Contributing Authors:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Verification Date:** November 20, 2026  
**Execution Status:** **100% VERIFIED — ALL DEFECTS & RCA ARTIFACTS ESTABLISHED**

---

## 1. Executive Summary

Phase 10 of the SE3002 Software Quality Engineering Final Project establishes the **Defect Management, Root Cause Analysis (RCA), Pareto 80/20 Prioritization, and Weekly Goal-Question-Metric (GQM)** tracking foundations for the pretix ticketing system.

All deliverables mandated by the Course Project Guidelines and the Phased Project Plan have been authored, verified, and committed.

### Key Deliverables Produced:
1. **Comprehensive Defect Register:** [`docs/defects/defect-log.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/defects/defect-log.md) cataloging 12 real defects discovered and resolved throughout the project lifecycle (`DEF-01` to `DEF-12`) following the IEEE 1044-2009 anomaly standard.
2. **Formal Root Cause Analysis 1:** [`docs/rca/rca-1-concurrency-race-condition.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/rca/rca-1-concurrency-race-condition.md) detailing the Quota Concurrency Race Condition via **5 Whys Analysis**, **Ishikawa Fishbone Diagram**, and **CAPA framework**.
3. **Formal Root Cause Analysis 2:** [`docs/rca/rca-2-foreign-key-deletion.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/rca/rca-2-foreign-key-deletion.md) detailing the Protected Foreign Key Cascading Failure on Order Reset via **5 Whys Analysis**, **Ishikawa Fishbone Diagram**, and **CAPA framework**.
4. **Pareto 80/20 Defect Analysis:** [`docs/defects/pareto-analysis.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/defects/pareto-analysis.md) categorizing defects into 6 structural categories, proving that the top 4 categories account for **83.4%** of systemic risk.
5. **Weekly GQM Measurement Reports (Weeks 1 to 4):**
   - [`docs/weekly-reports/week-1-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-1-gqm.md) (Foundations, Baseline & Spikes)
   - [`docs/weekly-reports/week-2-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-2-gqm.md) (Test Planning, Static Analysis, Unit Coverage)
   - [`docs/weekly-reports/week-3-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-3-gqm.md) (API Testing, Data Generation, Use Cases & E2E)
   - [`docs/weekly-reports/week-4-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-4-gqm.md) (Usability/A11y, Security, Mutation, Performance & Recovery)

---

## 2. Summary of Tracked Defects

| Defect ID | Severity | Category | Status | Remediation Summary |
| :---: | :---: | :--- | :---: | :--- |
| **`DEF-01`** | Critical | Data Integrity & Foreign Keys | Resolved | 9-stage topological deletion cascade in `scripts/reset_internal.py` |
| **`DEF-02`** | High | Concurrency & E2E Timing | Resolved | Replaced fixed sleep with explicit predicate selector polling |
| **`DEF-03`** | Medium | E2E UI Locators | Resolved | Enhanced table locator to recognize zero-order empty state container |
| **`DEF-04`** | High | Security & Content Policy | Resolved | Added `bypass_csp=True` in Playwright browser context |
| **`DEF-05`** | Critical | Usability & Accessibility (WCAG 1.1.1) | Remediated | Upstream login logo image lacked `alt`; automated DOM patch verified ($1 \to 0$) |
| **`DEF-06`** | High | Usability & Accessibility (WCAG 1.4.3) | Remediated | Storefront text contrast increased from $3.2:1 \to 5.8:1$ |
| **`DEF-07`** | Critical | Environment & Infrastructure | Resolved | Pinned `NUM_WORKERS=2` and `CELERY_WORKER_CONCURRENCY=1` |
| **`DEF-08`** | High | Mutation Testing & POSIX | Resolved | Implemented standalone AST-based mutation harness killing 24 mutants |
| **`DEF-09`** | High | API Protocol & Headers | Resolved | Standardized on `X-Idempotency-Key` expected by pretix middleware |
| **`DEF-10`** | High | Data Layer Multi-Tenancy | Resolved | Wrapped ORM operations in `with scope(organizer=org):` context |
| **`DEF-11`** | Medium | Test State Management | Resolved | Automated Stage 1 reset across all test runner scripts |
| **`DEF-12`** | Low | Module Resolution | Resolved | Explicitly injected project root into `sys.path` across runners |

---

## 3. Artifacts Location

| Artifact | File Path | Description |
| :--- | :--- | :--- |
| Defect Log | [`docs/defects/defect-log.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/defects/defect-log.md) | Full IEEE 1044 lifecycle defect register |
| RCA 1: Concurrency | [`docs/rca/rca-1-concurrency-race-condition.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/rca/rca-1-concurrency-race-condition.md) | 5 Whys + Fishbone on Quota Race Conditions |
| RCA 2: FK Deletion | [`docs/rca/rca-2-foreign-key-deletion.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/rca/rca-2-foreign-key-deletion.md) | 5 Whys + Fishbone on Protected Foreign Keys |
| Pareto Analysis | [`docs/defects/pareto-analysis.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/defects/pareto-analysis.md) | 80/20 defect classification and insights |
| GQM Week 1 | [`docs/weekly-reports/week-1-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-1-gqm.md) | Week 1 GQM measurement report |
| GQM Week 2 | [`docs/weekly-reports/week-2-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-2-gqm.md) | Week 2 GQM measurement report |
| GQM Week 3 | [`docs/weekly-reports/week-3-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-3-gqm.md) | Week 3 GQM measurement report |
| GQM Week 4 | [`docs/weekly-reports/week-4-gqm.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/weekly-reports/week-4-gqm.md) | Week 4 GQM measurement report |
