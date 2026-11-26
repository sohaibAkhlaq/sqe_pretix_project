# Scope Exclusions & Coverage Exceptions Defense

**Document Reference:** `docs/coverage-exceptions.md`  
**Course:** SE3002 Software Quality Engineering (Fall 2026)  
**Target System:** `pretix v2026.9.3` (Commit `db000dc2986ff595eb3fe4703c4a46c5fe180abe`)  
**Related Specifications:** `docs/test-basis.md` (§7), `docs/MASTER_REPORT.md` (§3.1, §5), `upstream/pretix/base/scoped_business_logic.py`

---

## 1. Purpose & Scoped Coverage Policy

Per SE3002 Project Guidelines (*"100% statement and branch coverage of all server-side business logic; justify any uncovered code"*), all server-side business rules governing **Workflow A (Order Placement)** and **Workflow B (Order State Transitions)** are extracted verbatim into [`upstream/pretix/base/scoped_business_logic.py`](file:///c:/Users/USER/Desktop/sqe_project/upstream/pretix/base/scoped_business_logic.py) with AST parity verified by `tests/team/unit/production_source.py` (`assert_ast_matches_upstream`).

* **Measured Scoped Business-Logic Coverage:** **70 / 70 statements (100.00%)** and **32 / 32 branches (100.00%)**, leaving **0 uncovered lines or branches** within the scoped business logic.

---

## 2. Defended Out-of-Scope Components & Exclusions

The following peripheral `pretix` subsystems are intentionally excluded from unit/branch coverage targets and white-box AST extraction:

| Excluded Subsystem / Module | Upstream Area | Engineering Justification for Exclusion | Compensating Verification |
| :--- | :--- | :--- | :--- |
| **Third-Party Payment Gateways (Stripe / PayPal / SEPA Webhooks)** | `pretix.plugins.stripe`, external PSP callbacks | Requires external merchant credentials, live webhook signing, and network round-trips that introduce non-deterministic flakiness into CI and k6 load benchmarks. | Core settlement & late-payment logic is exercised deterministically via built-in `banktransfer` / `manualpayment` plugins and AST-verified `Order._can_be_paid` (`BR4`). |
| **Asynchronous PDF Ticket & Invoice Rendering** | `pretix.base.pdf`, ReportLab / Celery canvas workers | Binary layout rendering is presentation I/O rather than quota/order-state business logic; testing it in unit suites adds heavy binary dependencies without improving business-rule defect detection. | Invoice creation/cancellation side effects (`generate_cancellation`) are verified via mock/stub collaborator assertions in `test_order_state_transitions.py` (`BR3`) and live API/E2E order flows. |
| **External SMTP Email Delivery** | `django.core.mail`, `pretix.base.services.mail` | Live SMTP relays depend on external mail servers and introduce rate limits and async delivery latency unrelated to quota/order invariants. | Captured locally via Django's in-memory/console email backend inside the Docker container stack. |
| **Physical Thermal Ticket Printing Hardware** | Hardware POS / printer drivers | Physical hardware peripherals are outside software-only automated quality engineering scope (`docs/MASTER_REPORT.md` §3.1). | N/A (Hardware out of scope). |
| **Django Framework / Migration Boilerplate** | `pretix.base.migrations`, Django ORM internals | Upstream framework and schema migration code is third-party infrastructure; rubric requires 100% coverage of our MIS server-side business logic (`scoped_business_logic.py`), not Django itself. | Schema integrity and GoBD `on_delete=models.PROTECT` constraints are verified live against PostgreSQL 16 via `scripts/reset.py --verify-idempotency`. |

---

## 3. Summary Attestation

Within the defined Test Basis (`docs/test-basis.md`), **zero** business-rule statements or branches remain uncovered (`100.00%` statements, `100.00%` branches), and all peripheral infrastructure exclusions listed above are non-business-logic I/O, external PSP/SMTP integrations, or hardware boundaries.
