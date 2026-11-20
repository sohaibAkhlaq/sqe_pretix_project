# Weekly Quality Report (Week 2) - Goal-Question-Metric (GQM) Framework

**Project:** SE3002 Software Quality Engineering - pretix Test Automation  
**Reporting Period:** Week 2 (Test Planning, Estimation, Static Analysis & White-Box Testing)  
**Authors:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Milestones Covered:** Gate 2 (`gate-2`), Gate 3 (`gate-3`)

---

## 1. GQM Hierarchy Definition

```mermaid
flowchart TD
    G1["Goal 1: Establish IEEE 829 Test Planning & PERT Estimation"]
    G2["Goal 2: Achieve Exhaustive White-Box Structural Coverage"]

    Q1_1["Q1.1: What is the 95% confidence interval for total project effort?"]
    Q1_2["Q1.2: Are all risks assessed and mitigated in a 5x5 matrix?"]
    Q2_1["Q2.1: Are all basis paths covered in decision functions?"]
    Q2_2["Q2.2: Is MC/DC achieved for multi-condition business rules?"]

    M1_1["M1.1: PERT E = 216.58h, sigma = 5.98h, CI [204.6h, 228.5h]"]
    M1_2["M1.2: 10 Risks (8 Product, 2 Project) mapped to RTM"]
    M2_1["M2.1: 100% Statement & 100% Branch Coverage (pytest-cov)"]
    M2_2["M2.2: 16-row MCC truth table + 5-test MC/DC minimal suite"]

    G1 --> Q1_1 --> M1_1
    G1 --> Q1_2 --> M1_2
    G2 --> Q2_1 --> M2_1
    G2 --> Q2_2 --> M2_2
```

---

## 2. Weekly Metric Tracking

| Goal | Question | Metric | Target | Measured Reality | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **G1: Planning** | Q1.1: Effort Model | PERT 3-point estimate distribution | $\pm 10\%$ CI | $E=216.58\text{h}$, $\sigma=5.98\text{h}$ | **PASS** |
| **G1: Planning** | Q1.2: Risk Management | Bi-directional RTM coverage | 100% | 12 Req + 10 Risks $\to$ 34 Tests | **PASS** |
| **G2: Coverage** | Q2.1: Statement Coverage | Pytest unit test statement coverage | 100% | **100.00% (161/161 statements)** | **PASS** |
| **G2: Coverage** | Q2.1: Branch Coverage | Pytest unit test branch coverage | 100% | **100.00% (28/28 branches)** | **PASS** |
| **G2: Coverage** | Q2.2: MC/DC Criteria | Orthogonal condition independence pairs | 4 pairs | 4 pairs proven in 5 tests | **PASS** |

---

## 3. Engineering Discoveries & Corrective Decisions
* **McCabe Cyclomatic Complexity:** Hand calculations confirmed exact 3-formula equality ($V(G) = E - N + 2P = P_R + 1 = R$) for `_compute_early_outs` ($V=6$) and `_check_quotas` ($V=8$).
* **SonarCloud Integration:** Identified radon maintainability index ($A, >85$) across all unit test modules.
