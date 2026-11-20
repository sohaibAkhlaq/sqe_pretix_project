#!/usr/bin/env python3
"""
Host-side Deterministic Database Reset Runner.
Locates Docker executable across platforms, executes container reset,
and empirically verifies reset idempotency.
"""
import os
import sys
import shutil
import subprocess
import argparse

def find_docker_bin():
    """Resolves docker binary across standard system and user locations."""
    # 1. Standard PATH lookup
    docker_bin = shutil.which("docker")
    if docker_bin:
        return docker_bin
    
    # 2. Windows Docker Desktop candidate locations
    candidates = [
        os.path.expanduser(r"~\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"),
        r"C:\Program Files\Docker\Docker\resources\bin\docker.exe",
        r"C:\Program Files\Docker\Docker\resources\docker.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
            
    # 3. Unix fallback
    for c in ["/usr/local/bin/docker", "/usr/bin/docker"]:
        if os.path.isfile(c):
            return c
            
    return "docker"

def run_reset_once(docker_bin):
    """Executes a single reset cycle inside pretix_web."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    internal_script = os.path.join(script_dir, "reset_internal.py")
    
    if not os.path.exists(internal_script):
        raise FileNotFoundError(f"Missing internal reset script: {internal_script}")
        
    # Copy reset script into container
    cp_cmd = [docker_bin, "cp", internal_script, "pretix_web:/data/reset_internal.py"]
    res = subprocess.run(cp_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Failed to copy reset_internal.py to container:\n{res.stderr}")
        
    # Execute reset inside container
    exec_cmd = [docker_bin, "exec", "pretix_web", "python3", "/data/reset_internal.py"]
    res = subprocess.run(exec_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Reset execution failed (exit code {res.returncode}):\n{res.stdout}\n{res.stderr}")
        
    # Parse success metrics
    metrics = {}
    for line in res.stdout.splitlines():
        if "RESET_SUCCESS:" in line:
            parts = line.split("RESET_SUCCESS:")[1].split(":")
            for p in parts:
                k, v = p.split("=")
                metrics[k] = int(v) if v.isdigit() else v
                
    if "ORDERS" not in metrics or "QUOTA_AVAILABILITY" not in metrics:
        raise ValueError(f"Reset did not return expected RESET_SUCCESS tokens. Raw output:\n{res.stdout}")
        
    return metrics, res.stdout

def main():
    parser = argparse.ArgumentParser(description="Deterministic pretix database reset tool.")
    parser.add_argument("--verify-idempotency", action="store_true", help="Run reset twice consecutively and assert zero delta.")
    args = parser.parse_args()
    
    docker_bin = find_docker_bin()
    print(f"[RESET_RUNNER] Using Docker binary: {docker_bin}")
    
    print("\n--- [CYCLE 1] Executing Database State Reset ---")
    metrics1, stdout1 = run_reset_once(docker_bin)
    print(f"Cycle 1 Result: Orders={metrics1['ORDERS']}, Quota Available={metrics1['QUOTA_AVAILABILITY']}, Size={metrics1['QUOTA_SIZE']}")
    
    if args.verify_idempotency:
        print("\n--- [CYCLE 2] Consecutive Idempotency Verification ---")
        metrics2, stdout2 = run_reset_once(docker_bin)
        print(f"Cycle 2 Result: Orders={metrics2['ORDERS']}, Quota Available={metrics2['QUOTA_AVAILABILITY']}, Size={metrics2['QUOTA_SIZE']}")
        
        # Mathematical verification: R(R(S)) == R(S)
        assert metrics1 == metrics2, f"Idempotency violation! Cycle 1: {metrics1} != Cycle 2: {metrics2}"
        assert metrics2["ORDERS"] == 0, f"Expected 0 orders, found {metrics2['ORDERS']}"
        assert metrics2["QUOTA_AVAILABILITY"] == 10, f"Expected 10 available quota, found {metrics2['QUOTA_AVAILABILITY']}"
        print("\n[IDEMPOTENCY_VERIFIED] Cycle 1 state is mathematically identical to Cycle 2 state (Zero delta).")

    print("\n[SUCCESS] pretix state reset complete and verified.")

if __name__ == "__main__":
    main()
