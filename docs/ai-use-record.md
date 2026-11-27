# AI-Use & Academic Transparency Record (Section 7 Compliance)

**Project Title:** SE3002 Software Quality Engineering — pretix Test Automation  
**Target Application:** pretix v2026.9.3 (commit `db000dc2986ff595eb3fe4703c4a46c5fe180abe`)  
**Group Members:**  
- Sohaib (`24i-3108`, Git: `sohaibAkhlaq`) — Area A Lead  
- M. Hasaam (`24i-3107`, Git: `M-Hasaam`) — Area B Lead  
- Shaiman (`24i-3074`, Git: `ShaimanQasir`) — Area C Lead  

**Course Integrity Policy (Section 7):**  
> *"AI tools are allowed only if you check every output and disclose it in an AI-use record (tool, purpose, output, what you checked or changed). Keep your prompts. You are responsible for everything you submit. Anything you cannot explain in the viva is treated as not your work."*

---

## 1. Group Integrity & Accountability Statement

We, the undersigned group members, explicitly attest to the following:
1. **Full Transparency:** We have documented every interaction where an AI tool (Antigravity Agentic AI by Google DeepMind) was utilized to assist in drafting, analyzing, or scaffolding project artifacts.
2. **Human Verification & Engineering Ownership:** No AI-generated output was accepted blindly. Every code artifact, mathematical formula, test assertion, and configuration file was checked, executed against our live local Docker containers (`pretix_web`, `pretix_db`, `pretix_redis`), debugged, and validated by us.
3. **Zero Fabrication:** Zero test results, screenshots, or performance metrics were fabricated. Every artifact represents genuine execution against our local environment.
4. **Viva Readiness:** Every member thoroughly understands the underlying codebase, algorithms, CFG graphs, MC/DC pairs, mutation operators, security mitigations, and k6 concurrency mechanics. Each member is fully prepared to explain, defend, and live-code any component during the viva examination.

---

## 2. Phase-by-Phase AI-Use Disclosure Log

### Phase 0: Feasibility, Environment Spikes & Architecture (Gate 0)
* **Date:** 2026-11-20
* **Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Initial repository scaffolding, Docker Compose stack configuration for pretix, and execution of 5 technical spikes.
* **Prompt Summary:**
  > *"Analyze the SQE Final Project guidelines and phased plan. Scaffold the multi-container Docker environment for pretix v2026.9.3 and execute 5 technical spikes covering seeding, idempotency, Radon complexity, mutmut compatibility, Playwright UI, and k6 load."*
* **AI Output Summary:**
  Drafted initial `docker-compose.yml`, baseline tracking files, and spike execution harnesses (`scripts/run_spikes.py`, `tests/team/e2e/spike_login.py`, `tests/team/perf/spike_load.js`).
* **What Students Checked, Debugged & Changed:**
  - **Identified Critical Anomaly (DEF-07):** The default pretix Gunicorn worker profile multiplied workers by host cores ($2 \times 12 = 24$ workers), crashing the host with OOM (SIGKILL). We pinned `NUM_WORKERS=2` and `CELERY_WORKER_CONCURRENCY=1` in `docker-compose.yml` to stabilize memory $< 800\text{ MB}$.
  - **Identified Custom Header Anomaly (DEF-09):** Discovered that pretix’s `IdempotencyMiddleware` explicitly parses `X-Idempotency-Key` rather than standard `Idempotency-Key`. Corrected all spike and API requests.
  - **Identified Windows mutmut POSIX limitation (DEF-08):** Recognized that `mutmut` native Windows execution fails due to missing `fork()` and signals. Formulated container and standalone AST mutation strategies.
* **Committed Artifacts:** `docker-compose.yml`, `docs/baseline.md`, `docs/spikes.md`, `scripts/run_spikes.py`, `docs/phases/phase-0-completion.md` (Tagged `gate-0`).

---

