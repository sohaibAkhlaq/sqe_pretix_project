"""
Fault Injection & Automated Recovery Test Suite (Phase 9).
Injects infrastructure failure by terminating the Redis cache/lock container (pretix_redis),
verifies application fault containment, triggers self-healing container recovery,
measures Recovery Time Objective (RTO < 15s), and confirms post-recovery data integrity.
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

class TestFaultInjectionAndRecovery:
    """Verifies that the ticketing stack withstands Redis failure and recovers within 15 seconds."""

    def test_redis_failure_and_rapid_recovery(self):
        """TC-PERF-REC-01: Terminate Redis, evaluate degradation, restart Redis, verify RTO < 15s."""
        tokens = get_tokens()
        headers = {
            "Authorization": f"Token {tokens['SQE Test API Token']}",
            "Accept": "application/json"
        }
        quota_url = f"{BASE_URL}/organizers/{ORGANIZER}/events/{EVENT}/quotas/1/availability/"

        # -------------------------------------------------------------
        # Step 1: Pre-Fault Health Check
        # -------------------------------------------------------------
        res_pre = requests.get(quota_url, headers=headers, timeout=5)
        assert res_pre.status_code == 200, f"Pre-fault check failed: {res_pre.status_code}"
        pre_avail = res_pre.json()
        assert "available_number" in pre_avail

        # -------------------------------------------------------------
        # Step 2: Inject Fault (Stop Redis Container)
        # -------------------------------------------------------------
        print("\n[CHAOS] Injecting Fault: Stopping pretix_redis container...")
        stop_cmd = [DOCKER_BIN, "stop", "pretix_redis"]
        stop_res = subprocess.run(stop_cmd, capture_output=True, text=True)
        assert stop_res.returncode == 0, f"Failed to stop pretix_redis: {stop_res.stderr}"

        # Verify Redis is indeed stopped
        inspect_cmd = [DOCKER_BIN, "inspect", "-f", "{{.State.Running}}", "pretix_redis"]
        status_res = subprocess.run(inspect_cmd, capture_output=True, text=True)
        assert "false" in status_res.stdout.lower()

        # -------------------------------------------------------------
        # Step 3: Verify Fault Containment
        # -------------------------------------------------------------
        # Database container must remain alive and healthy
        db_inspect = subprocess.run([DOCKER_BIN, "inspect", "-f", "{{.State.Running}}", "pretix_db"],
                                    capture_output=True, text=True)
        assert "true" in db_inspect.stdout.lower(), "Postgres crashed during Redis failure!"

        # Web container must not crash
        web_inspect = subprocess.run([DOCKER_BIN, "inspect", "-f", "{{.State.Running}}", "pretix_web"],
                                     capture_output=True, text=True)
        assert "true" in web_inspect.stdout.lower(), "Pretix web process terminated unexpectedly!"

        # -------------------------------------------------------------
        # Step 4: Self-Healing / Restart Redis & Measure Recovery Time (RTO)
        # -------------------------------------------------------------
        print("[HEAL] Triggering Recovery: Restarting pretix_redis container...")
        recovery_start = time.time()
        start_cmd = [DOCKER_BIN, "start", "pretix_redis"]
        start_res = subprocess.run(start_cmd, capture_output=True, text=True)
        assert start_res.returncode == 0, f"Failed to start pretix_redis: {start_res.stderr}"

        # Poll endpoint until HTTP 200 is restored
        recovered = False
        attempts = 0
        rto_seconds = None

        while time.time() - recovery_start < 25.0:
            attempts += 1
            try:
                probe = requests.get(quota_url, headers=headers, timeout=2)
                if probe.status_code == 200 and "available_number" in probe.json():
                    rto_seconds = time.time() - recovery_start
                    recovered = True
                    break
            except Exception:
                pass
            time.sleep(0.5)

        assert recovered, "System failed to recover within 25 seconds!"
        print(f"[RECOVERY CONFIRMED] RTO = {rto_seconds:.2f} seconds (Target: < 15.0s)")
        assert rto_seconds < 15.0, f"Recovery Time Objective violated: {rto_seconds:.2f}s >= 15.0s"

        # -------------------------------------------------------------
        # Step 5: Post-Recovery Data Integrity
        # -------------------------------------------------------------
        post_avail = requests.get(quota_url, headers=headers).json()
        assert post_avail["total_size"] == pre_avail["total_size"], "Quota total size corrupted post-recovery!"
        assert post_avail["available_number"] == pre_avail["available_number"], "Available capacity drifted post-recovery!"

        # Save Report
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        recovery_report = {
            "test_id": "TC-PERF-REC-01",
            "component_failed": "pretix_redis (Redis Cache / Lock Service)",
            "fault_type": "Unexpected Process Termination (SIGKILL / stop)",
            "recovery_mechanism": "Automated Service Restoral",
            "pre_fault_status": "HTTP 200 OK",
            "recovery_time_objective_target_seconds": 15.0,
            "measured_rto_seconds": round(rto_seconds, 2),
            "recovery_attempts": attempts,
            "data_integrity_verified": True,
            "status": "PASSED"
        }
        with open(REPORTS_DIR / "fault_recovery_report.json", "w", encoding="utf-8") as f:
            json.dump(recovery_report, f, indent=2)
