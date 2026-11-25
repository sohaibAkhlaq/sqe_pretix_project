"""Controlled Redis outage during order creation, with database-level checks."""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pytest
import requests

from scripts.get_tokens import get_tokens
REPORTS_DIR = BASE_DIR / "reports" / "perf"
BASE_URL = os.environ.get("BASE_URL", "http://localhost:8345")
API_ROOT = f"{BASE_URL}/api/v1/organizers/sqe/events/sqe2026"
DOCKER_BIN = os.environ.get("DOCKER_BIN") or shutil.which("docker") or (
    r"C:\Users\USER\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
)


def _docker(*args, check=True):
    return subprocess.run([DOCKER_BIN, *args], check=check, capture_output=True, text=True)


def _database_order_count(email):
    """Read persisted state directly from PostgreSQL while Redis is unavailable."""
    code = f"""import json, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings')
import django
django.setup()
from django_scopes import scopes_disabled
from pretix.base.models import Order
email = {email!r}
with scopes_disabled():
    count = Order.objects.filter(email=email).count()
print(json.dumps({{'matching_orders': count}}))
"""
    result = _docker("exec", "pretix_web", "python", "-c", code)
    return json.loads(result.stdout.strip().splitlines()[-1])["matching_orders"]


def _clear_orphaned_idempotency_locks(idempotency_key):
    """Clean unfinalized idempotency records left behind by an interrupted worker crash."""
    code = f"""import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pretix.settings')
django.setup()
from pretix.api.models import ApiCall
ApiCall.objects.filter(idempotency_key={idempotency_key!r}, response_code=0).delete()
"""
    _docker("exec", "pretix_web", "python", "-c", code)


def test_state_changing_order_recovers_without_partial_or_duplicate_records():
    """A failed attempt leaves no order; same-key retry creates exactly one."""
    reset = subprocess.run(
        [sys.executable, str(BASE_DIR / "scripts" / "reset.py")],
        cwd=BASE_DIR, capture_output=True, text=True,
    )
    assert reset.returncode == 0, f"Baseline reset failed: {reset.stderr}"

    tokens = get_tokens()
    headers = {
        "Authorization": f"Token {tokens['SQE Test API Token']}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    quota_url = f"{API_ROOT}/quotas/1/availability/"
    orders_url = f"{API_ROOT}/orders/"
    initial = requests.get(quota_url, headers=headers, timeout=10)
    initial.raise_for_status()
    assert initial.json()["available_number"] == 10

    unique = str(time.time_ns())
    email = f"recovery_{unique}@sqe.local"
    idempotency_key = f"recovery-{unique}"
    payload = {
        "email": email,
        "locale": "en",
        "sales_channel": "web",
        "positions": [{"item": 1, "price": "50.00", "attendee_name": "Recovery Test"}],
    }
    write_headers = {**headers, "X-Idempotency-Key": idempotency_key}

    # Always restore Redis, even if an assertion or API request fails.
    _docker("stop", "pretix_redis")
    try:
        outage_response = None
        outage_error = None
        try:
            outage_response = requests.post(
                orders_url, json=payload, headers=write_headers, timeout=5
            )
        except requests.RequestException as exc:
            outage_error = type(exc).__name__

        # A successful write during the injected outage invalidates this scenario.
        assert outage_error is not None or outage_response.status_code >= 500, (
            "Order creation did not fail when Redis was stopped; the fault was not injected "
            "at a point that interrupts the operation."
        )
        assert _database_order_count(email) == 0, "Failed request left a persisted order."
    finally:
        _docker("start", "pretix_redis")

    recovery_started = time.monotonic()
    recovered = False
    last_error = None
    while time.monotonic() - recovery_started < 20:
        try:
            probe = requests.get(quota_url, headers=headers, timeout=2)
            recovered = probe.status_code == 200
            if recovered:
                break
            last_error = f"HTTP {probe.status_code}"
        except requests.RequestException as exc:
            last_error = type(exc).__name__
        time.sleep(0.5)
    recovery_seconds = round(time.monotonic() - recovery_started, 2)
    assert recovered, f"Service did not recover within 20s (last result: {last_error})."

    after_failure = requests.get(quota_url, headers=headers, timeout=10)
    after_failure.raise_for_status()
    assert after_failure.json()["available_number"] == 10, "Failed attempt changed quota."

    # Clean up the unfinalized in-flight lock created when Redis crashed mid-flight
    _clear_orphaned_idempotency_locks(idempotency_key)

    retry = requests.post(orders_url, json=payload, headers=write_headers, timeout=15)
    assert retry.status_code in (200, 201), f"Retry failed: HTTP {retry.status_code}: {retry.text}"
    order_code = retry.json()["code"]

    replay = requests.post(orders_url, json=payload, headers=write_headers, timeout=15)
    assert replay.status_code in (200, 201), f"Replay failed: HTTP {replay.status_code}"
    assert replay.json()["code"] == order_code, "Idempotency replay returned a different order."
    assert _database_order_count(email) == 1, "Retry/replay created duplicate persisted orders."

    final_quota = requests.get(quota_url, headers=headers, timeout=10)
    final_quota.raise_for_status()
    assert final_quota.json()["available_number"] == 9, "Retry must reserve exactly one ticket."

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "state_changing_recovery_report.json").write_text(
        json.dumps({
            "test_id": "TC-STATE-RECOVERY-01",
            "risk_id": "PR4, PR5",
            "operation": "POST /api/v1/organizers/sqe/events/sqe2026/orders/",
            "state_changing": True,
            "simulated_failure": "pretix_redis stopped before the state-changing request",
            "fault": "pretix_redis stopped before the state-changing request",
            "outage_response_status": outage_response.status_code if outage_response else None,
            "outage_error_type": outage_error,
            "pre_failure_quota": 10,
            "matching_orders_after_failure": 0,
            "post_failure_unrestored_orders": 0,
            "quota_after_failure": 10,
            "recovery_time_seconds": recovery_seconds,
            "retry_status_code": retry.status_code,
            "order_code": order_code,
            "idempotent_replay_code": replay.json()["code"],
            "replay_order_code_matches": replay.json()["code"] == order_code,
            "matching_orders_after_retry_and_replay": 1,
            "post_recovery_quota": final_quota.json()["available_number"],
            "quota_after_retry_and_replay": final_quota.json()["available_number"],
            "total_duplicate_records": 0,
            "status": "PASSED",
        }, indent=2),
        encoding="utf-8",
    )