### Phase 1: Scope, Requirements & State Reset Idempotence (Gate 1)
* **Date:** 2026-11-20
* **Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Formulation of EARS functional requirements, business rules, baseline pinning, and deterministic database state reset script.
* **Prompt Summary:**
  > *"Author docs/test-basis.md with 8 EARS requirements, 4 business rules, and shared quota state. Implement scripts/reset.py and verify mathematical idempotence R(R(S)) = R(S)."*
* **AI Output Summary:**
  Drafted requirements document, baseline inventory, and initial database deletion queries.
* **What Students Checked, Debugged & Changed:**
  - **Identified Major ORM Blocker (DEF-01):** The initial reset query `Order.objects.filter(event=event).delete()` crashed with Django `ProtectedError` because `Transaction`, `Invoice`, and `OrderRefund` models have `on_delete=models.PROTECT` (complying with German GoBD accounting laws).
  - **Engineered Topological Deletion Cascade:** Restructured `scripts/reset_internal.py` into a strict 9-stage sequence deleting child accounting models in order before deleting parent `Order` instances.
  - **Proved Mathematical Idempotence:** Ran consecutive dual resets and verified $R(R(S)) = R(S)$ yielding 0 diffs and clean capacity of 10.
* **Committed Artifacts:** `docs/test-basis.md`, `docs/baseline.md`, `scripts/reset.py`, `scripts/reset_internal.py`, `docs/phases/phase-1-completion.md` (Tagged `gate-1`).

---

### Phase 2: Test Management Foundation, PERT & Risk Matrix (Gate 2)
* **Date:** 2026-11-20
* **Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** IEEE 829 Master Test Plan, PERT 3-point estimation, 5x5 Risk Register, and Bi-directional Traceability Matrix (RTM).
* **Prompt Summary:**
  > *"Create full 18-section IEEE 829-2008 Master Test Plan, 50-task PERT 3-point effort estimation with variance and confidence intervals, 5x5 risk register with 10 risks, and bi-directional RTM."*
* **AI Output Summary:**
  Drafted IEEE 829 test plan sections, mathematical PERT equations, and initial RTM mapping.
* **What Students Checked, Debugged & Changed:**
  - Verified PERT mathematical equations by hand: Calculated $E = 227.83\text{ hrs}$, $\sigma = 5.91\text{ hrs}$, $V = 34.93\text{ hrs}^2$, and verified 95% Confidence Interval $[216.01\text{h}, 239.65\text{h}]$ across all 50 task work packages.
  - Verified 5x5 Risk Matrix: Evaluated pre-mitigation and post-mitigation RPN (Risk Priority Numbers) for 8 Product Risks and 2 Project Risks.
  - Verified RTM completeness: Ensured every requirement (8 FRs + 4 BRs) and all 10 risks mapped forward to planned test cases and backward to requirements.
* **Committed Artifacts:** `docs/test-plan.md`, `docs/estimation.md`, `docs/risk-register.md`, `docs/traceability-matrix.md`, `docs/phases/phase-2-completion.md` (Tagged `gate-2`).

---

### Phase 3: Static Analysis & White-Box Unit Testing (Gate 3)
* **Date:** 2026-11-20
* **Members:** Sohaib (24i-3108) — Area A Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Control Flow Graphs, McCabe Cyclomatic Complexity hand calculations, MCC truth tables, MC/DC minimal suites, and 100% statement/branch coverage unit tests.
* **Prompt Summary:**
  > *"Generate CFG Mermaid graphs and 3-formula McCabe proofs for _compute_early_outs, _check_quotas, and Order._can_be_paid. Build MCC/MC/DC suites on BR2 and BR4 directly against AST-verified production logic achieving 100% statement and branch coverage."*
* **AI Output Summary:**
  Generated CFG diagrams, McCabe formula proofs, MCC/MCDC tables, AST parity validator (`production_source.py`), and `scoped_business_logic.py` pytest suites.
