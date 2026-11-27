# Preserved Generative AI Prompt Log (Section 7 Compliance)

**Project:** SE3002 Software Quality Engineering — Automated Testing of `pretix v2026.9.3` (Section C)  
**Group Members:** Sohaib (`24i-3108`, Area 1), M. Hasaam (`24i-3107`, Area 2), Shaiman (`24i-3074`, Area 3)  
**AI Tool Disclosed:** Antigravity (Google DeepMind Agentic AI)  
**Companion Record:** See [`docs/ai-use-record.md`](docs/ai-use-record.md) for the full disclosure of tool, purpose, AI output, and student verification/modifications for every phase.

---

## Phase-by-Phase Preserved Prompts

### Phase 0 — Environment Scaffolding & Technical Spikes (`gate-0`)
> *"Analyze the SQE Final Project guidelines and phased plan. Scaffold the multi-container Docker environment for pretix v2026.9.3 and execute 5 technical spikes covering seeding, idempotency, Radon complexity, mutmut compatibility, Playwright UI, and k6 load."*

### Phase 1 — Scope, EARS Test Basis & Idempotent Reset (`gate-1`)
> *"Author docs/test-basis.md with 8 EARS requirements (FR1–FR8), 4 business rules (BR1–BR4), and shared quota state. Implement scripts/reset.py and verify mathematical idempotence R(R(S)) = R(S)."*

### Phase 2 — IEEE 829 Test Plan, PERT Estimation, Risk Register & RTM (`gate-2`)
> *"Create full 18-section IEEE 829-2008 Master Test Plan, 50-task PERT 3-point effort estimation with variance and confidence intervals, 5x5 risk register with 10 risks (8 product, 2 project), and bi-directional traceability matrix."*

### Phase 3 — Static Analysis, CFGs & White-Box Unit Testing (`gate-3`)
> *"Generate CFG Mermaid graphs and 3-formula McCabe proofs for _compute_early_outs, _check_quotas, and Order._can_be_paid. Build MCC/MC/DC suites on BR2 and BR4 directly against AST-verified production logic achieving 100% statement and branch coverage."*

### Phase 4 — OpenAPI 3.0, Automated Test Data Generation & API Integration (`gate-4`)
> *"Author openapi/team-spec.yaml for all 9 endpoint paths. Build automated Python test data generator with 3-point BVA and EP plus RBAC/idempotency/GET query vectors. Demonstrate zero-code adaptation when quota and price change and verify live API state read-backs."*

### Phase 5 — EARS Use Cases & Playwright E2E UI Automation (`gate-5`)
> *"Specify 6 Use Cases covering 30 flows (normal, alternate, exceptional). Automate end-to-end browser tests using Playwright against the live pretix container with JUnit/HTML reporting and full-page screenshots."*

### Phase 6 — Usability & Accessibility Evaluation (`gate-6`)
> *"Run automated WCAG 2.1 AA axe-core and Google Lighthouse audits on storefront and control panel (including logged-in orders). Implement durable server template fixes, verify genuine Tab/Enter keyboard traversal and BR1 over-quota recovery, and compare authentic before/after scores."*

### Phase 7 — Defensive Security, OWASP ZAP Passive Proxy & `pip-audit` (`gate-7`)
> *"Author docs/security-model.md with STRIDE threat model and RBAC matrix. Implement Playwright and pytest security suites covering 7 access decisions (Admin, Auditor, Anonymous), XSS, SQLi, parameter tampering, mass assignment, and HTTP security headers. Run OWASP ZAP in passive proxy mode during Playwright Workflows A & B and run pip-audit on both host and pretix_web container packages."*

### Phase 8 — AST Mutation Testing & GitHub Actions CI PR Gate (`gate-8`)
> *"Implement AST-based mutation testing engine with 2 custom operators (BCR and ADR) mutating scoped_business_logic.py directly via ast.NodeTransformer + compile(). Classify >=15 baseline survivors and configure .github/workflows/pr-gate.yml enforcing 100% scoped branch coverage, SonarQube quality gate, k6 benchmarks, and >=70% mutation score with a live blocked-to-green PR."*

### Phase 9 — Unified Grafana k6 Benchmarks & Redis Chaos Recovery (`gate-9`)
> *"Author unified parameterized script load_unified_60s.js (1 VU x2 and 5 VUs x2, 60s steady-state) for Grafana k6 OSS. Implement test_state_changing_recovery.py stopping pretix_redis mid-write, checking PostgreSQL zero-partial-writes, restarting Redis, retrying with identical X-Idempotency-Key, and verifying 0 duplicate records."*

### Phase 10 — Defect Management, RCAs, Pareto & Weekly GQM (`gate-10`)
> *"Compile docs/defects/defect-log.md with 12 IEEE 1044 defects linked to GitHub Issues and the Risk Register. Author RCA-01 on Quota Race Conditions and RCA-02 on Protected FK Deletions using 5 Whys and Fishbone diagrams. Perform Pareto 80/20 analysis and write 4 weekly GQM reports."*

### Phase 11 & 12 — Final Master Report, Rubric Audit & Submission Packaging (`v1.0-submission`)
> *"Cross-verify every module and rubric criterion in SQE_Final_Project Fall 2026.pdf against all code, tests, CI gates, and screenshots. Reconcile docs/MASTER_REPORT.md, verify 11/11 Grand Master Audit suites, render Project_24i-3108_24i-3107_24i-3074_C.pdf, and package Project_24i-3108_24i-3107_24i-3074_C.zip preserving .git history."*
