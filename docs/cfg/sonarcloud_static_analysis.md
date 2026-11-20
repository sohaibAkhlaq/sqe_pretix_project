# SonarCloud & Static Code Analysis Report

**Document Reference:** `docs/cfg/sonarcloud_static_analysis.md`  
**Course:** SE3002 Software Quality Engineering  
**Application Under Test:** pretix (`upstream/pretix/base/services/`)  
**Lead Contributor / Author:** Sohaib (`24i-3108`, Member 1 — Area A Lead)  
**Reviewers:** M. Hasaam (`24i-3107`), Shaiman (`24i-3074`)  
**Status:** Approved & Frozen Baseline (Gate 3 Deliverable)  
**Date:** November 20, 2026  

---

## 1. Static Analysis Architecture & Tools

Static analysis was performed using three complementary tools:
1. **Radon 6.0.1:** Cyclomatic Complexity Numbers (CCN), Halstead metrics, and Maintainability Index (MI).
2. **Lizard 1.26.1:** Multidimensional complexity metrics (NLOC, CCN, Token count, parameter count).
3. **SonarCloud Platform Configuration:** Automated static quality gate configured via `sonar-project.properties` for pull request scanning.

---

## 2. Quantitative Complexity Metrics Summary

### 2.1. Scoped Module Metrics Summary

| Source Module | Physical LOC | Logical LOC (NLOC) | Functions Analyzed | Average CCN | High Risk Blocks (CCN > 15) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `pretix.base.services.quotas` | 507 | 359 | 12 | **13.2** | 6 |
| `pretix.base.services.orders` | 3,750 | 2,820 | 58 | **24.1** | 18 |

### 2.2. Selected White-Box Target Functions

| Function Name | Parent Class / File | Line # | NLOC | Radon CCN | Lizard CCN | Complexity Rank |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `_compute_early_outs` | `QuotaAvailability` (`quotas.py`) | 493 | 8 | **6** | **6** | Rank B (Low Risk) |
| `_check_quotas` | `OrderChangeManager` (`orders.py`) | 2285 | 10 | **8** | **8** | Rank B (Low Risk) |

Both selected functions fall precisely within the required range of 6 to 10 decision paths mandated by the SE3002 specification.

---

## 3. Maintainability Index (MI) & Technical Debt

Using Radon's Maintainability Index formula ($MI = 171 - 5.2 \ln(V) - 0.23(G) - 16.2 \ln(L) + 50 \sin(\sqrt{2.4 C})$):

* **`quotas.py` Maintainability Index:** **58.4 (Rank B)** — Moderate maintainability; modular caching logic.
* **`orders.py` Maintainability Index:** **42.1 (Rank B/C)** — High transactional coupling due to multi-step order approval and cancellation pipelines.

---

## 4. SonarCloud Configuration & CI Integration

The SonarCloud project configuration is frozen in `sonar-project.properties`:

```ini
sonar.projectKey=sqe-pretix-team
sonar.organization=sqe-fall-2026
sonar.projectName=pretix-sqe-testing
sonar.projectVersion=1.0.0

sonar.sources=upstream/pretix/base/services
sonar.tests=tests/team
sonar.python.coverage.reportPaths=reports/coverage/coverage.xml
sonar.sourceEncoding=UTF-8
sonar.exclusions=**/migrations/**, **/static/**, **/__pycache__/**
```

### SonarCloud PR Quality Gate Rules:
1. Zero new Blocker or Critical code smells.
2. Zero new Security Vulnerabilities.
3. Code Coverage on New Code $\ge 80\%$.
4. Duplicated Lines on New Code $< 3\%$.
