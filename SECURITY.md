# ClimateShield Security Policy & OWASP API Top 10 (2023) Compliance

## 1. Security Architecture & Threat Boundary Model
ClimateShield bridges climate intelligence with financial lending infrastructure at **Satin Finserv Ltd (SFL)**. All layers adhere to a zero-trust, security-first posture to prevent leakage of borrower Personally Identifiable Information (PII) and unauthorized loan modification actions.

### Demo Credentials & RBAC Roles
The demo environment features two pre-configured accounts with salted bcrypt hashes (passwords are never stored or logged in plaintext):

| Username | Role | Full Name | Capabilities | Password |
| :--- | :--- | :--- | :--- | :--- |
| `officer_sfl` | `credit_team` | SFL Credit Risk Manager | Full operational access: trigger simulations, loan interventions, audit ledger, and analytics. | `SFLCreditRisk@2026!` |
| `judge_auditor` | `viewer` | Hackathon Judge / Auditor Demo View | Read-only access: inspect portfolio summary, heatmap, risk scorecards, and audit logs. Mutating simulations forbidden (HTTP 403). | `ViewerJudge@2026!` |

---

## 2. OWASP API Security Top 10 (2023) Compliance Matrix

| Vulnerability | Description | ClimateShield Implementation & Defense | Demo vs. Production Posture |
| :--- | :--- | :--- | :--- |
| **API1:2023 Broken Object Level Authorization (BOLA)** | Attackers exploit endpoints that handle object identifiers without proper object-level access checks. | **Enforced**: Borrower IDs are validated against strict regex (`^[A-Za-z0-9_-]{3,50}$`). Route dependencies verify caller authorization (`require_role`) and validate borrower existence through `DataLayerService`. In production, tenant/branch ID scoping ensures officers can only view loans within their designated operational territory. | **Demo**: Scoped to pre-seeded synthetic SFL portfolio.<br>**Prod**: Row-level security in PostgreSQL with SFL branch/officer tenancy boundaries. |
| **API2:2023 Broken Authentication** | Compromised authentication mechanisms allow attackers to impersonate legitimate users. | **Enforced**: Cryptographically signed short-lived JWT access tokens (15-min lifespan) paired with longer-lived refresh tokens (7 days) signed via HMAC-SHA256 (`HS256`). Passwords hashed using salted `bcrypt` (12 work factor rounds). Constant-time verification blunts timing attacks. | **Demo**: Pre-seeded demo user store in memory with verified bcrypt hashes.<br>**Prod**: Integration with SFL corporate Okta/Active Directory SSO via OIDC. |
| **API3:2023 Broken Object Property Level Authorization (BOPLA)** | Exposure of sensitive object properties or unauthorized modification of internal fields (mass assignment). | **Enforced**: Strict Pydantic V2 schemas with `extra="forbid"` on input payloads. Output DTOs explicitly strip sensitive borrower data (Aadhaar/PAN, phone numbers, exact residential coordinates). | **Demo**: Synthetic borrower data only exposes anonymized alias and district centroid.<br>**Prod**: Dynamic column-masking proxy before external consumption. |
| **API4:2023 Unrestricted Resource Consumption** | Exploitation of missing rate limits or unconstrained payload sizes causing resource exhaustion / DoS. | **Enforced**: Thread-safe sliding-window rate limiting (`SlidingWindowRateLimiter`). Strict limits on auth endpoints (5 req/min) to prevent brute-force attacks; 60 req/min for general routes. Pagination enforced on all list endpoints (max 100 items per page). | **Demo**: In-memory sliding window per IP.<br>**Prod**: Distributed Redis-backed Token Bucket with Cloudflare API Shield. |
| **API5:2023 Broken Function Level Authorization (BFLA)** | Regular users accessing administrative or privileged functions. | **Enforced**: Declarative `require_role(*allowed_roles)` FastAPI dependencies on every route. High-impact mutating routes (e.g. `POST /api/v1/triggers/simulate` executing loan interventions) strictly require `credit_team`; `viewer` users receive HTTP 403 Forbidden. | **Demo**: RBAC enforced via JWT claims (`role`).<br>**Prod**: Fine-grained ABAC (Attribute-Based Access Control) with maker-checker approvals for loan write-downs exceeding INR 5,00,000. |
| **API6:2023 Unrestricted Access to Sensitive Business Flows** | Automated bots exploiting legitimate business workflows (e.g. rapid fire simulations or relief payouts). | **Enforced**: All simulation runs and loan interventions require authenticated `credit_team` credentials, are rate-limited, and log the caller ID (`actor=user:<user_id>`) to the immutable audit ledger. | **Demo**: Simulation engine dispatches mock LMS webhooks.<br>**Prod**: Mandatory dual-authorization maker-checker workflow before live core-banking ledger modifications. |
| **API7:2023 Server Side Request Forgery (SSRF)** | Exploiting URI inputs to access internal cloud metadata or backend services. | **Enforced**: No user-supplied URLs are fetched by the API or backend services. Upstream climate integrations (NASA POWER, Sentinel NDVI) use fixed, pre-configured HTTPS base URLs without dynamic user redirection. | **Demo**: Pre-configured synthetic and NASA API base endpoints.<br>**Prod**: Egress network security groups and AWS PrivateLink for LMS connectivity. |
| **API8:2023 Security Misconfiguration** | Unpatched flaws, permissive CORS, missing security headers, or leaking verbose stack traces. | **Enforced**: Centralized exception handlers catch all errors and return sanitized JSON envelopes without internal stack traces. Defensive HTTP headers injected: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, `Cache-Control: no-store`. CORS explicitly rejects wildcard `*`. | **Demo**: Localhost origin whitelist.<br>**Prod**: Production domain whitelist with automated TLS certificate rotation via Let's Encrypt. |
| **API9:2023 Improper Inventory Management** | Undocumented endpoints, zombie APIs, or outdated API versions exposed. | **Enforced**: Strict API versioning under `/api/v1/`. Interactive documentation automatically generated and kept synchronized via OpenAPI 3.1 (`/docs` and `/redoc`). Health probes (`/health`) monitor all subsystem states. | **Demo**: Single version `/api/v1/`.<br>**Prod**: API Gateway traffic shadowing and version sunset policies. |
| **API10:2023 Unsafe Consumption of APIs** | Blindly trusting data from third-party APIs without validation. | **Enforced**: Upstream weather data from external providers (NASA POWER, satellite feeds) is parsed and validated against strict Pydantic schemas (`ClimateObservation`) with deterministic boundary clamping (e.g. rainfall >= 0, temperature within -50°C to 70°C). | **Demo**: Strict boundary clamping and fallback to synthetic data.<br>**Prod**: Multiple redundant weather providers (IMD + NASA + ECMWF) with consensus voting. |

---

## 3. Secrets Management & Pre-Commit Scanning
- **Zero Secrets in Source Control**: All configuration loaded via environment variables (`JWT_SECRET_KEY`, `LMS_WEBHOOK_SECRET`, `NASA_POWER_API_KEY`).
- **Pre-Commit Secrets Scanner**: Executable at `scripts/check_secrets.py`. Scans for `.env` files, RSA certificates, private keys, and high-entropy credential patterns.
- **Git Ignore**: Root `.gitignore` explicitly prevents accidental commits of `.env`, `*.key`, `*.pem`, `*.pfx`, and sensitive credential files.

---

## 4. Audit Trail & Cryptographic Non-Repudiation
- **Immutable Audit Ledger**: Located in `integration-layer`. Every trigger simulation, loan intervention, and alert issuance writes a tamper-evident record chained via SHA-256 parent hash pointers (`previous_entry_hash`).
- **Audit Verification Endpoint**: `GET /api/v1/audit/verify` recomputes the entire cryptographic hash chain from the genesis block, detecting any unauthorized record alterations or deletions.
