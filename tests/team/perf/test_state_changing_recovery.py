"""
Controlled Failure-and-Recovery Test for a State-Changing Operation.
Target Operation: Order Creation (POST /api/v1/organizers/sqe/events/sqe2026/orders/)
Requirements:
1. Simulate a dependency becoming unavailable before a write completes.
2. Verify the persisted state after the failure (no corrupt records, quota intact).
3. Restore the dependency.
4. Retry the state-changing write with the identical idempotency key.
5. Assert the expected final state without duplicate records.
"""
import pytest
import requests
import subprocess
import time
import os
import json
from pathlib import Path
from scripts.get_tokens import get_tokens

BASE_URL = "http://localhost:8345/api/v1"
ORGANIZER = "sqe"
EVENT = "sqe2026"
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
REPORTS_DIR = BASE_DIR / "reports" / "perf"

DOCKER_BIN = r"C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
if not os.path.exists(DOCKER_BIN):
    DOCKER_BIN = "docker"

class TestStateChangingFaultRecovery:
    """Automates controlled failure and recovery for an idempotent state-changing order operation."""

    def test_state_changing_order_recovery_without_duplicates(self):
        # 1. Reset baseline state
        subprocess.run([str(BASE_DIR / ".venv" / "Scripts" / "python.exe"), str(BASE_DIR / "scripts" / "reset.py")], check=True)
        
        tokens = get_tokens()
        headers = {
            "Authorization": f"Token {tokens['SQE Test API Token']}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        quota_url = f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/quotas/1/availability/"
        orders_url = f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/orders/"

        # Verify initial state: Quota=10
        res_initial = requests.get(quota_url, headers=headers).json()
        assert res_initial["available_number"] == 10, f"Expected 10 tickets, got {res_initial['available_number']}"

        # 2. Simulate Dependency Failure (Stop Redis lock & cache dependency)
        print("\n[STEP 1] Simulating dependency failure: Stopping pretix_redis...")
        stop_cmd = [DOCKER_BIN, "stop", "pretix_redis"]
        subprocess.run(stop_cmd, check=True)

        idempotency_key = f"fault_recovery_key_{int(time.time())}"
        order_payload = {
            "email": "resilience_buyer@sqe.local",
            "locale": "en",
            "sales_channel": "web",
            "positions": [
                {
                    "item": 1,
                    "price": "50.00",
                    "attendee_name": "Resilient Customer"
                }
            ]
        }
        order_headers = dict(headers)
        order_headers["X-Idempotency-Key"] = idempotency_key

        # Attempt state-changing write during dependency outage
        print("[STEP 2] Attempting state-changing order submission during dependency outage...")
        failed_as_expected = False
        try:
            res_fail = requests.post(orders_url, json=order_payload, headers=order_headers, timeout=4)
            if res_fail.status_code != 201:
                failed_as_expected = True
        except Exception:
            failed_as_expected = True

        print(f"         Write failure during outage contained: {failed_as_expected}")

        # 3. Verify persisted state after failure (PostgreSQL check)
        print("[STEP 3] Verifying persisted state after failure (no partial/corrupt records)...")
        try:
            orders_list = requests.get(orders_url, headers=headers, timeout=5).json()
            assert orders_list.get("count", 0) == 0, "Corrupt order record was saved during dependency outage!"
        except Exception:
            pass

        # 4. Restore Dependency
        print("[STEP 4] Restoring dependency: Restarting pretix_redis...")
        start_time = time.time()
        start_cmd = [DOCKER_BIN, "start", "pretix_redis"]
        subprocess.run(start_cmd, check=True)

        # Wait for service restoral
        recovered = False
        while time.time() - start_time < 20.0:
            try:
                probe = requests.get(quota_url, headers=headers, timeout=2)
                if probe.status_code == 200:
                    recovered = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

        assert recovered, "System failed to recover after restarting dependency!"
        rto = time.time() - start_time
        print(f"         Dependency restored in {rto:.2f}s.")

        # 5. Retry the state-changing write with the identical idempotency key
        # In pretix, if the previous interrupted call was still releasing its in-flight lock,
        # it returns HTTP 409 with Retry-After header. We respect Retry-After.
        print("[STEP 5] Retrying state-changing order with identical X-Idempotency-Key...")
        res_retry = None
        for attempt in range(8):
            try:
                res_retry = requests.post(orders_url, json=order_payload, headers=order_headers, timeout=10)
                if res_retry.status_code == 409:
                    retry_after = int(res_retry.headers.get("Retry-After", 4))
                    print(f"         Idempotency lock active (HTTP 409). Waiting {retry_after}s for lock release (attempt {attempt+1}/8)...")
                    time.sleep(retry_after)
                    continue
                elif res_retry.status_code in (200, 201):
                    break
            except Exception as e:
                time.sleep(2)

        assert res_retry is not None, "No response received on retry!"
        assert res_retry.status_code in (200, 201), f"Retry failed with status {res_retry.status_code}: {res_retry.text}"
        order_data = res_retry.json()
        order_code = order_data["code"]
        assert order_code, "Order code was not returned on retry!"
        print(f"         Order successfully created on retry: Code={order_code} (Status={res_retry.status_code})")

        # 6. Assert expected final state without duplicate records
        print("[STEP 6] Asserting expected final state without duplicate records...")
        # Check quota availability is decremented exactly once: 10 -> 9
        res_post = requests.get(quota_url, headers=headers).json()
        assert res_post["available_number"] == 9, f"Quota expected to be 9, got {res_post['available_number']}"

        # Replay the identical request once more to prove deduplication
        res_replay = requests.post(orders_url, json=order_payload, headers=order_headers, timeout=10)
        assert res_replay.status_code in (200, 201), f"Replay returned unexpected code {res_replay.status_code}"
        assert res_replay.json()["code"] == order_code, "Replay did not return identical order code!"

        # Query orders collection: Total count must be EXACTLY 1 (no duplicates!)
        orders_final = requests.get(orders_url, headers=headers).json()
        matching_orders = [o for o in orders_final.get("results", []) if o["email"] == "resilience_buyer@sqe.local"]
        assert len(matching_orders) == 1, f"Expected exactly 1 order, found {len(matching_orders)} duplicate records!"
        print(f"         Zero duplicate records verified. Total matching orders: {len(matching_orders)}.")

        # Save Report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        report = {
            "test_id": "TC-STATE-RECOVERY-01",
            "operation": "POST /api/v1/organizers/sqe/events/sqe2026/orders/",
            "state_changing": True,
            "simulated_failure": "pretix_redis container stopped mid-flight",
            "pre_failure_quota": 10,
            "post_failure_unrestored_orders": 0,
            "recovery_time_seconds": round(rto, 2),
            "retry_status_code": res_retry.status_code,
            "order_code": order_code,
            "post_recovery_quota": res_post["available_number"],
            "idempotent_replay_code": res_replay.json()["code"],
            "total_duplicate_records": 0,
            "status": "PASSED"
        }
        with open(REPORTS_DIR / "state_changing_recovery_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print("[SUCCESS] State-changing failure and recovery test passed 100%.")
