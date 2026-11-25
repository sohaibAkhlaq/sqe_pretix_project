# Scoped Production Unit Statement & Branch Coverage Defense

**Document Reference:** `docs/cfg/branch_coverage_defense.md`  
**Owner:** Sohaib (`24i-3108`, Member 1 — Area A Lead)  
**Command:** `.venv\Scripts\python.exe scripts/run_unit_tests.py` (`--cov=upstream.pretix.base.scoped_business_logic --cov-branch --cov-fail-under=100`)  
**XML / HTML Evidence:** [`reports/coverage/coverage.xml`](file:///c:/Users/USER/Desktop/sqe_project/reports/coverage/coverage.xml), [`reports/coverage/html/index.html`](file:///c:/Users/USER/Desktop/sqe_project/reports/coverage/html/index.html)

---

## 1. Authoritative Production Coverage Measurement

Coverage is measured **directly on the production business logic module** [`upstream/pretix/base/scoped_business_logic.py`](file:///c:/Users/USER/Desktop/sqe_project/upstream/pretix/base/scoped_business_logic.py), **not** on test files (`tests/team/unit/`). Every method body in `scoped_business_logic.py` is programmatically verified for exact AST equality (`ast.dump(...)`) against the pinned `pretix v2026.9.3` source files (`commit db000dc2986ff595eb3fe4703c4a46c5fe180abe`) on every test run via `tests/team/unit/production_source.py`.

| Metric Dimension | Target (`scoped_business_logic.py`) | Measured Value | Threshold | Verdict |
| :--- | :--- | :---: | :---: | :---: |
| **Executable Statements** | BR1, BR2, BR3, BR4 production bodies | **70 / 70 (`100.00%`)** | $\ge 80\%$ (`100%` CI enforced) | **PASS** |
| **Executable Branches** | All conditional arcs across BR1–BR4 | **32 / 32 (`100.00%`)** | $\ge 80\%$ (`100%` CI enforced) | **PASS** |
| **Unit Tests Passed** | `tests/team/unit/` (4 modules) | **49 / 49 passed** | $100\%$ pass | **PASS** |
| **AST Integrity Parity** | `quotas.py`, `services/orders.py`, `models/orders.py` | **5 / 5 functions identical** | $100\%$ match | **PASS** |

---

## 2. Scoped Rule Inventory Covered (70 Statements, 32 Branches)

1. **BR1 — `OrderChangeManager._check_quotas`** (`services/orders.py:2285-2294`, Radon CCN = **8**):
   - Covered in `tests/team/unit/test_order_change_quotas.py`: empty diff, non-positive diff filtering (`0`, `-1`), unlimited quota (`size=None`), finite quota headroom, exact boundary (`avail == diff`), `AVAILABILITY_GONE`/`AVAILABILITY_ORDERED` rejection, over-demand `OrderError`, and short-circuit multi-quota pass-then-fail.
2. **BR2 — `QuotaAvailability._compute_early_outs`** (`services/quotas.py:493-500`, Radon CCN = **6**):
   - Covered in `tests/team/unit/test_quota_early_outs.py` and `test_mcc_mcdc_quota_policy.py`: all $2^2 = 4$ MCC vectors of `q.closed and not self._ignore_closed`, 2 MC/DC independence pairs, unlimited `size=None`, depleted `size=0`, positive size fallthrough, and mixed batches.
3. **BR3 — `Order.cancel_allowed` (`models/orders.py:646-648`, CCN = 2) & `mark_order_expired` (`services/orders.py:360-382`, CCN = 5):**
   - Covered in `tests/team/unit/test_order_state_transitions.py`: parameterized matrix over (`n`, `p`, `e`, `c`) and `count_positions` (`0`/`>=1`); integer PK vs ORM object lookup (`order`, `user`), `transaction.atomic()`, audit logging, invoice cancellation (`i and not i.refered.exists()`), zero-invoice guard, and `order_expired` signal emission.
4. **BR4 — `Order._can_be_paid` (`models/orders.py:1026-1047`, CCN = 10):**
   - Covered in `tests/team/unit/test_order_state_transitions.py`: `force` bypass vs `require_approval`, `payment_term_last` exact equality (`now == term_last`) vs past-due vs `ignore_date`, `STATUS_PENDING` fast-path, $2^3 = 8$-row MCC truth table on expired late-payment gate `not settings.get('payment_term_accept_late') and not ignore_date and not force`, and 4-condition MC/DC independence pairs including `_is_still_available(...)`.

---

## 3. Why Scoped Production Isolation Is Sound (Viva Defense)

Full Pretix Django modules (`upstream/pretix/base/services/orders.py` = `3,074` NCLOC, `models/orders.py` = `2,751` NCLOC) require initialized Django ORM settings, C-compiled extensions, and Postgres schemas at import time. Rather than either measuring coverage on hand-written mock files or omitting runtime checks, `upstream/pretix/base/scoped_business_logic.py` extracts the verbatim production methods with AST equivalence asserted automatically on every test run (`assert_ast_matches_upstream(...)`), ensuring `coverage.py` traces 100% genuine upstream control-flow logic with `70/70` statements and `32/32` branches covered.
