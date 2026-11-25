"""MCC and MC/DC checks against pretix's production closed-quota decision (BR2)."""
import pytest

from upstream.pretix.base.scoped_business_logic import Quota, QuotaAvailabilityPolicy

AVAILABILITY_ORDERED = Quota.AVAILABILITY_ORDERED


class StubQuota:
    def __init__(self, closed, size=10):
        self.closed = closed
        self.size = size


def run_production_decision(closed, ignore_closed):
    """Execute upstream QuotaAvailability._compute_early_outs with stubbed state."""
    subject = QuotaAvailabilityPolicy()
    subject.results = {}
    subject._ignore_closed = ignore_closed
    subject._compute_early_outs([StubQuota(closed=closed, size=10)])
    return subject.results


# BR2 compound condition: q.closed AND NOT self._ignore_closed
MCC_ROWS = [
    ("TC-MCC-01", True, False, True),
    ("TC-MCC-02", True, True, False),
    ("TC-MCC-03", False, False, False),
    ("TC-MCC-04", False, True, False),
]


@pytest.mark.parametrize("test_id,closed,ignore_closed,blocked", MCC_ROWS)
def test_br2_mcc_closed_quota_policy(test_id, closed, ignore_closed, blocked):
    results = run_production_decision(closed, ignore_closed)
    if blocked:
        assert len(results) == 1
        assert next(iter(results.values())) == (AVAILABILITY_ORDERED, 0)
    else:
        assert results == {}


def test_br2_mcdc_closed_flag_independently_changes_production_result():
    blocked = run_production_decision(closed=True, ignore_closed=False)
    not_closed = run_production_decision(closed=False, ignore_closed=False)
    assert next(iter(blocked.values())) == (AVAILABILITY_ORDERED, 0)
    assert not_closed == {}


def test_br2_mcdc_ignore_closed_independently_changes_production_result():
    blocked = run_production_decision(closed=True, ignore_closed=False)
    ignored = run_production_decision(closed=True, ignore_closed=True)
    assert next(iter(blocked.values())) == (AVAILABILITY_ORDERED, 0)
    assert ignored == {}
