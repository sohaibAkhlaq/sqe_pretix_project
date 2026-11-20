# Control Flow Graph (CFG) & Cyclomatic Complexity Analysis

**Document Reference:** `docs/cfg/cfg_analysis.md`  
**Course:** SE3002 Software Quality Engineering  
**Application Under Test:** pretix (`upstream/pretix/base/services/`)  
**Lead Contributor / Author:** Sohaib (`24i-3108`, Member 1 — Area A Lead)  
**Reviewers:** M. Hasaam (`24i-3107`), Shaiman (`24i-3074`)  
**Status:** Approved & Frozen (Gate 3 Deliverable)  
**Date:** November 20, 2026  

---

## 1. Executive Summary & Selection Criteria

In accordance with course guidelines for White-Box Testing, candidate functions were analyzed across `pretix.base.services.quotas` and `pretix.base.services.orders` using `radon cc` and `lizard`. Two functions exhibiting between 6 and 10 decision paths were selected:

1. **Function 1:** `QuotaAvailability._compute_early_outs`
   - *Module:* `pretix/base/services/quotas.py` (Lines 493–500)
   - *Lines of Code (NLOC):* 8
   - *McCabe's Cyclomatic Complexity (CCN):* **6** (Rank B)
   - *Role in Workflows:* Evaluates quota boundaries (closed, unlimited, or exhausted) for fast-path availability assignment.
2. **Function 2:** `OrderChangeManager._check_quotas`
   - *Module:* `pretix/base/services/orders.py` (Lines 2285–2294)
   - *Lines of Code (NLOC):* 10
   - *McCabe's Cyclomatic Complexity (CCN):* **8** (Rank B)
   - *Role in Workflows:* Validates inventory headroom during order item alterations and position updates.

---

## 2. Function 1: `QuotaAvailability._compute_early_outs` (CCN = 6)

### 2.1. Python Source Code
```python
493:    def _compute_early_outs(self, quotas):
494:        for q in quotas:
495:            if q.closed and not self._ignore_closed:
496:                self.results[q] = Quota.AVAILABILITY_ORDERED, 0
497:            elif q.size is None:
498:                self.results[q] = Quota.AVAILABILITY_OK, None
499:            elif q.size == 0:
500:                self.results[q] = Quota.AVAILABILITY_GONE, 0
```

### 2.2. Control Flow Graph (CFG)

```mermaid
flowchart TD
    N1(["N1: Entry: _compute_early_outs(quotas)"]) --> N2{"N2: for q in quotas (Next?)"}
    
    N2 -- "No (Loop Exhausted)" --> N11(["N11: Exit / Return"])
    N2 -- "Yes (Current q)" --> N3{"N3: q.closed?"}
    
    N3 -- "True" --> N4{"N4: not self._ignore_closed?"}
    N3 -- "False" --> N6{"N6: q.size is None?"}
    
    N4 -- "True" --> N5["N5: results[q] = (ORDERED, 0)"]
    N4 -- "False" --> N6
    
    N5 --> N2
    
    N6 -- "True" --> N7["N7: results[q] = (OK, None)"]
    N6 -- "False" --> N8{"N8: q.size == 0?"}
    
    N7 --> N2
    
    N8 -- "True" --> N9["N9: results[q] = (GONE, 0)"]
    N8 -- "False (size > 0)" --> N10["N10: Fallthrough (No Early Out)"]
    
    N9 --> N2
    N10 --> N2
```

### 2.3. Graph Properties
* **Node Inventory ($N = 11$):**
  - $N_1$: Function Entry
  - $N_2$: Loop iterator check (`for q in quotas`)
  - $N_3$: Predicate: `q.closed`
  - $N_4$: Predicate: `not self._ignore_closed`
  - $N_5$: Statement: `results[q] = Quota.AVAILABILITY_ORDERED, 0`
  - $N_6$: Predicate: `q.size is None`
  - $N_7$: Statement: `results[q] = Quota.AVAILABILITY_OK, None`
  - $N_8$: Predicate: `q.size == 0`
  - $N_9$: Statement: `results[q] = Quota.AVAILABILITY_GONE, 0`
  - $N_{10}$: Fallthrough branch (normal quota requiring deep calculation)
  - $N_{11}$: Function Exit
