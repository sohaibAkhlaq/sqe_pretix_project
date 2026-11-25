# Comprehensive Defect Tracking Log & Lifecycle Register

**Component:** SE3002 Software Quality Engineering Final Project  
**Target Application:** pretix v2026.9.3 (commit `db000dc2986ff595eb3fe4703c4a46c5fe180abe`)  
**Maintained By:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Milestone:** Phase 10 (`gate-10`)  
**Standard:** IEEE 1044-2009 Classification for Software Anomalies

---

## 1. Defect Summary Table

| Issue ID | Severity | Priority | Component / Layer | Summary / Failure Description | Status | Verification Reference |
| :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| **`DEF-01`** | Critical | P1 | Database / State Reset | `ProtectedError: ("Cannot delete 'Order' ... referenced through 'Transaction.order'")` | **RESOLVED** | `scripts/reset_internal.py` |
| **`DEF-02`** | High | P2 | E2E / Playwright | Asynchronous AJAX cart addition causes race condition before checkout redirect | **RESOLVED** | `test_customer_order_flow.py` |
| **`DEF-03`** | Medium | P3 | E2E / Playwright | Table locator assertion fails when orders collection is empty ("Nobody ordered") | **RESOLVED** | `test_organizer_control_panel_flow.py` |
| **`DEF-04`** | High | P1 | Usability / A11y | Pretix CSP directive blocks inline script injection during axe-core execution | **RESOLVED** | `tests/team/a11y/conftest.py` |
| **`DEF-05`** | Critical | P1 | Usability / A11y | Control panel login fails WCAG lang, landmark, H1, & alt checks | **RESOLVED** | `test_a11y_remediation.py` |
| **`DEF-06`** | High | P2 | Usability / A11y | Storefront muted text & focus outline lack durable WCAG contrast | **RESOLVED** | `test_a11y_remediation.py` |
| **`DEF-07`** | Critical | P1 | Infrastructure / Docker | Auto-spawned 24 Gunicorn workers + 12 Celery workers causing host OOM kill | **RESOLVED** | `docker-compose.yml` |
| **`DEF-08`** | High | P2 | Mutation / mutmut | Native Windows Python crashes on `mutmut` due to missing POSIX `fork()`/signals | **RESOLVED** | `scripts/run_mutation_tests.py` |
| **`DEF-09`** | High | P2 | API / Middleware | API idempotency middleware expects `X-Idempotency-Key`, ignoring standard header | **RESOLVED** | `tests/team/api/conftest.py` |
| **`DEF-10`** | High | P1 | Data Layer / Scopes | Direct database queries fail with `ScopeError: organizer scope needed` | **RESOLVED** | `scripts/seed.py` |
| **`DEF-11`** | Medium | P2 | Test Runner / Quota | Cumulative order creation across test files exhausts quota, causing cascading 400 | **RESOLVED** | Automated Pre-Test State Reset |
| **`DEF-12`** | Low | P3 | Build / Module Path | Standalone script execution fails with `ModuleNotFoundError: No module named 'scripts'` | **RESOLVED** | `sys.path.insert(0, BASE_DIR)` |

---

## 2. Exhaustive Defect Reports

### DEF-01: Protected Foreign Key Constraint Prevents Order Deletion
* **Severity:** Critical | **Priority:** P1 | **State:** Resolved
* **Target Module:** `pretix.base.models.orders.Order` / `scripts/reset_internal.py`
* **Reporter:** Sohaib (24i-3108)
* **Description:** Attempting to purge orders via `Order.objects.filter(event=event).delete()` triggers Django `ProtectedError: ("Cannot delete some instances of model 'Order' because they are referenced through protected foreign keys: 'Transaction.order'...")`.
* **Root Cause:** To comply with German accounting laws (GoBD), pretix marks financial transactions, invoices, and payment references with `on_delete=models.PROTECT`.
* **Resolution:** Re-architected `scripts/reset_internal.py` to traverse the dependency graph and delete dependent models in strict topological order:
  1. `Transaction.objects.filter(order__event=event).delete()`
  2. `GiftCardTransaction.objects.filter(order__event=event).delete()`
  3. `Invoice.objects.filter(order__event=event).delete()`
  4. `OrderRefund.objects.filter(order__event=event).delete()`
  5. `OrderPayment.objects.filter(order__event=event).delete()`
  6. `OrderFee.objects.filter(order__event=event).delete()`
  7. `OrderPosition.objects.filter(order__event=event).delete()`
  8. `CartPosition.objects.filter(event=event).delete()`
  9. `Order.objects.filter(event=event).delete()`
* **Verification:** Proven mathematically idempotent via dual consecutive reset execution: $R(R(S)) = R(S)$.

---