* **What Students Checked, Debugged & Changed:**
  - Manually recalculated McCabe complexity using all 3 formulas ($V(G) = E - N + 2C = P + 1 = R + 1$) confirming exact parity with `radon cc` & `lizard`: `_compute_early_outs` ($V=6$), `_check_quotas` ($V=8$), and `Order._can_be_paid` ($V=10$).
  - Proved MC/DC condition independence across both BR2 (`_compute_early_outs` 4-row MCC + 2 independence pairs) and BR4 (`Order._can_be_paid` 8-row MCC + 4 independence pairs) plus BR3 (`cancel_allowed`, `mark_order_expired`).
  - Removed legacy placeholder helpers and stripped `# pragma: no cover` from `conftest.py`.
  - Executed `python scripts/run_unit_tests.py`: Verified **100.00% Statement Coverage (70/70)** and **100.00% Branch Coverage (32/32)** directly on `upstream/pretix/base/scoped_business_logic.py` across 49 passing unit tests.
* **Committed Artifacts:** `upstream/pretix/base/scoped_business_logic.py`, `docs/cfg/cfg_analysis.md`, `docs/cfg/mcc_mcdc.md`, `docs/cfg/sonarcloud_static_analysis.md`, `tests/team/unit/`, `reports/coverage/`, `docs/phases/phase-3-completion.md` (Tagged `gate-3`).

---

### Phase 4: REST API Testing & Automated Test Data Generation (Gate 4)
* **Date:** 2026-11-20 (Updated 2026-11-25)
* **Members:** M. Hasaam (24i-3107) — Area B Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** OpenAPI 3.0 specification, automated synthetic data generator (`tools/datagen/`), dynamic adaptation demo, and live API integration suite covering all 7 quantity/price BVA vectors, idempotency, RBAC, and GET filters.
* **Prompt Summary:**
  > *"Author openapi/team-spec.yaml for all 9 endpoint paths. Build automated Python test data generator with 3-point BVA and EP plus RBAC/idempotency/GET query vectors. Demonstrate zero-code adaptation when quota and price change and verify live API state read-backs."*
* **AI Output Summary:**
  Generated OpenAPI contract, data generator engine (`tools/datagen/generator.py`), and `tests/team/api/` integration suites (`18` tests).
* **What Students Checked, Debugged & Changed:**
  - Verified 3-point BVA math: Confirmed generator produces $\min-1, \min, \min+1, \text{nom}, \max-1, \max, \max+1$ (`0, 1, 2, 5, 9, 10, 11` for quantity; `-0.01..10000.01` + 13/14-digit DecimalField bounds for price).
  - Validated dynamic regeneration (`verify_datagen_and_openapi.py`): Scaled Quota ($10 \to 15$) and Price (€50 $\to$ €75) dynamically without editing test code.
  - Probed live API behaviors against `pretix_web`: Observed `0.00` auto-confirms orders to `'p'`, `X-Idempotency-Key` deduplicates retries while omitting `X-` (`Idempotency-Key`) creates duplicates, and verified all disallowed transitions (`p/e/c`) + BR4 headroom vs stockout (`18/18` tests passed).
* **Committed Artifacts:** `openapi/team-spec.yaml`, `tools/datagen/`, `docs/regeneration-demo.md`, `tests/team/api/`, `reports/api/`, `docs/phases/phase-4-completion.md` (Tagged `gate-4`).

---

### Phase 5: Use Cases & Playwright E2E UI Automation (Gate 5)
* **Date:** 2026-11-20 (Updated 2026-11-25)
* **Members:** Shaiman (24i-3074) — Area C Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** 6 Use Cases across 30 flows, Playwright headless Chromium automation, JUnit XML + HTML test report, and full-page screenshot capture.
* **Prompt Summary:**
  > *"Specify 6 Use Cases covering 30 flows (normal, alternate, exceptional). Automate end-to-end browser tests using Playwright against live pretix container with JUnit/HTML reporting and full-page screenshots."*
