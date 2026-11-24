# MCC and MC/DC: Closed-Quota Decision

**Requirement:** BR2 in `docs/test-basis.md`
**Production target:** `upstream/pretix/base/services/quotas.py`, `QuotaAvailability._compute_early_outs`
**Automated checks:** `tests/team/unit/test_mcc_mcdc_quota_policy.py`
**Status:** Corrected source target; execution/coverage not rerun in this pass.

The production decision is `q.closed and not self._ignore_closed`. Let `C1 = q.closed` and `C2 = not self._ignore_closed`. When true, the method stores `(Quota.AVAILABILITY_ORDERED, 0)`. For false outcomes, the tests use a positive-size quota so no early-out entry is created.

## Complete MCC table

| Test ID | C1 closed | C2 not ignored | Decision | Expected production result |
|---|---:|---:|---:|---|
| TC-MCC-01 | True | True | True | `(AVAILABILITY_ORDERED, 0)` stored |
| TC-MCC-02 | True | False | False | No early-out result stored |
| TC-MCC-03 | False | True | False | No early-out result stored |
| TC-MCC-04 | False | False | False | No early-out result stored |

## MC/DC pairs

| Condition toggled | True case | False case | Held fixed | Decision changes |
|---|---|---|---|---|
| C1 (`q.closed`) | TC-MCC-01 | TC-MCC-03 | C2 = True | True to False |
| C2 (`not _ignore_closed`) | TC-MCC-01 | TC-MCC-02 | C1 = True | True to False |

Three unique cases (TC-MCC-01/02/03) establish both independent effects; TC-MCC-04 completes MCC.

## Scope boundary

`tests/team/unit/production_source.py` compiles the method body from the checked-in upstream source and stubs its collaborators. This evidence covers this one early-out decision only. It does not establish item purchasability, the full quota service, BR3 transitions, BR4 late payment, nor full Django integration. The historical four-condition/16-row write-up was invalid and is withdrawn. Coverage claims require fresh reports naming the measured production scope. See `docs/completion-report.md`.
