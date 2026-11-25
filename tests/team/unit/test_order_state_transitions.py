"""
White-Box Unit Tests for BR3 (Order State Eligibility & Expiration) and BR4 (Late Payment Decision).
Executes the exact production AST from:
- upstream/pretix/base/models/orders.py:646-649 (Order.cancel_allowed)
- upstream/pretix/base/services/orders.py:360-382 (mark_order_expired)
- upstream/pretix/base/models/orders.py:1026-1047 (Order._can_be_paid)
via upstream.pretix.base.scoped_business_logic, including full 8-row MCC + MC/DC pairs for BR4.
"""
from contextlib import contextmanager
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from production_source import assert_ast_matches_upstream
from upstream.pretix.base import scoped_business_logic as sbl
from upstream.pretix.base.scoped_business_logic import Order, mark_order_expired


class StubQuerySet:
    def __init__(self, last_invoice=None):
        self._last = last_invoice

    def last(self):
        return self._last


class StubInvoicesManager:
    def __init__(self, last_invoice=None):
        self._last = last_invoice

    def filter(self, **kwargs):
        return StubQuerySet(self._last)


class ProductionOrder(Order):
    def __init__(
        self,
        pk=1,
        code="SQE01",
        status=Order.STATUS_PENDING,
        count_positions=1,
        require_approval=False,
        payment_term_last=None,
        accept_late=False,
        available_result=True,
        invoice=None,
    ):
        self.pk = pk
        self.code = code
        self.status = status
        self.count_positions = count_positions
        self.require_approval = require_approval
        self.payment_term_last = payment_term_last
        self.event = SimpleNamespace(
            settings=SimpleNamespace(get=lambda key: accept_late if key == "payment_term_accept_late" else None)
        )
        self._available_result = available_result
        self.invoices = StubInvoicesManager(invoice)
        self.saved_fields = []
        self.logged_actions = []
        self.transactions_created = 0

    def _is_still_available(self, count_waitinglist=True, force=False, lock=False):
        return self._available_result

    def save(self, update_fields=None):
        self.saved_fields.append(update_fields)

    def log_action(self, action, user=None, auth=None):
        self.logged_actions.append((action, user, auth))

    def create_transactions(self):
        self.transactions_created += 1


def _bind_collaborators(monkeypatch, current_time=None, order_obj=None, user_obj=None, cancelled_invoices=None, expired_events=None):
    monkeypatch.setattr(sbl, "_", lambda msg: msg)
    monkeypatch.setattr(sbl, "time_machine_now", lambda: current_time or datetime(2026, 12, 1, 12, 0, 0))

    @contextmanager
    def dummy_atomic():
        yield

    monkeypatch.setattr(sbl, "transaction", SimpleNamespace(atomic=dummy_atomic))
    monkeypatch.setattr(Order, "objects", SimpleNamespace(get=lambda pk: order_obj))
    monkeypatch.setattr(sbl, "User", SimpleNamespace(objects=SimpleNamespace(get=lambda pk: user_obj)))
    monkeypatch.setattr(
        sbl,
        "generate_cancellation",
        lambda inv: cancelled_invoices.append(inv) if cancelled_invoices is not None else None,
    )
    monkeypatch.setattr(
        sbl,
        "order_expired",
        SimpleNamespace(
            send=lambda event, order: expired_events.append((event, order)) if expired_events is not None else None
        ),
    )


class TestUpstreamASTParity:
    def test_br3_cancel_allowed_matches_upstream_ast(self):
        assert_ast_matches_upstream("base/models/orders.py", "Order", "Order", "cancel_allowed")

    def test_br3_mark_order_expired_matches_upstream_ast(self):
        assert_ast_matches_upstream("base/services/orders.py", None, None, "mark_order_expired")

    def test_br4_can_be_paid_matches_upstream_ast(self):
        assert_ast_matches_upstream("base/models/orders.py", "Order", "Order", "_can_be_paid")


class TestOrderCancelEligibilityAndExpirationBR3:
    """Exercises real upstream Order.cancel_allowed and mark_order_expired for BR3."""

    @pytest.mark.parametrize(
        "status,positions,expected",
        [
            (Order.STATUS_PENDING, 1, True),
            (Order.STATUS_PAID, 2, True),
            (Order.STATUS_EXPIRED, 1, True),
            (Order.STATUS_CANCELED, 1, False),
            (Order.STATUS_PENDING, 0, False),
        ],
    )
    def test_cancel_allowed_matrix(self, status, positions, expected):
        order = ProductionOrder(status=status, count_positions=positions)
        assert bool(order.cancel_allowed()) is expected

    @pytest.mark.skip(reason="Red-Gate PR verification: simulate missing unit test dropping scoped coverage < 100%")
    def test_mark_order_expired_by_ids_cancels_unreferred_invoice(self, monkeypatch):
        inv = SimpleNamespace(refered=SimpleNamespace(exists=lambda: False))
        order = ProductionOrder(pk=10, status=Order.STATUS_PENDING, invoice=inv)
        user = SimpleNamespace(pk=7, email="cron@localhost")
        cancelled = []
        signals = []
        _bind_collaborators(monkeypatch, order_obj=order, user_obj=user, cancelled_invoices=cancelled, expired_events=signals)

        ret = mark_order_expired(10, user=7, auth="system-cron")

        assert ret is order
        assert order.status == Order.STATUS_EXPIRED
        assert order.saved_fields == [["status"]]
        assert order.logged_actions == [("pretix.event.order.expired", user, "system-cron")]
        assert cancelled == [inv]
        assert order.transactions_created == 1
        assert signals == [(order.event, order)]

    def test_mark_order_expired_with_objects_and_referred_invoice(self, monkeypatch):
        inv_already_canceled = SimpleNamespace(refered=SimpleNamespace(exists=lambda: True))
        order = ProductionOrder(pk=11, status=Order.STATUS_PENDING, invoice=inv_already_canceled)
        cancelled = []
        signals = []
        _bind_collaborators(monkeypatch, cancelled_invoices=cancelled, expired_events=signals)

        ret = mark_order_expired(order, user=None)
        assert ret.status == Order.STATUS_EXPIRED
        assert cancelled == []

    def test_mark_order_expired_without_invoice(self, monkeypatch):
        order = ProductionOrder(pk=12, status=Order.STATUS_PENDING, invoice=None)
        cancelled = []
        signals = []
        _bind_collaborators(monkeypatch, cancelled_invoices=cancelled, expired_events=signals)

        mark_order_expired(order)
        assert order.status == Order.STATUS_EXPIRED
        assert cancelled == []


