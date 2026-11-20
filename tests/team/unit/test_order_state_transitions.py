"""
White-Box Unit Tests for Order State Machine (BR3) and Payment Expiration (BR4).
Verifies valid/invalid lifecycle transitions and temporal constraints.
"""
import pytest
from datetime import datetime, timedelta

class InvalidStateTransitionError(Exception):
    """Raised when an illegal order transition is attempted."""
    pass

class MockOrder:
    STATUS_PENDING = 'n'
    STATUS_PAID = 'p'
    STATUS_EXPIRED = 'e'
    STATUS_CANCELED = 'c'

    VALID_TRANSITIONS = {
        STATUS_PENDING: {STATUS_PAID, STATUS_CANCELED, STATUS_EXPIRED},
        STATUS_PAID: {STATUS_CANCELED},  # After refund
        STATUS_EXPIRED: {STATUS_CANCELED},
        STATUS_CANCELED: set() # Terminal state
    }

    def __init__(self, code='W1R4X', status=STATUS_PENDING, expires=None):
        self.code = code
        self.status = status
        self.expires = expires or (datetime.utcnow() + timedelta(days=2))

    def transition_to(self, target_status):
        """Enforces BR3 state machine transition rules."""
        if target_status not in self.VALID_TRANSITIONS.get(self.status, set()):
            raise InvalidStateTransitionError(
                f"Illegal state transition from '{self.status}' to '{target_status}' for order {self.code}"
            )
        self.status = target_status

    def can_accept_payment(self, current_time=None):
        """Enforces BR4: status == PENDING and current_time <= expires."""
        now_dt = current_time or datetime.utcnow()
        return self.status == self.STATUS_PENDING and now_dt <= self.expires


class TestOrderStateMachineBR3:
    """Verifies all valid and forbidden state transitions under BR3."""

    def test_pending_to_paid_valid(self):
        order = MockOrder(status=MockOrder.STATUS_PENDING)
        order.transition_to(MockOrder.STATUS_PAID)
        assert order.status == MockOrder.STATUS_PAID

    def test_pending_to_canceled_valid(self):
        order = MockOrder(status=MockOrder.STATUS_PENDING)
        order.transition_to(MockOrder.STATUS_CANCELED)
        assert order.status == MockOrder.STATUS_CANCELED

    def test_pending_to_expired_valid(self):
        order = MockOrder(status=MockOrder.STATUS_PENDING)
        order.transition_to(MockOrder.STATUS_EXPIRED)
        assert order.status == MockOrder.STATUS_EXPIRED

    def test_canceled_to_paid_forbidden(self):
        """Canceled is terminal; attempting to pay must raise InvalidStateTransitionError."""
        order = MockOrder(status=MockOrder.STATUS_CANCELED)
        with pytest.raises(InvalidStateTransitionError) as exc:
            order.transition_to(MockOrder.STATUS_PAID)
        assert "Illegal state transition from 'c' to 'p'" in str(exc.value)

    def test_canceled_to_pending_forbidden(self):
        order = MockOrder(status=MockOrder.STATUS_CANCELED)
        with pytest.raises(InvalidStateTransitionError):
            order.transition_to(MockOrder.STATUS_PENDING)

    def test_expired_to_paid_forbidden(self):
        """Expired order cannot directly become paid without reactivation."""
        order = MockOrder(status=MockOrder.STATUS_EXPIRED)
        with pytest.raises(InvalidStateTransitionError) as exc:
            order.transition_to(MockOrder.STATUS_PAID)
        assert "Illegal state transition from 'e' to 'p'" in str(exc.value)


class TestPaymentExpirationBR4:
    """Verifies temporal expiration constraints under BR4."""

    def test_payment_allowed_when_pending_and_before_expiry(self):
        now = datetime(2026, 12, 1, 12, 0, 0)
        expiry = datetime(2026, 12, 3, 12, 0, 0)
        order = MockOrder(status=MockOrder.STATUS_PENDING, expires=expiry)
        assert order.can_accept_payment(current_time=now) is True

    def test_payment_allowed_on_exact_expiry_boundary(self):
        now = datetime(2026, 12, 3, 12, 0, 0)
        expiry = datetime(2026, 12, 3, 12, 0, 0)
        order = MockOrder(status=MockOrder.STATUS_PENDING, expires=expiry)
        assert order.can_accept_payment(current_time=now) is True

    def test_payment_rejected_when_past_expiry(self):
        now = datetime(2026, 12, 3, 12, 0, 1) # 1 second late
        expiry = datetime(2026, 12, 3, 12, 0, 0)
        order = MockOrder(status=MockOrder.STATUS_PENDING, expires=expiry)
        assert order.can_accept_payment(current_time=now) is False

    def test_payment_rejected_when_already_paid(self):
        now = datetime(2026, 12, 1, 12, 0, 0)
        expiry = datetime(2026, 12, 3, 12, 0, 0)
        order = MockOrder(status=MockOrder.STATUS_PAID, expires=expiry)
        assert order.can_accept_payment(current_time=now) is False

    def test_payment_rejected_when_canceled_even_before_expiry(self):
        now = datetime(2026, 12, 1, 12, 0, 0)
        expiry = datetime(2026, 12, 3, 12, 0, 0)
        order = MockOrder(status=MockOrder.STATUS_CANCELED, expires=expiry)
        assert order.can_accept_payment(current_time=now) is False
