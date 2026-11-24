"""
White-Box Unit Tests for QuotaAvailability._compute_early_outs (CCN = 6).
Verifies 100% Statement and 100% Branch Coverage across all 6 basis paths.
"""
import pytest
from types import MethodType

from production_source import load_upstream_method

# Constants aligned with pretix.base.models.Quota
AVAILABILITY_OK = 100
AVAILABILITY_GONE = 20
AVAILABILITY_ORDERED = 0

class MockQuota:
    def __init__(self, pk=1, name="General Admission", size=10, closed=False):
        self.pk = pk
        self.name = name
        self.size = size
        self.closed = closed

    def __repr__(self):
        return f"<MockQuota pk={self.pk} size={self.size} closed={self.closed}>"

class MockQuotaAvailability:
    def __init__(self, ignore_closed=False):
        self.results = {}
        self._ignore_closed = ignore_closed
        method = load_upstream_method(
            "base/services/quotas.py",
            "QuotaAvailability",
            "_compute_early_outs",
            {"Quota": type("QuotaConstants", (), {
                "AVAILABILITY_OK": AVAILABILITY_OK,
                "AVAILABILITY_GONE": AVAILABILITY_GONE,
                "AVAILABILITY_ORDERED": AVAILABILITY_ORDERED,
            })},
        )
        self._compute_early_outs = MethodType(method, self)


class TestQuotaEarlyOutsWhiteBox:
    """Covers all 6 Basis Paths of QuotaAvailability._compute_early_outs"""

    def test_path_1_empty_quotas(self):
        """Basis Path 1: Empty input list. Loop does not execute."""
        qa = MockQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([])
        assert qa.results == {}, "Expected empty results for empty quota list"
        assert "<MockQuota" in repr(MockQuota(1, "Test", 5))

    def test_path_2_closed_quota_not_ignored(self):
        """Basis Path 2: Closed quota with ignore_closed=False -> (ORDERED, 0)."""
        q = MockQuota(pk=1, closed=True, size=10)
        qa = MockQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert q in qa.results
        assert qa.results[q] == (AVAILABILITY_ORDERED, 0)

    def test_path_3_closed_quota_ignored_and_size_positive(self):
        """Basis Path 3: Closed quota with ignore_closed=True, size > 0 -> Fallthrough (not in results)."""
        q = MockQuota(pk=2, closed=True, size=10)
        qa = MockQuotaAvailability(ignore_closed=True)
        qa._compute_early_outs([q])
        assert q not in qa.results, "Quota with positive size should not receive early-out result"

    def test_path_4_unlimited_quota(self):
        """Basis Path 4: Open quota with size=None (unlimited) -> (OK, None)."""
        q = MockQuota(pk=3, closed=False, size=None)
        qa = MockQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert q in qa.results
        assert qa.results[q] == (AVAILABILITY_OK, None)

    def test_path_5_depleted_quota_size_zero(self):
        """Basis Path 5: Open quota with size=0 -> (GONE, 0)."""
        q = MockQuota(pk=4, closed=False, size=0)
        qa = MockQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert q in qa.results
        assert qa.results[q] == (AVAILABILITY_GONE, 0)

    def test_path_6_normal_positive_quota_fallthrough(self):
        """Basis Path 6: Open quota with size > 0 (e.g. 10) -> Fallthrough (no early-out)."""
        q = MockQuota(pk=5, closed=False, size=10)
        qa = MockQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q])
        assert q not in qa.results, "Normal quota must pass through to detailed computation"

    def test_closed_ignored_with_size_none(self):
        """Covers branch: q.closed=True, ignore_closed=True, q.size=None -> (OK, None)."""
        q = MockQuota(pk=6, closed=True, size=None)
        qa = MockQuotaAvailability(ignore_closed=True)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_OK, None)

    def test_closed_ignored_with_size_zero(self):
        """Covers branch: q.closed=True, ignore_closed=True, q.size=0 -> (GONE, 0)."""
        q = MockQuota(pk=7, closed=True, size=0)
        qa = MockQuotaAvailability(ignore_closed=True)
        qa._compute_early_outs([q])
        assert qa.results[q] == (AVAILABILITY_GONE, 0)

    def test_composite_multi_quota_batch(self):
        """Verifies multi-element iteration and heterogeneous state handling."""
        q1 = MockQuota(pk=101, closed=True, size=10)    # -> (ORDERED, 0)
        q2 = MockQuota(pk=102, closed=False, size=None) # -> (OK, None)
        q3 = MockQuota(pk=103, closed=False, size=0)    # -> (GONE, 0)
        q4 = MockQuota(pk=104, closed=False, size=5)    # -> Fallthrough (not in results)

        qa = MockQuotaAvailability(ignore_closed=False)
        qa._compute_early_outs([q1, q2, q3, q4])

        assert qa.results[q1] == (AVAILABILITY_ORDERED, 0)
        assert qa.results[q2] == (AVAILABILITY_OK, None)
        assert qa.results[q3] == (AVAILABILITY_GONE, 0)
        assert q4 not in qa.results
