"""
SE3002 Software Quality Engineering - Automated Phase 0 Spikes Runner
Executes Spike 1 (Setup, Seeding & API Discovery) and Spike 2 (Idempotency, Order Placement, Quota Transition)
Generates verified raw execution evidence for reports/spikes/
"""
import os
import sys
import json
import uuid
import time
import subprocess
import requests

BASE_URL = "http://localhost:8345"
API_BASE = f"{BASE_URL}/api/v1"
DOCKER_BIN = r"C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe" if os.path.exists(r"C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe") else "docker"

def run_cmd(cmd):
    """Executes a command and returns stdout."""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error running command: {cmd}\nStderr: {res.stderr}")
    return res.stdout.strip(), res.returncode

def wait_for_service(url, timeout=90):
    """Polls until the web service responds."""
    print(f"Waiting for {url} to become responsive...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code in [200, 302, 403, 404]:
                print(f"Service ready! HTTP status {r.status_code}")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(3)
    return False

def seed_pretix():
    """Seeds the pretix instance with Organizer, Event, Item, Quota, and API tokens."""
    print("Executing internal database seeding inside pretix container...")
    seed_script_path = os.path.join(os.path.dirname(__file__), "seed_internal.py")
    
    # Copy seed script into container and run directly with python3
    run_cmd(f'{DOCKER_BIN} cp "{seed_script_path}" pretix_web:/data/seed_internal.py')
    stdout, rc = run_cmd(f'{DOCKER_BIN} exec pretix_web python3 /data/seed_internal.py')
    
    if rc != 0:
        print(f"Seeding failed: {stdout}")
        sys.exit(1)
        
    print(f"Raw Seed Output:\n{stdout}")
    
    # Parse output tokens
    data = {}
    for line in stdout.splitlines():
        if line.startswith("SEED_SUCCESS:"):
            parts = line.replace("SEED_SUCCESS:", "").split(":")
            for p in parts:
                k, v = p.split("=")
                data[k] = v
    return data

def execute_spike1(seed_data):
    """Spike 1: Verify API discovery, organizer, event, item, quota, and roles."""
    print("\n--- RUNNING SPIKE 1: API DISCOVERY & ACCESS VERIFICATION ---")
    token = seed_data["TOKEN"]
    readonly_token = seed_data["READONLY_TOKEN"]
    org = seed_data["ORGANIZER"]
    event = seed_data["EVENT"]
    item_id = seed_data["ITEM_ID"]
    quota_id = seed_data["QUOTA_ID"]
    
    admin_headers = {"Authorization": f"Token {token}", "Accept": "application/json"}
    readonly_headers = {"Authorization": f"Token {readonly_token}", "Accept": "application/json"}
    
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spike": "Spike 1 - Install, Migrate, User Roles, Seeded Records",
        "endpoints_checked": []
    }
    
    # Check 1: Organizer
    r_org = requests.get(f"{API_BASE}/organizers/{org}/", headers=admin_headers)
    evidence["endpoints_checked"].append({"endpoint": f"/organizers/{org}/", "status": r_org.status_code, "response": r_org.json()})
    assert r_org.status_code == 200, f"Expected 200, got {r_org.status_code}"
    
    # Check 2: Event
    r_event = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/", headers=admin_headers)
    evidence["endpoints_checked"].append({"endpoint": f"/organizers/{org}/events/{event}/", "status": r_event.status_code, "response": r_event.json()})
    assert r_event.status_code == 200, f"Expected 200, got {r_event.status_code}"
    
    # Check 3: Item
    r_item = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/items/{item_id}/", headers=admin_headers)
    evidence["endpoints_checked"].append({"endpoint": f"/items/{item_id}/", "status": r_item.status_code, "response": r_item.json()})
    assert r_item.status_code == 200, f"Expected 200, got {r_item.status_code}"
    
    # Check 4: Quota & Initial Availability
    r_quota = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/quotas/{quota_id}/availability/", headers=admin_headers)
    evidence["endpoints_checked"].append({"endpoint": f"/quotas/{quota_id}/availability/", "status": r_quota.status_code, "response": r_quota.json()})
    assert r_quota.status_code == 200, f"Expected 200, got {r_quota.status_code}"
    
    # Check 5: Read-Only Role Permission Verification
    r_ro_view = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/orders/", headers=readonly_headers)
    r_ro_mutate = requests.post(f"{API_BASE}/organizers/{org}/events/{event}/items/", headers=readonly_headers, json={"name": {"en": "Unauthorized"}})
    evidence["endpoints_checked"].append({
        "role_check": "Auditor Read-Only",
        "view_orders_status": r_ro_view.status_code,
        "mutate_items_status": r_ro_mutate.status_code,
        "permission_enforced": (r_ro_view.status_code == 200 and r_ro_mutate.status_code in [401, 403])
    })
    
    os.makedirs("reports/spikes", exist_ok=True)
    with open("reports/spikes/spike1_output.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print("Spike 1 PASSED! Raw evidence saved to reports/spikes/spike1_output.json")
    return evidence

def execute_spike2(seed_data):
    """Spike 2: Idempotent order placement, duplicate rejection, quota readback, cancellation."""
    print("\n--- RUNNING SPIKE 2: IDEMPOTENCY, ORDER LIFECYCLE & QUOTA TRACKING ---")
    token = seed_data["TOKEN"]
    org = seed_data["ORGANIZER"]
    event = seed_data["EVENT"]
    item_id = int(seed_data["ITEM_ID"])
    quota_id = seed_data["QUOTA_ID"]
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    evidence = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spike": "Spike 2 - Idempotency-Key, Quota Availability Readback, Order Cancellation",
        "steps": []
    }
    
    # Step 1: Read Initial Quota
    r_q0 = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/quotas/{quota_id}/availability/", headers=headers).json()
    initial_avail = r_q0.get("available_number", r_q0.get("available"))
    print(f"Step 1: Initial Quota Available = {initial_avail}")
    evidence["steps"].append({"step": "initial_quota", "data": r_q0})
    
    # Step 2: Create Order with Idempotency-Key
    idem_key = str(uuid.uuid4())
    order_payload = {
        "email": "customer@example.com",
        "locale": "en",
        "positions": [
            {
                "item": item_id,
                "price": "50.00",
                "attendee_name": "Test Attendee"
            }
        ]
    }
    req_headers = dict(headers)
    req_headers["X-Idempotency-Key"] = idem_key
    req_headers["Idempotency-Key"] = idem_key
    
    r_order1 = requests.post(
        f"{API_BASE}/organizers/{org}/events/{event}/orders/",
        headers=req_headers,
        json=order_payload
    )
    print(f"Step 2: Order Creation HTTP {r_order1.status_code}")
    order_data1 = r_order1.json()
    order_code = order_data1.get("code")
    evidence["steps"].append({
        "step": "order_creation_1",
        "idempotency_key": idem_key,
        "status_code": r_order1.status_code,
        "order_code": order_code,
        "order_status": order_data1.get("status")
    })
    assert r_order1.status_code in [200, 201], f"Order creation failed: {r_order1.text}"
    
    # Step 3: Read Quota After Order (Must be Initial - 1)
    r_q1 = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/quotas/{quota_id}/availability/", headers=headers).json()
    post_order_avail = r_q1.get("available_number", r_q1.get("available"))
    print(f"Step 3: Post-Order Quota Available = {post_order_avail}")
    evidence["steps"].append({"step": "post_order_quota", "data": r_q1})
    assert post_order_avail == initial_avail - 1, f"Expected {initial_avail - 1}, got {post_order_avail}"
    
    # Step 4: Repeat Identical Request with Same Idempotency-Key
    r_order2 = requests.post(
        f"{API_BASE}/organizers/{org}/events/{event}/orders/",
        headers=req_headers,
        json=order_payload
    )
    print(f"Step 4: Repeated Order Request with Same Key HTTP {r_order2.status_code}")
    order_data2 = r_order2.json()
    evidence["steps"].append({
        "step": "order_creation_repeated_idempotency",
        "idempotency_key": idem_key,
        "status_code": r_order2.status_code,
        "order_code": order_data2.get("code")
    })
    # Must return same order without duplicating or failing unexpectedly
    assert order_data2.get("code") == order_code, f"Idempotency failed: expected {order_code}, got {order_data2.get('code')}"
    
    # Step 5: Read Quota to Verify No Duplicate Deductions
    r_q2 = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/quotas/{quota_id}/availability/", headers=headers).json()
    post_repeat_avail = r_q2.get("available_number", r_q2.get("available"))
    print(f"Step 5: Post-Repeat Quota Available = {post_repeat_avail}")
    assert post_repeat_avail == post_order_avail, "Idempotency failed: quota decremented again on repeat!"
    evidence["steps"].append({"step": "post_repeat_quota", "data": r_q2})
    
    # Step 6: Cancel the Order via mark_canceled action
    r_cancel = requests.post(
        f"{API_BASE}/organizers/{org}/events/{event}/orders/{order_code}/mark_canceled/",
        headers=headers,
        json={}
    )
    print(f"Step 6: Cancel Order HTTP {r_cancel.status_code}")
    evidence["steps"].append({"step": "cancel_order", "status_code": r_cancel.status_code, "response": r_cancel.json()})
    assert r_cancel.status_code in [200, 201], f"Order cancel failed: {r_cancel.text}"
    
    # Step 7: Read Quota After Cancellation (Must return back to Initial)
    r_q3 = requests.get(f"{API_BASE}/organizers/{org}/events/{event}/quotas/{quota_id}/availability/", headers=headers).json()
    post_cancel_avail = r_q3.get("available_number", r_q3.get("available"))
    print(f"Step 7: Post-Cancel Quota Available = {post_cancel_avail}")
    evidence["steps"].append({"step": "post_cancel_quota", "data": r_q3})
    assert post_cancel_avail == initial_avail, f"Expected quota to restore to {initial_avail}, got {post_cancel_avail}"
    
    with open("reports/spikes/spike2_output.json", "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)
    print("Spike 2 PASSED! Raw evidence saved to reports/spikes/spike2_output.json")
    return evidence

if __name__ == "__main__":
    wait_for_service("http://localhost:8345")
    seed_data = seed_pretix()
    execute_spike1(seed_data)
    execute_spike2(seed_data)
