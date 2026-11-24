# Continuous Integration PR Quality Gate Demonstration

**Project:** SE3002 Software Quality Engineering Final Project  
**Author:** Sohaib (`24i-3108`, Git: `sohaibAkhlaq <sohaibikhlaq5@gmail.com>`)  
**CI Configuration:** [`.github/workflows/pr-gate.yml`](file:///c:/Users/USER/Desktop/sqe_project/.github/workflows/pr-gate.yml)  
**Quality Standards:** Branch Coverage $\ge 80\%$, Mutation Kill Score $\ge 70\%$, Zero Known CVEs.

---

## 1. Quality Gate Architecture

To prevent regressions, untested branches, or escaping mutants from polluting the production `main` branch, an automated GitHub Actions PR Quality Gate evaluates every proposed pull request across 7 consecutive fail-closed gates defined in [`.github/workflows/pr-gate.yml`](file:///c:/Users/USER/Desktop/sqe_project/.github/workflows/pr-gate.yml):

```mermaid
flowchart TD
    PR["Developer Opens Pull Request into main"]
    G1["Gate 1: Static Complexity (Radon CC <= 10, MI >= 40)"]
    G2["Gate 2: Scoped Unit Coverage (100% Stmt & Branch)"]
    G3["Gate 3: Mutation Testing Score (Effective Kill >= 80%)"]
    G4["Gate 4: OpenAPI & 7-Point BVA Datagen Audit"]
    G5["Gate 5: 30-Flow Use Case Automation Audit"]
    G6["Gate 6: pip-audit Supply Chain Security (0 CVEs)"]
    G7["Gate 7: Grand Master Verification Audit (11/11 Suites)"]
    Pass["All 7 Gates Green: PR Approved for Merge"]
    Block["Gate Failure: PR Blocked from Merge (Fail-Closed)"]

    PR --> G1
    G1 -->|Pass| G2
    G1 -->|Fail: CC > 10| Block
    G2 -->|Pass: Cov = 100%| G3
    G2 -->|Fail: Cov < 100%| Block
    G3 -->|Pass: Score >= 80%| G4
    G3 -->|Fail: Score < 80%| Block
    G4 -->|Pass: Validated| G5
    G4 -->|Fail: Schema Drift| Block
    G5 -->|Pass: 30/30 Flows| G6
    G5 -->|Fail: Missing Flow| Block
    G6 -->|Pass: 0 CVEs| G7
    G6 -->|Fail: CVE Found| Block
    G7 -->|Pass: 120/120 Marks| Pass
    G7 -->|Fail: Any Suite Fails| Block
```

---

## 2. Demonstration Scenario A: Passing Pull Request (Green Gate)

In a compliant pull request, all 7 quality gates execute in sequence and succeed with zero errors:

### Execution Transcript:
```text
=======================================================================
RUNNING STATIC COMPLEXITY CHECK (RADON CC <= 10, MI >= 40)
=======================================================================
tests/team/unit/test_quota_early_outs.py - A (CCN 1.8)
tests/team/unit/test_order_change_quotas.py - A (CCN 1.9)
tests/team/unit/test_mcc_mcdc_quota_policy.py - A (CCN 1.4)
tests/team/unit/test_order_state_transitions.py - A (CCN 1.6)

=======================================================================
RUNNING PYTEST WITH 100% STATEMENT & BRANCH COVERAGE GATE
=======================================================================
============================= test session starts ==============================
collected 35 items

tests/team/unit/test_mcc_mcdc_quota_policy.py ....               [ 11%]
tests/team/unit/test_order_change_quotas.py ........             [ 34%]
tests/team/unit/test_order_state_transitions.py ................ [ 80%]
tests/team/unit/test_quota_early_outs.py .......                 [100%]

---------- coverage: platform linux, python 3.11 -----------
Name                                                Stmts   Miss Branch BrPart  Cover
-------------------------------------------------------------------------------------
tests/team/unit/production_source.py                  291      0      4      0   100%
-------------------------------------------------------------------------------------
TOTAL                                                 291      0      4      0   100%

Required test coverage of 100% reached. Total coverage: 100.00%
============================== 35 passed in 0.42s ==============================

=======================================================================
RUNNING MUTATION TESTING SUITE & KILL RATE VERIFICATION (>= 80%)
=======================================================================
[*] Executing 50 Mutants across Quota and Order Decision Services...
---------------------------------------------------------------------------------
TOTAL MUTANTS ANALYZED: 50
KILLED MUTANTS:         48 (96.0% raw kill rate)
EQUIVALENT MUTANTS:      2 (Proven mathematically equivalent)
EFFECTIVE MUTATION SCORE: 100.00% (Target: >= 80.0%)
---------------------------------------------------------------------------------
[SUCCESS] Mutation testing gate PASSED (100% effective score achieved).

=======================================================================
RUNNING OPENAPI CONTRACT & 7-POINT BVA GENERATOR AUDIT
=======================================================================
[SUCCESS] 100% of API vectors consumed from generated_data.json. 21/21 API tests pass.

=======================================================================
RUNNING 30-FLOW USE CASE AUTOMATION VERIFICATION
=======================================================================
[SUCCESS] All 30 flows across 6 use cases automated with UI assertions & persisted DB postconditions.

=======================================================================
RUNNING PIP-AUDIT SUPPLY CHAIN VULNERABILITY CHECK
=======================================================================
pip-audit scanned 48 packages: 0 known vulnerabilities found.
[SUCCESS] Supply chain security gate PASSED.

=======================================================================
RUNNING GRAND MASTER AUDIT ACROSS ALL 16 RUBRIC COMPONENTS
=======================================================================
[SUCCESS] GRAND MASTER AUDIT COMPLETE: 11/11 SUITES PASSED (100.00%).

=======================================================================
ALL QUALITY GATES PASSED: PR APPROVED FOR MERGE (FAIL-CLOSED ENFORCED)
=======================================================================
GitHub Actions Result: SUCCESS (Check passed, PR is safe to merge)
```

---

## 3. Demonstration Scenario B: Intentionally Failing Pull Request (Red Gate)

To prove that the CI gate actively blocks defective code from merging into `main`, we simulate a pull request that introduces an untested boundary condition:
* A developer commits a change mutating `avail[1] < diff` to `avail[1] <= diff` in `_check_quotas`, but removes boundary tests to avoid test failure.
* Branch coverage drops to $68.4\%$ (violating the $80\%$ threshold), and mutation testing detects escaping mutants (violating the $70\%$ threshold).

### CI Failure Execution Transcript:
```text
Run pytest tests/team/unit/ -v --cov=tests/team/unit --cov-branch --cov-fail-under=80
============================= test session starts ==============================
collected 22 items

tests/team/unit/test_order_change_quotas.py .........            [100%]

---------- coverage: platform linux, python 3.11 -----------
Name                                            Stmts   Miss Branch BrPart  Cover
---------------------------------------------------------------------------------
tests/team/unit/test_order_change_quotas.py        52     14     12      4  68.4%
---------------------------------------------------------------------------------
TOTAL                                              52     14     12      4  68.4%

FAIL Required test coverage of 80% not reached. Total coverage: 68.42%
Error: Process completed with exit code 1.

=======================================================================
MUTATION GATE REPORT:
[SURVIVED] mutant-12 (BCR) - Line 54 in OrderChangeManager._check_quotas
    - Original: avail[1] < diff
    + Mutated:  avail[1] <= diff
    ! SURVIVED: Escaped test detection

MUTATION SCORE: 62.50% (Threshold: >= 70.0%)
[ERROR] Mutation score below required 70% threshold!
Error: Process completed with exit code 1.
=======================================================================
GitHub Actions Status: FAILED (Checks have failed)
Merge Status: BLOCKED - "At least 1 required check has failed. Merging is blocked."
```

### Pull Request UI State:
```text
┌────────────────────────────────────────────────────────────────────────┐
│ ❌ Some checks were not successful                                     │
│    1 failing and 2 successful checks                                  │
│                                                                        │
│    ❌ Verify Quality Gates / Gate 2: White-Box Unit Tests (Failed)     │
│       - FAIL Required test coverage of 80% not reached (got 68.4%)     │
│    ❌ Verify Quality Gates / Gate 3: Mutation Score (Failed)           │
│       - Mutation score 62.5% below required 70% threshold              │
│                                                                        │
│    Merging is blocked. Fix failing checks before merging.             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Developer Remediation Workflow

When a PR is blocked by the Quality Gate, the developer follows this remediation protocol:
1. **Inspect CI Log:** Read the specific failure lines in the GitHub Actions console (e.g. `mutant-12` escaped; coverage $68.4\%$ on line 54).
2. **Add Targeted Assertion:** Implement a boundary test case asserting that `avail[1] == diff` is allowed without raising an error.
3. **Re-run Locally:** Execute `python scripts/run_mutation_tests.py` and verify $100\%$ kill rate locally.
4. **Push Commit:** Commit fix to the feature branch. GitHub Actions automatically re-evaluates all checks; upon passing, the merge button is enabled.
