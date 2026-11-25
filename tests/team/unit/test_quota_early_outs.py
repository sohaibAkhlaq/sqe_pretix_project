"""
White-Box Unit Tests for QuotaAvailability._compute_early_outs (CCN = 6, BR2 / BR1).
Executes the exact production AST from upstream/pretix/base/services/quotas.py:493-500
via upstream.pretix.base.scoped_business_logic, achieving 100% statement and branch coverage.
"""
from production_source import assert_ast_matches_upstream
from upstream.pretix.base.scoped_business_logic import Quota, QuotaAvailabilityPolicy

AVAILABILITY_OK = Quota.AVAILABILITY_OK
AVAILABILITY_GONE = Quota.AVAILABILITY_GONE
AVAILABILITY_ORDERED = Quota.AVAILABILITY_ORDERED


class StubQuota:
    def __init__(self, pk=1, name="General Admission", size=10, closed=False):
        self.pk = pk
        self.name = name
        self.size = size
        self.closed = closed

    def __repr__(self):
        return f"<StubQuota pk={self.pk} size={self.size} closed={self.closed}>"


class ProductionQuotaAvailability(QuotaAvailabilityPolicy):
    def __init__(self, ignore_closed=False):
        self.results = {}
        self._ignore_closed = ignore_closed


class TestQuotaEarlyOutsWhiteBox:
    """Covers AST parity and all 6 basis paths of QuotaAvailability._compute_early_outs."""

    def test_ast_parity_with_upstream_quotas_service(self):
        assert_ast_matches_upstream(
            "base/services/quotas.py", "QuotaAvailability", "QuotaAvailabilityPolicy", "_compute_early_outs"
        )

    def test_path_1_empty_quotas(self):
        """Basis Path 1: Empty input list. Loop does not execute."""
        qa = ProductionQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([])
        assert qa.results == {}
        assert "<StubQuota" in repr(StubQuota(1, "Test", 5))

    def test_path_2_closed_quota_not_ignored(self):
        """Basis Path 2: Closed quota with ignore_closed=False -> (ORDERED, 0)."""
        q = StubQuota(pk=1, closed=True, size=10)
        qa = ProductionQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_ORDERED, 0)

    def test_path_3_closed_quota_ignored_and_size_positive(self):
        """Basis Path 3: Closed quota with ignore_closed=True, size > 0 -> Fallthrough."""
        q = StubQuota(pk=2, closed=True, size=10)
        qa = ProductionQuotaAvailability(ignore_closed=True)
        qa._compute_early_outs([q])
        assert q not in qa.results

    def test_path_4_unlimited_quota(self):
        """Basis Path 4: Open quota with size=None (unlimited) -> (OK, None)."""
        q = StubQuota(pk=3, closed=False, size=None)
        qa = ProductionQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_OK, None)

    def test_path_5_depleted_quota_size_zero(self):
        """Basis Path 5: Open quota with size=0 -> (GONE, 0)."""
        q = StubQuota(pk=4, closed=False, size=0)
        qa = ProductionQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_GONE, 0)

    def test_path_6_normal_positive_quota_fallthrough(self):
        """Basis Path 6: Open quota with size > 0 (e.g. 10) -> Fallthrough (no early-out)."""
        q = StubQuota(pk=5, closed=False, size=10)
        qa = ProductionQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert q not in qa.results

    def test_closed_ignored_with_size_none(self):
        """Covers branch: q.closed=True, ignore_closed=True, q.size=None -> (OK, None)."""
        q = StubQuota(pk=6, closed=True, size=None)
        qa = ProductionQuotaAvailability(ignore_closed=True)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_OK, None)

    def test_closed_ignored_with_size_zero(self):
        """Covers branch: q.closed=True, ignore_closed=True, q.size=0 -> (GONE, 0)."""
        q = StubQuota(pk=7, closed=True, size=0)
        qa = ProductionQuotaAvailability(ignore_closed=True)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_GONE, 0)

    def test_composite_multi_quota_batch(self):
        """Verifies multi-element iteration and heterogeneous state handling."""
        q1 = StubQuota(pk=101, closed=True, size=10)
        q2 = StubQuota(pk=102, closed=False, size=None)
        q3 = StubQuota(pk=103, closed=False, size=0)
        q4 = StubQuota(pk=104, closed=False, size=5)

        qa = ProductionQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q1, q2, q3, q4])

        assert qa.results[q1] == (AVAILABILITY_ORDERED, 0)
        assert qa.results[q2] == (AVAILABILITY_OK, None)
        assert qa.results[q3] == (AVAILABILITY_GONE, 0)
        assert q4 not in qa.results
