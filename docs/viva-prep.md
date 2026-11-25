# SE3002 SQE Comprehensive Viva Preparation & Live Task Rehearsal Guide

**Project:** SE3002 Software Quality Engineering Final Project - pretix Test Automation  
**Team Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Standard:** Gold Medalist Defense - 100% Technical Mastery, Zero Hesitation  
**Milestone:** Phase 12

---

## 1. Member Defense Profiles & Individual Contribution Ownership

### Member 1: Sohaib (`24i-3108`, Git: `sohaibAkhlaq`) — Area A Lead
* **Primary Scope:** Static Analysis (SonarQube/Radon/Lizard), White-Box Unit Testing (100% Statement & Branch Coverage on `upstream/pretix/base/scoped_business_logic.py`, Basis Paths, MCC & MC/DC), Real AST Mutation Testing (BCR & ADR Operators), Two-Job GitHub Actions CI PR Quality Gate.
* **Key Codebase Artifacts:**
  - `upstream/pretix/base/scoped_business_logic.py`: Pinned production rules `BR1`–`BR4` (`70` stmts, `32` branches), AST-verified against upstream source via `production_source.py`.
  - `docs/cfg/cfg_analysis.md`: Control Flow Graphs and 3-formula CCN calculations ($V=6$ `_compute_early_outs`, $V=8$ `_check_quotas`, and $V=10$ `Order._can_be_paid`).
  - `docs/cfg/mcc_mcdc.md`: `BR2` (`4`-row MCC + `2` MC/DC pairs) and `BR4` (`8`-row MCC + `4` MC/DC pairs).
  - `tests/team/unit/`: `49` unit tests achieving **100.00% (`70/70`) statement and 100.00% (`32/32`) branch coverage**.
  - `scripts/run_mutation_tests.py`: `51` real AST mutants on `scoped_business_logic.py` (`48` killed, `3` proven equivalent = **100.00% effective score**, `94.12%` raw), custom BCR/ADR operators.
  - `.github/workflows/pr-gate.yml` & `docs/ci-gate-demo.md`: Two-job fail-closed CI Quality Gate blocking non-compliant PRs.
* **Core Theoretical Defense:**
  - *Cyclomatic Complexity Proof:* $V(G) = E - N + 2P = P_R + 1 = R$. For `_compute_early_outs` (`BR2`), $15 - 11 + 2 = 6 = 5 + 1$; for `_check_quotas` (`BR1`), $19 - 14 + 2 = 8 = 7 + 1$; for `Order._can_be_paid` (`BR4`), $25 - 17 + 2 = 10 = 9 + 1$.
  - *MC/DC Formulation:* For `BR2` ($q.\text{closed} \land \neg\text{\_ignore\_closed}$), $2^2=4$ MCC vectors prove $2$ independence pairs. For `BR4` ($\neg\text{accept\_late} \land \neg\text{ignore\_date} \land \neg\text{force}$), $2^3=8$ MCC combinations prove independence of every condition plus `_is_still_available(...)`.
  - *Custom Mutation Operators:*
    - Boundary Condition Replacement (BCR): Mutates relational comparisons (`<` $\leftrightarrow$ `<=`, `>` $\leftrightarrow$ `>=`, `== 0`), catching off-by-one capacity/expiration bugs (`8/10` killed + `2` proven equiv).
    - Arithmetic Delta Replacement (ADR): Shifts constants/offsets (`0 -> 1 / -1`, `diff -> diff +/- 1`) (`8/8` killed).

---

### Member 2: M. Hasaam (`24i-3107`, Git: `M-Hasaam`) — Area B Lead
* **Primary Scope:** OpenAPI 3.0 Contract Specification, Automated Synthetic Test Data Generation (`tools/datagen/`), REST API Integration Testing, Dual 60s k6 Benchmarks & State-Changing Chaos Fault Recovery.
* **Key Codebase Artifacts:**
  - `openapi/team-spec.yaml`: OpenAPI 3.0.3 contract covering catalog, quotas, `?status=` filtering, `401` responses, and order transitions.
  - `tools/datagen/generator.py` & `cli.py`: Dynamic 3-point BVA ($\min-1, \min, \min+1, \text{nom}, \max-1, \max, \max+1$) for both Quantity and Price, Decimal limits (`13` vs `14` digits), EP vectors, idempotency, and RBAC cases.
  - `docs/regeneration-demo.md`: Live zero-code test data adaptation under `S: 10 -> 15, P: 50 -> 75`.
  - `tests/team/api/`: `18` integration tests dynamically consuming `generated_data.json` with live quota/state read-backs.
  - `tests/team/perf/`: Dual 60s 1-VU (`p95 = 183.98 / 186.16 ms`) and 5-VU (`p95 = 354.47 / 212.14 ms`) k6 runs (`0.00%` unexpected failures across `2,352` reqs), plus Redis outage recovery (`RTO = 0.28s`, `0` duplicates, `PSELH`).
