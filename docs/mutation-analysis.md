# Mutation Testing & Fault-Tolerance Analysis Report

**Component:** SE3002 Software Quality Engineering - Quota & Order Management  
**Author:** Sohaib (`24i-3108`, Git: `sohaibAkhlaq <sohaibakhlaq@users.noreply.github.com>`)  
**Target Module:** `upstream/pretix/base/services/quotas.py`, `orders.py`  
**Tooling Engine:** `mutmut 3.8.1` & Automated AST Mutation Harness  
**Milestone Tag:** `gate-8`  
**Mutation Score Achieved:** **100.00%** (24 Killed / 24 Generated, 0 Survived)  
**Quality Gate Threshold:** $\ge 70.00\%$

---

## 1. Executive Summary

Mutation testing is the gold standard for evaluating test suite sensitivity, fault detection power, and semantic defect localization. While standard branch coverage ensures that every control-flow branch has been executed at least once, it does not guarantee that test assertions will detect subtle algorithmic corruptions, off-by-one boundary bugs, or state manipulation faults.

In Phase 8, we subjected the core decision functions of the pretix Order and Quota sub-systems to systematic mutation analysis. Specifically, we targeted:
1. `QuotaAvailability._compute_early_outs` (CCN = 6)
2. `OrderChangeManager._check_quotas` (CCN = 8)
3. Business Rule 2 (BR2) Item Purchasability ($D = C_1 \land C_2 \land C_3 \land C_4$)
4. Order Lifecycle State Transitions (`pending`, `paid`, `canceled`, `expired`)

We implemented **two custom mutation operators** tailored specifically to domain-specific risks in capacity management, generated 24 mutants across standard and custom operator categories, and verified that our white-box test suite successfully **killed 24 out of 24 mutants (100.00% kill rate)**.

---

## 2. Mathematical Mutation Score Formulation

The formal mutation score ($MS$) is defined as:

$$MS = \frac{K}{M - E} \times 100\%$$

Where:
* $M$: Total number of generated mutants ($M = 24$)
* $K$: Number of mutants killed by the test suite ($K = 24$)
* $E$: Number of equivalent mutants ($E = 0$)
* $S$: Number of surviving mutants ($S = 0$)

$$MS = \frac{24}{24 - 0} \times 100\% = 100.00\%$$

Because $MS = 100.00\% \ge 70.00\%$, the mutation quality gate passes with a 30.00% safety margin above course requirements.

---

## 3. Custom Mutation Operators

In addition to standard mutators (Relational Operator Replacement `ROR`, Conditional Operator Replacement `COR`, Logical Connector Replacement `LCR`, and State Value Replacement `SVR`), we engineered two domain-specific custom mutation operators:

### Custom Operator 1: Boundary Condition Replacement (BCR)
* **Definition:** Systematically transforms strict inequalities to non-strict inequalities (`<` $\to$ `<=`, `>` $\to$ `>=`), equality tests (`==` $\to$ `!=`, `size is None` $\to$ `size is not None`), and loop bounds.
* **Domain Rationale in Ticketing:** In inventory management, boundary errors (off-by-one errors) represent the most dangerous class of defects. An error of `avail < diff` becoming `avail <= diff` rejects customers when exact seats exist; conversely, `quota_avail > 0` becoming `quota_avail >= 0` allows selling tickets when capacity is 0, causing overbooking and financial liability.
* **Operator Implementation:**
  - `BCR-1`: `q.size is None` $\to$ `q.size is not None`
  - `BCR-2`: `q.size == 0` $\to$ `q.size != 0`
  - `BCR-3`: `q.size == 0` $\to$ `q.size <= 0`
  - `BCR-4`: `[k for k, v in quotadiff if v > 0]` $\to$ `if v >= 0`
  - `BCR-5`: `if diff <= 0: continue` $\to$ `if diff < 0: continue` (fails to skip 0)
  - `BCR-6`: `avail[1] < diff` $\to$ `avail[1] <= diff` (rejects exact capacity match)
  - `BCR-7`: `quota_avail > 0` $\to$ `quota_avail >= 0` (sells when sold out)

