# SE3002 SQE Comprehensive Viva Preparation & Live Task Rehearsal Guide

**Project:** SE3002 Software Quality Engineering Final Project - pretix Test Automation  
**Team Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Standard:** Gold Medalist Defense - 100% Technical Mastery, Zero Hesitation  
**Milestone:** Phase 12

---

## 1. Member Defense Profiles & Individual Contribution Ownership

### Member 1: Sohaib (`24i-3108`, Git: `sohaibAkhlaq`) — Area A Lead
* **Primary Scope:** Static Analysis, White-Box Unit Testing, Basis Paths & MC/DC, Mutation Testing (`mutmut`, Custom BCR & ADR Operators), GitHub Actions CI PR Quality Gate.
* **Key Codebase Artifacts:**
  - `docs/cfg/cfg_analysis.md`: Control Flow Graphs and 3-formula CCN calculations ($V=6$ and $V=8$).
  - `docs/cfg/mcc_mcdc.md`: 16-row MCC truth table and 5-test MC/DC minimal suite.
  - `tests/team/unit/`: 49 unit tests with 100% statement and 100% branch coverage.
  - `scripts/run_mutation_tests.py`: 24 mutants, 2 custom operators (BCR, ADR), 100% mutation kill rate.
  - `.github/workflows/pr-gate.yml` & `docs/ci-gate-demo.md`: CI Quality Gate blocking non-compliant PRs.
* **Core Theoretical Defense:**
  - *Cyclomatic Complexity Proof:* $V(G) = E - N + 2P = P_R + 1 = R$. For `_compute_early_outs`, $14 - 10 + 2 = 6 = 5 \text{ predicates} + 1 = 6 \text{ regions}$.
  - *MC/DC Formulation:* For $D = C_1 \land C_2 \land C_3 \land C_4$, each condition $C_i$ is shown to independently affect outcome $D$ while holding all other conditions $C_{j \neq i}$ constant. Requires exactly $N+1 = 5$ tests.
  - *Custom Mutation Operators:*
    - Boundary Condition Replacement (BCR): Mutates strict inequality to non-strict inequality (`<` to `<=`, `>` to `>=`), testing off-by-one errors in capacity checks.
    - Arithmetic Delta Replacement (ADR): Mutates capacity offsets ($\pm 1$) and suppresses state restoration on cancellation.

---

### Member 2: M. Hasaam (`24i-3107`, Git: `M-Hasaam`) — Area B Lead
* **Primary Scope:** OpenAPI 3.0 Contract Specification, Automated Synthetic Test Data Generation (`tools/datagen/`), REST API Integration Testing, k6 Performance Baseline, Concurrency Stress & Chaos Fault Recovery.
* **Key Codebase Artifacts:**
  - `openapi/team-spec.yaml`: OpenAPI 3.0.3 contract covering 8 core endpoints.
  - `tools/datagen/generator.py` & `cli.py`: Dynamic 3-point BVA ($\min-1, \min, \min+1, \text{nom}, \max-1, \max, \max+1$) and EP generator.
  - `docs/regeneration-demo.md`: Demonstration of live zero-code test data adaptation.
  - `tests/team/api/`: 16 integration tests verifying idempotency, lifecycle, and restoration.
  - `tests/team/perf/`: k6 baseline ($p95 = 92.3\text{ms} < 500\text{ms}$), 5 VU concurrency (0 oversold), and Redis chaos test ($RTO = 0.66\text{s} < 15\text{s}$).
* **Core Theoretical Defense:**
  - *Dynamic Test Data Generation:* Explaining how modifying `config.yaml` propagates new boundary values across all test payloads without editing test assertions.
  - *Idempotency Header Mechanism:* Explaining `X-Idempotency-Key` hash caching in Redis, preventing duplicate holds on network retransmissions.
  - *Concurrency Invariant Proof:* Demonstrating how Redis distributed locks serialize checkout requests so that $\sum \text{Orders} \le Q_{\text{capacity}}$, preventing negative inventory.

