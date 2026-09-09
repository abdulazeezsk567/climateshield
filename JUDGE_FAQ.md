# ClimateShield: Hackathon Evaluation & Architecture FAQ ("Judge FAQ")

This document provides a fast, authoritative technical reference for hackathon evaluators, credit risk committees, and technical judges reviewing **ClimateShield**.

---

## 1. How is the Trigger Threshold Calculated?

ClimateShield utilizes a **hybrid parametric risk calculation** combining 10-year rolling historical baselines, physical meteorological extremes, and industry vulnerability weights:

### 1.1 Baseline Modeling
The Data Layer precomputes monthly statistical parameters across 10 years of gridded weather observations for each district:
- **Monthly Mean Rainfall ($\mu$)** and **Standard Deviation ($\sigma$)**
- **95th Percentile Precipitation ($P_{95}$)**: The extreme daily cloudburst/flood cutoff
- **Historical Average Max Temperature ($\mu_{T_{\max}}$)** and **NDVI Vegetation Health ($\mu_{\text{NDVI}}$)**

### 1.2 Multi-Hazard Trigger Formulations
1. **Excess Rainfall / Cloudburst (Flood Risk)**:
   $$\text{Trigger Condition}: \quad R_{\text{daily}} \ge P_{95} \quad \lor \quad R_{\text{daily}} \ge (\mu + 2.0\sigma)$$
   Breaching this threshold initiates proactive **60-Day EMI Moratoriums** to prevent loan delinquency during localized inundation.
2. **Agricultural Drought**:
   $$\text{Trigger Condition}: \quad \Delta R_{14\text{d}} \le -45\% \quad \land \quad \Delta \text{NDVI} \le -25\%$$
   Combines rolling 14-day rainfall deficits with satellite-derived physiological crop stress. Initiates **Recovery Top-Up Liquidity Loans**.
3. **Heatwave Anomaly**:
   $$\text{Trigger Condition}: \quad T_{\max} \ge (\mu_{T_{\max}} + 4.5^\circ\text{C}) \quad \text{for } \ge 3 \text{ consecutive days}$$

### 1.3 Sector-Specific Sensitivity Modulation
Trigger sensitivity is calibrated across MSME industries: Agriculture/Allied ($w=1.00$) and Dairy ($w=0.85$) trigger faster than Retail ($w=0.50$), preventing unnecessary debt restructuring for climate-insulated businesses.

---

## 2. How is Basis Risk Mitigated?

*Basis risk* occurs when satellite macro-telemetry indicates a disaster that did not damage a specific borrower, or vice versa (e.g., ground-level pump irrigation protecting a crop during a regional drought). ClimateShield addresses this via a **4-tier mitigation architecture**:

1. **Dual-Stream Telemetry Corroboration**: Rain gauges (NASA POWER / IMD) are cross-referenced with Sentinel-2 satellite vegetation health (NDVI) before committing agricultural relief.
2. **Boundary-Proximity Surveillance**: If an observation sits within $\pm 3\%$ of a cutoff, the risk engine attaches a `BOUNDARY_THRESHOLD_PROXIMITY` caveat flag.
3. **Missing Telemetry Graceful Fallback**: If satellite imagery is obscured by heavy monsoonal cloud cover, the engine falls back to soil moisture heuristics and explicitly logs `MISSING_SATELLITE_NDVI_CONFIRMATION`.
4. **Human-in-the-Loop Field Officer Workflow**: Flagged edge cases do not trigger automated LMS disbursements; they queue an interactive dossier in the dashboard for Satin Finserv branch credit officers to inspect and confirm.

---

## 3. What Security Measures are in Place?

