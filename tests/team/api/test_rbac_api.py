"""
API Integration Tests for Role-Based Access Control (FR7, PR6).
Verifies strict separation between Privileged Admin Token and Restricted Auditor Token.
"""
import pytest
import requests
import uuid

class TestRBACPermissionsAPI:
    """Verifies that read-only tokens cannot execute state-mutating operations."""

    def test_auditor_can_inspect_all_read_endpoints(self, event_endpoints, auditor_headers):
        """TC-API-07a: Auditor token has full read visibility across organizer, event, items, quotas, and orders."""
        # 1. Organizer
        r1 = requests.get(event_endpoints["organizer"], headers=auditor_headers)
        assert r1.status_code == 200, f"Auditor failed GET organizer: {r1.status_code}"

        # 2. Event
        r2 = requests.get(event_endpoints["event"], headers=auditor_headers)
        assert r2.status_code == 200, f"Auditor failed GET event: {r2.status_code}"

        # 3. Item detail
        item_url = f"{event_endpoints['items']}1/"
        r3 = requests.get(item_url, headers=auditor_headers)
        assert r3.status_code == 200, f"Auditor failed GET item: {r3.status_code}"

        # 4. Quota availability
        r4 = requests.get(event_endpoints["quotas"], headers=auditor_headers)
        assert r4.status_code == 200, f"Auditor failed GET quota availability: {r4.status_code}"

        # 5. Orders list
        r5 = requests.get(event_endpoints["orders"], headers=auditor_headers)
        assert r5.status_code == 200, f"Auditor failed GET orders: {r5.status_code}"

    def test_auditor_cannot_place_orders(self, event_endpoints, auditor_headers):
        """TC-API-07b: Auditor token receives HTTP 403 Forbidden when attempting to place an order."""
        orders_url = event_endpoints["orders"]
        payload = {
            "email": "malicious_auditor@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "Auditor Exploit"}]
        }
        resp = requests.post(orders_url, json=payload, headers=auditor_headers)
        assert resp.status_code == 403, f"Auditor was able to place order! Status: {resp.status_code}"

    def test_auditor_cannot_mutate_items(self, event_endpoints, auditor_headers):
        """TC-API-07c: Auditor token receives HTTP 403 Forbidden when attempting to create/update items."""
        items_url = event_endpoints["items"]
        payload = {
            "name": {"en": "Unauthorized Ticket Tier"},
            "default_price": "10.00",
            "active": True
        }
        resp = requests.post(items_url, json=payload, headers=auditor_headers)
        assert resp.status_code == 403, f"Auditor was able to mutate items! Status: {resp.status_code}"

    def test_auditor_cannot_cancel_orders(self, event_endpoints, admin_headers, auditor_headers):
        """TC-API-07d: Auditor token receives HTTP 403 Forbidden when attempting to cancel an order."""
        orders_url = event_endpoints["orders"]

        # Admin creates order
        payload = {
            "email": f"rbac_cancel_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "RBAC Cancel"}]
        }
        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]

        # Auditor attempts cancellation
        cancel_url = f"{orders_url}{order_code}/mark_canceled/"
        auditor_resp = requests.post(cancel_url, headers=auditor_headers)
        assert auditor_resp.status_code == 403, f"Auditor canceled order! Status: {auditor_resp.status_code}"
