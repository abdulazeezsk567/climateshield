# ClimateShield Verification & Test Suite (`TESTING.md`)

This document describes the automated test architecture, coverage scope, and execution commands for the full ClimateShield stack.

---

## 1. Quick-Start Test Execution

### 1.1 Backend Test Suite (Pytest)
Run all 80 unit, integration, and security tests across all Python layers:
```bash
# From the repository root
pytest api/tests risk-engine/tests data-layer/tests integration-layer/tests
```

Individual subsystem test commands:
```bash
pytest data-layer/tests                  # Data layer & baseline tests (5 tests)
pytest risk-engine/tests                # Risk engine & adversarial tests (13 tests)
pytest integration-layer/tests          # LMS adapter & audit ledger tests (11 tests)
pytest api/tests                        # API, security, and rate-limit tests (51 tests)
```

### 1.2 Frontend Test Suite (Vitest + Testing Library)
Run all 13 component and end-to-end flow tests:
```bash
cd frontend
npm test
```

### 1.3 Security Pre-Commit Hygiene Scan
Run the automated pre-commit secrets and credentials detector:
```bash
python scripts/check_secrets.py
```

### 1.4 Frontend Production Bundle Verification
Verify complete TypeScript compilation and Vite production build:
```bash
cd frontend
npm run build
```

---

## 2. Test Coverage Matrix

### 2.1 Backend Risk & Trigger Engine (`risk-engine/tests`)
| Test File | Target Subsystem | Scenarios Covered |
| :--- | :--- | :--- |
| `test_risk_engine.py` | Deterministic Rules & ML Model | Normal baseline conditions, agricultural drought activation, excess rainfall activation, missing NDVI fallbacks, boundary threshold precision, configuration recalibration, and explainable ML feature contributions ($w_i x_i$). |
| `test_risk_engine_adversarial.py` | Edge Cases & Adversarial Inputs | Negative precipitation rejection via Pydantic schema validation, extreme hyperthermia shock (>65°C), single-millimeter P95 threshold precision, zero-exposure / empty loans resilience without division-by-zero. |

### 2.2 Backend Security & API Integration (`api/tests`)
| Test File | Target Subsystem | Scenarios Covered |
| :--- | :--- | :--- |
| `test_api.py` | REST API Layer | Health probes, portfolio summary metrics, geospatial heatmap clusters, paginated borrower queries with sector filters, borrower scorecard detail, and active trigger queries. |
| `test_interventions.py` | LMS Webhook & State Machine | Querying interventions, 404 on non-existent records, LMS webhook missing signature (401), invalid signature rejection (401), and valid HMAC-SHA256 signature verification (200). |
| `test_security.py` | Security & RBAC | Salted bcrypt login (`officer_sfl`, `judge_auditor`), refresh token rotation, invalid password rejection, RBAC route gating (`viewer` vs `credit_team`), path parameter directory traversal defense, and XSS string validation. |
| `test_api_integration_extended.py` | Extended Integration & Load | Unauthenticated rejection across all 8 sensitive routes (401), wrong-role rejection (403), malformed query/body validation (422), sliding-window auth burst rate limiting (429 with `Retry-After`), SQL injection attack safety, and defensive security headers (`HSTS`, `CSP`, `X-Frame-Options: DENY`, `Cache-Control: no-store`). |

### 2.3 Backend Action & Integration Layer (`integration-layer/tests`)
| Test File | Target Subsystem | Scenarios Covered |
| :--- | :--- | :--- |
| `test_integration.py` | LMS Adapter & Audit Ledger | 4-Stage state machine progression (`TRIGGERED` $\rightarrow$ `NOTIFIED` $\rightarrow$ `APPLIED` $\rightarrow$ `CONFIRMED`), illegal transition rejection, HMAC-SHA256 webhook signing, simulated SMS alert dispatch with zero-fabrication guarantees, correlation ID tracking, and SHA-256 parent-hash tamper detection. |

### 2.4 Frontend Component & Flow Tests (`frontend/src/__tests__`)
| Test File | Component / View | Scenarios Covered |
| :--- | :--- | :--- |
| `MaskedField.test.tsx` | Data Privacy Mask | Renders masked pattern `••••••••••••` by default; unmasks value upon clicking eye toggle; logs `SENSITIVE_FIELD_REVEALED` event to audit trail; toggles mask off on second click. |
| `PortfolioDashboard.test.tsx` | Portfolio Dashboard | Renders 4 KPI metric cards, renders district heatmap clusters with hazard tags, and tests sector dropdown filtering on the borrower roster. |
| `TriggerSimulator.test.tsx` | Trigger Simulator | Renders 3-point visual deviation calculation bars (baseline, threshold, simulated); updates dry days on hazard switch; dispatches simulation and renders LMS relief proposal. |
| `InterventionLog.test.tsx` | Intervention Log | Renders 4-stage state machine pills; displays correlation IDs; opens detailed intervention dossier modal with HMAC webhook payload on row click. |
| `e2e_flow.test.tsx` | End-to-End User Journey | Complete evaluator workflow: **Login $\rightarrow$ Inspect Dashboard KPIs $\rightarrow$ Configure & Execute Trigger Simulator $\rightarrow$ Follow Link into Intervention Log $\rightarrow$ Verify Dispatched Intervention Record**. |

---

## 3. What Is vs. What Isn't Covered

### What Is Covered
1. **Mathematical & Rule Correctness**: Deterministic rainfall/drought policy thresholds, boundary conditions, and calibrated logistic ML vulnerability probabilities.
2. **Security & Cryptography**: Salted bcrypt password verification, HMAC-SHA256 signature generation/verification, SHA-256 parent-hash audit chaining with tamper-detection, sliding-window rate limiting, and defensive HTTP security headers.
3. **API Contracts & Envelopes**: Versioned JSON API responses, sanitized error envelopes without stack trace leakage, and pagination parameters.
4. **UI Behavior & Accessibility**: Responsive layout rendering, role-aware button gating (`viewer` vs `credit_team`), sensitive field masking, and cross-view user flows.

### What Isn't Covered (Out of Scope for Hackathon Track)
1. **Live Satellite Hardware Transmissions**: Physical satellite uplinks to orbital sensors are abstracted via the NASA POWER and Sentinel-2 mock/synthetic telemetry connectors.
2. **Direct Core Banking System (CBS) Production Connections**: Satin Finserv's production core banking network is decoupled via the pluggable `LMSAdapter` interface and verified against the simulated LMS webhook receiver.