* **Edge Inventory ($E = 15$):**
  1. $e_1 = (N_1, N_2)$
  2. $e_2 = (N_2, N_{11})$
  3. $e_3 = (N_2, N_3)$
  4. $e_4 = (N_3, N_4)$
  5. $e_5 = (N_3, N_6)$
  6. $e_6 = (N_4, N_5)$
  7. $e_7 = (N_4, N_6)$
  8. $e_8 = (N_5, N_2)$
  9. $e_9 = (N_6, N_7)$
  10. $e_{10} = (N_6, N_8)$
  11. $e_{11} = (N_7, N_2)$
  12. $e_{12} = (N_8, N_9)$
  13. $e_{13} = (N_8, N_{10})$
  14. $e_{14} = (N_9, N_2)$
  15. $e_{15} = (N_{10}, N_2)$
* **Predicate Nodes ($P = 5$):** $\{N_2, N_3, N_4, N_6, N_8\}$
* **Connected Components ($C = 1$):** Single procedure graph.

### 2.4. Hand Calculation of McCabe's Cyclomatic Complexity

#### Formula 1 (Edges and Nodes):
$$V(G) = E - N + 2C = 15 - 11 + 2(1) = 4 + 2 = \mathbf{6}$$

#### Formula 2 (Predicate Nodes):
$$V(G) = P + 1 = 5 + 1 = \mathbf{6}$$

#### Formula 3 (Planar Bounded Regions):
Planar analysis reveals 5 enclosed regions:
* $R_1$: Enclosed by $N_2 \to N_3 \to N_4 \to N_5 \to N_2$
* $R_2$: Enclosed by $N_3 \to N_4 \to N_6 \to \dots$
* $R_3$: Enclosed by $N_6 \to N_7 \to N_2 \to \dots$
* $R_4$: Enclosed by $N_8 \to N_9 \to N_2 \to \dots$
* $R_5$: Enclosed by $N_8 \to N_{10} \to N_2 \to \dots$
* $R_6$: Unbounded external region.
$$V(G) = R_{\text{enclosed}} + 1 = 5 + 1 = \mathbf{6}$$

**Verification:** All three independent mathematical methods yield $V(G) = 6$, confirming tool metrics from Radon and Lizard.

### 2.5. Linearly Independent Basis Paths
1. **Path 1 (Empty Quotas):** $N_1 \to N_2 \to N_{11}$
2. **Path 2 (Closed Quota):** $N_1 \to N_2 \to N_3 \to N_4 \to N_5 \to N_2 \to N_{11}$
3. **Path 3 (Closed but Ignored):** $N_1 \to N_2 \to N_3 \to N_4 \to N_6 \to N_8 \to N_{10} \to N_2 \to N_{11}$
4. **Path 4 (Unlimited Quota):** $N_1 \to N_2 \to N_3 \to N_6 \to N_7 \to N_2 \to N_{11}$
5. **Path 5 (Depleted Quota, Size 0):** $N_1 \to N_2 \to N_3 \to N_6 \to N_8 \to N_9 \to N_2 \to N_{11}$
6. **Path 6 (Normal Quota, Size > 0):** $N_1 \to N_2 \to N_3 \to N_6 \to N_8 \to N_{10} \to N_2 \to N_{11}$

---

## 3. Function 2: `OrderChangeManager._check_quotas` (CCN = 8)

### 3.1. Python Source Code
```python
2285:    def _check_quotas(self):
2286:        qa = QuotaAvailability()
2287:        qa.queue(*[k for k, v in self._quotadiff.items() if v > 0])
2288:        qa.compute()
2289:        for quota, diff in self._quotadiff.items():
2290:            if diff <= 0:
2291:                continue
2292:            avail = qa.results[quota]
2293:            if avail[0] != Quota.AVAILABILITY_OK or (avail[1] is not None and avail[1] < diff):
2294:                raise OrderError(self.error_messages['quota'].format(name=quota.name))
```

### 3.2. Control Flow Graph (CFG)

```mermaid
flowchart TD
    M1(["M1: Entry: _check_quotas()"]) --> M2["M2: qa = QuotaAvailability()"]
    M2 --> M3{"M3: Generator filter (v > 0)?"}
    M3 -- "True" --> M4["M4: Add k to queue"]
    M3 -- "False" --> M5{"M5: More items in diff?"}
    M4 --> M5
    M5 -- "Yes" --> M3
    M5 -- "No" --> M6["M6: qa.compute()"]
    
    M6 --> M7{"M7: for quota, diff in _quotadiff (Next?)"}
    M7 -- "No (Loop Complete)" --> M14(["M14: Exit / Return Normal"])
    M7 -- "Yes" --> M8{"M8: diff <= 0?"}
    
    M8 -- "True (Continue)" --> M7
    M8 -- "False (diff > 0)" --> M9["M9: avail = qa.results[quota]"]
    
    M9 --> M10{"M10: avail[0] != AVAILABILITY_OK?"}
    M10 -- "True" --> M13["M13: raise OrderError()"]
    M10 -- "False" --> M11{"M11: avail[1] is not None?"}
    
    M11 -- "False (Unlimited)" --> M7
    M11 -- "True" --> M12{"M12: avail[1] < diff?"}
    
    M12 -- "True (Over capacity)" --> M13
    M12 -- "False (Available >= diff)" --> M7
```

