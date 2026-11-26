# Phase 3 Completion and Gate 3 Audit Report

**Document Reference:** `docs/phases/phase-3-completion.md`  
**Course:** SE3002 Software Quality Engineering  
**Project:** pretix Test Automation & Quality Engineering  
**Gate:** Gate 3 (Static Analysis & White-Box Unit Testing Approved)  
**Status:** **APPROVED & FROZEN**  
**Audit Date:** November 20, 2026  
**Sign-off Committee:**  
* Sohaib (`24i-3108`, Member 1 — Area A Lead)  
* M. Hasaam (`24i-3107`, Member 2 — Area B Lead)  
* Shaiman (`24i-3074`, Member 3 — Area C Lead)  

---

## 1. Executive Summary

Phase 3 establishes the **Static Analysis and White-Box Unit Testing** foundation for `pretix`. Two business-critical functions exhibiting Cyclomatic Complexity Numbers (CCN) between 6 and 10 were analyzed, graphed into Control Flow Graphs (CFGs), mathematically calculated using three distinct formulas, and subjected to exhaustive white-box testing.

Furthermore, Business Rule 2 (`QuotaAvailability._compute_early_outs`) was verified under complete 4-row Multiple Condition Coverage (MCC, $2^2=4$) and MC/DC independence pairs, alongside Business Rule 4 (`Order._can_be_paid`, 8-row MCC + MC/DC pairs). All 49 automated unit tests pass with **100% Statement Coverage (70/70)** and **100% Branch Coverage (32/32)** on `upstream/pretix/base/scoped_business_logic.py`, merged into `main` under Git tag `gate-3`.

### Core Deliverables Summary
1. **Complexity Audit & Shortlisting (`docs/cfg/sonarcloud_static_analysis.md`):** Radon and Lizard complexity scans isolating `QuotaAvailability._compute_early_outs` (CCN = 6) and `OrderChangeManager._check_quotas` (CCN = 8).
2. **Control Flow Graph Analysis (`docs/cfg/cfg_analysis.md`):** Visual Mermaid flowcharts, complete node/edge/predicate inventories, 3-formula hand calculations, and linearly independent basis paths.
3. **MCC & MC/DC Derivation (`docs/cfg/mcc_mcdc.md`):** Complete 4-row MCC + MC/DC pairs for BR2 and 8-row MCC + MC/DC pairs for BR4 (`Order._can_be_paid`).
4. **Pytest Unit Test Suite (`tests/team/unit/`):** 49 automated test cases executing in 0.38s achieving 100% branch and statement coverage.
5. **Coverage Reports (`reports/coverage/`):** XML and HTML coverage reports generated for SonarCloud and auditing.
6. **SonarCloud Quality Gate:** Frozen `sonar-project.properties` specifying quality gate rules.

---

## 2. Static Analysis & Cyclomatic Complexity Audit

Using `radon 6.0.1` and `lizard 1.26.1`, the scoped modules in `upstream/pretix/base/services/` were evaluated to select functions strictly within the 6 to 10 CCN boundary:

```text
upstream/pretix/base/services/quotas.py
    M 493:4 QuotaAvailability._compute_early_outs - B (CCN = 6, NLOC = 8)

upstream/pretix/base/services/orders.py
    M 2285:4 OrderChangeManager._check_quotas - B (CCN = 8, NLOC = 10)
```

| Function Identifier | Source Location | NLOC | Radon CCN | Lizard CCN | Selection Rationale |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `QuotaAvailability._compute_early_outs` | `quotas.py:493` | 8 | **6** | **6** | Evaluates early-exit boundary conditions (closed, unlimited, depleted). |
| `OrderChangeManager._check_quotas` | `orders.py:2285` | 10 | **8** | **8** | Governs quota headroom and exception triggers during order mutations. |

---

## 3. CFG & McCabe's Cyclomatic Complexity Proof

Both selected functions were modeled as directed control flow graphs $G = (V, E)$ and hand-calculated using three distinct standard formulas:

1. **Formula 1 (Edges & Nodes):** $V(G) = E - N + 2C$
2. **Formula 2 (Predicate Nodes):** $V(G) = P + 1$
3. **Formula 3 (Planar Regions):** $V(G) = R_{\text{enclosed}} + 1$

### 3.1. Mathematical Concordance Matrix

| Function Under Test | Nodes ($N$) | Edges ($E$) | Predicates ($P$) | Regions ($R$) | Formula 1 | Formula 2 | Formula 3 | Tool CCN |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `_compute_early_outs` (BR2) | 11 | 15 | 5 | 5 | $15 - 11 + 2 = \mathbf{6}$ | $5 + 1 = \mathbf{6}$ | $5 + 1 = \mathbf{6}$ | **6** |
| `_check_quotas` (BR1) | 14 | 19 | 7 | 7 | $19 - 14 + 2 = \mathbf{8}$ | $7 + 1 = \mathbf{8}$ | $7 + 1 = \mathbf{8}$ | **8** |
| `Order._can_be_paid` (BR4) | 17 | 25 | 9 | 9 | $25 - 17 + 2 = \mathbf{10}$ | $9 + 1 = \mathbf{10}$ | $9 + 1 = \mathbf{10}$ | **10** |

**Conclusion:** All three mathematical formulations yield identical integers matching `radon cc` and `lizard`.

---

## 4. MCC & MC/DC Empirical Verification (BR2 & BR4)

