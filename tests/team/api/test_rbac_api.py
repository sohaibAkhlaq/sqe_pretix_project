"""
REST API Integration Tests: Role-Based Access Control (RBAC) Matrix (FR7 / PR6).
All payloads and endpoints are consumed directly from tools/datagen/generator output.
"""
import requests

BASE_API = "http://localhost:8345/api/v1"


class TestAPIRoleBasedAccessControl:
    """Verifies Least-Privilege API Token enforcement for Admin, Auditor, Anonymous, and Invalid tokens."""

    def test_auditor_can_read_generated_endpoints_but_cannot_mutate(
        self, event_endpoints, admin_headers, auditor_headers, generated_data
    ):
        get_eps = generated_data["get_endpoints"]
        rbac = generated_data["rbac_cases"]

        for key in ("organizer", "event", "item_detail", "quota_availability", "orders_list", "orders_filter_pending"):
            r = requests.get(f"{BASE_API}{get_eps[key]}", headers=auditor_headers)
            assert r.status_code == 200, f"Auditor GET {key} expected 200, got {r.status_code}"

        r_post_denied = requests.post(
            event_endpoints["orders"],
            json=rbac["auditor_forbidden_post_payload"],
            headers=auditor_headers,
        )
        assert r_post_denied.status_code == 403

        # Admin creates an order; Auditor cannot mutate it
        r_admin = requests.post(event_endpoints["orders"], json=rbac["admin_post_payload"], headers=admin_headers)
        assert r_admin.status_code == 201
        code = r_admin.json()["code"]

        for action in ("mark_paid", "mark_canceled", "mark_expired"):
            r_mut = requests.post(f"{event_endpoints['orders']}{code}/{action}/", headers=auditor_headers)
            assert r_mut.status_code == 403, f"Auditor {action} expected 403, got {r_mut.status_code}"

        assert requests.post(f"{event_endpoints['orders']}{code}/mark_canceled/", headers=admin_headers).status_code == 200

    def test_anonymous_and_invalid_tokens_rejected(self, event_endpoints, generated_data):
        rbac = generated_data["rbac_cases"]
        anon_headers = {"Accept": "application/json", "Content-Type": "application/json"}
        bad_headers = {"Authorization": "Token invalid_token_000", "Accept": "application/json"}

        assert requests.get(event_endpoints["orders"], headers=anon_headers).status_code == 401
        assert requests.post(event_endpoints["orders"], json=rbac["anon_blocked_post_payload"], headers=anon_headers).status_code == 401
        assert requests.get(event_endpoints["orders"], headers=bad_headers).status_code == 401
        assert requests.post(event_endpoints["orders"], json=rbac["invalid_token_post_payload"], headers=bad_headers).status_code == 401
