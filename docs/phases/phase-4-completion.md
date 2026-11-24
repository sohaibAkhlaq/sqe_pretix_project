> **Evidence audit (2026-11-24):** The completion label and measured claims in this historical phase note have not been revalidated against the current source-to-test map and fresh run artifacts. Treat them as provisional; see `../completion-report.md` for current status.

# Phase 4 Completion and Gate 4 Audit Report

**Document Reference:** `docs/phases/phase-4-completion.md`  
**Course:** SE3002 Software Quality Engineering  
**Project:** pretix Test Automation & Quality Engineering  
**Gate:** Gate 4 (API Testing & Automated Data Generation Approved)  
**Status:** **APPROVED & FROZEN**  
**Audit Date:** November 20, 2026  
**Sign-off Committee:**  
* Sohaib (`24i-3108`, Member 1 — Area A Lead)  
* M. Hasaam (`24i-3107`, Member 2 — Area B Lead)  
* Shaiman (`24i-3074`, Member 3 — Area C Lead)  

---

## 1. Executive Summary

Phase 4 establishes the formal **REST API Testing and Automated Data Generation** foundation for `pretix`. The entire API interaction surface spanning Workflow A (order placement) and Workflow B (order cancellation, payment, expiration) has been modeled into an OpenAPI 3.0 specification (`openapi/team-spec.yaml`).

To eliminate brittle test data maintenance, an automated test data generation engine was developed in `tools/datagen/`, synthesizing datasets using 3-Point Boundary Value Analysis (BVA) and Equivalence Partitioning (EP). Complete zero-code test suite adaptation was demonstrated when business constraints changed (Quota $10 \to 15$, Price €50 $\to$ €75). The entire automated REST API test suite (16 tests) executed against the live multi-container Docker stack, achieving a **100% pass rate** in $6.40\text{ seconds}$, merged into `main` under Git tag `gate-4`.

### Core Deliverables Summary
1. **OpenAPI 3.0 Contract Specification (`openapi/team-spec.yaml`):** Formal schema definitions covering 8 core endpoints, HTTP methods, headers (`X-Idempotency-Key`), token authentication, and status codes (200, 201, 400, 403, 404, 409).
2. **Automated Test Data Generator (`tools/datagen/`):** Python package generating synthetic test datasets via 3-point BVA ($\min-1, \min, \min+1, \text{nom}, \max-1, \max, \max+1$) and Equivalence Partitioning (Valid, Invalid, Boundary partitions).
3. **Constraint Regeneration Demonstration (`docs/regeneration-demo.md`):** Complete documentation of automated test data recalibration under 2 constraint changes (Quota $10 \to 15$, Price €50 $\to$ €75) with side-by-side JSON payload diffs.
4. **REST API Test Suite (`tests/team/api/`):** 16 automated tests covering order creation, idempotency replay, cross-workflow quota restoration, and RBAC permissions.
5. **Execution Results (`reports/api/api_test_results.json`):** Machine-readable audit evidence proving 100% pass rate against live Docker services.

---

## 2. OpenAPI 3.0 Specification Audit

The API contract was authored in `openapi/team-spec.yaml` adhering to OpenAPI Specification v3.0.3:

| Endpoint Path | Method | Operations Tested | Status Codes Specified |
| :--- | :---: | :--- | :---: |
| `/organizers/{org}/` | GET | Tenant discovery | 200, 404 |
| `/organizers/{org}/events/{event}/` | GET | Event schedule & currency | 200, 404 |
| `/organizers/{org}/events/{event}/items/{id}/` | GET | Ticket product metadata & pricing | 200, 404 |
| `/organizers/{org}/events/{event}/quotas/{id}/availability/`| GET | Shared quota capacity inspection | 200, 404 |
| `/organizers/{org}/events/{event}/orders/` | GET, POST| Order listing & Order placement (Workflow A)| 200, 201, 400, 403 |
| `/organizers/{org}/events/{event}/orders/{code}/` | GET | Order details | 200, 404 |
| `/organizers/{org}/events/{event}/orders/{code}/mark_canceled/` | POST | Cancellation & quota return (Workflow B)| 200, 400, 403 |
| `/organizers/{org}/events/{event}/orders/{code}/mark_paid/` | POST | Payment confirmation & state lock | 200, 400, 403 |
| `/organizers/{org}/events/{event}/orders/{code}/mark_expired/` | POST | Expiration & quota release | 200, 400, 403 |