---

### Member 3: Shaiman (`24i-3074`, Git: `ShaimanQasir`) — Area C Lead
* **Primary Scope:** Use Case Analysis (6 UCs, 30 Flows), Playwright E2E UI Automation, Usability/Accessibility (axe-core WCAG 2.1 AA with Before/After Remediation), Defensive Security & STRIDE Threat Modeling.
* **Key Codebase Artifacts:**
  - `docs/use-cases.md`: 6 Use Cases covering 30 execution flows (6 normal, 12 alt, 12 exc).
  - `tests/team/e2e/`: Playwright browser suite driving customer purchase, sold-out lockout, and control panel.
  - `tests/team/a11y/`: Automated axe-core audits detecting upstream logo missing `alt` defect (WCAG 1.1.1) and remediating it ($1 \to 0$ violations).
  - `docs/security-model.md` & `tests/team/security/`: STRIDE threat model, 5 trust zones, 8-endpoint RBAC authorization matrix, injection defenses, and `pip-audit` scan.
* **Core Technical Defense:**
  - *Upstream Accessibility Defect:* Demonstrating how axe-core detected `<img src="...pretix-logo.svg">` lacking `alt` on `/control/login/`, and walking through the patch that remediates it.
  - *Color Contrast Calculations:* Explaining how `#888888` on `#f8f9fa` failed WCAG AA ($3.2:1 < 4.5:1$) and how adjusting to `#495057` restored compliance ($5.8:1$).
  - *RBAC Authorization Matrix:* Explaining why Auditor tokens receive HTTP 403 on mutations, while Anonymous requests return HTTP 401 or redirect to login.

---

## 2. Anticipated Live Examiner Tasks & Step-by-Step Defense

### Live Task 1: "Change quota size from 10 to 20 and show me what happens to your tests."
* **Examiner Goal:** Test whether the team's data generation and test suites are hardcoded or dynamically adaptive.
* **Resolution Steps (M. Hasaam):**
  1. Open `tools/datagen/config.yaml` and change `quota.total_size` from `10` to `20`.
  2. Run `python -m tools.datagen.cli --config tools/datagen/config.yaml --out tools/datagen/generated_dataset.json`.
  3. Show the examiner: The 3-point boundary values dynamically shift:
     - Old: $\min=1, \text{nom}=5, \max-1=9, \max=10, \max+1=11$.
     - New: $\min=1, \text{nom}=10, \max-1=19, \max=20, \max+1=21$.
  4. Point to `docs/regeneration-demo.md` proving this capability was architected from Day 1.

---

### Live Task 2: "Introduce an off-by-one mutant in `_check_quotas` (`<` to `<=`) and show me how you catch it."
* **Examiner Goal:** Test whether the team truly understands mutation testing and boundary condition coverage.
* **Resolution Steps (Sohaib):**
  1. Explain: "In `_check_quotas`, the condition `avail[1] < diff` checks if available capacity is strictly less than required tickets. If mutated to `avail[1] <= diff`, the system rejects requests where available capacity exactly equals required tickets (e.g. 5 tickets available, buyer requests 5)."
  2. Run `python scripts/run_mutation_tests.py`.
  3. Point to **`mutant-12`** in the output table:
     - Operator: `BCR (Custom 1)`
     - Mutated Code: `avail[1] <= diff`
     - Status: **`KILLED`**
     - Killing Test Case: `test_path_4_insufficient_capacity_raises` / `test_boundary_exact_capacity_allowed`.
  4. Explain: "Our boundary test explicitly sends `diff == avail` and asserts success. The mutant threw an unexpected `OrderError`, killing the mutant instantly."

---