* **Core Theoretical Defense:**
  - *Dynamic Test Data Generation:* Running `python -m tools.datagen.cli --quota-size <S> --price <P>` shifts all BVA boundaries in `reports/api/generated_data.json` without editing API assertions.
  - *Idempotency Header Mechanism:* Explaining `X-Idempotency-Key` middleware caching in Redis (whereas omitting `X-` causes duplicate creation, `DEF-09`).
  - *Concurrency Invariant Proof:* Demonstrating how PostgreSQL `SELECT FOR UPDATE` + Redlock serialize concurrent checkout attempts so `10` orders succeed and excess attempts return HTTP `400`, preserving $\sum \text{Orders} \le Q_{\text{capacity}}$.

---

### Member 3: Shaiman (`24i-3074`, Git: `ShaimanQasir`) — Area C Lead
* **Primary Scope:** Use Case Analysis (`6` UCs, `30` Flows), Playwright E2E UI Automation, Usability/Accessibility (axe-core & Lighthouse WCAG 2.1 AA with Durable Server-Side Template Remediation), Defensive Security & RBAC Matrix.
* **Key Codebase Artifacts:**
  - `docs/use-cases.md`: `6` Use Cases covering `30` execution flows (`6` normal, `12` alt, `12` exc) automated via `42` Playwright pytest cases (`e2e_report.html` + `41` screenshots).
  - `scripts/patch_a11y_container.py` & `tests/team/a11y/`: Durable server-template remediation on `auth/base.html`, `auth/login.html`, and `presale/base.html`, driving axe violations `4 -> 0` (`0` total) and Login Lighthouse Accessibility `69 -> 100`.
  - `docs/security-model.md` & `tests/team/security/`: `7`-decision Playwright RBAC access matrix (`DEC-01`..`DEC-07` across Admin, Auditor, Public/Anon), ZAP-aligned HTTP passive inspector, `pip-audit` (`0` CVEs / `48` host pkgs) + `152` container pkgs inventory (`26/26` security tests pass).
* **Core Technical Defense:**
  - *Durable Server Accessibility Fix:* Walking through `scripts/patch_a11y_container.py` adding `lang="en"`, `<main>`, `<h1>`, `alt="pretix official logo"`, `.text-muted` `#4a4a4a` ($\ge 5.8:1$), and `:focus-visible` `3px #ff9900` directly in Django templates.
  - *RBAC Authorization Matrix:* Demonstrating `DEC-06` (`auditor@localhost` Orders GET allowed HTTP `200`) and `DEC-07` (`auditor@localhost` Settings blocked HTTP `403 Permission denied`), alongside Anonymous `302`/login redirects and REST `401/403` enforcement.

---

## 2. Anticipated Live Examiner Tasks & Step-by-Step Defense

### Live Task 1: "Change quota size from 10 to 20 and show me what happens to your tests."
* **Examiner Goal:** Test whether the team's data generation and test suites are hardcoded or dynamically adaptive.
* **Resolution Steps (M. Hasaam):**
  1. Run `.venv\Scripts\python.exe -m tools.datagen.cli --quota-size 20 --price 50.00 --output reports/api/generated_data.json`.
  2. Show the examiner: The 3-point boundary values dynamically shift:
     - Old (`S=10`): `0, 1, 2, 5, 9, 10, 11`.
     - New (`S=20`): `0, 1, 2, 10, 19, 20, 21`.
  3. Point to `docs/regeneration-demo.md` and `tests/team/api/test_datagen_openapi_contract.py` proving dynamic consumption without test code edits.

---

### Live Task 2: "Introduce an off-by-one mutant in `_check_quotas` (`<` to `<=`) and show me how you catch it."
* **Examiner Goal:** Test whether the team truly understands mutation testing and boundary condition coverage.
* **Resolution Steps (Sohaib):**
  1. Explain: "In `_check_quotas` (`upstream/pretix/base/scoped_business_logic.py`), the condition `avail[1] < diff` checks if available capacity is strictly less than required tickets. Mutated to `avail[1] <= diff`, exact boundary requests (`avail == diff`) fail falsely."
  2. Run `.venv\Scripts\python.exe scripts/run_mutation_tests.py`.
  3. Point to the `BCR` `avail[1] < diff -> avail[1] <= diff` mutant (`KILLED`, out of `51` AST mutants: `48` killed, `3` equiv, `100.00%` effective kill rate).
  4. Explain: "Our boundary unit test sends `avail == diff` and asserts pass; the mutant throws `QuotaExceeded`, killing the mutant deterministically."

