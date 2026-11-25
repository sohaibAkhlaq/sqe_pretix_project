"""
REST API Integration Tests: Idempotency & Replay Deduplication (PR5 / FR4).
All payloads and UUID keys are consumed directly from tools/datagen/generator output.
"""
import uuid
import requests


class TestIdempotencyDeduplication:
    """Verifies X-Idempotency-Key deduplication, mismatched retry protection, and header naming rules."""

    def test_x_idempotency_key_deduplicates_duplicate_post_and_single_decrements_quota(
        self, event_endpoints, admin_headers, generated_data
    ):
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]
        cases = generated_data["idempotency_cases"]

        key = f"{cases['replay_key']}-{uuid.uuid4().hex[:6]}"
        headers_with_key = {**admin_headers, "X-Idempotency-Key": key}

        q_before = requests.get(quotas_url, headers=admin_headers).json()["available_number"]

        r1 = requests.post(orders_url, json=cases["primary_payload"], headers=headers_with_key)
        assert r1.status_code == 201
        code1 = r1.json()["code"]

        r2 = requests.post(orders_url, json=cases["primary_payload"], headers=headers_with_key)
        assert r2.status_code == 201
        assert r2.json()["code"] == code1
        assert r2.json()["secret"] == r1.json()["secret"]

        q_after = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert q_after == q_before - 1

        # Mismatched body reusing same key also replays original cached response without new allocation
        r3 = requests.post(orders_url, json=cases["mismatched_retry_payload"], headers=headers_with_key)
        assert r3.status_code == 201
        assert r3.json()["code"] == code1
        assert requests.get(quotas_url, headers=admin_headers).json()["available_number"] == q_before - 1

        assert requests.post(f"{orders_url}{code1}/mark_canceled/", headers=admin_headers).status_code == 200
        assert requests.get(quotas_url, headers=admin_headers).json()["available_number"] == q_before

    def test_non_standard_idempotency_key_without_x_prefix_does_not_deduplicate(
        self, event_endpoints, admin_headers, generated_data
    ):
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]
        cases = generated_data["idempotency_cases"]
        headers_bad_hdr = {**admin_headers, "Idempotency-Key": f"{cases['non_x_header_key']}-{uuid.uuid4().hex[:6]}"}

        q_before = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        r1 = requests.post(orders_url, json=cases["distinct_header_payload"], headers=headers_bad_hdr)
        r2 = requests.post(orders_url, json=cases["distinct_header_payload"], headers=headers_bad_hdr)
        assert r1.status_code == 201 and r2.status_code == 201
        assert r1.json()["code"] != r2.json()["code"]
        assert requests.get(quotas_url, headers=admin_headers).json()["available_number"] == q_before - 2

        for r in (r1, r2):
            requests.post(f"{orders_url}{r.json()['code']}/mark_canceled/", headers=admin_headers)
        assert requests.get(quotas_url, headers=admin_headers).json()["available_number"] == q_before
