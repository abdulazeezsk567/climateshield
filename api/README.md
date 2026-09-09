# ClimateShield API Gateway Service (`/api`)

The API Layer is the sole externally-facing surface of ClimateShield. It orchestrates downstream calls to `/data-layer`, `/risk-engine`, and `/integration-layer`, shaping outputs for the presentation layer while protecting internal subsystems from direct internet exposure.

---

## 1. Endpoints Specification

### 1.1 System Health & Observability
- `GET /health`: Health and deployment readiness probe reporting internal status of `data_layer`, `risk_engine`, and `integration_layer`.
- `GET /metrics`: Standard Prometheus exposition endpoint (`text/plain; version=0.0.4`) exposing request throughput, latencies, HTTP error rates, and climate trigger counts.
- `GET /api/v1/metrics/summary`: JSON metrics summary for the administrative dashboard.

### 1.2 Authentication & Identity (`/api/v1/auth`)
- `POST /api/v1/auth/login`: Salted bcrypt password verification issuing short-lived (15 min) JWT access tokens and long-lived (7 day) refresh tokens.
- `POST /api/v1/auth/refresh`: Cryptographic refresh token rotation issuing fresh access tokens.
- `GET /api/v1/auth/me`: Returns verified caller identity, role (`credit_team` or `viewer`), and permissions.

### 1.3 Portfolio Intelligence (`/api/v1/portfolio`)
- `GET /api/v1/portfolio/summary`: Aggregated MSME debt exposure, borrower counts, high-risk exposure %, and operational districts.
- `GET /api/v1/portfolio/heatmap`: District-level geospatial clusters containing coordinates (lat/lon), borrower counts, exposure totals, average vulnerability scores, and dominant hazards.

### 1.4 Borrower Risk Intelligence (`/api/v1/risk`)
- `GET /api/v1/risk/borrowers`: Paginated borrower risk scorecards, filterable by `district`, `sector`, and `min_risk_score`.
- `GET /api/v1/risk/borrowers/{borrower_id}`: Granular borrower scorecard including active loans, monthly district baselines, latest meteorological observations, and explainable ML feature contributions ($w_i x_i$).

### 1.5 Trigger Simulations & Interventions (`/api/v1/triggers`)
- `POST /api/v1/triggers/simulate`: Injects an interactive climate shock scenario (drought deficit, excess cloudburst, or heatwave), evaluates borrower parametric triggers via `risk-engine`, executes simulated LMS loan modifications (EMI moratoriums / recovery top-ups) via `integration-layer`, and records an immutable audit ledger entry.
- `GET /api/v1/triggers/active`: Retrieves all active or simulated parametric triggers.

### 1.6 LMS Interventions & Callbacks (`/api/v1/interventions`)
- `GET /api/v1/interventions`: Paginated list of active and historical loan-support interventions tracking the 4-stage lifecycle (`TRIGGERED` $\rightarrow$ `NOTIFIED` $\rightarrow$ `APPLIED` $\rightarrow$ `CONFIRMED`).
- `GET /api/v1/interventions/{intervention_id}`: Detailed intervention dossier with stage timestamps and HMAC signatures.
- `POST /api/v1/webhook/lms/loan-action`: Inbound LMS confirmation webhook endpoint protected via HMAC-SHA256 signature verification.

### 1.7 Governance & Audit Ledger (`/api/v1/audit`)
- `GET /api/v1/audit/interventions`: Paginated tamper-evident event log capturing all trigger activations, simulated LMS webhooks, and borrower notifications.
- `GET /api/v1/audit/verify`: Cryptographic verification traversing the SHA-256 parent-hash chain from genesis to confirm zero unauthorized ledger tampering.

---

## 2. Defensive Security Middleware

The API gateway enforces four layers of defensive HTTP middleware on every request:
1. **`RateLimitingMiddleware`**: Per-IP sliding-window rate limiting (stricter 5 req/min on `/auth/*` routes; 60 req/min on general endpoints).
2. **`SecurityHeadersMiddleware`**: Defensive HTTP security headers (`Strict-Transport-Security`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`, and `Cache-Control: no-store` on sensitive financial endpoints).
3. **`MetricsMiddleware`**: Intercepts all requests to measure duration, record status codes, and track errors in `MetricsRegistry`.
4. **`CORSMiddleware`**: Strict origin whitelisting forbidding wildcard (`*`) origins.

---

## 3. Running Tests
```bash
pytest api/tests -v
```
Verifies all 55 API, security, RBAC, intervention, and telemetry tests with 100% pass rate.