---

### Live Task 3: "Show me an Auditor token trying to cancel an order or mark it paid."
* **Examiner Goal:** Verify RBAC authorization enforcement live.
* **Resolution Steps (Shaiman):**
  1. Run `.venv\Scripts\python.exe -m pytest tests/team/api/test_rbac_api.py tests/team/security/test_playwright_rbac_access_matrix.py -v`.
  2. Show live output (`HTTP 403 Forbidden` on auditor POST/PATCH mutations + Playwright `DEC-06` Allowed `GET orders` vs `DEC-07` Denied `GET settings`).
  3. Explain how `has_event_permission(..., 'can_change_orders')` separates read-only Auditor roles from Admin mutations.

---

### Live Task 4: "Show me the upstream accessibility defect and your durable server-side fix."
* **Examiner Goal:** Verify authentic usability defect discovery and remediation.
* **Resolution Steps (Shaiman):**
  1. Open `docs/a11y-before-after.md` and `scripts/patch_a11y_container.py`.
  2. Show unpatched baseline `reports/a11y/lighthouse_before.html` (Accessibility `69/100`) vs durably patched `reports/a11y/lighthouse_after.html` (Accessibility `100/100`) and `lighthouse_storefront.html` (`100/100` A11y & SEO).
  3. Run `.venv\Scripts\python.exe -m pytest tests/team/a11y/ -v` proving `0` axe-core violations natively from server HTML (`8/8` tests pass) and show screenshots (`02_login_remediation_before.png` vs `03_login_remediation_after.png`).

---

### Live Task 5: "Kill Redis right now and show me the system recovering cleanly."
* **Examiner Goal:** Verify chaos testing and state-changing fault recovery.
* **Resolution Steps (M. Hasaam):**
  1. Run `.venv\Scripts\python.exe -m pytest tests/team/perf/test_state_changing_recovery.py -v -s`.
  2. Point to `docker stop pretix_redis`, PostgreSQL check (`0` partial orders committed), `docker start pretix_redis` (`RTO = 0.28s`), retry with identical `X-Idempotency-Key` (`HTTP 201`, `PSELH`), and replay asserting `total_duplicate_records == 0`.

---

## 3. High-Yield Question & Answer Defense Cheat-Sheet

**Q1: Why did you test two related workflows instead of just one?**  
*Answer:* "Workflow A (Order Placement) reads quota availability and decrements it upon completion. Workflow B (Order Cancellation / State Transitions) mutates order states and restores availability. Testing them together proves shared state consistency and conservation of finite inventory."

**Q2: What is the difference between MCC and MC/DC?**  
*Answer:* "Multiple Condition Coverage (MCC) tests all $2^N$ combinations of conditions in a compound decision (`4` rows for BR2's `q.closed and not _ignore_closed`; `8` rows for BR4's late-payment compound gate). Modified Condition/Decision Coverage (MC/DC) scales linearly ($N+1$ minimum vectors) by proving every atomic boolean condition independently flips the overall decision outcome while holding all other conditions fixed."

**Q3: How do you mathematically prove that no overselling occurred during concurrency tests?**  
*Answer:* "Initial quota before each 5-VU run was reset deterministically to $Q = 10$. Across two 60-second 5-VU runs (`461` and `546` concurrent POST attempts), strictly `10` orders succeeded per run with HTTP 201 and all remaining competing attempts (`451` and `536`) returned domain HTTP 400 (`quota_sold_out`) with `0` unexpected failures (`0.00%`)."

**Q4: How does your GitHub Actions PR Quality Gate work?**  
*Answer:* "`.github/workflows/pr-gate.yml` enforces two fail-closed jobs: Job 1 checks Radon/Lizard complexity, enforces `pytest --cov=upstream.pretix.base.scoped_business_logic --cov-branch --cov-fail-under=100`, verifies $\ge 70\%$ AST mutation kill rate, runs offline OpenAPI datagen verification, and runs `pip-audit` (`0` CVEs). Job 2 boots the containerized Pretix stack and executes the live API, E2E, a11y, security, and master verification audits."
