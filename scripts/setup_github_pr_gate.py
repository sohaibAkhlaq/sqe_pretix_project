#!/usr/bin/env python3
"""
SE3002 Automated GitHub Branch Protection & Red-to-Green PR Gate Lifecycle.
Author: Sohaib (24i-3108) | Area 1 (Mutation Testing & CI Quality Gate)

Implements end-to-end live GitHub governance for sohaibAkhlaq/sqe_pretix_project:
1. Configures Branch Protection Rules on `main` requiring PRs and both CI checks:
   - Offline Quality Gates (Static, 100% Scoped Coverage, Real AST Mutation, OpenAPI, Supply Chain)
   - Live Container Integration Gates (API, E2E, Accessibility, Security, Master Audit)
2. Opens a Pull Request from `ci/pr-quality-gate-demo` -> `main` with an intentional
   unit-test coverage gap (`94.12% < 100%`), confirming GitHub Actions fails RED and
   GitHub Branch Protection sets `mergeable_state=blocked`.
3. Restores 100% unit test coverage, commits this script + live PR/Branch Protection
   evidence in `docs/ci-gate-demo.md` and `docs/MASTER_REPORT.md` (§12.4), pushes Commit 2,
   waits for BOTH GitHub Actions jobs to pass GREEN, and merges the PR cleanly into `main`.
4. Syncs local `main`, updates `v1.0-submission` tag, cleans the merged demo branch,
   and rebuilds `Project_24i-3108_24i-3107_24i-3074_C.pdf` and `.zip`.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPO_SLUG = "sohaibAkhlaq/sqe_pretix_project"
API_BASE = f"https://api.github.com/repos/{REPO_SLUG}"
DEMO_BRANCH = "ci/pr-quality-gate-demo"
COMMIT_AUTHOR = "sohaibAkhlaq <sohaibikhlaq5@gmail.com>"

CHECK_OFFLINE = (
    "Offline Quality Gates (Static, 100% Scoped Coverage, Real AST Mutation, OpenAPI, Supply Chain)"
)
CHECK_INTEGRATION = (
    "Live Container Integration Gates (API, E2E, Accessibility, Security, Master Audit)"
)
GITHUB_ACTIONS_APP_ID = 15368

UNIT_TEST_REL = "tests/team/unit/test_order_state_transitions.py"
CI_DEMO_DOC_REL = "docs/ci-gate-demo.md"
MASTER_REPORT_REL = "docs/MASTER_REPORT.md"
SELF_REL = "scripts/setup_github_pr_gate.py"

PDF_NAME = "Project_24i-3108_24i-3107_24i-3074_C.pdf"
ZIP_NAME = "Project_24i-3108_24i-3107_24i-3074_C.zip"

PYTHON_BIN = str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_BIN):
    PYTHON_BIN = sys.executable

RED_GATE_MARKER = "    def test_mark_order_expired_by_ids_cancels_unreferred_invoice(self, monkeypatch):"
RED_GATE_SKIP = (
    '    @pytest.mark.skip(reason="Red-Gate PR verification: simulate missing unit test dropping scoped coverage < 100%")\n'
    + RED_GATE_MARKER
)

CI_DEMO_OLD_NOTE = (
    "> **Publication Scope Note:** `.github/workflows/pr-gate.yml` is committed locally and verified via local execution + Red-Gate failure simulation (`scripts/verify_mutation_and_ci_gate.py`). Remote GitHub Actions PR run URLs (`github.com/sohaibAkhlaq/sqe_pretix_project/actions/...`) require pushing the repository and opening live blocking/passing PRs against GitHub after authentication."
)

MASTER_SEED_OLD = "Spins up ephemeral Docker Compose Pretix stack (`scripts/seed.py`)"
MASTER_SEED_NEW = "Spins up ephemeral Docker Compose Pretix stack (`scripts/seed_internal.py` + `scripts/patch_a11y_container.py`)"

MASTER_NOTE_OLD = (
    "* **Remote GitHub Actions Status Note:** Workflow YAML and local verification gates are complete and tested; remote GitHub PR run links depend on repository publication with GitHub credentials (`https://github.com/sohaibAkhlaq/sqe_pretix_project.git`)."
)


def _api(method, path_or_url, token, payload=None):
    url = path_or_url if path_or_url.startswith("https://") else f"{API_BASE}{path_or_url}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "sqe-pretix-pr-gate",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, (json.loads(raw) if raw.strip() else {})
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {url} -> HTTP {exc.code}: {body}") from exc


def _git(args, check=True):
    res = subprocess.run(
        ["git", *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and res.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed (code {res.returncode}):\n{res.stdout}\n{res.stderr}"
        )
    return res


def _run_py(args, check=True):
    res = subprocess.run(
        [PYTHON_BIN, *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check and res.returncode != 0:
        raise RuntimeError(
            f"python {' '.join(args)} failed (code {res.returncode}):\n{res.stdout}\n{res.stderr}"
        )
    return res


def validate_token(token):
    lowered = (token or "").strip().lower()
    if not lowered or any(bad in lowered for bad in ("your-", "<", ">", "example", "placeholder", "xxxx")):
        raise RuntimeError(
            "GITHUB_TOKEN env var is missing or looks like a placeholder.\n"
            "Set a real PAT in PowerShell first (never paste it into chat or code):\n"
            '  $env:GITHUB_TOKEN = "<your-pat>"\n'
            "Required scopes: Classic PAT `repo`, OR Fine-Grained PAT on sqe_pretix_project with\n"
            "  Administration (R/W), Pull requests (R/W), Contents (R/W), Actions (Read)."
        )
    _, user = _api("GET", "https://api.github.com/user", token)
    _, repo = _api("GET", "", token)
    perms = repo.get("permissions", {})
    print(f"[AUTH] Authenticated as `{user.get('login')}` | repo admin={perms.get('admin')} push={perms.get('push')}")
    if not perms.get("admin"):
        raise RuntimeError(
            "Token lacks repository admin permission (`permissions.admin=False`), which is required "
            "for Branch Protection (`PUT /branches/main/protection`). Use a classic PAT with `repo` scope "
            "or a Fine-Grained PAT with Administration: Read and write."
        )


def verify_local_preconditions():
    allowed_untracked = {PDF_NAME, ZIP_NAME, SELF_REL}
    st = _git(["status", "--porcelain"]).stdout.splitlines()
    unexpected = []
    for line in st:
        if not line.strip():
            continue
        code = line[:2]
        path = line[3:].strip().replace("\\", "/")
        if code == "??" and path in allowed_untracked:
            continue
        unexpected.append(line)
    if unexpected:
        raise RuntimeError(f"Working tree has unexpected local changes:\n" + "\n".join(unexpected))

    ci_demo_text = (PROJECT_ROOT / CI_DEMO_DOC_REL).read_text(encoding="utf-8")
    if CI_DEMO_OLD_NOTE not in ci_demo_text:
        raise RuntimeError(f"Expected anchor note not found in {CI_DEMO_DOC_REL}")

    report_text = (PROJECT_ROOT / MASTER_REPORT_REL).read_text(encoding="utf-8")
    if MASTER_SEED_OLD not in report_text:
        raise RuntimeError(f"Expected seed anchor not found in {MASTER_REPORT_REL}")
    if MASTER_NOTE_OLD not in report_text:
        raise RuntimeError(f"Expected remote note anchor not found in {MASTER_REPORT_REL}")

    unit_text = (PROJECT_ROOT / UNIT_TEST_REL).read_text(encoding="utf-8")
    if RED_GATE_MARKER not in unit_text:
        raise RuntimeError(f"Expected unit test method not found in {UNIT_TEST_REL}")
    print("[DRY-RUN] Local git state and exact document/test patch anchors verified cleanly.")


def configure_branch_protection(token):
    payload = {
        "required_status_checks": {
            "strict": True,
            "checks": [
                {"context": CHECK_OFFLINE, "app_id": GITHUB_ACTIONS_APP_ID},
                {"context": CHECK_INTEGRATION, "app_id": GITHUB_ACTIONS_APP_ID},
            ],
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": False,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 0,
        },
        "restrictions": None,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    _, prot = _api("PUT", "/branches/main/protection", token, payload)
    contexts = [c.get("context") for c in prot.get("required_status_checks", {}).get("checks", [])]
    if not contexts:
        contexts = prot.get("required_status_checks", {}).get("contexts", [])
    assert CHECK_OFFLINE in contexts and CHECK_INTEGRATION in contexts, f"Unexpected contexts: {contexts}"
    assert prot.get("enforce_admins", {}).get("enabled") is True, "enforce_admins was not enabled!"
    print("[BRANCH PROTECTION] Enforced on `main`: strict=True, enforce_admins=True, PR required, 2 CI checks required.")
    return prot


def wait_for_actions_run(token, head_sha, event, expected_conclusion, timeout_sec):
    deadline = time.time() + timeout_sec
    start = time.time()
    seen_id = None
    while time.time() < deadline:
        _, data = _api("GET", f"/actions/runs?event={event}&per_page=15", token)
        matches = [r for r in data.get("workflow_runs", []) if r.get("head_sha") == head_sha]
        if matches:
            run = sorted(matches, key=lambda r: r.get("run_number", 0), reverse=True)[0]
            seen_id = run["id"]
            status = run.get("status")
            elapsed = int(time.time() - start)
            print(f"  [{elapsed:>4}s] Run #{run['id']} ({event} @ {head_sha[:7]}): status={status} conclusion={run.get('conclusion')}")
            if status == "completed":
                _, jobs_data = _api("GET", f"/actions/runs/{run['id']}/jobs", token)
                for j in jobs_data.get("jobs", []):
                    print(f"           Job: {j['name']} -> {j['conclusion']}")
                if run.get("conclusion") != expected_conclusion:
                    raise RuntimeError(
                        f"Expected conclusion={expected_conclusion!r} for Run {run['id']}, got {run.get('conclusion')!r}: {run['html_url']}"
                    )
                return run, jobs_data.get("jobs", [])
        else:
            elapsed = int(time.time() - start)
            print(f"  [{elapsed:>4}s] Waiting for GitHub Actions `{event}` run on {head_sha[:7]}...")
        time.sleep(15)
    raise TimeoutError(f"Timed out after {timeout_sec}s waiting for `{event}` run on {head_sha} (last seen id={seen_id})")


def open_or_reuse_pr(token):
    _, prs = _api("GET", f"/pulls?state=open&head=sohaibAkhlaq:{DEMO_BRANCH}", token)
    if prs:
        pr = prs[0]
        print(f"[PR] Reusing open PR #{pr['number']}: {pr['html_url']}")
        return pr
    payload = {
        "title": "ci(gate): enforce live branch protection and verify Red-to-Green PR CI gate",
        "head": DEMO_BRANCH,
        "base": "main",
        "body": (
            "## Summary\n"
            "- Enforces Branch Protection Rules on `main` requiring PRs (`strict: true`, `enforce_admins: true`) "
            "and both CI checks (`Offline Quality Gates` + `Live Container Integration Gates`).\n"
            "- Demonstrates a real **Blocked PR (Red Gate)** caused by a simulated coverage drop to `94.12% (< 100%)` "
            "on Gate 2 (`--cov-fail-under=100`), followed by remediation restoring `100.00%` scoped branch coverage "
            "and updating [docs/ci-gate-demo.md](docs/ci-gate-demo.md) and [docs/MASTER_REPORT.md](docs/MASTER_REPORT.md).\n"
        ),
    }
    _, pr = _api("POST", "/pulls", token, payload)
    print(f"[PR] Opened PR #{pr['number']}: {pr['html_url']}")
    return pr


def wait_for_pr_state(token, pr_number, desired_states, timeout_sec=90):
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        _, pr = _api("GET", f"/pulls/{pr_number}", token)
        state = pr.get("mergeable_state")
        if state in desired_states:
            print(f"[PR #{pr_number}] mergeable={pr.get('mergeable')} mergeable_state={state!r}")
            return pr
        time.sleep(5)
    _, pr = _api("GET", f"/pulls/{pr_number}", token)
    print(f"[PR #{pr_number}] settled with mergeable={pr.get('mergeable')} mergeable_state={pr.get('mergeable_state')!r}")
    return pr


def update_docs_and_verify(pr_number, pr_url, failed_run_id, failed_run_url, commit1_sha):
    # 1. Update docs/ci-gate-demo.md
    ci_demo_path = PROJECT_ROOT / CI_DEMO_DOC_REL
    ci_demo_text = ci_demo_path.read_text(encoding="utf-8")
    assert CI_DEMO_OLD_NOTE in ci_demo_text, "Missing Publication Scope Note in docs/ci-gate-demo.md"
    ci_demo_new_note = (
        f"> **Live GitHub Actions & Branch Protection Verification:** `.github/workflows/pr-gate.yml` is live and enforced via Branch Protection on `main` (`strict: true`, `enforce_admins: true`, requiring both `Offline Quality Gates` and `Live Container Integration Gates`). Baseline `main` verified green in Run [`45657663612`](https://github.com/sohaibAkhlaq/sqe_pretix_project/actions/runs/45657663612); Live Pull Request [#{pr_number}]({pr_url}) proved end-to-end PR blocking when commit `{commit1_sha[:7]}` triggered Red-Gate failure [`{failed_run_id}`]({failed_run_url}) (`94.12%` scoped coverage `< 100%` on Gate 2, `mergeable_state=blocked`), followed by remediation commit restoring `100.00%` parity."
    )
    ci_demo_path.write_text(ci_demo_text.replace(CI_DEMO_OLD_NOTE, ci_demo_new_note, 1), encoding="utf-8")

    # 2. Update docs/MASTER_REPORT.md §12.4
    report_path = PROJECT_ROOT / MASTER_REPORT_REL
    report_text = report_path.read_text(encoding="utf-8")
    assert MASTER_SEED_OLD in report_text and MASTER_NOTE_OLD in report_text
    report_text = report_text.replace(MASTER_SEED_OLD, MASTER_SEED_NEW, 1)
    master_note_new = (
        f"* **Live GitHub Actions, Branch Protection & Blocked-PR Verification:** Branch Protection is active on `main` (`strict: true`, `enforce_admins: true`, requiring PRs and both GitHub Actions checks). Push baseline Run [`45657663612`](https://github.com/sohaibAkhlaq/sqe_pretix_project/actions/runs/45657663612) passed both jobs cleanly, and Pull Request [#{pr_number}]({pr_url}) verified live PR blocking on commit `{commit1_sha[:7]}` (Red-Gate Run [`{failed_run_id}`]({failed_run_url}), `94.12% < 100%` coverage -> `mergeable_state=blocked`) prior to remediation and green merge (`https://github.com/sohaibAkhlaq/sqe_pretix_project.git`)."
    )
    report_text = report_text.replace(MASTER_NOTE_OLD, master_note_new, 1)
    report_path.write_text(report_text, encoding="utf-8")

    # 3. Verify locally before pushing Commit 2
    assert "\t" not in report_text and "\ufffd" not in report_text, "Corrupt chars detected in MASTER_REPORT.md"
    _run_py([
        "-m", "pytest", "tests/team/unit/",
        "--cov=upstream.pretix.base.scoped_business_logic",
        "--cov-branch", "--cov-fail-under=100",
    ])
    _run_py(["scripts/verify_ai_use_record.py"])
    _run_py([
        "-c",
        (
            "import markdown_it; "
            "md = markdown_it.MarkdownIt('commonmark', {'html': True, 'breaks': True}).enable('table'); "
            "html = md.render(open('docs/MASTER_REPORT.md', encoding='utf-8').read()); "
            "cnt = html.count('<table>'); "
            "assert cnt == 32, f'Expected 32 HTML tables, got {cnt}'; "
            "print(f'Verified {cnt} HTML tables in MASTER_REPORT.md')"
        ),
    ])
    print("[LOCAL CHECKS] Unit 100% coverage, AI-Use audit, and 32 HTML tables verified cleanly.")


def merge_pr_with_retry(token, pr_number, title):
    wait_for_pr_state(token, pr_number, {"clean", "has_hooks", "unstable"}, timeout_sec=60)
    payload = {
        "commit_title": f"{title} (#{pr_number})",
        "commit_message": f"Verified Red-to-Green PR Quality Gate lifecycle on PR #{pr_number} with main branch protection active.",
        "merge_method": "squash",
    }
    for attempt in range(1, 7):
        try:
            _, res = _api("PUT", f"/pulls/{pr_number}/merge", token, payload)
            print(f"[MERGED] PR #{pr_number} merged cleanly into `main`: sha={res.get('sha', '')[:7]}")
            return res["sha"]
        except RuntimeError as exc:
            if "HTTP 405" in str(exc) and attempt < 6:
                print(f"  [RETRY {attempt}/6] PR #{pr_number} still recomputing mergeability; waiting 5s...")
                time.sleep(5)
                continue
            raise


def execute_full_lifecycle(token):
    validate_token(token)
    verify_local_preconditions()

    # Ensure local main matches origin/main
    _git(["checkout", "main"])
    _git(["pull", "--ff-only", "origin", "main"])
    _git(["fetch", "origin"])

    # Step 1: Configure Branch Protection on main
    configure_branch_protection(token)

    # Step 2: Create Red-Gate branch & Commit 1
    _git(["checkout", "-B", DEMO_BRANCH, "main"])
    unit_path = PROJECT_ROOT / UNIT_TEST_REL
    unit_text = unit_path.read_text(encoding="utf-8")
    if "@pytest.mark.skip" not in unit_text:
        unit_path.write_text(unit_text.replace(RED_GATE_MARKER, RED_GATE_SKIP, 1), encoding="utf-8")

    red_check = _run_py([
        "-m", "pytest", "tests/team/unit/",
        "--cov=upstream.pretix.base.scoped_business_logic",
        "--cov-branch", "--cov-fail-under=100",
    ], check=False)
    if red_check.returncode == 0:
        raise RuntimeError("Expected Red-Gate unit coverage check to fail < 100%, but it exited 0!")
    print(f"[RED-GATE LOCAL] Confirmed coverage failure (exit={red_check.returncode}) before pushing Commit 1.")

    _git(["add", UNIT_TEST_REL])
    _git([
        "commit",
        f"--author={COMMIT_AUTHOR}",
        "-m", "test(gate-demo): simulate coverage gap for live PR blocking check (Area 1 - Sohaib)",
    ])
    commit1_sha = _git(["rev-parse", "HEAD"]).stdout.strip()
    _git(["push", "-u", "origin", DEMO_BRANCH, "--force"])

    # Step 3: Open PR & verify GitHub Actions fails RED + PR is Blocked
    pr = open_or_reuse_pr(token)
    pr_number = pr["number"]
    pr_url = pr["html_url"]
    failed_run, _ = wait_for_actions_run(token, commit1_sha, "pull_request", "failure", timeout_sec=360)
    failed_run_id = failed_run["id"]
    failed_run_url = failed_run["html_url"]
    pr_blocked = wait_for_pr_state(token, pr_number, {"blocked", "dirty"}, timeout_sec=60)
    if pr_blocked.get("mergeable_state") != "blocked":
        raise RuntimeError(f"Expected PR #{pr_number} mergeable_state='blocked', got {pr_blocked.get('mergeable_state')!r}")

    # Step 4: Remediation Commit 2 on same branch
    _git(["checkout", "main", "--", UNIT_TEST_REL])
    update_docs_and_verify(pr_number, pr_url, failed_run_id, failed_run_url, commit1_sha)
    _git(["add", UNIT_TEST_REL, CI_DEMO_DOC_REL, MASTER_REPORT_REL, SELF_REL])
    _git([
        "commit",
        f"--author={COMMIT_AUTHOR}",
        "-m", "fix(ci-gate,docs): restore 100% coverage and document live PR gate & branch protection (Area 1 - Sohaib)",
    ])
    commit2_sha = _git(["rev-parse", "HEAD"]).stdout.strip()
    _git(["push", "origin", DEMO_BRANCH])

    # Step 5: Wait for BOTH CI jobs to pass GREEN on Commit 2, then Merge PR
    green_run, _ = wait_for_actions_run(token, commit2_sha, "pull_request", "success", timeout_sec=1200)
    print(f"[GREEN-GATE PR] Both CI checks passed on PR #{pr_number}: {green_run['html_url']}")
    merged_sha = merge_pr_with_retry(token, pr_number, pr["title"])

    # Step 6: Cleanup merged branch, sync main, wait for main push CI, update tag, repackage
    try:
        _api("DELETE", f"/git/refs/heads/{DEMO_BRANCH}", token)
        print(f"[CLEANUP] Deleted remote merged branch `{DEMO_BRANCH}` (PR #{pr_number} history preserved).")
    except RuntimeError as exc:
        print(f"[NOTE] Remote branch delete returned: {exc}")

    _git(["fetch", "origin", "main"])
    _git(["checkout", "-B", "main", "origin/main"])
    _git(["branch", "-D", DEMO_BRANCH], check=False)

    main_sha = _git(["rev-parse", "HEAD"]).stdout.strip()
    assert main_sha == merged_sha, f"Local main {main_sha} != merged {merged_sha}"

    print("[MAIN CI] Waiting for post-merge `push` workflow on `main` to finish green...")
    main_run, _ = wait_for_actions_run(token, main_sha, "push", "success", timeout_sec=1200)
    print(f"[MAIN CI] Post-merge `main` run passed: {main_run['html_url']}")

    _git(["tag", "-f", "-a", "v1.0-submission", "-m", "SE3002 SQE Final Submission Release (PR Gate & Branch Protection Verified)"])
    _git(["push", "origin", "--force", "refs/tags/v1.0-submission"])

    print("[PACKAGE] Regenerating submission PDF and ZIP from final `main`...")
    _run_py(["scripts/verify_ai_use_record.py"])
    _run_py(["scripts/generate_pdf_report.py"])
    _run_py(["scripts/package_submission.py", "--output", ZIP_NAME, "--pdf", PDF_NAME])
    print("=" * 72)
    print(f"[SUCCESS] PR #{pr_number}: {pr_url}")
    print(f"          Blocked Run: {failed_run_url}")
    print(f"          PR Green Run: {green_run['html_url']}")
    print(f"          Main Push Run: {main_run['html_url']}")
    print(f"          Final main SHA: {main_sha[:7]} (tagged v1.0-submission)")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Configure GitHub branch protection and execute live Red->Green PR gate verification.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Verify local clean tree and exact patch anchors without touching GitHub.")
    group.add_argument("--run-all", action="store_true", help="Execute full Branch Protection + Blocked PR -> Remediated Green PR -> Merge -> Repackage flow.")
    args = parser.parse_args()

    if args.dry_run:
        verify_local_preconditions()
        return

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    execute_full_lifecycle(token)


if __name__ == "__main__":
    main()