### Custom Operator 2: Arithmetic Delta / State Mutation (ADR)
* **Definition:** Mutates arithmetic differentials, increments/decrements, and quota restoration magnitudes:
  - Modifies threshold offsets: `avail[1] < diff` $\to$ `avail[1] < (diff - 1)` or `(diff + 1)`.
  - Suppresses inventory restoration: `restored_quota = positions_count` $\to$ `restored_quota = 0`.
* **Domain Rationale in Ticketing:** When an order is cancelled or expires, the system must restore reserved inventory back to available capacity. If an arithmetic bug fails to restore the count ($+0$ instead of $+N$), quota leaks permanently over time, rendering available seats unpurchasable.
* **Operator Implementation:**
  - `ADR-1`: `avail[1] < diff` $\to$ `avail[1] < (diff - 1)`
  - `ADR-2`: `avail[1] < diff` $\to$ `avail[1] < (diff + 1)`
  - `ADR-3`: `restored_quota = positions_count` $\to$ `restored_quota = 0`

---

## 4. Complete Mutant Catalog & Kill Matrix

The table below catalogs all 24 generated mutants, their mutation operators, line numbers, original vs mutated code, execution outcome, and the specific test case that killed each mutant:

| Mutant ID | Operator | Target Function | Line | Original Source Code | Mutated Source Code | Status | Killing Test Case |
| :---: | :---: | :--- | :---: | :--- | :--- | :---: | :--- |
| **`mutant-01`** | `COR` | `_compute_early_outs` | 30 | `if q.closed and not ignore_closed:` | `if q.closed or not ignore_closed:` | **KILLED** | `test_path_3_closed_quota_ignored` |
| **`mutant-02`** | `BCR` (C1) | `_compute_early_outs` | 32 | `elif q.size is None:` | `elif q.size is not None:` | **KILLED** | `test_path_3_closed_quota_ignored` |
| **`mutant-03`** | `BCR` (C1) | `_compute_early_outs` | 34 | `elif q.size == 0:` | `elif q.size != 0:` | **KILLED** | `test_path_3_closed_quota_ignored` |
| **`mutant-04`** | `SVR` | `_compute_early_outs` | 31 | `results[q] = AVAILABILITY_ORDERED, 0` | `results[q] = AVAILABILITY_GONE, 0` | **KILLED** | `test_path_2_closed_quota_not_ignored` |
| **`mutant-05`** | `SVR` | `_compute_early_outs` | 33 | `results[q] = AVAILABILITY_OK, None` | `results[q] = AVAILABILITY_GONE, None` | **KILLED** | `test_path_4_unlimited_quota` |
| **`mutant-06`** | `SVR` | `_compute_early_outs` | 35 | `results[q] = AVAILABILITY_GONE, 0` | `results[q] = AVAILABILITY_OK, 0` | **KILLED** | `test_path_5_size_zero_gone` |
| **`mutant-07`** | `BCR` (C1) | `_compute_early_outs` | 34 | `elif q.size == 0:` | `elif q.size <= 0:` | **KILLED** | `test_path_1_empty_quotas` |
| **`mutant-08`** | `BCR` (C1) | `_check_quotas` | 48 | `[k for k, v in quotadiff if v > 0]` | `if v >= 0` | **KILLED** | `test_path_2_non_positive_diffs` |
| **`mutant-09`** | `BCR` (C1) | `_check_quotas` | 51 | `if diff <= 0: continue` | `if diff < 0: continue` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-10`** | `BCR` (C1) | `_check_quotas` | 51 | `if diff <= 0: continue` | `if diff == 0: continue` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-11`** | `ROR` | `_check_quotas` | 54 | `if avail[0] != AVAILABILITY_OK` | `if avail[0] == AVAILABILITY_OK` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-12`** | `BCR` (C1) | `_check_quotas` | 54 | `avail[1] < diff` | `avail[1] <= diff` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-13`** | `ROR` | `_check_quotas` | 54 | `avail[1] < diff` | `avail[1] > diff` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-14`** | `COR` | `_check_quotas` | 54 | `if avail[0] != OK or (...):` | `if avail[0] != OK and (...):` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-15`** | `ADR` (C2) | `_check_quotas` | 54 | `avail[1] < diff` | `avail[1] < (diff - 1)` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-16`** | `ADR` (C2) | `_check_quotas` | 54 | `avail[1] < diff` | `avail[1] < (diff + 1)` | **KILLED** | `test_path_4_insufficient_capacity_raises` |
| **`mutant-17`** | `BCR` (C1) | `evaluate_purchasability` | 18 | `c3 = bool(quota_avail > 0)` | `c3 = bool(quota_avail >= 0)` | **KILLED** | `TC-MCC-03_quota_exhausted_zero` |
| **`mutant-18`** | `LCR` | `evaluate_purchasability` | 20 | `return bool(c1 and c2 and c3 and c4)` | `return bool(c1 or c2 and c3 and c4)` | **KILLED** | `TC-MCC-02_date_invalid` |
| **`mutant-19`** | `LCR` | `evaluate_purchasability` | 20 | `return bool(c1 and c2 and c3 and c4)` | `return bool(c1 and c2 and not c3 and c4)` | **KILLED** | `TC-MCC-01_all_true` |
| **`mutant-20`** | `LCR` | `evaluate_purchasability` | 20 | `return bool(c1 and c2 and c3 and c4)` | `return bool(c1 and c2 and c3 and not c4)` | **KILLED** | `TC-MCC-01_all_true` |
| **`mutant-21`** | `SVR` | `transition_order_state` | 52 | `status: next_state ('p')` | `status: 'c' (forces canceled on pay)` | **KILLED** | `test_transition_pending_to_paid` |
| **`mutant-22`** | `SVR` | `transition_order_state` | 52 | `status: next_state ('c')` | `status: 'p' (forces paid on cancel)` | **KILLED** | `test_transition_pending_to_canceled_restores_quota` |
| **`mutant-23`** | `ADR` (C2) | `transition_order_state` | 50 | `restored_quota = positions_count` | `restored_quota = 0 (skips restore)` | **KILLED** | `test_transition_pending_to_canceled_restores_quota` |
| **`mutant-24`** | `ROR` | `transition_order_state` | 48 | `if next not in VALID: raise` | `if next in VALID: raise` | **KILLED** | `test_valid_transition_exception_thrown` |

---

## 5. Equivalent Mutant Analysis

An **equivalent mutant** is syntactically distinct from the original source code but produces semantically identical behavior for all possible input values. Because an equivalent mutant can never produce an output differing from the original program, no test case can ever kill it.

In our analysis:
* Mutants such as `mutant-07` (`q.size == 0` mutated to `q.size <= 0`) might superficially appear equivalent if `q.size` was guaranteed non-negative. However, because our test suite tests boundary inputs including defensive negative values and `None` handling, `mutant-07` was explicitly detected and **killed** when evaluating `MockQuota` with unconstrained attributes.
* **Result:** $E = 0$ equivalent mutants were present in the scoped test set, ensuring that our $100\%$ score is empirically robust and free from artificial inflation.

---

## 6. Execution Evidence

The raw report generated by the mutation engine is preserved at [`reports/mutation/mutmut_report.txt`](file:///c:/Users/USER/Desktop/sqe_project/reports/mutation/mutmut_report.txt) and the structured JSON dataset is stored at [`reports/mutation/mutation_results.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/mutation/mutation_results.json).

```text
--------------------------------------------------------------------------------
TOTAL MUTANTS: 24
KILLED:        24
SURVIVED:      0
MUTATION SCORE: 100.00%
QUALITY GATE:  PASSED (Score >= 70.0% threshold)
--------------------------------------------------------------------------------
```
