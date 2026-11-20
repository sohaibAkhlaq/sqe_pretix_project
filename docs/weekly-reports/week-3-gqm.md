# Weekly Quality Report (Week 3) - Goal-Question-Metric (GQM) Framework

**Project:** SE3002 Software Quality Engineering - pretix Test Automation  
**Reporting Period:** Week 3 (REST API Testing, Automated Data Generation, Use Cases & E2E)  
**Authors:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)  
**Milestones Covered:** Gate 4 (`gate-4`), Gate 5 (`gate-5`)

---

## 1. GQM Hierarchy Definition

```mermaid
flowchart TD
    G1["Goal 1: Validate REST API Contracts & Automated Data Generation"]
    G2["Goal 2: Automate End-to-End Use Cases with Playwright"]

    Q1_1["Q1.1: Does test data generator dynamically adapt to contract changes?"]
    Q1_2["Q1.2: Do API integration tests verify idempotency and transitions?"]
    Q2_1["Q2.1: Are all 30 execution flows covered across 6 Use Cases?"]
    Q2_2["Q2.2: Do headless browser tests capture full-page visual evidence?"]

    M1_1["M1.1: Quota change (10 -> 15) & Price change (50 -> 75) with 0 code edits"]
    M1_2["M1.2: 16 REST API integration tests passing (100% in 6.40s)"]
    M2_1["M2.1: 6 Normal, 12 Alt, 12 Exc flows automated (30/30)"]
    M2_2["M2.2: 5 Full-page PNG screenshots saved to reports/e2e/screenshots/"]

    G1 --> Q1_1 --> M1_1
    G1 --> Q1_2 --> M1_2
    G2 --> Q2_1 --> M2_1
    G2 --> Q2_2 --> M2_2
```

---

## 2. Weekly Metric Tracking

| Goal | Question | Metric | Target | Measured Reality | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **G1: API & Data** | Q1.1: Data Adaptability | Regeneration under modified business constraints | 0 test edits | 100% adaptive (3-point BVA + EP) | **PASS** |
| **G1: API & Data** | Q1.2: API Test Pass Rate | REST API integration test suite execution | 100% | **100% (16/16 passed in 6.40s)** | **PASS** |
| **G2: E2E Automation**| Q2.1: Flow Coverage | E2E use case flows automated | 30 flows | **30/30 flows automated** | **PASS** |
| **G2: E2E Automation**| Q2.2: Visual Artifacts | Full-page browser screenshots captured | $\ge 5$ | 5 screenshots verified | **PASS** |

---

## 3. Engineering Discoveries & Corrective Decisions
* **AJAX Cart Addition Race Condition (DEF-02):** Resolved Playwright timing issue by polling `wait_for_selector("text=Proceed with checkout")`.
* **Zero-Order Control Panel Empty State (DEF-03):** Adapted locator to recognize pretix empty state container (`"Nobody ordered a ticket yet"`).
