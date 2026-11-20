# Upstream System Baseline & Environment Specification

## 1. Upstream Repository Reference
* **System Name:** pretix
* **Application Type:** Open-Source Web-Based Management Information System (Ticketing, Shop, & Order Management)
* **Upstream Repository URL:** [https://github.com/pretix/pretix](https://github.com/pretix/pretix)
* **Target Version / Tag:** `pretix/standalone:stable` (pinned against stable release)
* **Baseline Git Tag:** `v0.1-baseline`
* **Licence:** GNU Affero General Public License v3.0 (AGPL-3.0) with additional terms (fully documented in `LICENSE`)

## 2. Core Workflows & Target Scope
* **Selected Module:** Order and Quota Management (`pretix.base.services.quotas` and `pretix.base.services.orders`)
* **Workflow A (Order Creation):**
  - *Starting Condition:* An event has an active item with a quota limit > 0.
  - *User Action:* Customer places an order for tickets via API or Storefront.
  - *Expected Outcome:* Order is created in `Pending` state; quota is reserved; if quota is 0, the order is rejected.
* **Workflow B (Order Cancellation / State Transition):**
  - *Starting Condition:* An order is in `Pending` state with held quota.
  - *User Action:* Customer or Organizer cancels the order (or it expires).
  - *Expected Outcome:* Order transitions to `Canceled` or `Expired`; held quota is returned to the available pool.
* **Shared State / Value:** `Quota Availability` (Workflow A reads and decrements; Workflow B updates order status, which recalculates and releases availability).

## 3. Toolchain & Environment Baseline
* **Host Operating System:** Windows 10/11 x64
* **Container Runtime:** Docker Desktop (Engine v29.9.3)
* **Database Backend:** PostgreSQL 16 (Alpine)
* **Cache / Task Broker:** Redis 7 (Alpine)
* **Application Framework:** Django 4.x / Python 3.11+
* **Testing Toolchain:**
  - Unit & White-Box: `pytest`, `coverage.py`, `mutmut`
  - Static Analysis: `SonarCloud` / `SonarQube`
  - API Testing & Datagen: Python `requests`, OpenAPI 3.0 spec, custom `tools/datagen/`
  - End-to-End & Usability: `Playwright` (Chromium), `@axe-core/playwright`, Google Lighthouse
  - Defensive Security: `OWASP ZAP` (passive scanner), `pip-audit`
  - Performance & Concurrency: Grafana `k6` OSS (v0.50+)
