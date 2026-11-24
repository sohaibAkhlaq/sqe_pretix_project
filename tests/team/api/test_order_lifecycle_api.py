"""
API Integration Tests for Order Lifecycle & Quota Restoration (Workflow B, BR3, BR4).
Verifies state transitions (mark_canceled, mark_paid, mark_expired), quota replenishment,
and rejection of invalid state transitions with state read-backs.
"""
import copy
import uuid
import pytest
import requests

class TestOrderLifecycleAPI:
    """Verifies Workflow B operations and cross-workflow quota state coupling."""

    def test_cancellation_restores_quota_availability(self, event_endpoints, admin_headers, generated_data):
        """TC-API-03 / FR3: Canceling an order returns held capacity to available quota pool."""
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]

        # 1. Baseline availability reading
        initial_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]

        # 2. Place order using generated vector
        vector = generated_data["equivalence_partitions"]["valid_partition"][0]
        payload = copy.deepcopy(vector["payload"])
        payload["email"] = f"cancel_test_{uuid.uuid4().hex[:6]}@example.com"

        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]

        # 3. Verify availability decremented
        mid_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert mid_avail == initial_avail - 1, f"Expected {initial_avail - 1}, got {mid_avail}"

        # 4. Cancel the order (Workflow B)
        cancel_url = f"{orders_url}{order_code}/mark_canceled/"
        cancel_resp = requests.post(cancel_url, headers=admin_headers)
        assert cancel_resp.status_code == 200, f"Cancel failed: {cancel_resp.status_code} {cancel_resp.text}"
        cancel_data = cancel_resp.json()
        assert cancel_data["status"] == "c", f"Expected status 'c', got '{cancel_data['status']}'"

        # 5. State Read-Back: Quota availability is restored to baseline!
        restored_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert restored_avail == initial_avail, (
            f"Quota not restored after cancellation! Expected {initial_avail}, got {restored_avail}"
        )

    def test_order_mark_paid(self, event_endpoints, admin_headers, generated_data):
        """TC-API-04 / FR4: Marking order paid transitions status to 'p' without double quota hold."""
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]

        # 1. Place order using generated vector
        vector = generated_data["equivalence_partitions"]["valid_partition"][0]
        payload = copy.deepcopy(vector["payload"])
        payload["email"] = f"pay_test_{uuid.uuid4().hex[:6]}@example.com"

        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]
        held_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]

        # 2. Mark Paid
        pay_url = f"{orders_url}{order_code}/mark_paid/"
        pay_resp = requests.post(pay_url, headers=admin_headers)
        assert pay_resp.status_code == 200, f"Mark paid failed: {pay_resp.status_code} {pay_resp.text}"
        assert pay_resp.json()["status"] == "p"

        # 3. State Read-Back: Quota remains allocated (not decremented twice)
        post_pay_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert post_pay_avail == held_avail, "Paid order should retain initial reservation without double deduction"

    def test_order_mark_expired_restores_quota(self, event_endpoints, admin_headers, generated_data):
        """TC-API-05 / FR5: Expiring a pending order restores quota to the pool."""
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]

        initial_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]

        # 1. Place order using generated vector
        vector = generated_data["equivalence_partitions"]["valid_partition"][0]
        payload = copy.deepcopy(vector["payload"])
        payload["email"] = f"expire_test_{uuid.uuid4().hex[:6]}@example.com"

        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        assert create_resp.status_code == 201
        order_code = create_resp.json()["code"]

        # 2. Mark Expired
        expire_url = f"{orders_url}{order_code}/mark_expired/"
        exp_resp = requests.post(expire_url, headers=admin_headers)
        assert exp_resp.status_code == 200, f"Expire failed: {exp_resp.status_code} {exp_resp.text}"
        assert exp_resp.json()["status"] == "e"

        # 3. State Read-Back: Quota availability is restored
        final_avail = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert final_avail == initial_avail, "Expired order must release quota back to pool"

    def test_illegal_transition_canceled_to_paid_rejected(self, event_endpoints, admin_headers, generated_data):
        """TC-API-10 / BR3: Attempting to pay an already canceled order is strictly rejected (Terminal State)."""
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]

        # 1. Place and cancel order
        vector = generated_data["equivalence_partitions"]["valid_partition"][0]
        payload = copy.deepcopy(vector["payload"])
        payload["email"] = f"illegal_{uuid.uuid4().hex[:6]}@example.com"

        create_resp = requests.post(orders_url, json=payload, headers=admin_headers)
        order_code = create_resp.json()["code"]

        cancel_url = f"{orders_url}{order_code}/mark_canceled/"
        requests.post(cancel_url, headers=admin_headers)

        q_before_illegal = requests.get(quotas_url, headers=admin_headers).json()["available_number"]

        # 2. Attempt illegal mark_paid on canceled order
        pay_url = f"{orders_url}{order_code}/mark_paid/"
        pay_resp = requests.post(pay_url, headers=admin_headers)
        assert pay_resp.status_code in [400, 409], (
            f"Expected 400/409 for illegal transition Canceled -> Paid, got {pay_resp.status_code}"
        )

        # 3. State Read-Back: Order remains 'c' and quota remains unchanged
        order_status = requests.get(f"{orders_url}{order_code}/", headers=admin_headers).json()["status"]
        assert order_status == "c", f"Illegal transition mutated status to {order_status}"

        q_after_illegal = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert q_after_illegal == q_before_illegal, "Illegal transition attempt mutated quota availability"
