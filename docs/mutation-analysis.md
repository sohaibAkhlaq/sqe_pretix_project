# Mutation Testing Analysis & Operator Design

**Document Reference:** `docs/mutation-analysis.md`  
**Owner:** Sohaib (`24i-3108`, Member 1 — Area A Lead)  
**Target Source:** `upstream/pretix/base/scoped_business_logic.py` (AST-verified bodies for BR1–BR4)  
**Runner & Artifacts:** [`scripts/run_mutation_tests.py`](file:///c:/Users/USER/Desktop/sqe_project/scripts/run_mutation_tests.py), [`mutation_results.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/mutation/mutation_results.json), [`surviving_mutants_analysis.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/mutation/surviving_mutants_analysis.json), [`mutmut_report.txt`](file:///c:/Users/USER/Desktop/sqe_project/reports/mutation/mutmut_report.txt)

---

## 1. Execution Engine & Methodology (Windows `fork()` Workaround — `PRJ2`)

Because `mutmut` requires UNIX `os.fork()` and `SIGALRM` signals unsupported on Windows (`DEF-08`), `scripts/run_mutation_tests.py` implements an authentic **Python `ast.NodeTransformer` single-site mutation engine** that parses and mutates [`upstream/pretix/base/scoped_business_logic.py`](file:///c:/Users/USER/Desktop/sqe_project/upstream/pretix/base/scoped_business_logic.py) directly in memory via `compile()`/`exec()` across all five scoped production functions (`_compute_early_outs`, `_check_quotas`, `cancel_allowed`, `mark_order_expired`, and `_can_be_paid`).

---

## 2. Empirical Summary & Operator Breakdown

| Metric | Value | Threshold / Requirement |
| :--- | :---: | :---: |
| **Total Real AST Mutants Generated ($M$)** | **51** | $\ge 24$ |
| **Stage 1 Baseline Survivors Analyzed** | **33** | $\ge 15$ survivors classified |
| **Final Mutants Killed in Stage 2 ($K$)** | **48** | — |
| **Mathematically Proven Equivalent Mutants ($E$)** | **3** | Justified below |
| **Killable Survivors Remaining** | **0** | **0** (100% killable killed) |
| **Effective Mutation Score ($K / (M - E)$)** | **100.00%** (`48 / 48`) | $\ge 70.0\%$ |
| **Raw Kill Rate ($K / M$)** | **94.12%** (`48 / 51`) | Recorded transparently |

### Custom & Standard Operator Breakdown
| Operator Category | Generated | Killed | Equivalent | Killable Rate | Target Pattern in `scoped_business_logic.py` |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Custom Operator 1 (`BCR` — Boundary Condition Replacement)** | **10** | **8** | **2** | **100.0%** (`8/8`) | Mutates `>`, `<`, `<=`, `== 0` (`diff <= 0`, `v > 0`, `avail[1] < diff`, `now > term_last`, `q.size == 0`) |
| **Custom Operator 2 (`ADR` — Arithmetic Delta Replacement)** | **8** | **8** | **0** | **100.0%** (`8/8`) | Mutates `0 -> 1 / -1` and shifts numeric bounds `diff -> diff + 1 / diff - 1` |
| **Standard Operators (`ROR`, `COR`, `LCR`, `SVR`)** | **33** | **32** | **1** | **100.0%** (`32/32`) | Replaces `is`/`is not`, `and`->`or`, deletes unary `not`, flips bools, swaps `AVAILABILITY_*` & `STATUS_*` |

---

## 3. Classification of Stage 1 Surviving Mutants & Equivalence Proofs

Against the Stage 1 weak baseline suite, **33 real AST mutants survived** (`surviving_mutants_analysis.json`), categorized across **Missing Test** (missed boundary points like `avail[1] == diff` or `now == term_last`, `require_approval`, `accept_late`), **Weak Assertion** (e.g., not inspecting `qa.queued` calls, missing `generate_cancellation(i)` checks on `mark_order_expired`, or calling `_can_be_paid(...)` with explicit kwargs instead of testing default parameters), and **3 Proven Equivalent Mutants**:

1. **`diff <= 0` $\to$ `diff < 1` (`BCR` in `OrderChangeManager._check_quotas`):** Because ticket position deltas $\text{diff} \in \mathbb{Z}$ are discrete integers, $\text{diff} \le 0 \iff \text{diff} < 1$ holds identically for all integer inputs.
2. **`q.size == 0` $\to$ `q.size <= 0` (`BCR` in `QuotaAvailabilityPolicy._compute_early_outs`):** Pretix's Django ORM schema enforces `models.PositiveIntegerField(null=True)` on `Quota.size`, restricting valid domain values to $\mathbb{N}_0 \cup \{\text{None}\}$ so `q.size < 0` is unreachable.
3. **Tuple permutation `(STATUS_PENDING, STATUS_PAID, STATUS_EXPIRED)` $\to$ `(STATUS_PAID, STATUS_PENDING, STATUS_EXPIRED)` (`SVR` in `Order.cancel_allowed`):** Python's `in` operator on constant status tuples is strictly set-membership equivalent.

All remaining **30 killable Stage 1 survivors** were eliminated in Stage 2 (including subtle survivors caught by the AST runner such as default keyword flips `count_waitinglist=True -> False`, `ignore_date=False -> True`, `force=False -> True` on `_can_be_paid()` and unreferred-invoice checks `if i and not i.refered.exists():` on `mark_order_expired`), yielding **`48 / 48` (`100.00%`)** effective score.
