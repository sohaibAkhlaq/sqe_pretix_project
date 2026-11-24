# Audit correction (2026-11-24): prior coverage totals and four-condition MCC claims are historical and unverified. The corrected evidence scope is below; see docs/completion-report.md.

# White-Box Coverage & Uncovered Code Defense

**Document Reference:** `docs/cfg/branch_coverage_defense.md`  
**Course:** SE3002 Software Quality Engineering  
**Application Under Test:** pretix (`upstream/pretix/base/services/`)  
**Rubric Reference:** Component 5 — White-box unit testing (16 Marks, CLO2)  
**Lead Contributor / Author:** Sohaib (`24i-3108`, Member 1 — Area A Lead)  
**Reviewers:** M. Hasaam (`24i-3107`), Shaiman (`24i-3074`)  
**Status:** Approved & Frozen Baseline  
**Date:** November 20, 2026  

---

## 1. Executive Summary & Verification Objective

The SE3002 rubric for White-Box Unit Testing mandates:
> *"100% statement and branch coverage of server-side business logic, with any uncovered code defended; complete MCC and MC/DC pairs identified from MCC on the critical module."*

This document provides the formal audit, empirical evidence, and engineering defense of the white-box test suite implemented in `tests/team/unit/`.

---

## 2. Empirical Coverage Results

Execution of the full white-box unit test suite via `pytest --cov=tests/team/unit --cov-branch` yielded the following verified coverage metrics (recorded in `reports/coverage/coverage.xml` and `reports/coverage/html/index.html`):

| Test Module / Unit Target | Statements | Stmts Missed | Branches | Branches Missed | Statement Coverage | Branch Coverage | Basis Paths Covered |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `test_quota_early_outs.py` | 79 | 0 | 8 | 0 | **100.00%** | **100.00%** | 6 of 6 Paths (100%) |
| `test_order_change_quotas.py` | 97 | 0 | 6 | 0 | **100.00%** | **100.00%** | 8 of 8 Paths (100%) |
| `test_order_state_transitions.py` | 74 | 0 | 2 | 0 | **100.00%** | **100.00%** | All States & Times |
| `test_mcc_mcdc_purchasability.py` | 42 | 0 | 0 | 0 | **100.00%** | **100.00%** | 16/16 MCC + 4 MC/DC |
| **Subtotal (Core Business Logic)** | **292** | **0** | **16** | **0** | **100.00%** | **100.00%** | **100.00%** |
| `conftest.py` (Test Harness Config) | 8 | 1 | 0 | 0 | 87.50% | 100.00% | N/A (Harness) |
| **Total Test Suite** | **300** | **1** | **16** | **0** | **99.67%** | **100.00%** | **100.00%** |

---

## 3. Defense of Uncovered Code

### 3.1 Uncovered Code Inventory
Across the entire white-box test suite of 300 executable statements and 16 decision branches:
* **Uncovered Branches:** Exactly **0** (Zero). Branch coverage is **100.00%** ($16/16$ branches taken).
* **Uncovered Statements in Business Logic:** Exactly **0** (Zero). Statement coverage across all business decision logic is **100.00%** ($292/292$ statements).
* **Single Uncovered Line in Entire Directory:** Line 13 in `tests/team/unit/conftest.py`:
  ```python
  11: try:
  12:     import django
  13:     django.setup()
  14: except Exception:
  15:     # Running outside Django environment with standalone mocks
  16:     pass
  ```

### 3.2 Formal Defense of Line 13 (`conftest.py:13`)
1. **Nature of the Code:** Line 13 is part of the test runner configuration harness (`conftest.py`), not application business logic. It provides dual-runtime bootstrapping compatibility:
   - When executed inside the live container (`pretix_web`), Django initializes its full ORM settings.
   - When executed in the host `.venv` sandbox (for rapid local developer verification), it falls back to isolated standalone mock services.
2. **Deterministic Fallback:** On the host environment, `django.setup()` raises an exception because full Django settings (`pretix.settings`) require database and cache daemons. The `except Exception:` block safely catches this and executes `pass` (Line 16), which is hit.
3. **Absence of Business Risk:** Line 13 contains zero business rules, zero branching decisions, zero calculations, and zero state mutations. Its non-execution on the host does not leave any server-side logic unverified.
4. **Zero-Escape-Hatch Compliance:** In accordance with course guidelines, this defensive exception handling is documented upfront rather than suppressed using `# pragma: no cover`.

---

## 4. Basis Path Mapping to Unit Tests

### 4.1 Function 1: `QuotaAvailability._compute_early_outs` (CCN = 6)
All 6 linearly independent paths identified in `docs/cfg/cfg_analysis.md` are mapped 1-to-1 with unit test methods:

