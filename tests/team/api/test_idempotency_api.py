"""
API Integration Tests for Idempotent Order Submission (FR1, PR5).
Verifies that duplicate requests with identical X-Idempotency-Key do not create duplicate records
or consume additional quota.
"""
import pytest
import requests
import uuid

class TestIdempotencyAPI:
    """Tests idempotency middleware and cache deduplication."""

    def test_repeated_submissions_return_identical_order(self, event_endpoints, admin_headers):
        """TC-API-01 / FR1: 5 identical requests with same X-Idempotency-Key return identical code."""
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]

        # 1. Read baseline quota availability
        init_quota = requests.get(quotas_url, headers=admin_headers).json()
        init_avail = init_quota["available_number"]

        # 2. First submission with idempotency key
        idempotency_key = str(uuid.uuid4())
        headers_with_key = admin_headers.copy()
        headers_with_key["X-Idempotency-Key"] = idempotency_key

        payload = {
            "email": f"idempotent_{uuid.uuid4().hex[:6]}@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "Idempotent Attendee"}]
        }

        resp1 = requests.post(orders_url, json=payload, headers=headers_with_key)
        assert resp1.status_code == 201, f"First request failed: {resp1.status_code} {resp1.text}"
        order_code = resp1.json()["code"]

        # 3. Verify quota decremented by exactly 1
        post_order_quota = requests.get(quotas_url, headers=admin_headers).json()
        assert post_order_quota["available_number"] == init_avail - 1

        # 4. Replay identical request 5 times consecutively
        for replay_idx in range(5):
            resp_replay = requests.post(orders_url, json=payload, headers=headers_with_key)
            assert resp_replay.status_code == 201, f"Replay {replay_idx} returned {resp_replay.status_code}"
            replayed_code = resp_replay.json()["code"]
            assert replayed_code == order_code, (
                f"Replay {replay_idx} generated divergent order code {replayed_code} instead of {order_code}!"
            )

        # 5. Verify final quota availability has NOT changed (zero duplicate holds)
        final_quota = requests.get(quotas_url, headers=admin_headers).json()
        assert final_quota["available_number"] == post_order_quota["available_number"], (
            f"Quota leaked during idempotency replay! Initial: {post_order_quota['available_number']}, "
            f"Final: {final_quota['available_number']}"
        )

    def test_divergent_idempotency_keys_create_distinct_orders(self, event_endpoints, admin_headers):
        """Verifies distinct keys yield distinct order entities."""
        orders_url = event_endpoints["orders"]

        key1 = str(uuid.uuid4())
        key2 = str(uuid.uuid4())

        payload1 = {
            "email": "key1@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "User 1"}]
        }
        payload2 = {
            "email": "key2@example.com",
            "locale": "en",
            "sales_channel": "web",
            "positions": [{"item": 1, "price": "50.00", "attendee_name": "User 2"}]
        }

        h1 = admin_headers.copy()
        h1["X-Idempotency-Key"] = key1
        h2 = admin_headers.copy()
        h2["X-Idempotency-Key"] = key2

        r1 = requests.post(orders_url, json=payload1, headers=h1)
        r2 = requests.post(orders_url, json=payload2, headers=h2)

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert r1.json()["code"] != r2.json()["code"], "Different keys must create different orders"
