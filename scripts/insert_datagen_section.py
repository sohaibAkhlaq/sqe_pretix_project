import os

def run():
    with open('docs/MASTER_REPORT.md', 'r', encoding='utf-8') as f:
        text = f.read()

    sec7_text = """## 7. Automated Test Data Generation (Rubric Component 7 — 7 Marks, CLO2)

### 7.1 Objective & Architectural Rationale
A primary cause of software test failure and maintenance overhead in enterprise continuous delivery is **hardcoded test data fragility**. When business analysts or event organizers alter operational parameters (e.g., event venue capacity or ticket pricing tiers), hardcoded test suites fail and require expensive, error-prone manual rewrites.

To solve this, Area 2 Lead M. Hasaam (`24i-3107`) developed an automated, declarative test data generation engine in `tools/datagen/`. This tool mathematically synthesizes comprehensive test datasets from declarative business constraints and guarantees **zero-code test suite adaptation** whenever specifications change.

---

### 7.2 OpenAPI 3.0 Contract Specification & Schema Constraints
The test data generator is strictly governed by the formal contract defined in `openapi/team-spec.yaml` (OpenAPI 3.0.3). All synthesized test vectors conform to Pretix's formal request schemas:

```yaml
components:
  schemas:
    OrderCreatePayload:
      type: object
      required:
        - email
        - locale
        - positions
      properties:
        email:
          type: string
          format: email
        locale:
          type: string
          example: en
        sales_channel:
          type: string
          example: web
        positions:
          type: array
          items:
            $ref: '#/components/schemas/PositionCreatePayload'
    
    PositionCreatePayload:
      type: object
      required:
        - item
        - price
      properties:
        item:
          type: integer
          example: 1
        price:
          type: string
          pattern: '^[0-9]+\\.[0-9]{2}$'
          example: "50.00"
        attendee_name:
          type: string
        attendee_email:
          type: string
          format: email
```

---

### 7.3 Working Test Data Generator Architecture (`tools/datagen/`)
The generator is implemented as a production-grade Python package with full CLI support:
* **`tools/datagen/generator.py`:** Core `DataGenerator` class implementing 3-Point Boundary Value Analysis and Equivalence Partitioning algorithms.
* **`tools/datagen/cli.py`:** Command-line runner supporting argument parsing, constraint overrides, and output formatting.
* **`tools/datagen/config.yaml`:** Declarative configuration defining active event parameters:
  ```yaml
  constraints:
    organizer_slug: sqe
    event_slug: sqe2026
    item_id: 1
    item_name: "Conference Admission Ticket"
    quota_size: 10
    default_price: "50.00"
    currency: EUR
    locale: en
    sales_channel: web
  ```
* **Deterministic Seeding (`seed=42`):** Guarantees that generated test vectors (attendee names, RFC 5322 emails, UUID keys) are 100% reproducible across developer machines and automated CI pipelines.

---

### 7.4 Correct Regeneration for a Changed Specification
To fulfill the rubric requirement (*"correct regeneration for a changed specification"*), the generator's adaptability was demonstrated under a dual business specification shift:
1. **Constraint 1 (Venue Capacity):** Quota size increased by $+50\%$ from **$10$ to $15$ tickets**.
2. **Constraint 2 (Ticket Price):** Admission price increased by $+50\%$ from **€50.00 to €75.00**.

#### Execution Commands:
```powershell
# 1. Baseline Generation (Quota=10, Price=50.00)
python -m tools.datagen.cli --output reports/api/generated_data.json

# 2. Changed Specification Regeneration (Quota=15, Price=75.00)
python -m tools.datagen.cli --quota 15 --price 75.00 --output reports/api/regenerated_data.json
```

---

### 7.5 Side-by-Side Empirical Diff Analysis
The generator automatically recalculated all boundary points and re-synthesized all partition payloads without modifying a single line of test code:

```mermaid
flowchart LR
    subgraph Baseline_Capacity_10
        B1["min-1: 0"]
        B2["min: 1"]
        B3["min+1: 2"]
        B4["nominal: 5"]
        B5["max-1: 9"]
        B6["max: 10"]
        B7["max+1: 11"]
    end

    subgraph Regenerated_Capacity_15
        R1["min-1: 0"]
        R2["min: 1"]
        R3["min+1: 2"]
        R4["nominal: 7"]
        R5["max-1: 14"]
        R6["max: 15"]
        R7["max+1: 16"]
    end

    B4 -.->|"Shifted (+2)"| R4
    B5 -.->|"Shifted (+5)"| R5
    B6 -.->|"Shifted (+5)"| R6
    B7 -.->|"Shifted (+5)"| R7
```

#### 1. 3-Point Boundary Value Analysis (Quantity) Comparison:

| BVA Point Index | Point Name | Baseline Vector ($S=10$) | Regenerated Vector ($S=15$) | Mathematical Recalibration Formula |
| :---: | :--- | :---: | :---: | :--- |
| **Point 1** | $\min - 1$ (Underflow) | **0** | **0** | Constant lower underflow bound |
| **Point 2** | $\min$ (Valid Minimum) | **1** | **1** | Single ticket transaction floor |
| **Point 3** | $\min + 1$ (Above Min) | **2** | **2** | Minimal multi-ticket transaction |
| **Point 4** | $\text{nominal}$ (Midpoint) | **5** | **7** | Recalculated as $\lfloor S/2 \rfloor$: $\lfloor 10/2 \rfloor = 5 \to \lfloor 15/2 \rfloor = 7$ |
| **Point 5** | $\max - 1$ (Penultimate) | **9** | **14** | Recalculated as $S - 1$: $10-1=9 \to 15-1=14$ |
| **Point 6** | $\max$ (Capacity Limit) | **10** | **15** | Recalculated as $S$: $10 \to 15$ |
| **Point 7** | $\max + 1$ (Overflow) | **11** | **16** | Recalculated as $S + 1$: $10+1=11 \to 15+1=16$ |

#### 2. Equivalence Partitioning Payload Comparison (JSON Excerpt):

```json
// Baseline Payload (reports/api/generated_data.json) - Case EP-VAL-03
{
  "case_id": "EP-VAL-03",
  "description": "Bulk Order Consuming Full Available Quota",
  "quantity": 10,
  "expected_status": 201,
  "total_expected": "500.00",
  "payload": {
    "email": "full_quota@example.com",
    "locale": "en",
    "sales_channel": "web",
    "positions": [ /* 10 positions @ 50.00 EUR each */ ]
  }
}

// Regenerated Payload (reports/api/regenerated_data.json) - Case EP-VAL-03
{
  "case_id": "EP-VAL-03",
  "description": "Bulk Order Consuming Full Available Quota",
  "quantity": 15,
  "expected_status": 201,
  "total_expected": "1125.00",
  "payload": {
    "email": "full_quota@example.com",
    "locale": "en",
    "sales_channel": "web",
    "positions": [ /* 15 positions @ 75.00 EUR each */ ]
  }
}
```

---

### 7.6 Integration with Automated API Test Suites
In `tests/team/api/test_order_creation_api.py`, the test suite consumes datasets directly via Python module import:
```python
from tools.datagen.generator import generate_ep_datasets, generate_bva_quantity
```
When specification updates occur, the test suite dynamically loads the recalculated test vectors without requiring manual test rewrites or script modifications. Full documentation and validation logs are recorded in `docs/regeneration-demo.md`.

---

"""

    # Replace section headings after Section 6
    target_sec7 = "## 7. Use Cases & Playwright E2E Automation"
    idx = text.find(target_sec7)
    if idx == -1:
        print("Target '## 7. Use Cases' not found!")
        return

    prefix = text[:idx]
    suffix = text[idx:]

    # Renumber suffix headings
    replacements = [
        ("## 7. Use Cases & Playwright E2E Automation (Rubric Components 8 & 9 — 9 Marks, CLO2 & CLO3)", "## 8. Use Cases & Playwright E2E Automation (Rubric Components 8 & 9 — 9 Marks, CLO2 & CLO3)"),
        ("## 8. Usability & Accessibility Testing (Rubric Component 11 — 5 Marks, CLO3)", "## 9. Usability & Accessibility Testing (Rubric Component 11 — 5 Marks, CLO3)"),
        ("## 9. Defensive Security & Threat Modeling (Rubric Component 12 — 6 Marks, CLO3)", "## 10. Defensive Security & Threat Modeling (Rubric Component 12 — 6 Marks, CLO3)"),
        ("## 10. Mutation Testing & CI PR Quality Gate (Rubric Component 10 — 8 Marks, CLO2)", "## 11. Mutation Testing & CI PR Quality Gate (Rubric Component 10 — 8 Marks, CLO2)"),
        ("## 11. Performance, Concurrency & Fault Recovery (Rubric Component 13 — 5 Marks, CLO2)", "## 12. Performance, Concurrency & Fault Recovery (Rubric Component 13 — 5 Marks, CLO2)"),
        ("## 12. Defect Tracking, Root Cause Analysis & Structured Findings (Rubric Component 14 — 7 Marks, CLO3)", "## 13. Defect Tracking, Root Cause Analysis & Structured Findings (Rubric Component 14 — 7 Marks, CLO3)"),
        ("## 13. Goal-Question-Metric (GQM) Framework Tracking (Rubric Component 15 — 5 Marks, CLO3)", "## 14. Goal-Question-Metric (GQM) Framework Tracking (Rubric Component 15 — 5 Marks, CLO3)"),
        ("## 14. Tool Versions & Independent Reproduction Guide (Viva Live Task Readiness)", "## 15. Tool Versions & Independent Reproduction Guide (Viva Live Task Readiness)"),
        ("## 15. Academic Integrity & AI-Use Disclosure (Rubric Component 16 Part A)", "## 16. Academic Integrity & AI-Use Disclosure (Rubric Component 16 Part A)"),
        ("## 16. Release Decision, Exit Criteria Evaluation & Final Sign-Off", "## 17. Release Decision, Exit Criteria Evaluation & Final Sign-Off")
    ]

    for old, new in replacements:
        suffix = suffix.replace(old, new)

    # Update Table of Contents in prefix
    toc_old = """## Table of Contents
* [1. Executive Summary & System Architecture](#1-executive-summary--system-architecture)
* [2. System and Scope (Rubric Component 1 — 5 Marks, CLO3)](#2-system-and-scope-rubric-component-1--5-marks-clo3)
* [3. Test Plan, Estimation and Traceability (Rubric Components 3 & 4 — 12 Marks, CLO3)](#3-test-plan-estimation-and-traceability-rubric-components-3--4--12-marks-clo3)
* [4. Static Analysis and Metrics (Rubric Component 2 — 5 Marks, CLO3)](#4-static-analysis-and-metrics-rubric-component-2--5-marks-clo3)
* [5. White-Box Unit Testing (Rubric Component 5 — 16 Marks, CLO2)](#5-white-box-unit-testing-rubric-component-5--16-marks-clo2)
* [6. REST API Testing & Automated Test Data Generation (Rubric Components 6 & 7 — 17 Marks, CLO2)](#6-rest-api-testing--automated-test-data-generation-rubric-components-6--7--17-marks-clo2)
* [7. Use Cases & Playwright E2E Automation (Rubric Components 8 & 9 — 9 Marks, CLO2 & CLO3)](#7-use-cases--playwright-e2e-automation-rubric-components-8--9--9-marks-clo2--clo3)
* [8. Usability & Accessibility Testing (Rubric Component 11 — 5 Marks, CLO3)](#8-usability--accessibility-testing-rubric-component-11--5-marks-clo3)
* [9. Defensive Security & Threat Modeling (Rubric Component 12 — 6 Marks, CLO3)](#9-defensive-security--threat-modeling-rubric-component-12--6-marks-clo3)
* [10. Mutation Testing & CI PR Quality Gate (Rubric Component 10 — 8 Marks, CLO2)](#10-mutation-testing--ci-pr-quality-gate-rubric-component-10--8-marks-clo2)
* [11. Performance, Concurrency & Fault Recovery (Rubric Component 13 — 5 Marks, CLO2)](#11-performance-concurrency--fault-recovery-rubric-component-13--5-marks-clo2)
* [12. Defect Tracking, Root Cause Analysis & Structured Findings (Rubric Component 14 — 7 Marks, CLO3)](#12-defect-tracking-root-cause-analysis--structured-findings-rubric-component-14--7-marks-clo3)
* [13. Goal-Question-Metric (GQM) Framework Tracking (Rubric Component 15 — 5 Marks, CLO3)](#13-goal-question-metric-gqm-framework-tracking-rubric-component-15--5-marks-clo3)
* [14. Tool Versions & Independent Reproduction Guide (Viva Live Task Readiness)](#14-tool-versions--independent-reproduction-guide-viva-live-task-readiness)
* [15. Academic Integrity & AI-Use Disclosure (Rubric Component 16 Part A)](#15-academic-integrity--ai-use-disclosure-rubric-component-16-part-a)
* [16. Release Decision, Exit Criteria Evaluation & Final Sign-Off](#16-release-decision-exit-criteria-evaluation--final-sign-off)"""

    toc_new = """## Table of Contents
* [1. Executive Summary & System Architecture](#1-executive-summary--system-architecture)
* [2. System and Scope (Rubric Component 1 — 5 Marks, CLO3)](#2-system-and-scope-rubric-component-1--5-marks-clo3)
* [3. Test Plan, Estimation and Traceability (Rubric Components 3 & 4 — 12 Marks, CLO3)](#3-test-plan-estimation-and-traceability-rubric-components-3--4--12-marks-clo3)
* [4. Static Analysis and Metrics (Rubric Component 2 — 5 Marks, CLO3)](#4-static-analysis-and-metrics-rubric-component-2--5-marks-clo3)
* [5. White-Box Unit Testing (Rubric Component 5 — 16 Marks, CLO2)](#5-white-box-unit-testing-rubric-component-5--16-marks-clo2)
* [6. API and Integration Testing (Rubric Component 6 — 10 Marks, CLO2)](#6-api-and-integration-testing-rubric-component-6--10-marks-clo2)
* [7. Automated Test Data Generation (Rubric Component 7 — 7 Marks, CLO2)](#7-automated-test-data-generation-rubric-component-7--7-marks-clo2)
* [8. Use Cases & Playwright E2E Automation (Rubric Components 8 & 9 — 9 Marks, CLO2 & CLO3)](#8-use-cases--playwright-e2e-automation-rubric-components-8--9--9-marks-clo2--clo3)
* [9. Usability & Accessibility Testing (Rubric Component 11 — 5 Marks, CLO3)](#9-usability--accessibility-testing-rubric-component-11--5-marks-clo3)
* [10. Defensive Security & Threat Modeling (Rubric Component 12 — 6 Marks, CLO3)](#10-defensive-security--threat-modeling-rubric-component-12--6-marks-clo3)
* [11. Mutation Testing & CI PR Quality Gate (Rubric Component 10 — 8 Marks, CLO2)](#11-mutation-testing--ci-pr-quality-gate-rubric-component-10--8-marks-clo2)
* [12. Performance, Concurrency & Fault Recovery (Rubric Component 13 — 5 Marks, CLO2)](#12-performance-concurrency--fault-recovery-rubric-component-13--5-marks-clo2)
* [13. Defect Tracking, Root Cause Analysis & Structured Findings (Rubric Component 14 — 7 Marks, CLO3)](#13-defect-tracking-root-cause-analysis--structured-findings-rubric-component-14--7-marks-clo3)
* [14. Goal-Question-Metric (GQM) Framework Tracking (Rubric Component 15 — 5 Marks, CLO3)](#14-goal-question-metric-gqm-framework-tracking-rubric-component-15--5-marks-clo3)
* [15. Tool Versions & Independent Reproduction Guide (Viva Live Task Readiness)](#15-tool-versions--independent-reproduction-guide-viva-live-task-readiness)
* [16. Academic Integrity & AI-Use Disclosure (Rubric Component 16 Part A)](#16-academic-integrity--ai-use-disclosure-rubric-component-16-part-a)
* [17. Release Decision, Exit Criteria Evaluation & Final Sign-Off](#17-release-decision-exit-criteria-evaluation--final-sign-off)"""

    prefix = prefix.replace(toc_old, toc_new)

    new_full = prefix + sec7_text + suffix
    with open('docs/MASTER_REPORT.md', 'w', encoding='utf-8') as f:
        f.write(new_full)
    print("SUCCESS: Section 7 inserted into MASTER_REPORT.md successfully!")

if __name__ == '__main__':
    run()
