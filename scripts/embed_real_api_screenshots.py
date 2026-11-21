import os

def embed_real_screenshots():
    with open('docs/MASTER_REPORT.md', 'r', encoding='utf-8') as f:
        text = f.read()

    screenshots_md = """
### 6.9 Authentic Live REST API Evidence Screenshots (Thunder Client / VS Code)
The following authentic screenshots were captured directly from VS Code using Thunder Client, communicating in real-time with the containerized Pretix web server on `http://localhost:8345`:

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.1: Live Quota Availability Inspection (GET /quotas/1/availability/ -> HTTP 200 OK, Total Size: 10)</strong></p>
  <img src="reports/api/01_thunder_client_quota_availability.png" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="Quota Availability Baseline">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.2: Equivalence Partitioning (Valid Partition): Order Creation (POST /orders/ -> HTTP 201 Created, Order Code: Y9HAH)</strong></p>
  <img src="reports/api/02_thunder_client_order_creation_ep_valid.jpg" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="EP Valid Order Creation">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.3: Equivalence Partitioning (Invalid Partition): Empty Positions Rejection (POST /orders/ -> HTTP 400 Bad Request)</strong></p>
  <img src="reports/api/03_thunder_client_ep_invalid_empty.png" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="EP Invalid Empty Rejection">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.4: 3-Point Boundary Value Analysis: Capacity Overflow (11 Tickets > Capacity 10 -> HTTP 400 Bad Request)</strong></p>
  <img src="reports/api/04_thunder_client_bva_overflow.jpg" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="BVA Quantity Overflow Rejection">
</div>

<div style="text-align: center; margin: 12px 0;">
  <p><strong>Figure 6.5: Cross-Workflow Integration: Workflow B Order Cancellation & Quota Restoral (POST /orders/Y9HAH/mark_canceled/ -> HTTP 200 OK, Status: 'c')</strong></p>
  <img src="reports/api/05_thunder_client_cross_workflow_cancel.jpg" width="95%" style="border: 1px solid #ccc; border-radius: 4px;" alt="Cross-Workflow Cancellation Restoral">
</div>
"""

    anchor = "* Audit Report Saved: `reports/api/api_test_results.json`\n\n---"
    if anchor in text:
        text = text.replace(anchor, "* Audit Report Saved: `reports/api/api_test_results.json`\n" + screenshots_md + "\n---")
        with open('docs/MASTER_REPORT.md', 'w', encoding='utf-8') as f:
            f.write(text)
        print("SUCCESS: Real Thunder Client screenshots embedded into docs/MASTER_REPORT.md!")
    else:
        print("Anchor not found! Please check formatting.")

if __name__ == '__main__':
    embed_real_screenshots()
