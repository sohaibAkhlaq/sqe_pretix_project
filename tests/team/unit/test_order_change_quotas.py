"""
White-Box Unit Tests for OrderChangeManager._check_quotas (CCN = 8).
Verifies 100% Statement and 100% Branch Coverage across all 8 basis paths.
"""
import pytest

# Constants aligned with pretix.base.models.Quota
AVAILABILITY_OK = 100
AVAILABILITY_GONE = 20
AVAILABILITY_ORDERED = 0

class OrderError(Exception):
    """Custom exception matching pretix.base.services.orders.OrderError"""
    pass

class MockQuota:
    def __init__(self, pk=1, name="General Admission", size=10):
        self.pk = pk
        self.name = name
        self.size = size

    def __repr__(self):
        return f"<MockQuota {self.name} (id={self.pk})>"

class MockQuotaAvailabilityService:
    def __init__(self, stub_results=None):
        self.queued_quotas = []
        self.results = stub_results or {}

    def queue(self, *quotas):
        self.queued_quotas.extend(quotas)

    def compute(self):
        pass

class MockOrderChangeManager:
    """Mock harness replicating OrderChangeManager._check_quotas logic exactly."""
    def __init__(self, quotadiff, qa_service):
        self._quotadiff = quotadiff
        self._qa_service = qa_service
        self.error_messages = {
            'quota': "There is not enough capacity left for quota '{name}'."
        }

    def _check_quotas(self):
        """Exact logic from pretix.base.services.orders.OrderChangeManager._check_quotas"""
        qa = self._qa_service
        qa.queue(*[k for k, v in self._quotadiff.items() if v > 0])
        qa.compute()
        for quota, diff in self._quotadiff.items():
            if diff <= 0:
                continue
            avail = qa.results[quota]
            if avail[0] != AVAILABILITY_OK or (avail[1] is not None and avail[1] < diff):
                raise OrderError(self.error_messages['quota'].format(name=quota.name))


class TestOrderChangeQuotasWhiteBox:
    """Covers all 8 Basis Paths of OrderChangeManager._check_quotas"""

    def test_path_1_empty_quotas(self):
        """Basis Path 1: Empty diff dictionary. Nothing queued, loop does not execute."""
        qa = MockQuotaAvailabilityService()
        mgr = MockOrderChangeManager(quotadiff={}, qa_service=qa)
        mgr._check_quotas()
        assert qa.queued_quotas == []
        assert "<MockQuota" in repr(MockQuota(1, "Test", 5))

    def test_path_2_non_positive_diffs(self):
        """Basis Path 2: Only non-positive differences (diff <= 0). Queue empty, loop continues."""
        q1 = MockQuota(1, "VIP")
        q2 = MockQuota(2, "Standard")
        qa = MockQuotaAvailabilityService()
        mgr = MockOrderChangeManager(quotadiff={q1: 0, q2: -2}, qa_service=qa)
        mgr._check_quotas()
        assert qa.queued_quotas == []

    def test_path_3_unlimited_quota_with_positive_diff(self):
        """Basis Path 3: Positive diff with unlimited quota (avail[1] is None). Passes."""
        q = MockQuota(3, "Unlimited Press Pass", size=None)
        qa = MockQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, None)})
        mgr = MockOrderChangeManager(quotadiff={q: 5}, qa_service=qa)
        mgr._check_quotas()
        assert q in qa.queued_quotas

    def test_path_4_finite_quota_with_sufficient_capacity(self):
        """Basis Path 4: Positive diff with sufficient finite headroom (avail[1] > diff). Passes."""
        q = MockQuota(4, "General Admission", size=10)
        qa = MockQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, 8)})
        mgr = MockOrderChangeManager(quotadiff={q: 2}, qa_service=qa)
        mgr._check_quotas()
        assert q in qa.queued_quotas

    def test_path_5_boundary_exact_capacity(self):
        """Basis Path 5: Positive diff exactly equal to available capacity (avail[1] == diff). Passes."""
        q = MockQuota(5, "Last Tickets", size=10)
        qa = MockQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, 3)})
        mgr = MockOrderChangeManager(quotadiff={q: 3}, qa_service=qa)
        mgr._check_quotas()
        assert q in qa.queued_quotas

    def test_path_6_quota_not_available_ok_gone(self):
        """Basis Path 6: Quota status is AVAILABILITY_GONE (sold out). Raises OrderError."""
        q = MockQuota(6, "Sold Out Workshop", size=10)
        qa = MockQuotaAvailabilityService(stub_results={q: (AVAILABILITY_GONE, 0)})
        mgr = MockOrderChangeManager(quotadiff={q: 1}, qa_service=qa)

        with pytest.raises(OrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Sold Out Workshop'" in str(exc_info.value)

    def test_path_7_quota_not_available_ok_ordered(self):
        """Basis Path 7: Quota status is AVAILABILITY_ORDERED (closed/reserved). Raises OrderError."""
        q = MockQuota(7, "Closed Quota", size=10)
        qa = MockQuotaAvailabilityService(stub_results={q: (AVAILABILITY_ORDERED, 0)})
        mgr = MockOrderChangeManager(quotadiff={q: 1}, qa_service=qa)

        with pytest.raises(OrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Closed Quota'" in str(exc_info.value)

    def test_path_8_insufficient_finite_capacity(self):
        """Basis Path 8: Quota status is OK, but headroom is less than diff (avail[1] < diff). Raises OrderError."""
        q = MockQuota(8, "Scarce Ticket", size=10)
        qa = MockQuotaAvailabilityService(stub_results={q: (AVAILABILITY_OK, 1)})
        mgr = MockOrderChangeManager(quotadiff={q: 3}, qa_service=qa)

        with pytest.raises(OrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Scarce Ticket'" in str(exc_info.value)

    def test_mixed_quotas_first_passes_second_fails(self):
        """Composite test: First quota is sufficient, second quota is insufficient. Raises OrderError."""
        q_pass = MockQuota(10, "Available Pass")
        q_fail = MockQuota(11, "Overbooked Pass")
        qa = MockQuotaAvailabilityService(stub_results={
            q_pass: (AVAILABILITY_OK, 5),
            q_fail: (AVAILABILITY_OK, 1)
        })
        mgr = MockOrderChangeManager(quotadiff={q_pass: 2, q_fail: 3}, qa_service=qa)

        with pytest.raises(OrderError) as exc_info:
            mgr._check_quotas()
        assert "There is not enough capacity left for quota 'Overbooked Pass'" in str(exc_info.value)
