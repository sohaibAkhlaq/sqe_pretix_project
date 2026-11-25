"""
REST API Integration Tests: Order State Machine, Workflow B Transitions & BR4 Late-Payment Rules.
Covers:
- n -> c (cancellation + quota restoration)
- n -> p (payment confirmation + quota held)
- n -> e (expiration + quota release)
- Disallowed transitions from p, e, and terminal c
- BR4 expired late payment: allowed when quota available, 400 rejected at stockout
"""
import requests


def _create_pending_order(event_endpoints, admin_headers, generated_data):
    payload = generated_data["equivalence_partitions"]["valid_partition"][0]["payload"]
    resp = requests.post(event_endpoints["orders"], json=payload, headers=admin_headers)
    assert resp.status_code == 201, f"Order creation failed: {resp.text}"
    return resp.json()["code"]


def _get_avail(event_endpoints, admin_headers):
    r = requests.get(event_endpoints["quotas"], headers=admin_headers)
    assert r.status_code == 200
    return r.json()["available_number"]


class TestOrderLifecycleTransitions:
    """State-transition integration tests on Workflow B endpoints."""

    def test_cancel_pending_order_restores_quota(self, event_endpoints, admin_headers, generated_data):
        initial_avail = _get_avail(event_endpoints, admin_headers)
        code = _create_pending_order(event_endpoints, admin_headers, generated_data)

        during_avail = _get_avail(event_endpoints, admin_headers)
        assert during_avail == initial_avail - 1

        r_cancel = requests.post(f"{event_endpoints['orders']}{code}/mark_canceled/", headers=admin_headers)
        assert r_cancel.status_code == 200
        assert r_cancel.json()["status"] == "c"

        restored_avail = _get_avail(event_endpoints, admin_headers)
        assert restored_avail == initial_avail

    def test_mark_order_paid_holds_quota_and_blocks_duplicate_pay_or_expire(
        self, event_endpoints, admin_headers, generated_data
    ):
        initial_avail = _get_avail(event_endpoints, admin_headers)
        code = _create_pending_order(event_endpoints, admin_headers, generated_data)

        r_paid = requests.post(f"{event_endpoints['orders']}{code}/mark_paid/", headers=admin_headers)
        assert r_paid.status_code == 200
        assert r_paid.json()["status"] == "p"
        assert _get_avail(event_endpoints, admin_headers) == initial_avail - 1

        # Disallowed transitions from Paid state 'p'
        assert requests.post(f"{event_endpoints['orders']}{code}/mark_paid/", headers=admin_headers).status_code == 400
        assert requests.post(f"{event_endpoints['orders']}{code}/mark_expired/", headers=admin_headers).status_code == 400

        # Cleanup via p -> c
        r_cancel = requests.post(f"{event_endpoints['orders']}{code}/mark_canceled/", headers=admin_headers)
        assert r_cancel.status_code == 200
        assert r_cancel.json()["status"] == "c"
        assert _get_avail(event_endpoints, admin_headers) == initial_avail

    def test_mark_order_expired_releases_quota_and_blocks_double_expire(
        self, event_endpoints, admin_headers, generated_data
    ):
        initial_avail = _get_avail(event_endpoints, admin_headers)
        code = _create_pending_order(event_endpoints, admin_headers, generated_data)
        assert _get_avail(event_endpoints, admin_headers) == initial_avail - 1

        r_exp = requests.post(f"{event_endpoints['orders']}{code}/mark_expired/", headers=admin_headers)
        assert r_exp.status_code == 200
        assert r_exp.json()["status"] == "e"

        final_avail = _get_avail(event_endpoints, admin_headers)
        assert final_avail == initial_avail

        # Disallowed transition from 'e': re-expiring must fail 400
        assert requests.post(f"{event_endpoints['orders']}{code}/mark_expired/", headers=admin_headers).status_code == 400
        # Cancel expired order cleans up without altering quota further
        assert requests.post(f"{event_endpoints['orders']}{code}/mark_canceled/", headers=admin_headers).status_code == 200
        assert _get_avail(event_endpoints, admin_headers) == initial_avail

    def test_terminal_canceled_state_rejects_all_transitions(self, event_endpoints, admin_headers, generated_data):
        initial_avail = _get_avail(event_endpoints, admin_headers)
        code = _create_pending_order(event_endpoints, admin_headers, generated_data)
        assert requests.post(f"{event_endpoints['orders']}{code}/mark_canceled/", headers=admin_headers).status_code == 200

        for action in ("mark_canceled", "mark_paid", "mark_expired"):
            r = requests.post(f"{event_endpoints['orders']}{code}/{action}/", headers=admin_headers)
            assert r.status_code == 400, f"Canceled order should reject {action}, got {r.status_code}"

        assert _get_avail(event_endpoints, admin_headers) == initial_avail

    def test_br4_expired_order_late_payment_with_headroom_vs_stockout(
        self, event_endpoints, admin_headers, generated_data
    ):
        """BR4 Integration: expired e -> p succeeds when quota > 0, and fails 400 when quota == 0."""
        orders_url = event_endpoints["orders"]
        initial_avail = _get_avail(event_endpoints, admin_headers)

        # Case A: Headroom available -> mark_paid reclaims 1 unit and sets status 'p'
        code_ok = _create_pending_order(event_endpoints, admin_headers, generated_data)
        assert requests.post(f"{orders_url}{code_ok}/mark_expired/", headers=admin_headers).status_code == 200
        assert _get_avail(event_endpoints, admin_headers) == initial_avail

        r_late_ok = requests.post(f"{orders_url}{code_ok}/mark_paid/", headers=admin_headers)
        assert r_late_ok.status_code == 200
        assert r_late_ok.json()["status"] == "p"
        assert _get_avail(event_endpoints, admin_headers) == initial_avail - 1
        assert requests.post(f"{orders_url}{code_ok}/mark_canceled/", headers=admin_headers).status_code == 200

        # Case B: Stockout -> saturate remaining quota with bulk boundary order (EP-BND-02)
        code_exp = _create_pending_order(event_endpoints, admin_headers, generated_data)
        assert requests.post(f"{orders_url}{code_exp}/mark_expired/", headers=admin_headers).status_code == 200

        bulk_case = next(c for c in generated_data["equivalence_partitions"]["valid_partition"] if c["case_id"] == "EP-VAL-03")
        r_bulk = requests.post(orders_url, json=bulk_case["payload"], headers=admin_headers)
        assert r_bulk.status_code == 201
        code_bulk = r_bulk.json()["code"]
        assert _get_avail(event_endpoints, admin_headers) == 0

        r_late_denied = requests.post(f"{orders_url}{code_exp}/mark_paid/", headers=admin_headers)
        assert r_late_denied.status_code == 400
        detail_after = requests.get(f"{orders_url}{code_exp}/", headers=admin_headers).json()
        assert detail_after["status"] == "e"
        assert _get_avail(event_endpoints, admin_headers) == 0

        # Cleanup
        assert requests.post(f"{orders_url}{code_bulk}/mark_canceled/", headers=admin_headers).status_code == 200
        assert requests.post(f"{orders_url}{code_exp}/mark_canceled/", headers=admin_headers).status_code == 200
        assert _get_avail(event_endpoints, admin_headers) == initial_avail