### 3.3. Graph Properties
* **Node Inventory ($N = 14$):**
  - $M_1$: Entry
  - $M_2$: Instantiate `QuotaAvailability`
  - $M_3$: Predicate: Generator filter `v > 0`
  - $M_4$: Generator yield/append
  - $M_5$: Predicate: Generator iteration check
  - $M_6$: Statement: `qa.compute()`
  - $M_7$: Predicate: Loop iterator check `for quota, diff`
  - $M_8$: Predicate: `diff <= 0`
  - $M_9$: Statement: `avail = qa.results[quota]`
  - $M_{10}$: Predicate: `avail[0] != Quota.AVAILABILITY_OK`
  - $M_{11}$: Predicate: `avail[1] is not None`
  - $M_{12}$: Predicate: `avail[1] < diff`
  - $M_{13}$: Statement: `raise OrderError`
  - $M_{14}$: Exit / Return
* **Edge Inventory ($E = 19$):**
  - $(M_1, M_2)$, $(M_2, M_5)$, $(M_5, M_3)$, $(M_3, M_4)$, $(M_3, M_5)$, $(M_4, M_5)$, $(M_5, M_6)$,
  - $(M_6, M_7)$, $(M_7, M_{14})$, $(M_7, M_8)$, $(M_8, M_7)$, $(M_8, M_9)$,
  - $(M_9, M_{10})$, $(M_{10}, M_{13})$, $(M_{10}, M_{11})$, $(M_{11}, M_7)$, $(M_{11}, M_{12})$,
  - $(M_{12}, M_{13})$, $(M_{12}, M_7)$.
* **Predicate Nodes ($P = 7$):** $\{M_3, M_5, M_7, M_8, M_{10}, M_{11}, M_{12}\}$
* **Connected Components ($C = 1$):** Single procedure graph.

### 3.4. Hand Calculation of McCabe's Cyclomatic Complexity

#### Formula 1 (Edges and Nodes):
$$V(G) = E - N + 2C = 19 - 14 + 2(1) = 5 + 2 = \mathbf{8}$$

#### Formula 2 (Predicate Nodes):
$$V(G) = P + 1 = 7 + 1 = \mathbf{8}$$

#### Formula 3 (Planar Bounded Regions):
Planar analysis identifies 7 enclosed regions plus 1 unbounded outer region:
$$V(G) = R_{\text{enclosed}} + 1 = 7 + 1 = \mathbf{8}$$

**Verification:** All three mathematical approaches yield $V(G) = 8$, in exact concordance with Radon.

### 3.5. Linearly Independent Basis Paths
1. **Path 1 (Empty Diff):** $M_1 \to M_2 \to M_5 \to M_6 \to M_7 \to M_{14}$
2. **Path 2 (Generator with $v \le 0$):** $M_1 \to M_2 \to M_5 \to M_3 \to M_5 \to M_6 \to M_7 \to M_{14}$
3. **Path 3 (Generator with $v > 0$):** $M_1 \to M_2 \to M_5 \to M_3 \to M_4 \to M_5 \to M_6 \to M_7 \to M_{14}$
4. **Path 4 (Loop with diff $\le 0$):** $M_6 \to M_7 \to M_8 \to M_7 \to M_{14}$
5. **Path 5 (Quota Sold Out / Ordered):** $M_6 \to M_7 \to M_8 \to M_9 \to M_{10} \to M_{13}$
6. **Path 6 (Quota Unlimited, `avail[1] is None`):** $M_6 \to M_7 \to M_8 \to M_9 \to M_{10} \to M_{11} \to M_7 \to M_{14}$
7. **Path 7 (Finite Quota Over-Demanded, `avail[1] < diff`):** $M_6 \to M_7 \to M_8 \to M_9 \to M_{10} \to M_{11} \to M_{12} \to M_{13}$
8. **Path 8 (Finite Quota Sufficient, `avail[1] >= diff`):** $M_6 \to M_7 \to M_8 \to M_9 \to M_{10} \to M_{11} \to M_{12} \to M_7 \to M_{14}$