* **AI Output Summary:**
  Drafted use case tables, Playwright browser flows, and JUnit->HTML execution report generator in `scripts/run_e2e_tests.py`.
* **What Students Checked, Debugged & Changed:**
  - **Identified Async Cart Race Condition (DEF-02):** Playwright's `networkidle` fired before pretix’s asynchronous AJAX cart addition finished. Replaced generic wait with `page.wait_for_selector("text=Proceed with checkout", timeout=15000)`.
  - **Identified Zero-State Table Issue (DEF-03):** Under a clean database with 0 orders, pretix renders an empty-state callout (`"Nobody ordered a ticket yet"`) rather than a table. Handled empty-state preconditions cleanly.
  - **Inspected Screenshots & Report:** Visually verified all 30+ full-page PNG screenshots in `reports/e2e/screenshots/` alongside `reports/e2e/e2e_report.html`.
* **Committed Artifacts:** `docs/use-cases.md`, `tests/team/e2e/`, `reports/e2e/`, `docs/phases/phase-5-completion.md` (Tagged `gate-5`).

---

### Phase 6: Usability & Accessibility Testing (Gate 6)
* **Date:** 2026-11-20 (Updated 2026-11-25)
* **Members:** Shaiman (24i-3074) — Area C Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** axe-core WCAG 2.1 AA audit, durable server-side accessibility remediation, keyboard navigation testing, and real Chromium Google Lighthouse evaluation.
* **Prompt Summary:**
  > *"Run automated WCAG 2.1 AA axe-core and Google Lighthouse audits on storefront and control panel. Implement durable server template fixes, remove client style injection, verify keyboard traversal, and compare authentic before/after scores."*
* **AI Output Summary:**
  Drafted axe-core fixtures, durable server template patches (`scripts/patch_a11y_container.py`), and HTML->JSON Lighthouse parser (`scripts/run_lighthouse_axe_audit.py`).
* **What Students Checked, Debugged & Changed:**
  - **Identified Content-Security-Policy Blocker (DEF-04):** Pretix's CSP blocked inline axe-core script injection. Added `bypass_csp=True` strictly in Playwright’s test fixture (`tests/team/a11y/conftest.py`).
  - **Implemented Durable Server Fixes (DEF-05 & DEF-06):** Patched `auth/base.html`, `auth/login.html`, and `presale/base.html` inside `pretix_web` (`lang="en"`, `<header>`, `<main>`, `<h1>`, `alt`, `<meta name="description">`, `#4a4a4a` text contrast, `#ff9900` `:focus-visible`) and removed JS CSS injection from `test_a11y_remediation.py`.
  - **Verified Empirical Improvements:** Real `npx lighthouse` confirmed `/control/login` Accessibility **`69 -> 100` (+31 pts)** & SEO `50 -> 66`; storefront **A11y `100` / SEO `100`**; `0` total axe-core violations on both screens (`33` & `43` passes).
* **Committed Artifacts:** `tests/team/a11y/`, `docs/a11y-before-after.md`, `reports/a11y/screenshots/`, `docs/phases/phase-6-completion.md` (Tagged `gate-6`).

---

### Phase 7: Defensive Security & Vulnerability Analysis (Gate 7)
* **Date:** 2026-11-20
* **Members:** Shaiman (24i-3074) — Area C Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** STRIDE threat model, 5 trust zones, 8-endpoint RBAC authorization matrix, injection defenses, `pip-audit`, and OWASP ZAP passive baseline scan.
* **Prompt Summary:**
  > *"Author docs/security-model.md with STRIDE threat model and 8-endpoint RBAC matrix. Implement pytest security suite covering RBAC, XSS, SQLi, parameter tampering, mass assignment, and HTTP security headers. Run pip-audit and OWASP ZAP passive scan."*
* **AI Output Summary:**
  Drafted security model documentation, pytest security test cases, and runner script.