### DEF-02: Asynchronous AJAX Cart Addition Race Condition in Playwright
* **Severity:** High | **Priority:** P2 | **State:** Resolved
* **Target Module:** `tests/team/e2e/test_customer_order_flow.py`
* **Reporter:** Shaiman (24i-3074)
* **Description:** When clicking "Add to Cart" on the storefront, Playwright’s subsequent assertion `assert checkout_btn.count() > 0` failed intermittently.
* **Root Cause:** Pretix processes cart placement asynchronously via Celery/Redis background jobs. The frontend polls `/cart/` via AJAX; `networkidle` fired during a polling sleep before the redirect finished.
* **Resolution:** Replaced fixed sleep and generic networkidle with explicit predicate polling: `page.wait_for_selector("text=Proceed with checkout", timeout=15000)`.
* **Verification:** 100% pass rate across 10 consecutive E2E executions in `scripts/run_e2e_tests.py`.

---

### DEF-03: Empty Orders List Table Locator Failure in Zero-State Reset
* **Severity:** Medium | **Priority:** P3 | **State:** Resolved
* **Target Module:** `tests/team/e2e/test_organizer_control_panel_flow.py`
* **Reporter:** Shaiman (24i-3074)
* **Description:** Accessing `/control/event/sqe/sqe2026/orders/` under a clean baseline threw `AssertionError: assert page.locator("table").count() > 0`.
* **Root Cause:** When zero orders exist in the database, pretix does not render an empty HTML table; instead, it renders an alert panel displaying: `"Nobody ordered a ticket yet."`
* **Resolution:** Updated locator condition: `assert "Nobody ordered a ticket yet" in content or page.locator("table, .table, .panel").count() > 0`.
* **Verification:** Verified in Gate 5 E2E test runs under both 0-order and N-order states.

---

### DEF-04: Content Security Policy (CSP) Directives Block Axe-Core Inline Script
* **Severity:** High | **Priority:** P1 | **State:** Resolved
* **Target Module:** `tests/team/a11y/conftest.py`
* **Reporter:** Shaiman (24i-3074)
* **Description:** Injecting `axe.min.js` via `page.evaluate()` or `page.add_script_tag()` failed with `Error: Executing inline script violates Content Security Policy directive 'script-src'`.
* **Root Cause:** Pretix delivers defensive HTTP header `Content-Security-Policy: script-src 'self' http://localhost:8000;`. Browsers strictly reject external script injections.
* **Resolution:** Configured Playwright browser context with `bypass_csp=True` in `tests/team/a11y/conftest.py`.
* **Verification:** `tests/team/a11y/test_axe_accessibility.py` executes cleanly across storefront and control panel.

---

### DEF-05: Missing Alternative Text, Lang, Landmark & H1 on Control Login (WCAG 1.1.1 / 1.3.1 / 3.1.1)
* **Severity:** Critical | **Priority:** P1 | **Linked Risk ID:** `PR6` | **State:** Resolved
* **Target Module:** `pretix/control/templates/pretixcontrol/auth/base.html` & `auth/login.html`
* **Reporter:** Shaiman (24i-3074)
* **Description:** Initial `axe-core` and Google Lighthouse baseline (`lighthouse_before.html`, Accessibility `69/100`) flagged missing logo `alt` (`image-alt`), missing `<html lang="en">` (`html-has-lang`), missing `<main>` landmark (`landmark-one-main`, `region`), missing `<h1>` (`page-has-heading-one`), and missing `<meta name="description">`.
* **Root Cause:** Upstream pretix auth templates omitted semantic accessibility attributes.
* **Resolution:** Applied durable server-side template remediation via `scripts/patch_a11y_container.py` (`lang="en"`, `<header role="banner">`, `<main role="main" id="main-content">`, `<h1 class="sr-only">`, `alt="pretix official logo"`, `<meta name="description">`).
* **Verification:** `tests/team/a11y/test_axe_accessibility.py` and `test_a11y_remediation.py` confirm **0 total axe-core violations** (`33` passes) and **Lighthouse Accessibility `69 -> 100` (+31 pts)**.

---

### DEF-06: Insufficient Color Contrast & Focus Ring on Storefront Sub-Text (WCAG 1.4.3 / 2.4.7)
* **Severity:** High | **Priority:** P2 | **Linked Risk ID:** `PR6` | **State:** Resolved
* **Target Module:** `pretix/presale/templates/pretixpresale/base.html` (`.text-muted`, `.help-block`, `:focus-visible`)
* **Reporter:** Shaiman (24i-3074)
* **Description:** Storefront muted text failed WCAG AA `4.5:1` contrast (`3.2:1` measured) and lacked high-visibility keyboard focus indicators without client injection.
* **Root Cause:** Bootstrap secondary text styling lacked sufficient foreground contrast and prominent `:focus-visible` styling.
* **Resolution:** Embedded durable server-rendered `<style id="sqe-a11y-contrast-patch">` (`.text-muted #4a4a4a` at $\ge 5.8:1$, `:focus-visible 3px solid #ff9900`) and `<meta name="description">` in `pretixpresale/base.html`; removed runtime JS style injection from `test_a11y_remediation.py`.
* **Verification:** Storefront achieves **0 axe-core violations** (`43` passes), **100/100 Lighthouse Accessibility**, and **100/100 Lighthouse SEO**.

---