class TestLatePaymentDecisionBR4:
    """Exercises real upstream Order._can_be_paid covering all branches, 8 MCC rows, and MC/DC pairs."""

    def test_requires_approval_blocks_when_not_forced(self, monkeypatch):
        _bind_collaborators(monkeypatch)
        order = ProductionOrder(status=Order.STATUS_PENDING, require_approval=True)
        res = order._can_be_paid(force=False)
        assert "not yet approved" in res

    def test_payment_term_last_past_due_blocks_unless_ignored(self, monkeypatch):
        now_dt = datetime(2026, 12, 5, 12, 0, 1)
        past_last = datetime(2026, 12, 5, 12, 0, 0)
        _bind_collaborators(monkeypatch, current_time=now_dt)

        order = ProductionOrder(status=Order.STATUS_PENDING, payment_term_last=past_last)
        res = order._can_be_paid(ignore_date=False, force=False)
        assert "last date of payments" in res

        # Within term_last allows pending payment
        _bind_collaborators(monkeypatch, current_time=past_last)
        assert order._can_be_paid(ignore_date=False, force=False) is True

        # ignore_date=True bypasses term_last guard
        _bind_collaborators(monkeypatch, current_time=now_dt)
        assert order._can_be_paid(ignore_date=True, force=False) is True

    def test_pending_order_allowed_when_no_term_limit(self, monkeypatch):
        _bind_collaborators(monkeypatch)
        order = ProductionOrder(status=Order.STATUS_PENDING, payment_term_last=None)
        assert order._can_be_paid() is True

    # BR4 Multi-condition late-payment decision (models/orders.py:1044):
    # D = (not accept_late) and (not ignore_date) and (not force)
    BR4_MCC_ROWS = [
        # (case_id, accept_late, ignore_date, force, avail_ret, expected_blocked)
        ("TC-BR4-MCC-01", False, False, False, True, True),
        ("TC-BR4-MCC-02", False, False, True, True, False),
        ("TC-BR4-MCC-03", False, True, False, True, False),
        ("TC-BR4-MCC-04", False, True, True, True, False),
        ("TC-BR4-MCC-05", True, False, False, True, False),
        ("TC-BR4-MCC-06", True, False, True, True, False),
        ("TC-BR4-MCC-07", True, True, False, True, False),
        ("TC-BR4-MCC-08", True, True, True, True, False),
    ]

    @pytest.mark.parametrize("case_id,accept_late,ignore_date,force,avail_ret,expected_blocked", BR4_MCC_ROWS)
    def test_br4_mcc_expired_order_late_payment(
        self, monkeypatch, case_id, accept_late, ignore_date, force, avail_ret, expected_blocked
    ):
        _bind_collaborators(monkeypatch)
        order = ProductionOrder(
            status=Order.STATUS_EXPIRED,
            accept_late=accept_late,
            available_result=avail_ret,
        )
        res = order._can_be_paid(ignore_date=ignore_date, force=force)
        if expected_blocked:
            assert isinstance(res, str) and "expired" in res
        else:
            assert res is True

    def test_br4_mcdc_condition_independence_and_quota_exhaustion(self, monkeypatch):
        """Proves each condition (accept_late, ignore_date, force) independently flips _can_be_paid, plus over-quota reject."""
        _bind_collaborators(monkeypatch)

        # Baseline blocking vector (accept_late=False, ignore_date=False, force=False)
        order_base = ProductionOrder(status=Order.STATUS_EXPIRED, accept_late=False, available_result=True)
        assert "no late payments" in order_base._can_be_paid(ignore_date=False, force=False)

        # Toggle A (accept_late: False -> True) while B, C fixed
        order_late_ok = ProductionOrder(status=Order.STATUS_EXPIRED, accept_late=True, available_result=True)
        assert order_late_ok._can_be_paid(ignore_date=False, force=False) is True

        # Toggle B (ignore_date: False -> True) while A, C fixed
        assert order_base._can_be_paid(ignore_date=True, force=False) is True

        # Toggle C (force: False -> True) while A, B fixed
        assert order_base._can_be_paid(ignore_date=False, force=True) is True

        # Over-quota expired late payment rejection (FR8 / BR4): quota exhausted
        order_sold_out = ProductionOrder(
            status=Order.STATUS_EXPIRED,
            accept_late=True,
            available_result='The ordered product "General Admission" is no longer available.',
        )
        res = order_sold_out._can_be_paid(ignore_date=False, force=False)
        assert "no longer available" in res
