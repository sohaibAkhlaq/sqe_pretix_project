"""
Multiple Condition Coverage (MCC) & MC/DC Automated Verification Suite.
Targets Business Rule 2 (BR2): Multi-Condition Item Purchasability.
Formula: D = C1 and C2 and C3 and C4
"""
import pytest

def evaluate_purchasability(event_live: bool, item_active: bool, quota_avail: int, date_valid: bool) -> bool:
    """
    Evaluates Business Rule 2 (BR2) purchasability decision logic:
    C1: event_live
    C2: item_active
    C3: quota_avail > 0
    C4: date_valid
    """
    c1 = bool(event_live)
    c2 = bool(item_active)
    c3 = bool(quota_avail > 0)
    c4 = bool(date_valid)
    return bool(c1 and c2 and c3 and c4)


# -----------------------------------------------------------------------------
# Part 1: Complete Multiple Condition Coverage (MCC) - All 16 Truth Table Rows
# -----------------------------------------------------------------------------
MCC_TRUTH_TABLE = [
    # (Test ID, C1, C2, C3, C4, Expected Decision D)
    ("TC-MCC-01", True,  True,  10, True,  True),
    ("TC-MCC-02", True,  True,  10, False, False),
    ("TC-MCC-03", True,  True,  0,  True,  False),
    ("TC-MCC-04", True,  True,  0,  False, False),
    ("TC-MCC-05", True,  False, 10, True,  False),
    ("TC-MCC-06", True,  False, 10, False, False),
    ("TC-MCC-07", True,  False, 0,  True,  False),
    ("TC-MCC-08", True,  False, 0,  False, False),
    ("TC-MCC-09", False, True,  10, True,  False),
    ("TC-MCC-10", False, True,  10, False, False),
    ("TC-MCC-11", False, True,  0,  True,  False),
    ("TC-MCC-12", False, True,  0,  False, False),
    ("TC-MCC-13", False, False, 10, True,  False),
    ("TC-MCC-14", False, False, 10, False, False),
    ("TC-MCC-15", False, False, 0,  True,  False),
    ("TC-MCC-16", False, False, 0,  False, False),
]

class TestPurchasabilityMCC:
    """Parametric execution of all 16 MCC combinations (2^4)."""

    @pytest.mark.parametrize("test_id,c1,c2,c3_qty,c4,expected_decision", MCC_TRUTH_TABLE)
    def test_mcc_row(self, test_id, c1, c2, c3_qty, c4, expected_decision):
        actual_decision = evaluate_purchasability(c1, c2, c3_qty, c4)
        assert actual_decision == expected_decision, (
            f"MCC Row {test_id} failed! Conditions: (C1={c1}, C2={c2}, C3_qty={c3_qty}, C4={c4}). "
            f"Expected {expected_decision}, got {actual_decision}."
        )


# -----------------------------------------------------------------------------
# Part 2: Modified Condition/Decision Coverage (MC/DC) Independence Verification
# -----------------------------------------------------------------------------
class TestPurchasabilityMCDC:
    """Verifies orthogonal condition independence using minimal 5-test set (4 pairs)."""

    def test_mcdc_pair_c1_event_live(self):
        """
        Tests independence of C1 (event_live):
        Pair: TC-MCC-01 (T, T, T, T -> True) vs TC-MCC-09 (F, T, T, T -> False)
        Fixed: C2=True, C3=True, C4=True.
        """
        c2, c3_qty, c4 = True, 10, True

        # Test A: C1 = True
        decision_true = evaluate_purchasability(event_live=True, item_active=c2, quota_avail=c3_qty, date_valid=c4)
        assert decision_true is True, "TC-MCC-01 must evaluate to True"

        # Test B: C1 = False
        decision_false = evaluate_purchasability(event_live=False, item_active=c2, quota_avail=c3_qty, date_valid=c4)
        assert decision_false is False, "TC-MCC-09 must evaluate to False"

        # Proof of independent influence
        assert decision_true != decision_false, "C1 must independently toggle decision outcome"

    def test_mcdc_pair_c2_item_active(self):
        """
        Tests independence of C2 (item_active):
        Pair: TC-MCC-01 (T, T, T, T -> True) vs TC-MCC-05 (T, F, T, T -> False)
        Fixed: C1=True, C3=True, C4=True.
        """
        c1, c3_qty, c4 = True, 10, True

        # Test A: C2 = True
        decision_true = evaluate_purchasability(event_live=c1, item_active=True, quota_avail=c3_qty, date_valid=c4)
        assert decision_true is True, "TC-MCC-01 must evaluate to True"

        # Test B: C2 = False
        decision_false = evaluate_purchasability(event_live=c1, item_active=False, quota_avail=c3_qty, date_valid=c4)
        assert decision_false is False, "TC-MCC-05 must evaluate to False"

        assert decision_true != decision_false, "C2 must independently toggle decision outcome"

    def test_mcdc_pair_c3_quota_headroom(self):
        """
        Tests independence of C3 (quota_available > 0):
        Pair: TC-MCC-01 (T, T, T, T -> True) vs TC-MCC-03 (T, T, F, T -> False)
        Fixed: C1=True, C2=True, C4=True.
        """
        c1, c2, c4 = True, True, True

        # Test A: C3 = True (qty = 10 > 0)
        decision_true = evaluate_purchasability(event_live=c1, item_active=c2, quota_avail=10, date_valid=c4)
        assert decision_true is True, "TC-MCC-01 must evaluate to True"

        # Test B: C3 = False (qty = 0 <= 0)
        decision_false = evaluate_purchasability(event_live=c1, item_active=c2, quota_avail=0, date_valid=c4)
        assert decision_false is False, "TC-MCC-03 must evaluate to False"

        assert decision_true != decision_false, "C3 must independently toggle decision outcome"

    def test_mcdc_pair_c4_date_valid(self):
        """
        Tests independence of C4 (date_valid):
        Pair: TC-MCC-01 (T, T, T, T -> True) vs TC-MCC-02 (T, T, T, F -> False)
        Fixed: C1=True, C2=True, C3=True.
        """
        c1, c2, c3_qty = True, True, 10

        # Test A: C4 = True
        decision_true = evaluate_purchasability(event_live=c1, item_active=c2, quota_avail=c3_qty, date_valid=True)
        assert decision_true is True, "TC-MCC-01 must evaluate to True"

        # Test B: C4 = False
        decision_false = evaluate_purchasability(event_live=c1, item_active=c2, quota_avail=c3_qty, date_valid=False)
        assert decision_false is False, "TC-MCC-02 must evaluate to False"

        assert decision_true != decision_false, "C4 must independently toggle decision outcome"
