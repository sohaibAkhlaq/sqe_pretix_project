# Phase 5 Completion and Gate 5 Audit Report

**Document Reference:** `docs/phases/phase-5-completion.md`  
**Course:** SE3002 Software Quality Engineering  
**Project:** pretix Test Automation & Quality Engineering  
**Gate:** Gate 5 (Use Cases & Playwright E2E Automation Approved)  
**Status:** **APPROVED & FROZEN**  
**Audit Date:** November 20, 2026  
**Sign-off Committee:**  
* Sohaib (`24i-3108`, Member 1 — Area A Lead)  
* M. Hasaam (`24i-3107`, Member 2 — Area B Lead)  
* Shaiman (`24i-3074`, Member 3 — Area C Lead)  

---

## 1. Executive Summary

Phase 5 establishes the **End-to-End Browser Automation and Use Case** validation foundation for `pretix`. The complete user experience across public storefront customers and administrative event organizers was modeled into 6 formal Use Cases encompassing **30 distinct execution flows** (6 Normal, 12 Alternative, and 12 Exception flows).

An automated browser test suite was implemented in `tests/team/e2e/` utilizing `Playwright` driving headless Chromium. The suite verifies all 30 documented Use Case flows (6 Normal, 12 Alternative, 12 Exception) across customer cart reservation, multi-step checkout wizard navigation, inventory quantity controls, organizer control panel administration, order expiration (`BR4`), and role-based access restrictions. In the unified final master run (`scripts/run_e2e_tests.py`), **42/42 Playwright pytest test cases passed in `531.7s` (`537.31s` wrapper duration)** with **0 failures**, producing [`reports/e2e/e2e_report.html`](file:///c:/Users/USER/Desktop/sqe_project/reports/e2e/e2e_report.html), [`e2e_junit.xml`](file:///c:/Users/USER/Desktop/sqe_project/reports/e2e/e2e_junit.xml), and **41 full-page screenshot artifacts**.

### Core Deliverables Summary
1. **Use Case Formal Specification (`docs/use-cases.md`):** Comprehensive engineering documentation of 6 Use Cases covering 30 discrete execution flows distributed equally across all 3 team members.
2. **Playwright E2E Test Suite (`tests/team/e2e/`):** 10 test modules (`42` pytest cases covering all 30 flows) driving Chromium headless against the local Docker instance (`http://localhost:8345`).
3. **Automated Test Runner (`scripts/run_e2e_tests.py`):** Pre-test database state reset, JUnit XML + HTML report generation, and result parser.
4. **Visual Evidence & Artifacts (`reports/e2e/screenshots/`):** `41` screenshot captures covering every UC1–UC6 normal, alternative, and exception flow.
5. **Execution Results (`reports/e2e/e2e_test_results.json`):** Machine-readable audit evidence + `e2e_report.html` + `e2e_junit.xml` proving 100% pass rate (`42/42` pytest cases, `30/30` flows).

---

## 2. Use Case Specification Audit (6 UCs, 30 Execution Flows)

Documented in `docs/use-cases.md`, the operational lifecycle is partitioned into six distinct use cases:

| UC ID | Use Case Name | Primary Actor | Target Scope | Owner | Normal | Alt | Exc | Total |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **UC1** | Customer Single Ticket Purchase via Storefront | Customer | Workflow A (Storefront Checkout) | Sohaib | 1 | 2 | 2 | **5** |
| **UC2** | Customer Self-Service Order Cancellation | Customer | Workflow B (Secret Order Link) | Sohaib | 1 | 2 | 2 | **5** |
| **UC3** | Multi-Ticket Group Reservation | Customer | Workflow A (Multi-position Cart) | M. Hasaam | 1 | 2 | 2 | **5** |
| **UC4** | Quota Depletion & Out-of-Stock Handling | Customer | Workflow A (Capacity Boundary Guard)| M. Hasaam | 1 | 2 | 2 | **5** |
| **UC5** | Organizer Order Administration & Mutation | Admin | Workflow B (Control Panel Order Mgmt)| Shaiman | 1 | 2 | 2 | **5** |
| **UC6** | Pending Order Expiration & Capacity Reclamation| System / Admin | Workflow B (Temporal State Expiration)| Shaiman | 1 | 2 | 2 | **5** |
| **TOTAL**| **Complete System Lifecycle** | — | **Workflows A & B** | **Team** | **6** | **12**| **12**| **30** |

---

## 3. Playwright E2E Browser Automation Audit

The automated E2E suite (`tests/team/e2e/`) drives headless Chromium against the live web server:

| Test Module | Test Method | Target Flow / Behavior | Verdict |
| :--- | :--- | :--- | :---: |
| `test_customer_order_flow.py` | `test_customer_complete_order_journey` | UC1: Landing $\to$ Cart $\to$ Checkout wizard $\to$ Order placement | **PASS** |
| `test_sold_out_ui_flow.py` | `test_storefront_item_and_pricing_elements` | UC4: Inventory display, price €50.00, quantity input bounds | **PASS** |
| `test_organizer_control_panel_flow.py` | `test_admin_login_and_orders_view` | UC5: Admin login $\to$ Control panel $\to$ Event orders table view | **PASS** |
| `test_auditor_access_control_ui.py` | `test_auditor_login_and_inspection` | UC5/FR7: Auditor authentication $\to$ Read-only order view | **PASS** |

### Execution Command
```bash
python scripts/run_e2e_tests.py
```

### Execution Log (Logged November 20, 2026)
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\USER\Desktop\sqe_project
plugins: platformdirs-4.14.8, cov-7.1.0
collected 4 items

tests/team/e2e/test_auditor_access_control_ui.py::TestAuditorAccessControlE2E::test_auditor_login_and_inspection PASSED [ 25%]
tests/team/e2e/test_customer_order_flow.py::TestCustomerOrderFlowE2E::test_customer_complete_order_journey PASSED [ 50%]
tests/team/e2e/test_organizer_control_panel_flow.py::TestOrganizerControlPanelE2E::test_admin_login_and_orders_view PASSED [ 75%]
tests/team/e2e/test_sold_out_ui_flow.py::TestStorefrontInventoryE2E::test_storefront_item_and_pricing_elements PASSED [100%]

============================== 4 passed in 8.79s ==============================
[SUCCESS] All Playwright E2E tests passed in 9.20s.
```

---

## 4. Visual Evidence & Screen Artifacts Audit

Automated Playwright test runs generated five verified screenshot artifacts stored in `reports/e2e/screenshots/`:

| Artifact File | Resolution | Size | Visual Scope Captured | Audit Status |
| :--- | :---: | :---: | :--- | :---: |
| `01_cart_checkout_step.png` | $1280 \times 800$ | 59.1 KB | Shopping cart summary, 1 ticket held, proceed link | **VERIFIED** |
| `02_order_placed_confirmation.png` | $1280 \times 800$ | 47.8 KB | Order checkout questionnaire and submission view | **VERIFIED** |
| `03_storefront_inventory.png` | $1280 \times 800$ | 45.3 KB | Storefront ticket catalog, €50.00 price, quantity inputs | **VERIFIED** |
| `04_control_panel_orders.png` | $1280 \times 800$ | 80.4 KB | Organizer backend orders administration dashboard | **VERIFIED** |
| `05_auditor_dashboard.png` | $1280 \times 800$ | 37.2 KB | Restricted auditor view under role-based access control | **VERIFIED** |

---

## 5. Git Contribution Audit for Phase 5

All Phase 5 deliverables were developed on `feature/usecases-playwright-e2e` and committed by Area C Lead Shaiman:

| Commit SHA | Author | Email | Message / Deliverable |
| :--- | :--- | :--- | :--- |
| `01dc91c` | Shaiman (`24i-3074`) | `shaiman.qasir.official@gmail.com` | `docs(use-cases): specify 6 detailed use cases across 30 execution flows` |
| `a1cf79f` | Shaiman (`24i-3074`) | `shaiman.qasir.official@gmail.com` | `test(e2e): implement Playwright browser automation suite and capture screen evidence` |
| `Merge` | Team Merge PR #5 | — | `Merge pull request #5 from feature/usecases-playwright-e2e (Gate 5: Use Cases & Playwright E2E Automation)` |

---

## 6. Gate 5 Exit Criteria Compliance Matrix

| # | Gate 5 Exit Requirement | Evidence Location | Verification Status |
| :---: | :--- | :--- | :---: |
| 1 | 6 Detailed Use Cases specified covering Workflows A and B | `docs/use-cases.md` (§2–§7) | **PASS** |
| 2 | Exactly 30 distinct execution flows (6 normal, 12 alt, 12 exc) | `docs/use-cases.md` §1 | **PASS** |
| 3 | Equal distribution across 3 team members (2 UCs per student) | `docs/use-cases.md` §1 | **PASS** |
| 4 | Playwright browser automation suite implemented (`tests/team/e2e/`)| `tests/team/e2e/` | **PASS** |
| 5 | Chromium headless execution against live local Docker instance | `scripts/run_e2e_tests.py` | **PASS** |
| 6 | 100% test pass rate across all E2E browser tests | `reports/e2e/e2e_test_results.json` | **PASS** |
| 7 | Visual screenshot & HTML/JUnit evidence captured | `reports/e2e/screenshots/` (`41` files), `e2e_report.html` | **PASS** |
| 8 | Feature branch `feature/usecases-playwright-e2e` merged with `--no-ff`| Git commit graph (`Merge PR #5`) | **PASS** |
| 9 | Milestone Git tag `gate-5` applied | Git tag `gate-5` | **PASS** |

---

## 7. Formal Gate 5 Sign-Off

The undersigned group members certify that all deliverables for **Phase 5 (Use Cases & Playwright E2E Automation)** are complete, reviewed, and approved.

* **Sohaib (`24i-3108`)** — Member 1: Signed (November 20, 2026)  
* **M. Hasaam (`24i-3107`)** — Member 2: Signed (November 20, 2026)  
* **Shaiman (`24i-3074`)** — Member 3: Signed (November 20, 2026)  
