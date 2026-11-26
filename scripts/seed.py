#!/usr/bin/env python3
"""
Host-side Deterministic Database Seeding Runner.
Copies scripts/seed_internal.py into `pretix_web` and executes it inside
the containerized Django environment to seed Organizer, Event, Item, Quota,
payment plugins, and Admin/Auditor roles.
"""
import argparse
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from reset import find_docker_bin  # noqa: E402


def run_seed(container="pretix_web"):
    """Copy seed_internal.py into pretix_web and execute it."""
    internal_script = os.path.join(SCRIPT_DIR, "seed_internal.py")
    if not os.path.exists(internal_script):
        raise FileNotFoundError(f"Missing internal seed script: {internal_script}")

    docker_bin = find_docker_bin()
    target = f"{container}:/tmp/seed_internal.py"

    cp_res = subprocess.run([docker_bin, "cp", internal_script, target], capture_output=True, text=True)
    if cp_res.returncode != 0:
        raise RuntimeError(f"docker cp failed: {cp_res.stderr.strip()}")

    exec_res = subprocess.run(
        [docker_bin, "exec", container, "python3", "/tmp/seed_internal.py"],
        capture_output=True,
        text=True,
    )
    if exec_res.stdout:
        print(exec_res.stdout.strip())
    if exec_res.returncode != 0:
        raise RuntimeError(f"Seeding failed in {container}:\n{exec_res.stderr.strip()}")
    print("[SUCCESS] Deterministic pretix seed data verified.")


def main():
    parser = argparse.ArgumentParser(description="Seed deterministic pretix test data inside pretix_web.")
    parser.add_argument("--container", default="pretix_web", help="Target Docker container name (default: pretix_web).")
    args = parser.parse_args()
    run_seed(container=args.container)


if __name__ == "__main__":
    main()
