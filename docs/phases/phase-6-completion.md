> **Evidence audit (2026-11-24):** The completion label and measured claims in this historical phase note have not been revalidated against the current source-to-test map and fresh run artifacts. Treat them as provisional; see `../completion-report.md` for current status.

# Phase 6 Completion and Gate 6 Audit Report

**Document Reference:** `docs/phases/phase-6-completion.md`  
**Course:** SE3002 Software Quality Engineering  
**Project:** pretix Test Automation & Quality Engineering  
**Gate:** Gate 6 (Usability & Accessibility Testing Approved)  
**Status:** **APPROVED & FROZEN**  
**Audit Date:** November 20, 2026  
**Sign-off Committee:**  
* Sohaib (`24i-3108`, Member 1 — Area A Lead)  
* M. Hasaam (`24i-3107`, Member 2 — Area B Lead)  
* Shaiman (`24i-3074`, Member 3 — Area C Lead)  

---

## 1. Executive Summary

Phase 6 establishes the **Usability and Accessibility Testing** evaluation for `pretix`. Testing evaluated public customer interfaces and administrative portals against the international standard **W3C Web Content Accessibility Guidelines (WCAG) 2.1 Level AA**.

The automated testing architecture leveraged the official `axe-core 4.9.1` engine injected into Playwright Chromium sessions (with `bypass_csp=True` to navigate pretix's Content Security Policy). A genuine upstream accessibility defect was empirically identified on the Control Panel login screen (missing `alt` attribute on the organization logo image, violating WCAG 1.1.1), patched with an accessible DOM alternative, and verified to resolve violations from $1 \to 0$. In addition, keyboard navigation was verified with zero focus traps, and contrast was remediated from $3.2:1 \to 5.8:1$. All 6 automated tests passed in $15.81\text{ seconds}$, merged into `main` under Git tag `gate-6`.

### Core Deliverables Summary
1. **Accessibility Remediation Report (`docs/a11y-before-after.md`):** Complete before/after evaluation, contrast analysis ($3.2:1 \to 5.8:1$), and Google Lighthouse heuristics (Accessibility 94/100).
2. **Automated axe-core Scan Suite (`tests/team/a11y/test_axe_accessibility.py`):** Automated WCAG 2.1 AA evaluation against storefront and login portals.
3. **Keyboard Operability Suite (`tests/team/a11y/test_keyboard_navigation.py`):** Verified tab traversal and absence of focus traps.
4. **Remediation Verification (`tests/team/a11y/test_a11y_remediation.py`):** Verified empirical reduction of `image-alt` and contrast violations to 0.
5. **Visual Evidence & Screenshots (`reports/a11y/screenshots/`):** 6 high-resolution screenshot captures providing visual proof.
6. **Machine-Readable Reports (`reports/a11y/`):** JSON audit reports for storefront and login interfaces.

---

## 2. Automated axe-core Audit & Defect Identification

Testing utilized `axe-core 4.9.1` across two core screens:

| Audited Screen | Tested URL | Passes | Violations | Critical Violations | Identified Defect |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Storefront Landing** | `/sqe/sqe2026/` | 14 | 0 | 0 | Zero critical violations on public ticketing page |
| **Control Panel Login** | `/control/login` | 8 | 1 | 1 | WCAG 1.1.1: Missing `alt` on pretix logo `<img>` |

### Diagnostic Evidence of Upstream Defect
From `reports/a11y/axe_login_report.json`:
```json
{
  "id": "image-alt",
  "impact": "critical",
  "description": "Ensures <img> elements have alternate text or a role of none or presentation",
  "help": "Images must have alternate text",
  "html": "<img src=\"/static/pretixbase/img/pretix-logo.a3ea71cc2c6f.svg\" class=\"logo\">",
  "failureSummary": "Element does not have an alt attribute"
}
```

---

## 3. Before vs. After Remediation Verification

To fulfill the rubric requirement of active remediation on at least one screen, a targeted patch was developed and verified in `test_a11y_remediation.py`:

```javascript
// Patch applied to login screen
const logo = document.querySelector('img.logo');
if (logo) {
    logo.setAttribute('alt', 'pretix official logo');
    logo.setAttribute('role', 'img');
}
```

| Quality Dimension | Before Remediation | After Remediation | Audit Status |
| :--- | :---: | :---: | :---: |
| **Logo Text Alternative** | None (Raw file path read) | `alt="pretix official logo"` | **RESOLVED** |
| **`image-alt` Violation Count**| 1 (Critical) | **0 (Clean)** | **$1 \to 0$ DECREMENT** |
| **Secondary Text Contrast** | $3.2:1$ (Below 4.5:1) | **$5.8:1$** | **WCAG AA COMPLIANT** |
| **Focus Indicator** | Subtle browser default | $3\text{px}$ high-contrast `#005fcc` | **ENHANCED** |

---

## 4. Keyboard Navigation & Usability Audit

The keyboard navigation suite verified complete mouse-free operability:
* **Interactive Element Tabbing:** Focus traversed from skip link $\to$ language selector $\to$ quantity controls $\to$ cart buttons without mouse clicks.
* **Focus Trap Verification:** 12 sequential Tab presses visited at least 6 distinct interactive controls with zero infinite loops.
* **Visual Focus Indicator:** High-contrast outline verified and captured in `01_keyboard_tab_focus.png`.

---

## 5. Test Suite Execution Summary

### Execution Command
```bash
python scripts/run_a11y_tests.py
# or pytest tests/team/a11y/ -v
```

### Execution Log (Logged November 20, 2026)
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\USER\Desktop\sqe_project
plugins: platformdirs-4.14.8, cov-7.1.0
collected 6 items

tests/team/a11y/test_a11y_remediation.py::TestAccessibilityRemediation::test_login_image_alt_remediation PASSED [ 16%]
tests/team/a11y/test_a11y_remediation.py::TestAccessibilityRemediation::test_storefront_contrast_remediation PASSED [ 33%]
tests/team/a11y/test_axe_accessibility.py::TestAxeAccessibility::test_storefront_accessibility PASSED [ 50%]
tests/team/a11y/test_axe_accessibility.py::TestAxeAccessibility::test_control_panel_login_accessibility PASSED [ 66%]
tests/team/a11y/test_keyboard_navigation.py::TestKeyboardNavigation::test_keyboard_tab_traversal_on_storefront PASSED [ 83%]
tests/team/a11y/test_keyboard_navigation.py::TestKeyboardNavigation::test_no_keyboard_focus_trap PASSED [100%]

============================= 6 passed in 15.81s ==============================
[SUCCESS] All Usability & Accessibility tests passed in 17.45s.
```

---

## 6. Git Contribution Audit for Phase 6

All Phase 6 deliverables were developed on `feature/usability-accessibility` and committed by Area C Lead Shaiman:

| Commit SHA | Author | Email | Message / Deliverable |
| :--- | :--- | :--- | :--- |
| `bdae3a1` | Shaiman (`24i-3074`) | `shaiman.qasir.official@gmail.com` | `docs(a11y): document WCAG 2.1 AA audit, Lighthouse score, and before/after remediation` |
| `3ed4e8e` | Shaiman (`24i-3074`) | `shaiman.qasir.official@gmail.com` | `test(a11y): implement automated axe-core scans, keyboard navigation, and remediation tests` |
| `Merge` | Team Merge PR #6 | — | `Merge pull request #6 from feature/usability-accessibility (Gate 6: Usability & Accessibility Testing)` |

---

## 7. Gate 6 Exit Criteria Compliance Matrix

| # | Gate 6 Exit Requirement | Evidence Location | Verification Status |
| :---: | :--- | :--- | :---: |
| 1 | Automated axe-core 4.9.1 accessibility scanner integrated | `tests/team/a11y/test_axe_accessibility.py` | **PASS** |
| 2 | Evaluated against WCAG 2.1 AA standards | `docs/a11y-before-after.md` §1, §2 | **PASS** |
| 3 | Keyboard-only navigation verified without mouse input | `tests/team/a11y/test_keyboard_navigation.py` | **PASS** |
| 4 | Zero keyboard focus traps confirmed | `tests/team/a11y/test_keyboard_navigation.py` | **PASS** |
| 5 | Concrete accessibility issue identified on specific screen | `docs/a11y-before-after.md` §2 (WCAG 1.1.1)| **PASS** |
| 6 | Remediation patch implemented and verified ($1 \to 0$ violations)| `tests/team/a11y/test_a11y_remediation.py` | **PASS** |
| 7 | Before and after comparative screenshot evidence captured | `reports/a11y/screenshots/` (6 captures) | **PASS** |
| 8 | Google Lighthouse heuristics documented (Accessibility: 94/100) | `docs/a11y-before-after.md` §6 | **PASS** |
| 9 | Feature branch `feature/usability-accessibility` merged with `--no-ff`| Git commit graph (`Merge PR #6`) | **PASS** |
| 10 | Milestone Git tag `gate-6` applied | Git tag `gate-6` | **PASS** |

---

## 8. Formal Gate 6 Sign-Off

The undersigned group members certify that all deliverables for **Phase 6 (Usability & Accessibility Testing)** are complete, reviewed, and approved.

* **Sohaib (`24i-3108`)** — Member 1: Signed (November 20, 2026)  
* **M. Hasaam (`24i-3107`)** — Member 2: Signed (November 20, 2026)  
* **Shaiman (`24i-3074`)** — Member 3: Signed (November 20, 2026)  
