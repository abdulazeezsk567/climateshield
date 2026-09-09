# ClimateShield Engineering Changelog (`CHANGELOG.md`)

All notable technical achievements, architectural deliverables, security implementations, and test suites completed across the ClimateShield project lifecycle are documented here.

---

## [Module 10] - Final Documentation, Operations Runbooks & Evaluator Resources
### Added
- **Root `README.md` Polish**: Complete institutional overview of ClimateShield, ASCII/Mermaid architecture diagrams, single-command run instructions, and live Trigger Simulator demo guide.
- **One-Page Judge FAQ (`JUDGE_FAQ.md` & `docs/JUDGE_FAQ.md`)**: Concise reference explaining trigger threshold mathematics, basis risk mitigation, security architecture, live vs. simulated component matrix, and enterprise production gaps.
- **Repository Documentation Consistency Audit**: Audited and synchronized all module READMEs (`api`, `data-layer`, `risk-engine`, `integration-layer`, `frontend`, `infra`, `packages/shared`).

---

## [Module 9] - Infrastructure, Containerization, CI/CD & Telemetry (`/infra`)
### Added
- **Dedicated Microservice Dockerfiles** (`infra/docker/`): Built hardened, unprivileged (`appuser`, UID 10001) containers for all 5 layers with automated healthcheck probes.
- **Autonomous Service Daemons**: Implemented `python -m data_layer`, `python -m risk_engine`, and `python -m integration_layer` with signal handling (`SIGINT`, `SIGTERM`) and graceful shutdown.
- **Unified Docker Compose Orchestrator** (`docker-compose.yml`): Single-command local deployment (`docker compose up --build`) on a shared bridge network (`climateshield-network`) with persistent volume binding (`./data`).
- **Multi-Environment Configuration Framework** (`infra/env/`): Added `.env.dev.example`, `.env.staging.example`, `.env.prod.example`, and authoritative reference matrix [`CONFIG_SPEC.md`](file:///C:/Users/Abdul%20Azeez/.gemini/antigravity/scratch/climateshield/infra/env/CONFIG_SPEC.md).
- **Runtime Secret Guard**: Integrated Pydantic model validator in `api/core/config.py` rejecting default development secrets when booting in `staging` or `production`.
- **Automated CI Pipeline** (`.github/workflows/ci.yml`): Configured 4 GitHub Actions quality gates: pre-commit secret scanning, Flake8 linting, `pip-audit`, `npm audit --audit-level=critical`, and full test suite execution.
- **Structured JSON Logging** (`StructuredJsonFormatter`): Standardized single-line JSON log format with ISO-8601 UTC timestamps, severity, service markers, and automated borrower PII redaction.
- **Prometheus & JSON Metrics Exposition** (`/metrics` & `/api/v1/metrics/summary`): Operational metrics registry tracking throughput, latencies, HTTP error rates, trigger evaluations/activations, and LMS relief dispatches.
- **Production Operations Roadmap** (`DEPLOYMENT.md`): Detailed enterprise specifications for AWS Secrets Manager, Amazon RDS PostgreSQL with PostGIS, mTLS CBS integration, and AWS WAF/CDN.

---

## [Module 8] - Full-Stack Test Suite & Adversarial Validation
### Added
- **Backend Test Suite (84 Pytest Tests - 100% Pass)**:
  - Unit tests for deterministic thresholds, historical baselines, and explainable ML features.
  - Adversarial tests: negative rainfall validation rejection, hyperthermia shock (>65°C), single-millimeter P95 threshold precision, and zero-exposure resilience.
  - Security tests: parameterized 401 unauthenticated route checks, 403 RBAC role checks, malformed input rejection (422), sliding-window rate limit bursts (429 with `Retry-After`), SQLi attack safety, and defensive security headers.
- **Frontend Test Suite (13 Vitest Tests - 100% Pass)**:
  - Component tests for `MaskedField`, `PortfolioDashboard`, `TriggerSimulator`, and `InterventionLog`.
  - Comprehensive end-to-end flow test (`e2e_flow.test.tsx`): Login $\rightarrow$ Dashboard $\rightarrow$ Simulate Trigger $\rightarrow$ Deep Link $\rightarrow$ Intervention Log.
- **Test Documentation** (`TESTING.md`): Detailed test execution guide, coverage matrix, and boundary scope.

---

## [Module 7] - Presentation Layer (React + Tailwind Dashboard)
### Added
- **Institutional Design System** (`frontend/src/design-system/`): High-density monospace figures, deep midnight surfaces (`#070B12`), 18 bespoke SVG icons, and WCAG AA contrast compliance.
- **Secure Auth & Session Management**: In-memory token storage with quick-switch role toggle (`officer_sfl` as `credit_team` vs. `judge_auditor` as `viewer`).
- **Portfolio Climate-Risk Dashboard** (`PortfolioDashboard.tsx`): 4 KPI metric cards, interactive 7-district geospatial heatmap grid, and filterable borrower roster table.
- **Interactive Trigger Simulator** (`TriggerSimulator.tsx`): Live parametric scenario injector with 3-point visual deviation calculation bars, dynamic $\Delta\%$, and automated LMS relief proposal dispatch.
- **Intervention Log & Dossier** (`InterventionLog.tsx`): 4-stage status machine badge tracker with correlation ID filtering and detail inspection modal.
- **Sensitive Field Privacy Masking** (`MaskedField.tsx`): Default masking (`••••••••••••`) with click-to-reveal emitting `SENSITIVE_FIELD_REVEALED` events to the audit trail.
- **Cryptographic Audit Ledger View** (`AuditLedgerView.tsx`): Live session reveal audit feed and on-demand SHA-256 chain integrity verification.

---

## [Module 6] - Action & Integration Layer (`/integration-layer`)
### Added
- **4-Stage Intervention State Machine**: Authoritative lifecycle progression: `TRIGGERED` $\rightarrow$ `NOTIFIED` $\rightarrow$ `APPLIED` $\rightarrow$ `CONFIRMED`.
- **Pluggable LMS Webhook Adapter**: Interface abstraction supporting `SimulatedLMSAdapter` (instantaneous HMAC confirmations) and `HttpLMSAdapter` (production HTTP POST with HMAC headers).
- **Inbound LMS Webhook Receiver**: Endpoint `/api/v1/webhook/lms/loan-action` verifying callbacks in constant time via HMAC-SHA256 signatures.
- **Bilingual Borrower Alert Service**: Localized Hindi and English SMS/WhatsApp advisory generation with strict zero-fabrication logging (`is_simulated=True`).
- **Tamper-Evident SHA-256 Audit Trail**: Append-only cryptographic ledger where each record hashes a block preimage containing the previous block's SHA-256 digest.

---

## [Module 5] - Security Hardening & Defensive Middleware (`/api`)
### Added
- **Bcrypt & JWT Bearer Authentication**: 12-round salted bcrypt hashing, 15-minute access tokens, and 7-day rotating refresh tokens.
- **Declarative Role-Based Access Control (RBAC)**: Route dependencies enforcing role-based permissions (`credit_team` vs `viewer`).
- **Sliding-Window Rate Limiter**: Per-IP sliding-window algorithm enforcing strict throttling (5 req/min on auth endpoints) to prevent brute-force attacks.
- **Defensive HTTP Security Headers**: Middleware injecting HSTS, CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff, and Cache-Control: no-store.
- **Automated Secrets Scanner** (`scripts/check_secrets.py`): Pre-commit scanner blocking private keys, tokens, and untracked `.env` files.

---

## [Module 4] - API Gateway & Orchestration (`/api`)
### Added
- **FastAPI Asynchronous Gateway**: Unified external REST surface orchestrating `data-layer`, `risk-engine`, and `integration-layer`.
- **Versioned API Routes**: Blueprints for `/portfolio/*`, `/risk/*`, `/triggers/*`, and `/audit/*`.
- **Standardized Pagination & Error Envelopes**: Reusable `PaginatedResponse[T]` and sanitized `ErrorResponse` envelopes without internal stack trace leakage.

---

## [Module 3] - Risk & Trigger Engine (`/risk-engine`)
### Added
- **Config-Driven Threshold Evaluator**: Sector-specific trigger thresholds loaded from `thresholds.json`.
- **Multi-Hazard Anomaly Detection**: Evaluation algorithms for excess rainfall, agricultural drought, and heatwave events.
- **Explainable ML Microclimate Zoning**: Transparent Logistic Regression model ($0-100$ score) with mathematical feature attribution breakdown ($w_i x_i$).
- **Basis-Risk Mitigation Flags**: Anomaly caveat tagging for boundary proximity ($\pm 3\%$) and unconfirmed satellite telemetry.

---

## [Module 2] - Data Layer & Baseline Management (`/data-layer`)
### Added
- **Meteorological Connectors**: NASA POWER REST API provider with exponential backoff retries, IMD weather stub, and synthetic fallback generator.
- **Copernicus Sentinel-2 Vegetation Proxy**: Seasonal NDVI curve modeling across Indian Kharif/Rabi agricultural calendars.
- **10-Year Rolling Historical Baselines**: Statistical precomputation ($\mu, \sigma, P_{95}, \mu_{\text{NDVI}}$) across 7 SFL operational districts.
- **Synthetic MSME Borrower Seed Database**: Realistic profiles for 56 borrowers across 6 key lending sectors.

---

## [Module 1] - Monorepo Foundation & Domain Schemas (`packages/shared`)
### Added
- **Cross-Layer Domain Schemas (Pydantic V2)**: Standardized data contracts for Borrowers, ClimateObservations, TriggerEvents, and AuditLogEntries.
- **Domain Enums & Financial Constants**: `RiskTier`, `ClimateHazardType`, `TriggerActionType`, `InterventionStatus`, and explicit financial configuration placeholders.