Summarized from [`SECURITY.md`](file:///C:/Users/Abdul%20Azeez/.gemini/antigravity/scratch/climateshield/SECURITY.md):

- **Authentication & Password Cryptography**: 12-round salted `bcrypt` hashing with constant-time verification; short-lived (15 min) JWT access tokens and rotating (7 day) refresh tokens signed via HMAC-SHA256.
- **Declarative Role-Based Access Control (RBAC)**: Enforces role gating (`credit_team` has full simulation and dispatch authority; `viewer` / judge role is strictly read-only).
- **Borrower PII Masking with Audit Surveillance**: Financial identifiers (`account_number`, `pan`, `phone`) are masked by default (`••••••••••••`). Clicking to unmask emits a `SENSITIVE_FIELD_REVEALED` event recorded to the audit log.
- **Tamper-Evident SHA-256 Chained Audit Ledger**: Every trigger simulation, LMS webhook dispatch, and field reveal computes a parent-hash preimage digest. The `/api/v1/audit/verify` endpoint verifies chain integrity from genesis.
- **Defensive API Gateways**: Sliding-window rate limiting (5 req/min on `/auth/*`), HTTP Strict Transport Security (`HSTS`), `Content-Security-Policy`, and non-wildcard CORS.
- **Zero-Secret CI Scanning**: Automated pre-commit script ([`scripts/check_secrets.py`](file:///C:/Users/Abdul%20Azeez/.gemini/antigravity/scratch/climateshield/scripts/check_secrets.py)) fails builds if credentials exist in Git; runtime configs fail startup if default keys are detected in staging or production.

---

## 4. What's Simulated vs. Real in this Build?

ClimateShield is engineered as a **hackathon-to-production-track** system. We maintain absolute transparency regarding what is live versus simulated:

| Subsystem | Live / Real in this Build | Simulated / Abstracted for Demo |
| :--- | :--- | :--- |
| **API & Security Gateway** | **100% Real**: FastAPI async service, bcrypt hashing, JWT rotation, rate limiter, security headers. | None. |
| **Risk & Trigger Engine** | **100% Real**: 10-year rolling baselines, deterministic threshold rules, calibrated Logistic Regression ML model. | None. |
| **Frontend Dashboard** | **100% Real**: React 18, Tailwind design system, interactive simulator, real-time API client, session store. | None. |
| **Weather / Satellite Telemetry** | **Real Schema & Adapters**: Fully functional NASA POWER REST connector with retries and timeout controls. | In offline demo mode, telemetry is fed by synthetic observation generators to avoid NASA API rate limits during judging. |
| **LMS Core Banking System** | **Real Adapter Pattern**: Outbound HTTP requests with HMAC-SHA256 headers (`X-ClimateShield-Signature`). | Target receiver is a simulated LMS webhook container (`SimulatedLMSAdapter`) rather than Satin Finserv's production Finnone CBS. |
| **Borrower Notifications** | **Real Copy & Zero Fabrication**: Localized bilingual Hindi/English SMS templates formatted with transaction IDs. | Payloads are logged and marked as `SIMULATED_DISPATCHED` (`is_simulated=True`) to adhere to our zero-fabrication security standard. |

---

## 5. What Would an Enterprise Production Rollout Need Next?

To transition ClimateShield from staging to full enterprise deployment across Satin Finserv's branch network, four infrastructure integrations are planned:

```
[Edge CDN / WAF] ──> [AWS ECS Auto-Scaling] ──> [Amazon RDS PostGIS] ──> [mTLS LMS Adapter]
  (Cloudflare)            (API Gateway)           (Spatial Queries)         (Core Banking)
```

1. **Managed Geospatial Database (PostgreSQL + PostGIS)**:
   - Index borrower GPS coordinates using spatial R-trees (`GEOMETRY(Point, 4326)`).
   - Execute spatial polygon queries (`ST_Contains`) against official IMD meteorological hazard shapefiles down to the taluka/village boundary.
2. **Enterprise Cloud Secret Manager**:
   - Transition `.env` templates to AWS Secrets Manager or HashiCorp Vault with automated 90-day credential rotation.
3. **Enterprise LMS Integration via Mutual TLS (mTLS) & DLQ**:
   - Provision client X.509 certificates issued by SFL's enterprise PKI.
   - Buffer outbound loan modifications through an asynchronous message queue (Amazon SQS / Apache Kafka) backed by a Dead-Letter Queue (DLQ) for idempotent retries during core banking maintenance windows.
4. **Edge CDN, WAF & DDoS Protection**:
   - Position Cloudflare Enterprise or AWS CloudFront + AWS WAF ahead of the Application Load Balancer to blunt Layer 7 attacks and enforce office-network IP whitelisting.
