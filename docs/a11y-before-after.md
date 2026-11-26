# Usability, Accessibility & Heuristic Evaluation (Before vs. After)

**Document Reference:** `docs/a11y-before-after.md`  
**Owner:** Shaiman (`24i-3074`, Member 3 — Area C)  
**Test Suite & Patch Script:** [`tests/team/a11y/`](file:///c:/Users/USER/Desktop/sqe_project/tests/team/a11y/), [`scripts/patch_a11y_container.py`](file:///c:/Users/USER/Desktop/sqe_project/scripts/patch_a11y_container.py), [`scripts/run_lighthouse_axe_audit.py`](file:///c:/Users/USER/Desktop/sqe_project/scripts/run_lighthouse_axe_audit.py)  
**Raw Evidence Artifacts:** [`lighthouse_before.html`](file:///c:/Users/USER/Desktop/sqe_project/reports/a11y/lighthouse_before.html), [`lighthouse_after.html`](file:///c:/Users/USER/Desktop/sqe_project/reports/a11y/lighthouse_after.html), [`lighthouse_storefront.html`](file:///c:/Users/USER/Desktop/sqe_project/reports/a11y/lighthouse_storefront.html), [`lighthouse_axe_unified_report.json`](file:///c:/Users/USER/Desktop/sqe_project/reports/a11y/lighthouse_axe_unified_report.json)

---

## 1. Deduplicated Accessibility Issue Register (Lighthouse + axe-core)

Findings from headless Chromium Google Lighthouse (`v13.6.0`) and Playwright `@axe-core` are consolidated so issues detected by multiple tools count strictly once:

| ID | Detecting Tools (Deduplicated) | Screen | Element / Defect | WCAG 2.1 AA Criterion | Severity | Status |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **`A11Y-ISSUE-01`** | axe-core (`html-has-lang`, `landmark-one-main`, `page-has-heading-one`, `region`, `image-alt`) + Lighthouse A11y/SEO | `/control/login` | Missing `lang="en"`, `<main>`, `<h1>`, `<meta name="description">`, and logo `alt` | **1.1.1, 1.3.1, 2.4.6, 3.1.1 (Level A/AA)** | **Critical** | **REMEDIATED** (0 axe violations; Lighthouse A11y `69 -> 100`) |
| **`A11Y-ISSUE-02`** | axe-core (`color-contrast`) + Lighthouse (`color-contrast`, `meta-description`) | `/sqe/sqe2026/` | `.text-muted` / `.help-block` low contrast (`3.2:1`), weak `:focus-visible`, missing meta description | **1.4.3 Contrast Minimum & 2.4.7 Focus Visible (AA)** | **High** | **REMEDIATED** (server-side `<style id="sqe-a11y-contrast-patch">`; 0 axe violations) |
| **`A11Y-ISSUE-03`** | Google Lighthouse | `/sqe/sqe2026/` (Mobile) | Item stepper buttons `<button class="btn btn-default input-item-count-dec">` (`< 44x44px`) | **2.5.5 Target Size (Best Practice)** | **Minor** | **DOCUMENTED_BEST_PRACTICE** |

---

## 2. Durable Server-Side Engineering Remediation (No Client Style Injection)

1. **Control Panel Auth Templates (`/pretix/src/pretix/control/templates/pretixcontrol/auth/base.html` & `login.html`):**
   - Added `lang="en"` on `<html>`, `<meta name="description">`, semantic `<header role="banner">` around `<img.logo alt="pretix official logo" role="img">`, `<main role="main" id="main-content">` wrapping page content, `<h1 class="sr-only">Log in</h1>`, and `<footer>` landmark.
2. **Storefront Presale Base Template (`/pretix/src/pretix/presale/templates/pretixpresale/base.html`):**
   - Embedded durable server-rendered `<style id="sqe-a11y-contrast-patch">` setting `.text-muted, .help-block { color: #4a4a4a !important; }` ($\ge 5.8:1$ contrast) and high-visibility `:focus-visible { outline: 3px solid #ff9900 !important; outline-offset: 2px !important; }`, plus `<meta name="description">`.
   - Removed all client-side `document.head.appendChild(style)` JS injection from `tests/team/a11y/test_a11y_remediation.py`; tests assert the server HTML delivers the fixes natively.

---

## 3. Empirical Before vs. After Verification (Extracted from Raw HTML & JSON)

| Audited Screen & State | Raw Artifact | Lighthouse Accessibility | Best Practices | SEO | Perf | axe-core Violations | axe-core Passes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Control Login — BEFORE** | `lighthouse_before.html` | **69 / 100** | 96 / 100 | 50 / 100 | — | **4 active rule groups** (`html-has-lang`, `landmark-one-main`, `page-has-heading-one`, `region`) + `image-alt` | — |
| **Control Login — AFTER** | `lighthouse_after.html` | **100 / 100 (+31 pts)** | **96 / 100** | **66 / 100 (+16 pts)** | **100 / 100** | **0 violations** (`axe_login_report.json`) | **33 rules passed** |
| **Event Storefront — AFTER** | `lighthouse_storefront.html` | **100 / 100** | **92 / 100** | **100 / 100** | **50 / 100** (cold throttling) | **0 violations** (`axe_storefront_report.json`) | **43 rules passed** |
| **Control Orders (Logged-In) — Audit** | `lighthouse_orders_logged_in.html` | **78 / 100** | **100 / 100** | **50 / 100** | **80 / 100** | **10 violations** (`axe_orders_report.json`) | **38 rules passed** |

*Note on Storefront Lighthouse Performance (`50/100`):* Headless Chromium CPU/network simulation on an uncached local development container reports `50/100` for mobile rendering, reported unmodified directly from `lighthouse_storefront.html`. All WCAG 2.1 AA accessibility (`100/100`), keyboard traversal (`01_keyboard_tab_focus.png`), and usability task recovery (`workflow_a_01/02`, `workflow_b_01`) tests pass `8/8`.