### Live Task 3: "Show me an Auditor token trying to cancel an order or mark it paid."
* **Examiner Goal:** Verify RBAC authorization enforcement live.
* **Resolution Steps (Shaiman):**
  1. Run `pytest tests/team/security/test_rbac_security.py -k "test_auditor_forbidden" -v`.
  2. Show live output:
     - `test_auditor_forbidden_from_creating_orders PASSED` (HTTP 403)
     - `test_auditor_forbidden_from_marking_order_paid PASSED` (HTTP 403)
     - `test_auditor_forbidden_from_canceling_order PASSED` (HTTP 403)
  3. Explain: "Pretix checks `has_event_permission(request.user, 'can_change_orders')`. The Auditor role only has `can_view_orders`. Django's permission middleware intercepts the request before touching business logic and returns `403 Forbidden`."

---

### Live Task 4: "Show me the upstream accessibility defect and your before/after fix."
* **Examiner Goal:** Verify authentic usability defect discovery and remediation.
* **Resolution Steps (Shaiman):**
  1. Open `docs/a11y-before-after.md`.
  2. Run `pytest tests/team/a11y/test_axe_accessibility.py -v`.
     - Show: axe-core detects `image-alt` violation on `<img src="...pretix-logo.svg">` on `/control/login/`.
  3. Run `pytest tests/team/a11y/test_a11y_remediation.py -v`.
     - Show: Test injects `alt="pretix logo"`, re-runs axe-core evaluation, and proves violations drop from **$1 \to 0$**.
  4. Show visual screenshots in `reports/a11y/screenshots/`:
     - `02_login_unremediated.png` (Missing alt)
     - `05_login_remediated.png` (Remediated)

---

### Live Task 5: "Kill Redis right now and show me the system recovering within 15 seconds."
* **Examiner Goal:** Verify chaos testing and high availability.
* **Resolution Steps (M. Hasaam):**
  1. Run `pytest tests/team/perf/test_fault_recovery.py -v -s`.
  2. The test prints:
     - `[CHAOS] Injecting Fault: Stopping pretix_redis container...`
     - Verifies database and web containers remain alive.
     - `[HEAL] Triggering Recovery: Restarting pretix_redis container...`
     - Measures recovery time and prints: `[RECOVERY CONFIRMED] RTO = 0.66 seconds (Target: < 15.0s)`.
  3. Explain: "Pretix’s connection pool catches socket drops gracefully. Once the container restarts, Redis socket re-attaches in $< 1\text{ second}$, preserving complete PostgreSQL data integrity."

---

## 3. High-Yield Question & Answer Defense Cheat-Sheet

**Q1: Why did you test two related workflows instead of just one?**  
*Answer:* "Workflow A (Order Placement) reads quota availability and decrements it upon completion. Workflow B (Order Cancellation / State Transitions) mutates order states and restores availability. Testing them together proves shared state consistency and conservation of finite inventory."

**Q2: What is the difference between MCC and MC/DC?**  
*Answer:* "Multiple Condition Coverage (MCC) tests all $2^N$ combinations of conditions in a compound decision (16 tests for BR2). Modified Condition/Decision Coverage (MC/DC) achieves linear scaling ($N+1 = 5$ tests) while still proving that every individual condition can independently affect the decision outcome."

**Q3: How do you mathematically prove that no overselling occurred during concurrency tests?**  
*Answer:* "Initial quota was $Q = 10$. Under 5 concurrent VUs issuing 280 order requests, exactly 10 orders received HTTP 201 Created. The remaining 130 requests received HTTP 400 (The quota is full). Final available quota was exactly 0. The capacity conservation invariant $\sum \text{Orders} \le Q_{\text{initial}}$ was preserved 100%."

**Q4: How does your GitHub Actions PR Quality Gate work?**  
*Answer:* "Every pull request into `main` must pass 4 gates: (1) Static complexity analysis ($CCN \le 10$), (2) Pytest with branch coverage $\ge 80\%$, (3) Mutation testing score $\ge 70\%$, and (4) Dependency vulnerability check (`pip-audit`). If any gate fails, GitHub Actions exits with code 1, marking the check red and blocking the merge."