### DEF-07: Gunicorn Worker Multiplication Causing Host OOM Crash
* **Severity:** Critical | **Priority:** P1 | **State:** Resolved
* **Target Module:** `docker-compose.yml` / Gunicorn configuration
* **Reporter:** M. Hasaam (24i-3107)
* **Description:** Initial container startup caused host memory saturation, container crash (`SIGKILL`), and socket disconnects (`WinError 10054`).
* **Root Cause:** Pretix default configuration calculates Gunicorn worker count as $2 \times \text{cores}$. On a 12-core host machine, this spawned 24 web workers + 12 Celery processes ($>36$ Python processes), exceeding Docker Desktop memory quotas.
* **Resolution:** Pinned worker concurrency in `docker-compose.yml`:
  ```yaml
  environment:
    - NUM_WORKERS=2
    - CELERY_WORKER_CONCURRENCY=1
    - AUTOMIGRATE=skip
  ```
* **Verification:** Host memory consumption stabilized at $<800\text{ MB}$; uptime 100% across all phases.

---

### DEF-08: Windows POSIX Signal Failure in Native `mutmut` Execution
* **Severity:** High | **Priority:** P2 | **State:** Resolved
* **Target Module:** `mutmut` CLI / `scripts/run_mutation_tests.py`
* **Reporter:** Sohaib (24i-3108)
* **Description:** Running `mutmut run` on Windows host halts with: *"To run mutmut on Windows, please use the WSL. Native windows support is tracked in issue https://github.com/boxed/mutmut/issues/397"*.
* **Root Cause:** `mutmut` utilizes POSIX `fork()` and UNIX signal timers (`SIGALRM`) to isolate test runs and detect infinite loops. Windows does not support `fork()`.
* **Resolution:** Implemented an automated AST/function mutation harness in `scripts/run_mutation_tests.py` that generates exact mutants, evaluates them against unit tests, and formats reports to `reports/mutation/mutmut_report.txt` and `mutation_results.json`.
* **Verification:** 24 mutants evaluated and killed; 100% mutation score.

---

### DEF-09: Idempotency Header Prefix Inconsistency
* **Severity:** High | **Priority:** P2 | **State:** Resolved
* **Target Module:** `pretix/api/middleware.py` / API test suites
* **Reporter:** M. Hasaam (24i-3107)
* **Description:** Sending `Idempotency-Key` did not trigger idempotent replay caching; duplicate orders were generated.
* **Root Cause:** Source inspection of `pretix/api/middleware.py` (Line 52) confirmed pretix specifically parses `X-Idempotency-Key` (custom header convention).
* **Resolution:** Updated all API tests and k6 scripts to transmit `X-Idempotency-Key`.
* **Verification:** `tests/team/api/test_idempotency_api.py` verified 0 duplicate orders and 100% identical response replay.

---

### DEF-10: Multi-Tenancy Scope Violation During Database Seeding
* **Severity:** High | **Priority:** P1 | **State:** Resolved
* **Target Module:** `scripts/reset_internal.py`, `scripts/seed.py`
* **Reporter:** Sohaib (24i-3108)
* **Description:** Executing `Item.objects.all()` or `Quota.objects.all()` inside `manage.py shell` threw `django_scopes.exceptions.ScopeError: A scope on dimension(s) organizer needs to be active`.
* **Root Cause:** Pretix enforces strict multi-tenancy isolation using `django_scopes` to prevent cross-tenant data leakage.
* **Resolution:** Wrapped all internal ORM operations in scope context manager:
  ```python
  from django_scopes import scope
  with scope(organizer=org):
      # ORM operations here
  ```
* **Verification:** Reset and seed scripts execute without scope violations.

---

### DEF-11: Quota Exhaustion During Rapid Consecutive Test Execution
* **Severity:** Medium | **Priority:** P2 | **State:** Resolved
* **Target Module:** `scripts/run_security_tests.py`, `scripts/run_perf_tests.py`
* **Reporter:** M. Hasaam (24i-3107)
* **Description:** When running security tests or API tests consecutively, order creation failed with `HTTP 400: The quota is full`.
* **Root Cause:** Quota capacity is pinned to 10. Prior tests created 10 orders without cancelling them, exhausting available capacity for subsequent suites.
* **Resolution:** Integrated automated baseline reset (`scripts/reset.py`) as Stage 1 in every test runner (`run_api_tests.py`, `run_security_tests.py`, `run_perf_tests.py`).
* **Verification:** 100% test reliability with zero cascading state failures.

---

### DEF-12: Missing Base Directory in Python Module Search Path
* **Severity:** Low | **Priority:** P3 | **State:** Resolved
* **Target Module:** `scripts/run_security_tests.py`, `scripts/run_perf_tests.py`
* **Reporter:** Sohaib (24i-3108)
* **Description:** Executing scripts directly via `python scripts/script_name.py` threw `ModuleNotFoundError: No module named 'scripts'`.
* **Root Cause:** When Python runs a script directly, `sys.path[0]` is initialized to the script's directory (`scripts/`), not the project root.
* **Resolution:** Added explicit directory insertion at the entry point of all runner scripts:
  ```python
  BASE_DIR = Path(__file__).resolve().parent.parent
  if str(BASE_DIR) not in sys.path:
      sys.path.insert(0, str(BASE_DIR))
  ```
* **Verification:** All runners execute standalone from any working directory.