---

## 3. Automated Test Data Generator Audit

Developed in `tools/datagen/`, the generator synthesizes inputs deterministically (`seed=42`) using standard quality engineering partition techniques:

### 3.1. 3-Point Boundary Value Analysis (BVA) Metrics
For Quota Capacity $S = 10$:

$$\text{BVA Points} = \{0, 1, 2, 5, 9, 10, 11\}$$

* Point 1 ($\min - 1 = 0$): Invalid (Underflow)
* Point 2 ($\min = 1$): Valid (Single pass)
* Point 3 ($\min + 1 = 2$): Valid (Pair pass)
* Point 4 (Nominal $= 5$): Valid (Standard booking)
* Point 5 ($\max - 1 = 9$): Valid (Penultimate booking)
* Point 6 ($\max = 10$): Valid (Full venue sellout)
* Point 7 ($\max + 1 = 11$): Invalid (Overflow rejection)

### 3.2. Equivalence Partitions
* **Valid Partition (`EP-VAL-01` to `EP-VAL-03`):** 1-ticket, multi-ticket, and full-capacity bulk orders.
* **Invalid Partition (`EP-INV-01` to `EP-INV-04`):** Zero tickets, over-capacity order, malformed email, non-existent item ID.
* **Boundary Partition (`EP-BND-01` to `EP-BND-03`):** Exact quota limits and threshold transitions.

---

## 4. Constraint Regeneration Demonstration Audit

Documented in `docs/regeneration-demo.md`, the generator was tested with altered constraints:
* **Baseline Constraints:** Quota $= 10$, Price $= \text{€}50.00$
* **Updated Constraints:** Quota $= 15$, Price $= \text{€}75.00$
* **Output Analysis:**
  - BVA nominal shifted from $5 \to 7$.
  - BVA maximum shifted from $10 \to 15$.
  - BVA overflow boundary shifted from $11 \to 16$.
  - All ticket positions automatically re-priced at €75.00.
* **Impact on Tests:** Zero manual test code edits required; tests dynamically consume the regenerated dataset.

---

## 5. REST API Test Execution & Empirical Results

### 5.1. Execution Command
```bash
python scripts/run_api_tests.py
# or pytest tests/team/api/ -v
```

### 5.2. Test Execution Log (Logged November 20, 2026)
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\USER\Desktop\sqe_project
collected 16 items

tests/team/api/test_idempotency_api.py::TestIdempotencyAPI::test_repeated_submissions_return_identical_order PASSED [  6%]
tests/team/api/test_idempotency_api.py::TestIdempotencyAPI::test_divergent_idempotency_keys_create_distinct_orders PASSED [ 12%]
tests/team/api/test_order_creation_api.py::TestOrderCreationAPI::test_ep_valid_single_ticket PASSED [ 18%]
tests/team/api/test_order_creation_api.py::TestOrderCreationAPI::test_ep_valid_multi_ticket PASSED [ 25%]
tests/team/api/test_order_creation_api.py::TestOrderCreationAPI::test_ep_invalid_empty_positions PASSED [ 31%]
tests/team/api/test_order_creation_api.py::TestOrderCreationAPI::test_ep_invalid_email_format PASSED [ 37%]
tests/team/api/test_order_creation_api.py::TestOrderCreationAPI::test_ep_invalid_nonexistent_item_id PASSED [ 43%]
tests/team/api/test_order_creation_api.py::TestOrderCreationAPI::test_bva_quantity_overflow PASSED [ 50%]
tests/team/api/test_order_lifecycle_api.py::TestOrderLifecycleAPI::test_cancellation_restores_quota_availability PASSED [ 56%]
tests/team/api/test_order_lifecycle_api.py::TestOrderLifecycleAPI::test_order_mark_paid PASSED [ 62%]
tests/team/api/test_order_lifecycle_api.py::TestOrderLifecycleAPI::test_order_mark_expired_restores_quota PASSED [ 68%]
tests/team/api/test_order_lifecycle_api.py::TestOrderLifecycleAPI::test_illegal_transition_canceled_to_paid_rejected PASSED [ 75%]
tests/team/api/test_rbac_api.py::TestRBACPermissionsAPI::test_auditor_can_inspect_all_read_endpoints PASSED [ 81%]
tests/team/api/test_rbac_api.py::TestRBACPermissionsAPI::test_auditor_cannot_place_orders PASSED [ 87%]
tests/team/api/test_rbac_api.py::TestRBACPermissionsAPI::test_auditor_cannot_mutate_items PASSED [ 93%]
tests/team/api/test_rbac_api.py::TestRBACPermissionsAPI::test_auditor_cannot_cancel_orders PASSED [100%]