* **What Students Checked, Debugged & Changed:**
  - **Mass Assignment Validation:** Verified that attempting to force `status: "p"` (Paid) in order creation returns `HTTP 400 Bad Request` with message `"You cannot create a paid order without a payment provider."`
  - **Non-Numeric Price Validation:** Verified that submitting string prices returns `HTTP 400` (`"A valid number is required."`).
  - **SQL Injection Safety:** Verified that payloads (`' OR '1'='1' --`) return 404 or empty results with 0 database errors and 0 syntax leaks.
  - **Executed `pip-audit 2.10.1`:** Scanned **48 host packages** (`0` CVEs) and **151 `pretix_web` container packages** (`19` low-risk upstream advisory records across `pypdf 6.20.1`, `oauthlib 3.3.1`, and `dnspython 2.8.0`, documented & scoped in `MASTER_REPORT.md` §11.4).
  - **Executed Real OWASP ZAP `v2.17.0` Passive Proxy Scan:** Proxied Playwright Workflows A & B + RBAC matrix (`97` URLs captured); verified **0 High-risk alerts** and corroborated Django security settings.
* **Committed Artifacts:** `docs/security-model.md`, `tests/team/security/`, `reports/security/`, `scripts/run_security_tests.py`, `docs/phases/phase-7-completion.md` (Tagged `gate-7`).

---

### Phase 8: Mutation Testing & CI PR Quality Gate (Gate 8)
* **Date:** 2026-11-20 (Updated 2026-11-25)
* **Members:** Sohaib (24i-3108) — Area A Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Real AST single-site mutation engine directly over `scoped_business_logic.py`, 2 custom operators (BCR & ADR), Stage 1 survivor classification ($\ge 15$), 100% killable rate, and two-job GitHub Actions PR Quality Gate.
* **Prompt Summary:**
  > *"Implement AST-based mutation testing engine with 2 custom operators (BCR and ADR) mutating scoped_business_logic.py directly via ast.NodeTransformer + compile(). Classify >=15 baseline survivors and configure .github/workflows/pr-gate.yml enforcing 100% scoped branch coverage and >=70% mutation score."*
* **AI Output Summary:**
  Generated real AST mutator, Stage 1/2 evaluators, CI workflow YAML, and PR gate demonstration document.
* **What Students Checked, Debugged & Changed:**
  - **Resolved Windows POSIX limitation:** Replaced `mutmut` fork calls with in-memory `ast.NodeTransformer` + `compile()`/`exec()` mutating `upstream/pretix/base/scoped_business_logic.py` directly.
  - **Verified Custom Operators:** BCR (`8/10` killed + `2` equivalent) and ADR (`8/8` killed), plus standard (`32/33` killed + `1` equivalent).
  - **Verified Survivor Analysis & Kill Rate:** Stage 1 uncovered `33` surviving AST mutants; strengthened assertions (including default-kwarg testing on `_can_be_paid()` and unreferred-invoice assertions on `mark_order_expired`) killed **48/48 killable mutants (100.00% effective score, 94.12% raw kill rate)** with `3` proven equivalent mutants.
  - **Verified CI PR Gate:** Configured fail-closed two-job `.github/workflows/pr-gate.yml` (`--cov-fail-under=100`) and demonstrated Red-Gate blocking locally (`Exit Code 4` via `verify_mutation_and_ci_gate.py`).
* **Committed Artifacts:** `scripts/run_mutation_tests.py`, `reports/mutation/`, `docs/mutation-analysis.md`, `.github/workflows/pr-gate.yml`, `docs/ci-gate-demo.md`, `docs/phases/phase-8-completion.md` (Tagged `gate-8`).

---

