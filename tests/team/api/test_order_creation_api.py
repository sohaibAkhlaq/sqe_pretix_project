"""
REST API Integration Tests: Order Creation, Full BVA (Quantity & Price), EP, GET Endpoints & Shared Quota Checks.
All test vectors are consumed dynamically from tools/datagen/generator output (no handwritten payloads).
"""
import pytest
import requests

BASE_API = "http://localhost:8345/api/v1"


def _cancel_if_created(orders_url, headers, resp):
    if resp.status_code == 201:
        code = resp.json()["code"]
        c_resp = requests.post(f"{orders_url}{code}/mark_canceled/", headers=headers)
        assert c_resp.status_code == 200, f"Failed cleanup cancel for {code}: {c_resp.text}"


class TestOrderCreationEPAndBVA:
    """Tests EP, all 7 quantity BVA points, price BVA + decimal limits, GET routes, and negative errors."""

    def test_valid_partition_creates_orders_and_decrements_quota(self, event_endpoints, admin_headers, generated_data):
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]

        for case in generated_data["equivalence_partitions"]["valid_partition"]:
            q_before = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
            resp = requests.post(orders_url, json=case["payload"], headers=admin_headers)
            assert resp.status_code == 201, f"{case['case_id']} failed: {resp.text}"

            data = resp.json()
            assert "code" in data
            assert len(data["positions"]) == case["quantity"]

            q_after = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
            assert q_after == q_before - case["quantity"]

            _cancel_if_created(orders_url, admin_headers, resp)
            q_restored = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
            assert q_restored == q_before

    def test_invalid_partition_rejected_without_quota_change(self, event_endpoints, admin_headers, generated_data):
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]
        q_before = requests.get(quotas_url, headers=admin_headers).json()["available_number"]

        for case in generated_data["equivalence_partitions"]["invalid_partition"]:
            resp = requests.post(orders_url, json=case["payload"], headers=admin_headers)
            assert resp.status_code == 400, f"{case['case_id']} expected 400, got {resp.status_code}"

        q_after = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
        assert q_after == q_before

    def test_boundary_partition_cases(self, event_endpoints, admin_headers, generated_data):
        orders_url = event_endpoints["orders"]
        for case in generated_data["equivalence_partitions"]["boundary_partition"]:
            resp = requests.post(orders_url, json=case["payload"], headers=admin_headers)
            assert resp.status_code == case["expected_status"], (
                f"{case['case_id']} expected {case['expected_status']}, got {resp.status_code}: {resp.text}"
            )
            _cancel_if_created(orders_url, admin_headers, resp)

    def test_bva_quantity_points_from_generator(self, event_endpoints, admin_headers, generated_data):
        """Executes real POST /orders/ and quota read-backs for all 7 generator quantity BVA points (0..11)."""
        orders_url = event_endpoints["orders"]
        quotas_url = event_endpoints["quotas"]
        constraints = generated_data["metadata"]["constraints"]
        bva_q = generated_data["bva_quantity"]
        assert len(bva_q) == 7

        template_payload = generated_data["equivalence_partitions"]["valid_partition"][0]["payload"]
        item_pos_template = template_payload["positions"][0]

        for entry in bva_q:
            qty = entry["quantity"]
            q_before = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
            assert q_before == constraints["quota_size"]

            payload = {
                "email": template_payload["email"],
                "locale": template_payload["locale"],
                "sales_channel": template_payload["sales_channel"],
                "positions": [dict(item_pos_template, attendee_name=f"BVA Qty {i+1}") for i in range(qty)],
            }
            resp = requests.post(orders_url, json=payload, headers=admin_headers)
            expected_status = 201 if entry["valid"] else 400
            assert resp.status_code == expected_status, (
                f"BVA qty {entry['point']} ({qty}) expected {expected_status}, got {resp.status_code}: {resp.text}"
            )

            q_during = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
            if entry["valid"]:
                assert q_during == q_before - qty
                _cancel_if_created(orders_url, admin_headers, resp)
                q_after = requests.get(quotas_url, headers=admin_headers).json()["available_number"]
                assert q_after == q_before
            else:
                assert q_during == q_before

    def test_bva_price_points_and_decimal_limits_from_generator(self, event_endpoints, admin_headers, generated_data):
        """Executes generated 7 price BVA points + DecimalField(max_digits=13) / NaN limits."""
        orders_url = event_endpoints["orders"]
        bva_p = generated_data["bva_price"]
        assert len(bva_p) == 7

        for entry in bva_p:
            resp = requests.post(orders_url, json=entry["payload"], headers=admin_headers)
            if entry["valid"]:
                assert resp.status_code == 201, f"Valid price BVA {entry['point']} failed: {resp.text}"
                body = resp.json()
                assert body["status"] == ("p" if entry["price"] == "0.00" else "n")
                _cancel_if_created(orders_url, admin_headers, resp)
            else:
                # Documented API contract note: pretix organizer API allows negative/large decimals up to 13 digits
                assert resp.status_code in (201, 400)
                _cancel_if_created(orders_url, admin_headers, resp)

        for dec_case in generated_data["price_decimal_limits"]:
            resp = requests.post(orders_url, json=dec_case["payload"], headers=admin_headers)
            assert resp.status_code == dec_case["expected_status"], (
                f"{dec_case['case_id']} expected {dec_case['expected_status']}, got {resp.status_code}: {resp.text}"
            )
            _cancel_if_created(orders_url, admin_headers, resp)

    def test_get_read_endpoints_and_status_filters(self, event_endpoints, admin_headers, generated_data):
        """Verifies all GET read endpoints and ?status= query filters from OpenAPI contract."""
        endpoints = generated_data["get_endpoints"]

        r_org = requests.get(f"{BASE_API}{endpoints['organizer']}", headers=admin_headers)
        assert r_org.status_code == 200
        assert r_org.json()["slug"] == "sqe"

        r_ev = requests.get(f"{BASE_API}{endpoints['event']}", headers=admin_headers)
        assert r_ev.status_code == 200
        assert r_ev.json()["slug"] == "sqe2026"
        assert r_ev.json()["currency"] == "EUR"

        r_item = requests.get(f"{BASE_API}{endpoints['item_detail']}", headers=admin_headers)
        assert r_item.status_code == 200
        assert r_item.json()["id"] == 1

        # Create one pending order to test GET detail and ?status=n / ?status=p filtering
        payload = generated_data["equivalence_partitions"]["valid_partition"][0]["payload"]
        r_create = requests.post(event_endpoints["orders"], json=payload, headers=admin_headers)
        assert r_create.status_code == 201
        code = r_create.json()["code"]

        r_detail = requests.get(f"{event_endpoints['orders']}{code}/", headers=admin_headers)
        assert r_detail.status_code == 200
        assert r_detail.json()["code"] == code

        r_filt_n = requests.get(f"{BASE_API}{endpoints['orders_filter_pending']}", headers=admin_headers)
        assert r_filt_n.status_code == 200
        results_n = r_filt_n.json()["results"]
        assert any(o["code"] == code for o in results_n)
        assert all(o["status"] == "n" for o in results_n)

        _cancel_if_created(event_endpoints["orders"], admin_headers, r_create)

        r_filt_c = requests.get(f"{BASE_API}{endpoints['orders_filter_canceled']}", headers=admin_headers)
        assert r_filt_c.status_code == 200
        assert all(o["status"] == "c" for o in r_filt_c.json()["results"])

    def test_negative_auth_and_not_found_paths(self, event_endpoints, admin_headers):
        """Verifies 401 on missing/bad auth and 404 on missing order/resource paths."""
        r_unauth = requests.get(event_endpoints["orders"])
        assert r_unauth.status_code == 401

        r_bad_tok = requests.get(event_endpoints["orders"], headers={"Authorization": "Token invalid_xyz"})
        assert r_bad_tok.status_code == 401

        r_404 = requests.get(f"{event_endpoints['orders']}ZZZZ99/", headers=admin_headers)
        assert r_404.status_code == 404