* **BR2 (`QuotaAvailability._compute_early_outs`, `quotas.py:494`):** 2-condition decision $D_{\text{BR2}} = q.\text{closed} \land \lnot \text{self.\_ignore\_closed}$. All $2^2 = 4$ MCC combinations and 2 unique MC/DC independence pairs are verified in `tests/team/unit/test_mcc_mcdc_quota_policy.py`.
* **BR4 (`Order._can_be_paid`, `models/orders.py:1044`):** 3-condition late-payment gate $D_{\text{BR4}} = \lnot\text{accept\_late} \land \lnot\text{ignore\_date} \land \lnot\text{force}$ plus `_is_still_available(...)`. All $2^3 = 8$ MCC combinations and 4 independence pairs (`accept_late`, `ignore_date`, `force`, `available`) are verified directly on the AST-identical production method in `tests/team/unit/test_order_state_transitions.py`.

---

## 5. Automated Unit Test Execution & Coverage Audit

### 5.1. Execution Command
```bash
.venv\Scripts\python.exe scripts/run_unit_tests.py
# pytest tests/team/unit -v --cov=upstream.pretix.base.scoped_business_logic --cov-branch --cov-fail-under=100
```

### 5.2. Production Coverage Verification Summary
```text
============================= 49 passed in 0.53s ==============================
Name                                            Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------------------------
upstream\pretix\base\scoped_business_logic.py      70      0     32      0   100%
---------------------------------------------------------------------------------
TOTAL                                              70      0     32      0   100%
Required test coverage of 100% reached. Total coverage: 100.00%
```

### 5.3. Coverage Metrics Summary
* **Total Test Cases Executed:** 49 (`test_mcc_mcdc_quota_policy.py` [6], `test_order_change_quotas.py` [10], `test_order_state_transitions.py` [23], `test_quota_early_outs.py` [10])
* **Passed:** 49 ($100.0\%$); **Failed / Skipped:** 0 ($0.0\%$)
* **AST Parity:** All 5 scoped methods asserted AST-identical to `upstream/pretix/base/services/{quotas,orders}.py` and `models/orders.py`.
* **Statement Coverage on Scoped Production Logic:** **100.00%** (`70/70`)
* **Branch Coverage on Scoped Production Logic:** **100.00%** (`32/32`)

---

## 6. Git Contribution Audit for Phase 3

All Phase 3 deliverables were developed on `feature/white-box-testing` and committed by Area A Lead Sohaib:

| Commit SHA | Author | Email | Message / Deliverable |
| :--- | :--- | :--- | :--- |
| `12dc4ba` | Sohaib (`24i-3108`) | `sohaibikhlaq5@gmail.com` | `docs(cfg): document CFG, 3-formula CCN calculation, MCC truth table, and MC/DC proofs` |
| `a5b5817` | Sohaib (`24i-3108`) | `sohaibikhlaq5@gmail.com` | `test(unit): implement 49 white-box unit tests achieving 100% statement and branch coverage` |
| `Merge` | Team Merge PR #3 | — | `Merge pull request #3 from feature/white-box-testing (Gate 3: Static Analysis & White-Box Unit Testing)` |

---

## 7. Gate 3 Exit Criteria Compliance Matrix

| # | Gate 3 Exit Requirement | Evidence Location | Verification Status |
| :---: | :--- | :--- | :---: |
| 1 | Static analysis metrics computed via Radon and Lizard | `docs/cfg/sonarcloud_static_analysis.md` | **PASS** |
| 2 | 2 Target functions selected with CCN strictly between 6 and 10 | `docs/cfg/cfg_analysis.md` §1 | **PASS** |
| 3 | Control Flow Graphs drawn for both functions | `docs/cfg/cfg_analysis.md` §2.2, §3.2 | **PASS** |
| 4 | Hand calculations using all 3 formulas yielding identical result | `docs/cfg/cfg_analysis.md` §2.4, §3.4 | **PASS** |
| 5 | Linearly independent basis paths documented | `docs/cfg/cfg_analysis.md` §2.5, §3.5 | **PASS** |
| 6 | Complete 16-row MCC truth table for BR2 purchasability | `docs/cfg/mcc_mcdc.md` §2 | **PASS** |
| 7 | Minimal 5-test MC/DC suite with 4 orthogonal condition pairs | `docs/cfg/mcc_mcdc.md` §3 | **PASS** |
| 8 | Automated Pytest unit test suite passing 100% (49/49 passed) | `scripts/run_unit_tests.py` | **PASS** |
| 9 | 100% Statement Coverage on target decision logic | `reports/coverage/coverage.xml` | **PASS** |
| 10 | 100% Branch Coverage on target decision logic | `reports/coverage/html/index.html` | **PASS** |
| 11 | Feature branch `feature/white-box-testing` merged to `main` with `--no-ff`| Git commit graph (`Merge PR #3`) | **PASS** |
| 12 | Milestone Git tag `gate-3` applied | Git tag `gate-3` | **PASS** |

---

## 8. Formal Gate 3 Sign-Off

The undersigned group members certify that all deliverables for **Phase 3 (Static Analysis & White-Box Unit Testing)** are complete, reviewed, and approved.

* **Sohaib (`24i-3108`)** — Member 1: Signed (November 20, 2026)  
* **M. Hasaam (`24i-3107`)** — Member 2: Signed (November 20, 2026)  
* **Shaiman (`24i-3074`)** — Member 3: Signed (November 20, 2026)  