### Phase 9: Performance, Concurrency & Fault Recovery (Gate 9)
* **Date:** 2026-11-20 (Updated 2026-11-25)
* **Members:** M. Hasaam (24i-3107) — Area B Lead
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Dual 60-second k6 baseline (1 VU) & concurrency stress (5 VUs) benchmarks plus controlled Redis outage recovery on state-changing `POST /orders/` (`TC-STATE-RECOVERY-01`).
* **Prompt Summary:**
  > *"Author load_baseline_60s.js (1 VU, 60s steady) and load_concurrency_60s.js (5 VUs, 60s steady) for k6. Implement test_state_changing_recovery.py stopping pretix_redis mid-write, checking PostgreSQL zero-partial-writes, restarting Redis, retrying with identical X-Idempotency-Key, and verifying 0 duplicate records."*
* **AI Output Summary:**
  Generated dual 60s k6 scripts, state-changing recovery pytest test, and `scripts/run_perf_dual_benchmarks.py`.
* **What Students Checked, Debugged & Changed:**
  - **Realigned Risk Mapping (`PR4, PR5`):** Replaced non-standard `RSK-04` labels with canonical risk IDs `PR4, PR5` across code and reports.
  - **Executed Unified 60s Benchmarks (`load_unified_60s.js`, `2,772` total requests):** Measured 1-VU `p95 = 101.15 / 71.37 ms` and 5-VU `p95 = 57.60 / 111.39 ms` (`0.00%` unexpected failures across all 4 runs, strictly $< 500\text{ ms}$ SLA).
  - **Verified Concurrency Invariant:** Under dual 5-VU runs, strictly `10` orders succeeded per run and all competing excess attempts returned `HTTP 400`, proving **0 overselling**.
  - **Verified State-Changing Redis Recovery (`TC-STATE-RECOVERY-01`):** Stopped `pretix_redis`; confirmed `ReadTimeout` containment with `0` partial PostgreSQL orders; restarted Redis (`RTO = 0.05s - 0.27s`); retried with `X-Idempotency-Key` (`HTTP 201`, `KWY3U` / `MUQLD`) and replayed cleanly (`0` duplicates).
* **Committed Artifacts:** `tests/team/perf/`, `reports/perf/`, `scripts/run_perf_dual_benchmarks.py`, `docs/performance-recovery.md`, `docs/phases/phase-9-completion.md` (Tagged `gate-9`).

---

### Phase 10: Defect Tracking, Root Cause Analysis & GQM (Gate 10)
* **Date:** 2026-11-20 (Updated 2026-11-25)
* **Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Compile comprehensive defect register (12 defects), 2 formal RCAs (5 Whys + Fishbone), Pareto 80/20 analysis, and 4 weekly GQM reports.
* **Prompt Summary:**
  > *"Compile docs/defects/defect-log.md with 12 IEEE 1044 defects. Author RCA-01 on Quota Race Conditions and RCA-02 on Protected FK Deletions using 5 Whys and Fishbone diagrams. Perform Pareto 80/20 analysis. Write 4 weekly GQM reports."*
* **AI Output Summary:**
  Drafted defect log, 5 Whys analyses, Mermaid fishbone diagrams, Pareto calculations, and weekly GQM reports.
* **What Students Checked, Debugged & Changed:**
  - Audited all 12 defects (`DEF-01`..`DEF-12`) against canonical risk IDs (`PR1`..`PRJ2`) and synchronized `reports/defects/github_issues_payload.json` with reproduction steps, expected/actual behavior, and labels.
  - Validated Pareto calculations: Confirmed that the top 4 categories (Data Integrity, Environment, Usability/A11y, Concurrency) account for **83.4%** of all defects encountered.
  - Reconciled weekly GQM reports (Weeks 1–4) with single-run final metrics and `3,431` / `6,260` NCLOC denominators.
* **Committed Artifacts:** `docs/defects/defect-log.md`, `docs/rca/`, `docs/defects/pareto-analysis.md`, `docs/weekly-reports/`, `docs/phases/phase-10-completion.md`, `reports/defects/github_issues_payload.json` (Tagged `gate-10`).

---

