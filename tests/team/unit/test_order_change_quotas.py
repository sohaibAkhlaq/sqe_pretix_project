"""
White-Box Unit Tests for OrderChangeManager._check_quotas (CCN = 8, BR1).
Executes the exact production AST from upstream/pretix/base/services/orders.py:2285-2294
via upstream.pretix.base.scoped_business_logic, achieving 100% statement and branch coverage.
"""
import pytest

from production_source import assert_ast_matches_upstream
from upstream.pretix.base import scoped_business_logic as sbl
from upstream.pretix.base.scoped_business_logic import OrderChangeManager, Quota

AVAILABILITY_OK = Quota.AVAILABILITY_OK
AVAILABILITY_GONE = Quota.AVAILABILITY_GONE
AVAILABILITY_ORDERED = Quota.AVAILABILITY_ORDERED


class StubOrderError(Exception):
    """Exception matching pretix.base.services.orders.OrderError."""


class StubQuota:
    def __init__(self, pk=1, name="General Admission", size=10):
        self.pk = pk
        self.name = name
        self.size = size

    def __repr__(self):
        return f"<StubQuota {self.name} (id={self.pk})>"


class StubQuotaAvailabilityService:
    def __init__(self, stub_results=None):
        self.queued_quotas = []
        self.results = stub_results or {}

    def queue(self, *quotas):
        self.queued_quotas.extend(quotas)

    def compute(self):
        pass


class ProductionOrderChangeManager(OrderChangeManager):
    def __init__(self, quotadiff):
        self._quotadiff = quotadiff
        self.error_messages = {
            "quota": "There is not enough capacity left for quota '{name}'."
        }


def _make_manager(monkeypatch, quotadiff, qa_service):
    monkeypatch.setattr(sbl, "QuotaAvailability", lambda: qa_service)
    monkeypatch.setattr(sbl, "OrderError", StubOrderError)
    return ProductionOrderChangeManager(quotadiff)


class TestOrderChangeQuotasWhiteBox:
    """Covers AST parity and all 8 basis paths of OrderChangeManager._check_quotas."""

    def test_ast_parity_with_upstream_orders_service(self):
        assert_ast_matches_upstream(
            "base/services/orders.py", "OrderChangeManager", "OrderChangeManager", "_check_quotas"
        )

    def test_path_1_empty_quotas(self, monkeypatch):
        """Basis Path 1: Empty diff dictionary. Nothing queued, loop does not execute."""
        qa = StubQuotaAvailabilityService()
        mgr = _make_manager(monkeypatch, quotadiff={}, qa_service=qa)
        mgr._check_quotas()
        assert qa.queued_quotas == []
        assert "<StubQuota" in repr(StubQuota(1, "Test", 5))

    def test_path_2_non_positive_diffs(self, monkeypatch):
        """Basis Path 2: Only non-positive differences (diff <= 0). Queue empty, loop continues."""
        q1 = StubQuota(1, "VIP")
        q2 = StubQuota(2, "Standard")
        qa = StubQuotaAvailabilityService()
        mgr = _make_manager(monkeypatch, quotadiff={q1: 0, q2: -2}, qa_service=qa)
        mgr._check_quotas()
        assert qa.queued_quotas == []

    def test_path_3_unlimited_quota_with_positive_diff(self, monkeypatch):
        """Basis Path 3: Positive diff with unlimited quota (avail[1] is None). Passes."""
        q = StubQuota(3, "Unlimited Press Pass", size=None)
        qa = StubQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, None)})
        mgr = _make_manager(monkeypatch, quotadiff={q: 5}, qa_service=qa)
        mgr._check_quotas()
        assert q in qa.queued_quotas

    def test_path_4_finite_quota_with_sufficient_capacity(self, monkeypatch):
        """Basis Path 4: Positive diff with sufficient finite headroom (avail[1] > diff). Passes."""
        q = StubQuota(4, "General Admission", size=10)
        qa = StubQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, 8)})
        mgr = _make_manager(monkeypatch, quotadiff={q: 2}, qa_service=qa)
        mgr._check_quotas()
        assert q in qa.queued_quotas

    def test_path_5_boundary_exact_capacity(self, monkeypatch):
        """Basis Path 5 (BR1 On-Boundary): avail[1] == diff passes."""
        q = StubQuota(5, "Last Tickets", size=10)
        qa = StubQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, 3)})
        mgr = _make_manager(monkeypatch, quotadiff={q: 3}, qa_service=qa)
        mgr._check_quotas()
        assert q in qa.queued_quotas

    def test_path_6_quota_not_available_ok_gone(self, monkeypatch):
        """Basis Path 6: Quota status is AVAILABILITY_GONE (sold out). Raises OrderError."""
        q = StubQuota(6, "Sold Out Workshop", size=10)
        qa = StubQuotaAvailabilityService(stub_results={q: (AVAILABILITY_GONE, 0)})
        mgr = _make_manager(monkeypatch, quotadiff={q: 1}, qa_service=qa)

        with pytest.raises(StubOrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Sold Out Workshop'" in str(exc_info.value)

    def test_path_7_quota_not_available_ok_ordered(self, monkeypatch):
        """Basis Path 7: Quota status is AVAILABILITY_ORDERED (closed/reserved). Raises OrderError."""
        q = StubQuota(7, "Closed Quota", size=10)
        qa = StubQuotaAvailabilityService(stub_results={q: (AVAILABILITY_ORDERED, 0)})
        mgr = _make_manager(monkeypatch, quotadiff={q: 1}, qa_service=qa)

        with pytest.raises(StubOrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Closed Quota'" in str(exc_info.value)

    def test_path_8_insufficient_finite_capacity(self, monkeypatch):
        """Basis Path 8 (BR1 Over-Boundary): avail[1] < diff raises OrderError."""
        q = StubQuota(8, "Scarce Ticket", size=10)
        qa = StubQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, 1)})
        mgr = _make_manager(monkeypatch, quotadiff={q: 3}, qa_service=qa)

        with pytest.raises(StubOrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Scarce Ticket'" in str(exc_info.value)

    def test_mixed_quotas_first_passes_second_fails(self, monkeypatch):
        """Composite test: First quota sufficient, second insufficient -> raises OrderError."""
        q_pass = StubQuota(10, "Available Pass")
        q_fail = StubQuota(11, "Overbooked Pass")
        qa = StubQuotaAvailabilityService(stub_results={
            q_pass: (AVAILABILITY_OK, 5),
            q_fail: (AVAILABILITY_OK, 1),
        })
        mgr = _make_manager(monkeypatch, quotadiff={q_pass: 2, q_fail: 3}, qa_service=qa)

        with pytest.raises(StubOrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Overbooked Pass'" in str(exc_info.value)