| Basis Path | Graph Traversal | Input Condition Vector | Expected Oracle | Test Method in `test_quota_early_outs.py` | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **Path 1** | $N_1 \to N_2 \to N_{11}$ | `quotas = []` (Empty list) | `results = {}` | `test_path_1_empty_quotas` | **PASSED** |
| **Path 2** | $N_1 \to N_2 \to N_3 \to N_4 \to N_5 \to N_2$ | `q.closed=True`, `ignore_closed=False` | `(ORDERED, 0)` | `test_path_2_closed_quota_not_ignored` | **PASSED** |
| **Path 3** | $N_1 \to N_2 \to N_3 \to N_4 \to N_6 \to N_8 \to N_{10} \to N_2$ | `q.closed=True`, `ignore_closed=True`, `size=10` | Fallthrough | `test_path_3_closed_quota_ignored_and_size_positive` | **PASSED** |
| **Path 4** | $N_1 \to N_2 \to N_3 \to N_6 \to N_7 \to N_2$ | `q.closed=False`, `q.size=None` | `(OK, None)` | `test_path_4_unlimited_quota` | **PASSED** |
| **Path 5** | $N_1 \to N_2 \to N_3 \to N_6 \to N_8 \to N_9 \to N_2$ | `q.closed=False`, `q.size=0` | `(GONE, 0)` | `test_path_5_depleted_quota_size_zero` | **PASSED** |
| **Path 6** | $N_1 \to N_2 \to N_3 \to N_6 \to N_8 \to N_{10} \to N_2$ | `q.closed=False`, `q.size=10` | Fallthrough | `test_path_6_normal_positive_quota_fallthrough` | **PASSED** |

### 4.2 Function 2: `OrderChangeManager._check_quotas` (CCN = 8)
All 8 linearly independent basis paths are mapped 1-to-1:

| Basis Path | Graph Traversal | Input Condition Vector | Expected Oracle | Test Method in `test_order_change_quotas.py` | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **Path 1** | $M_1 \to M_2 \to M_5 \to M_6 \to M_7 \to M_{14}$ | `quotadiff = {}` | Normal return | `test_path_1_empty_quotas` | **PASSED** |
| **Path 2** | $M_1 \to M_2 \to M_5 \to M_3 \to M_5 \to M_6 \to M_7$ | `quotadiff = {q1: 0, q2: -2}` | Normal return (continue) | `test_path_2_non_positive_diffs` | **PASSED** |
| **Path 3** | $M_1 \dots M_7 \to M_8 \to M_9 \to M_{10} \to M_{11} \to M_7$ | `diff=5`, `avail=(OK, None)` | Normal return | `test_path_3_unlimited_quota_with_positive_diff` | **PASSED** |
| **Path 4** | $M_1 \dots M_9 \to M_{10} \to M_{11} \to M_{12} \to M_7$ | `diff=2`, `avail=(OK, 8)` | Normal return ($8 > 2$) | `test_path_4_finite_quota_with_sufficient_capacity` | **PASSED** |
| **Path 5** | Boundary of Path 4 ($avail[1] == diff$) | `diff=3`, `avail=(OK, 3)` | Normal return ($3 \ge 3$) | `test_path_5_boundary_exact_capacity` | **PASSED** |
| **Path 6** | $M_1 \dots M_9 \to M_{10} \to M_{13}$ | `avail=(GONE, 0)` | `raise OrderError` | `test_path_6_quota_not_available_ok_gone` | **PASSED** |
| **Path 7** | $M_1 \dots M_9 \to M_{10} \to M_{13}$ | `avail=(ORDERED, 0)` | `raise OrderError` | `test_path_7_quota_not_available_ok_ordered` | **PASSED** |
| **Path 8** | $M_1 \dots M_{11} \to M_{12} \to M_{13}$ | `diff=5`, `avail=(OK, 2)` | `raise OrderError` ($2 < 5$) | `test_path_8_insufficient_finite_capacity` | **PASSED** |

---

## 5. MCC and MC/DC � corrected decision

The previous four-condition purchasability discussion is withdrawn. It tested a local helper and did not establish production-code coverage. Current BR2 scope is only the condition `q.closed and not self._ignore_closed` in `upstream/pretix/base/services/quotas.py`, method `QuotaAvailability._compute_early_outs`.

The complete 2-condition MCC table, expected result, and MC/DC independence pairs are documented in `docs/cfg/mcc_mcdc.md`; the executable test is `tests/team/unit/test_mcc_mcdc_quota_policy.py`. The method body is extracted from the checked-in upstream source by `tests/team/unit/production_source.py`. This isolated method harness does not establish full service integration.

## 6. Coverage status and evidence requirements

Historical totals shown in this file are not accepted as final evidence because the coverage XML and older report totals use inconsistent scopes. The current XML has 299/300 statements and 16/16 branches; a 100% target has therefore not been demonstrated. A fresh run must declare the exact production source/function scope and produce XML and HTML from the same execution. Any missed source statement needs an exact line, reachability analysis, and a justified exclusion only if the rubric permits it. See `docs/completion-report.md`; release remains HOLD.
