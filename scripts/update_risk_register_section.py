import re
from pathlib import Path

def update_risk_section():
    report_path = Path("docs/MASTER_REPORT.md")
    content = report_path.read_text(encoding="utf-8")
    
    new_risk_content = """### 3.4 5x5 Product & Project Risk Register (Rubric Component 4 — 5 Marks, CLO3)
Authored in `docs/risk-register.md` adhering to ISO/IEC/IEEE 29119-2. Every risk is evaluated on a $5 \\times 5$ Risk Heat Map ($\\text{Probability } P \\times \\text{Impact } I = \\text{Score } R \\in [1, 25]$). **The risk level dictates the testing technique and rigor/depth**: Extreme risks ($R \\ge 15$) demand white-box branch & condition testing (MCC/MCDC) and high-concurrency stress; High risks ($R \\ge 10$) require 3-point BVA and automated security matrix checks; Medium/Low risks ($R < 10$) use boundary equivalence partitioning.

| Risk ID | Category | Risk Description & Failure Trigger | Pre-Score ($P \\times I$) | Testing Technique & Depth (Decided by Risk Level) | Post-Score ($P \\times I$) | Residual Risk | Owner |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: | :---: |
| **PR1** | Concurrency | Simultaneous checkouts when $A=1$ causing quota overselling ($A < 0$) | **15 (Extreme)** ($3 \\times 5$) | **Technique:** Grafana k6 concurrent load (5 VUs) & PostgreSQL `SELECT FOR UPDATE` locks. **Depth:** Stress testing 2,171 requests across dual 60s runs. | **5 (Medium)** ($1 \\times 5$) | Acceptable | M. Hasaam |
| **PR2** | Financial | Floating-point rounding errors in multi-ticket order total sums | **8 (Medium)** ($2 \\times 4$) | **Technique:** Unit testing price calculations. **Depth:** Fixed-point Python `Decimal('50.00')` precision enforcement. | **4 (Low)** ($1 \\times 4$) | Acceptable | Sohaib |
| **PR3** | State Machine | Incomplete order cancellation leaving orphaned reserved quota holds | **15 (Extreme)** ($3 \\times 5$) | **Technique:** Cross-workflow API & White-Box state machine verification. **Depth:** Dynamic quota assertion ($10 \\to 9 \\to 10$) across all transitions. | **5 (Medium)** ($1 \\times 5$) | Acceptable | Sohaib |
| **PR4** | Atomicity | Partial order failure during multi-ticket checkout leaving DB inconsistent | **12 (High)** ($3 \\times 4$) | **Technique:** White-box transaction rollback testing. **Depth:** Multi-position payload with 1 invalid item asserting 0 inserted rows. | **4 (Low)** ($1 \\times 4$) | Acceptable | Sohaib |
| **PR5** | Resilience | Idempotency replay flaw under dropped connections causing duplicate orders | **12 (High)** ($3 \\times 4$) | **Technique:** Automated REST API idempotency replay testing. **Depth:** 10 consecutive identical requests with `X-Idempotency-Key`. | **4 (Low)** ($1 \\times 4$) | Acceptable | M. Hasaam |
| **PR6** | Security | Privilege escalation on read-only Auditor token mutating orders or items | **10 (High)** ($2 \\times 5$) | **Technique:** Automated Playwright & REST API RBAC matrix. **Depth:** 8 endpoints tested across 3 roles; OWASP ZAP passive audit. | **5 (Medium)** ($1 \\times 5$) | Acceptable | Shaiman |
| **PR7** | Temporal | Timezone inconsistency between server and event in expiration logic | **9 (Medium)** ($3 \\times 3$) | **Technique:** Business rule unit testing. **Depth:** Enforcing timezone-aware UTC timestamps (`django.utils.timezone.now()`). | **3 (Low)** ($1 \\times 3$) | Acceptable | Shaiman |
| **PR8** | Settlement | Payment settlement deadlock during simultaneous worker order expiration | **8 (Medium)** ($2 \\times 4$) | **Technique:** State machine concurrency guard assertions. **Depth:** Concurrent `mark_paid` and `mark_expired` asserting HTTP 409 Conflict. | **4 (Low)** ($1 \\times 4$) | Acceptable | M. Hasaam |
| **PRJ1** | Infrastructure | Docker Desktop RAM exhaustion (>36 Gunicorn/Celery procs crashing host) | **16 (Extreme)** ($4 \\times 4$) | **Technique:** Container resource constraint tuning & monitoring. **Depth:** Pinned `NUM_WORKERS=2` and `CELERY_WORKER_CONCURRENCY=1`. | **4 (Low)** ($1 \\times 4$) | Acceptable | Sohaib |
| **PRJ2** | Tooling | mutmut POSIX `fork()` worker crash / freeze on native Windows | **12 (High)** ($4 \\times 3$) | **Technique:** Automated AST-based custom mutation test synthesis. **Depth:** Implemented BCR and ADR operators in native Python runner. | **3 (Low)** ($1 \\times 3$) | Acceptable | Sohaib |

### 3.5 Measurable Exit Criteria Tied to Highest Risks (Actual vs Target)
To ensure objective, evidence-based quality verification, three measurable exit criteria were defined upfront in the IEEE 829 Test Plan. In accordance with the course rubric, **all three criteria are directly tied to the highest-scoring risks**:

| Release Criterion # | Quality Metric & Description | Linked Highest Risk(s) | Pre-Set Target Threshold | Actual Measured Result | Evaluation Status |
| :---: | :--- | :---: | :--- | :--- | :---: |
| **Criterion 1 (Functional & White-Box)** | Statement and branch coverage across core server-side order and quota business logic | **PR3 (Extreme 15):** Incomplete cancellation & orphaned quota hold leakage | $\\ge 80.00\\%$ Branch Coverage; 0 open critical/high defects | **100.00% Branch Coverage** (28/28 branches)<br>**99.67% Statement Coverage** (300/301 statements)<br>0 open critical defects | **MET / EXCEEDED**<br>(Exceeds target by $+20.00\\%$) |
| **Criterion 2 (Performance & Recovery)** | Latency SLA and zero-overselling integrity under concurrent load and chaos injection | **PR1 (Extreme 15):** Concurrency quota oversell<br>**PRJ1 (Extreme 16):** Host container RAM crash | $p95 \\le 500\\text{ ms}$; Unexpected failures $< 1.0\\%$; Strictly 0 oversold items ($Q_{\\text{final}} \\ge 0$) | **$p95 = 87.71\\text{ms} - 214.70\\text{ms}$** (well below 500ms limit)<br>**0.00% Unexpected Failures** across 2,171 requests<br>**0 oversold items** (10 sold, 130 rejected) | **MET / EXCEEDED**<br>(Zero overselling, zero corruption) |
| **Criterion 3 (Security & Usability)** | Zero high-severity vulnerabilities, clean dependency audit, and zero critical accessibility violations | **PR6 (High 10):** Auditor privilege escalation<br>**PR7 (Medium 9):** Standards compliance | 0 WCAG 2.1 AA critical violations on core screens; 0 High/Critical CVEs (`pip-audit`); 0 unauthorized RBAC escalations | **0 Critical A11y Violations** (login logo `alt` remediated $1 \\to 0$)<br>**0 Known CVEs** across 48 packages (`pip-audit 2.10.1`)<br>**0 Privilege Escalations** (5/5 RBAC checks passed) | **MET / EXCEEDED**<br>(100% security controls verified) |
"""

    pattern = r'### 3\.4 5x5 Product & Project Risk Register[\s\S]*?(?=---\s*\n\s*## 4\. Static Analysis)'
    if re.search(pattern, content):
        updated = re.sub(pattern, lambda m: new_risk_content + "\n", content)
        report_path.write_text(updated, encoding="utf-8")
        print("[SUCCESS] docs/MASTER_REPORT.md Risk Register & Exit Criteria expanded!")
    else:
        print("[ERROR] Pattern not found in docs/MASTER_REPORT.md")

if __name__ == "__main__":
    update_risk_section()