============================= 16 passed in 6.40s ==============================
```

### 5.3. Verified Functional Properties
1. **Idempotency (FR1, PR5):** 5 consecutive replays of identical `X-Idempotency-Key` returned identical order code with 0 duplicate quota holds.
2. **Cross-Workflow Quota Coupling (Shared State):** Quota transitioned from $10 \to 9$ on creation, and restored from $9 \to 10$ upon cancellation.
3. **State Machine Integrity (BR3):** Illegal transition ($\text{Canceled} \to \text{Paid}$) was strictly rejected with HTTP 400.
4. **Role-Based Access Control (FR7, PR6):** Read-Only Auditor token successfully accessed all 5 read endpoints (HTTP 200) and was denied on all mutating endpoints (HTTP 403 Forbidden).

---

## 6. Git Contribution Audit for Phase 4

All Phase 4 deliverables were developed on `feature/api-testing-datagen` and committed by Area B Lead M. Hasaam:

| Commit SHA | Author | Email | Message / Deliverable |
| :--- | :--- | :--- | :--- |
| `c8523a6` | M. Hasaam (`24i-3107`) | `m.hasaam.official@gmail.com` | `docs(api-spec): create OpenAPI 3.0 specification and constraint regeneration demo` |
| `07fa75e` | M. Hasaam (`24i-3107`) | `m.hasaam.official@gmail.com` | `feat(datagen): implement automated BVA and EP test data generator tool` |
| `a76f071` | M. Hasaam (`24i-3107`) | `m.hasaam.official@gmail.com` | `test(api): implement 16 REST API integration tests covering workflows A and B, idempotency, and RBAC` |
| `Merge` | Team Merge PR #4 | — | `Merge pull request #4 from feature/api-testing-datagen (Gate 4: API Testing & Automated Data Generation)` |

---

## 7. Gate 4 Exit Criteria Compliance Matrix

| # | Gate 4 Exit Requirement | Evidence Location | Verification Status |
| :---: | :--- | :--- | :---: |
| 1 | OpenAPI 3.0 contract specification for all 8 target endpoints | `openapi/team-spec.yaml` | **PASS** |
| 2 | Automated test data generator tool implemented (`tools/datagen/`) | `tools/datagen/generator.py` | **PASS** |
| 3 | 3-Point Boundary Value Analysis ($\min-1, \min, \min+1, \text{nom}, \dots$) | `tools/datagen/generator.py` | **PASS** |
| 4 | Equivalence Partitioning (Valid, Invalid, Boundary partitions) | `reports/api/generated_data.json` | **PASS** |
| 5 | Live regeneration demo with 2 altered constraints (Quota & Price) | `docs/regeneration-demo.md` | **PASS** |
| 6 | Automated REST API test suite passing 100% against Docker stack | `scripts/run_api_tests.py` (16/16 passed)| **PASS** |
| 7 | Idempotency verified on repeated submissions with zero quota leaks | `tests/team/api/test_idempotency_api.py` | **PASS** |
| 8 | Cross-workflow quota restoration verified upon cancellation | `tests/team/api/test_order_lifecycle_api.py` | **PASS** |
| 9 | Role-Based Access Control verified (Auditor mutation HTTP 403) | `tests/team/api/test_rbac_api.py` | **PASS** |
| 10 | Results captured in machine-readable JSON | `reports/api/api_test_results.json` | **PASS** |
| 11 | Feature branch `feature/api-testing-datagen` merged to `main` with `--no-ff`| Git commit graph (`Merge PR #4`) | **PASS** |
| 12 | Milestone Git tag `gate-4` applied | Git tag `gate-4` | **PASS** |

---

## 8. Formal Gate 4 Sign-Off

The undersigned group members certify that all deliverables for **Phase 4 (API Testing & Automated Data Generation)** are complete, reviewed, and approved.

* **Sohaib (`24i-3108`)** — Member 1: Signed (November 20, 2026)  
* **M. Hasaam (`24i-3107`)** — Member 2: Signed (November 20, 2026)  
* **Shaiman (`24i-3074`)** — Member 3: Signed (November 20, 2026)  