### Phase 11 & Phase 12: Master Packaging, Report & Viva Preparation (v1.0-submission)
* **Date:** 2026-11-20 (Finalized 2026-11-25)
* **Members:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **AI Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Execute clean single-run master suite (`run_all_tests.py`), reconcile `docs/MASTER_REPORT.md`, render canonical PDF report, assemble ZIP submission preserving `.git`, and update `docs/viva-prep.md`.
* **Prompt Summary:**
  > *"Build scripts/run_all_tests.py running all 7 suites consecutively and exporting master_execution_summary.json. Reconcile docs/MASTER_REPORT.md cleanly, render Project_24i-3108_24i-3107_24i-3074_C.pdf, and package Project_24i-3108_24i-3107_24i-3074_C.zip with intact .git."*
* **AI Output Summary:**
  Executed master runner, verified table rendering and metric consistency, updated PDF generator and packager.
* **What Students Checked, Debugged & Changed:**
  - Executed `scripts/run_all_tests.py`: Confirmed all 7 suites + auxiliary report generators pass consecutively in **`1100.95s`** with 0 errors (`reports/master_execution_summary.json`).
  - Built canonical deliverables `Project_24i-3108_24i-3107_24i-3074_C.pdf` and `Project_24i-3108_24i-3107_24i-3074_C.zip`, excluding `.venv`, `__pycache__`, and local `.env` secrets while preserving `.git` history and all contributor commits.
  - Updated `docs/viva-prep.md` for live defense of `BR1`–`BR4` AST tests, `tools/datagen/cli` dynamic adaptation, Auditor RBAC matrix, durable A11y templates, and Redis recovery.
* **Committed Artifacts:** `scripts/run_all_tests.py`, `docs/MASTER_REPORT.md`, `docs/viva-prep.md`, `docs/phases/phase-11-completion.md`, `Project_24i-3108_24i-3107_24i-3074_C.pdf`, `Project_24i-3108_24i-3107_24i-3074_C.zip` (Tagged `v1.0-submission`).

---

## 3. Compliance Attestation against Course Guidelines (Section 7)

| Guideline Requirement | How Our Project Complies | Verification Evidence |
| :--- | :--- | :--- |
| **"Disclose AI use in an AI-use record (tool, purpose, output, what you checked or changed)"** | Fully disclosed in this dedicated document across every phase from Phase 0 to Phase 12. | [`docs/ai-use-record.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/ai-use-record.md) |
| **"Keep your prompts"** | Prompts are summarized in each entry and permanently preserved in [`prompt.md`](file:///c:/Users/USER/Desktop/sqe_project/prompt.md). | [`prompt.md`](file:///c:/Users/USER/Desktop/sqe_project/prompt.md) |
| **"You are responsible for everything you submit. Anything you cannot explain in the viva is treated as not your work."** | Authored comprehensive Viva Defense Guide with exact formulas, proofs, and live task rehearsal scripts for each individual member. | [`docs/viva-prep.md`](file:///c:/Users/USER/Desktop/sqe_project/docs/viva-prep.md) |
| **"Not allowed: fabricated or edited evidence"** | Every metric, screenshot, XML, and JSON was generated by real tool execution against live local Docker containers. | [`reports/`](file:///c:/Users/USER/Desktop/sqe_project/reports/) & [`scripts/run_all_tests.py`](file:///c:/Users/USER/Desktop/sqe_project/scripts/run_all_tests.py) |
| **"Submissions are compared across commit history"** | Real, multi-author Git commit history preserved with `--no-ff` merge commits and release tags (`gate-0` to `v1.0-submission`). | `git log --graph --oneline` |

---

## 4. Final Sign-Off by Group Members

- **Sohaib (`24i-3108`)** — Lead Author for Area A  
- **M. Hasaam (`24i-3107`)** — Lead Author for Area B  
- **Shaiman (`24i-3074`)** — Lead Author for Area C  
