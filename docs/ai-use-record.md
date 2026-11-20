# AI-Use Record (Academic Transparency Log)
**Project:** SE3002 Software Quality Engineering — pretix Test Automation  
**Course Rule:** "AI tools are allowed only if you check every output and disclose it in an AI-use record (tool, purpose, output, what you checked or changed). Keep your prompts."

---

## Log Entries

### Entry 1
* **Date:** 2026-11-20
* **Member:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Initial project specification analysis, rubric mapping, and architectural scoping for SE3002 Final Project.
* **Prompt Summary:**
  > "Read the attached SQE_Final_Project Fall 2026 PDF and SQE Phased Project Plan PDF word by word, line by line to understand all requirements, rubric mapping, phase plans, and compile into context.md. Guide Docker setup and clarify instructor queries."
* **Output Summary:**
  Generated exhaustive `context.md` synthesizing all 16 rubric components (120 marks), mapped the 3 group members to Area A, B, and C responsibilities, formulated engineering rationales for the 4 instructor queries based on the project brief, and drafted the Docker Desktop deployment guide.
* **What We Checked and Changed:**
  - Verified every rubric mark against `SQE_Final_Project Fall 2026.pdf` (120 marks total).
  - Confirmed the 3-member team role split aligns with Course Learning Outcomes (CLO1, CLO2, CLO3).
  - Validated that `pretix` Order and Quota services match Workflow A (order placement) and Workflow B (order state change) with shared state `Quota Availability`.
  - Added specific student roll numbers (`24i-3108`, `24i-3107`, `24i-3074`).
* **Repository Location:** `context.md`, `docs/ai-use-record.md`

---

### Entry 2
* **Date:** 2026-11-20
* **Member:** Sohaib (24i-3108), M. Hasaam (24i-3107), Shaiman (24i-3074)
* **Tool:** Antigravity (Google DeepMind Agentic AI)
* **Purpose:** Phase 0 (Gate 0) Spike planning, repository scaffolding, and Docker Compose stack configuration for pretix.
* **Prompt Summary:**
  > "Proceed with Phase 0 (Gate 0) setup following gold-medalist guidelines. Create Docker compose configuration, baseline tracking, and execute Phase 0 spikes."
* **Output Summary:**
  Configured `docker-compose.yml` for pretix standalone with PostgreSQL 16 and Redis 7, set up `docs/baseline.md` tracking the upstream pretix release, initialized directory structures for unit, API, e2e, a11y, security, perf, and reports.
* **What We Checked and Changed:**
  - Confirmed Docker Desktop 29.9.3 is installed and operational.
  - Verified pretix container port mappings (`8345:80`) to prevent port conflicts with standard local web servers.
  - Checked that all raw spike outputs will be placed in `reports/spikes/`.
* **Repository Location:** `docker-compose.yml`, `docs/baseline.md`, `scripts/`
