"""
RBAC Security & Authorization Test Suite.
Verifies Role-Based Access Control across Admin, Auditor, and Anonymous roles
against all 8 core API endpoints and UI control pathways.
"""
import pytest
import requests
import uuid

class TestRBACSecurityMatrix:
    """Verifies that privileged operations require valid admin permissions and that auditor/anonymous roles are strictly bounded."""

    def test_admin_full_access_to_read_endpoints(self, event_endpoints, admin_headers):
        """SEC-RBAC-01: Admin token has full read access to event, items, quotas, availability, and orders."""
        for endpoint in ["event", "items", "quotas", "quota_avail", "orders"]:
            url = event_endpoints[endpoint]
            resp = requests.get(url, headers=admin_headers)
            assert resp.status_code == 200, f"Admin failed GET {endpoint}: {resp.status_code}"

    def test_auditor_allowed_read_endpoints(self, event_endpoints, auditor_headers):
        """SEC-RBAC-02: Auditor token has read access to event, items, quotas, availability, and orders."""
        for endpoint in ["event", "items", "quotas", "quota_avail", "orders"]:
            url = event_endpoints[endpoint]
            resp = requests.get(url, headers=auditor_headers)
            assert resp.status_code == 200, f"Auditor failed GET {endpoint}: {resp.status_code}"

    def test_auditor_forbidden_from_creating_orders(self, event_endpoints, auditor_headers):
        """SEC-RBAC-03: Auditor receives HTTP 403 Forbidden when attempting to place an order."""
        orders_url = event_endpoints["orders"]
        payload = {
            "email": "exploit_auditor_order@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "Unauthorized Auditor"}]
        }
        resp = requests.post(orders_url, json=payload, headers=auditor_headers)
        assert resp.status_code == 403, f"Auditor placed order! Expected 403, got {resp.status_code}"
        assert "detail" in resp.json() or "permission" in str(resp.content).lower()

    def test_auditor_forbidden_from_creating_items(self, event_endpoints, auditor_headers):
        """SEC-RBAC-04: Auditor receives HTTP 403 Forbidden when attempting to create a new ticket item."""
        items_url = event_endpoints["items"]
        payload = {
            "name": {"en": "Unauthorized VIP Pass"},
            "default_price": "100.00",
            "active": True
        }
        resp = requests.post(items_url, json=payload, headers=auditor_headers)
        assert resp.status_code == 403, f"Auditor created item! Expected 403, got {resp.status_code}"

    def test_auditor_forbidden_from_creating_quotas(self, event_endpoints, auditor_headers):
        """SEC-RBAC-05: Auditor receives HTTP 403 Forbidden when attempting to create or mutate quotas."""
        quotas_url = event_endpoints["quotas"]
        payload = {
            "name": "Unauthorized Backdoor Quota",
            "size": 100,
            "items": [1]
        }
        resp = requests.post(quotas_url, json=payload, headers=auditor_headers)
        assert resp.status_code == 403, f"Auditor created quota! Expected 403, got {resp.status_code}"

    def test_auditor_forbidden_from_marking_order_paid(self, event_endpoints, admin_headers, auditor_headers):
        """SEC-RBAC-06: Auditor receives HTTP 403 Forbidden when attempting to transition an order to paid."""
        # 1. Admin creates an order
        orders_url = event_endpoints["orders"]
        payload = {
            "email": f"sec_paid_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "SEC Paid Test"}]
        }
        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]

        # 2. Auditor attempts mark_paid
        paid_url = f"{orders_url}{order_code}/mark_paid/"
        auditor_resp = requests.post(paid_url, headers=auditor_headers)
        assert auditor_resp.status_code == 403, f"Auditor marked order paid! Expected 403, got {auditor_resp.status_code}"

    def test_auditor_forbidden_from_canceling_order(self, event_endpoints, admin_headers, auditor_headers):
        """SEC-RBAC-07: Auditor receives HTTP 403 Forbidden when attempting to cancel an order."""
        # 1. Admin creates an order
        orders_url = event_endpoints["orders"]
        payload = {
            "email": f"sec_cancel_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "SEC Cancel Test"}]
        }
        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]

        # 2. Auditor attempts mark_canceled
        cancel_url = f"{orders_url}{order_code}/mark_canceled/"
        auditor_resp = requests.post(cancel_url, headers=auditor_headers)
        assert auditor_resp.status_code == 403, f"Auditor cancelled order! Expected 403, got {auditor_resp.status_code}"

    def test_anonymous_requests_rejected_with_401(self, event_endpoints, anonymous_headers):
        """SEC-RBAC-08: Anonymous unauthenticated requests to protected API endpoints return HTTP 401 Unauthorized."""
        for endpoint in ["event", "items", "quotas", "orders"]:
            url = event_endpoints[endpoint]
            resp = requests.get(url, headers=anonymous_headers)
            assert resp.status_code == 401, f"Anonymous GET {endpoint} returned {resp.status_code}, expected 401"

    def test_invalid_token_rejected_with_401(self, event_endpoints, invalid_token_headers):
        """SEC-RBAC-09: Requests with invalid or forged API tokens return HTTP 401 Unauthorized."""
        url = event_endpoints["orders"]
        resp = requests.get(url, headers=invalid_token_headers)
        assert resp.status_code == 401, f"Forged token returned {resp.status_code}, expected 401"

    def test_anonymous_control_panel_redirects_to_login(self):
        """SEC-RBAC-10: Anonymous browser client attempting to access control panel is redirected to login (HTTP 302)."""
        control_url = "http://localhost:8345/control/event/sqe/sqe2026/orders/"
        resp = requests.get(control_url, allow_redirects=False)
        assert resp.status_code in [302, 301], f"Expected redirect, got {resp.status_code}"
        assert "/control/login" in resp.headers.get("Location", ""), f"Redirect target not login: {resp.headers.get('Location')}"
