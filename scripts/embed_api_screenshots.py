import os

def embed_api_screenshots():
    with open('docs/MASTER_REPORT.md', 'r', encoding='utf-8') as f:
        text = f.read()

    screenshots_md = """
### 6.9 Genuine Live REST API Execution Evidence Screenshots
The following authentic screenshots were captured from the live Pretix Docker container executing real HTTP transactions at `http://localhost:8345`:

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.1: Live Workflow A Order Creation (HTTP 201 Created with Order Code & Pending Status)</strong></p>
  <img src="reports/api/screenshots/02_api_order_creation_success_201.png" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="Order Creation Success">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.2: Live Cross-Workflow Quota Restoral (Workflow B mark_canceled Replenishing Quota 1 from 9 to 10)</strong></p>
  <img src="reports/api/screenshots/04_api_order_cancellation_quota_restored.png" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="Order Cancellation Quota Restoral">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.3: Live 3-Point BVA Boundary Overflow Rejection (11 > 10 Tickets -> HTTP 400 Bad Request)</strong></p>
  <img src="reports/api/screenshots/05_api_bva_overflow_400_rejected.png" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="BVA Quantity Overflow Rejection">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.4: Live RBAC Security Enforcement (Auditor Read Token Blocked on Order Mutation -> HTTP 403 Forbidden)</strong></p>
  <img src="reports/api/screenshots/06_api_rbac_auditor_403_forbidden.png" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="RBAC Auditor 403 Forbidden">
</div>
"""

    anchor = "* Audit Report Saved: `reports/api/api_test_results.json`\n\n---"
    if anchor in text:
        text = text.replace(anchor, "* Audit Report Saved: `reports/api/api_test_results.json`\n" + screenshots_md + "\n---")
        with open('docs/MASTER_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(text)
        print("SUCCESS: Screenshots embedded into docs/MASTER_REPORT.md!")
    else:
        print("Anchor not found! Please check formatting.")

if __name__ == '__main__':
    embed_api_screenshots()
