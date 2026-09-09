# ClimateShield Architecture

## 1. Executive Summary
**ClimateShield** is an automated climate-risk intelligence and parametric loan-support layer designed for NBFC MSME lending (specifically tailored for Satin Finserv Ltd - SFL). It continuously correlates granular weather and satellite observations against geolocated borrower loan portfolios, identifies microclimate shock anomalies through a hybrid risk engine, and initiates pre-emptive loan-support actions (such as moratoriums/EMI restructuring and liquidity top-ups) through an integrated Loan Management System (LMS) simulator.

The core operational feedback cycle is:
$$\text{Monitor} \longrightarrow \text{Assess} \longrightarrow \text{Act} \longrightarrow \text{Learn}$$

---

## 2. Five-Layer Architecture Overview

```
+-------------------------------------------------------------------------------+
|                           5. Presentation Layer                               |
|          (React 18 + TypeScript Dashboard: Heatmap, Triggers, Alerts)         |
+---------------------------------------+---------------------------------------+
                                        |  HTTPS / REST / WebSocket (Role-based)
                                        v
+-------------------------------------------------------------------------------+
|                              3. API Layer                                     |
|                 (FastAPI Gateway: Auth, Routing, Orchestration)              |
+-------------------+---------------------------------------+-------------------+
                    |                                       |
       Internal Call / RPC                     Internal Call / Webhook
                    v                                       v
+---------------------------------------+   +-----------------------------------+
|       2. Risk & Trigger Engine        |   |   4. Action & Integration Layer   |
| (Baselines, Rules, ML Climate Zoning) |   | (LMS Webhook, Alerts, Audit Log)  |
+-------------------+-------------------+   +-----------------------------------+
                    ^
                    | Read Baselines & Geo Observations
+-------------------+-----------------------------------------------------------+
|                              1. Data Layer                                    |
|   (NASA POWER, IMD Weather, Sentinel NDVI Ingestion & Borrower Portfolios)   |
+-------------------------------------------------------------------------------+
```

### Layer 1: Data Ingestion & Storage Layer (`/data-layer`)
- **Mission**: Ingest, normalize, and store environmental time-series data and borrower demographic/loan geolocation seed profiles.
- **Components**:
  - Weather Ingestion Connectors (NASA POWER API, IMD-style gridded weather).
  - Satellite/Vegetation Indices Connector (Sentinel-2 / NDVI proxies for crop/flood stress).
  - Borrower Portfolio Store (MSME loan metadata, pin codes, district centroids, sector classification).
  - Historical Baselines Store (10-year rolling averages for precipitation, temperature extremes, heat degree days).
- **Interface**: Internal repository / query interface returning standardized `ClimateObservation` and `BorrowerProfile` records.

### Layer 2: Risk & Trigger Engine (`/risk-engine`)
- **Mission**: Perform anomaly detection, risk categorization, and parametric trigger evaluation.
- **Components**:
  - Baseline Evaluator: Computes standard deviations and anomaly percentiles against historical baselines.
  - Deterministic Rule Engine: Parametric thresholds (e.g. cumulative 72-hour rainfall exceeding district 95th percentile).
  - Lightweight ML Risk Zoning: Microclimate vulnerability classification combining exposure, crop/enterprise sensitivity, and hazard severity.
- **Interface**: `evaluate_risk(borrower_id, time_window)` and `evaluate_triggers(district_id, climate_event) -> TriggerEvent`.

### Layer 3: API Layer (`/api`)
- **Mission**: High-performance, secure REST gateway mediating presentation requests, triggering on-demand assessments, and serving portfolio intelligence.
- **Components**:
  - Authentication & Role-Based Access Control (RBAC): Differentiates between SFL Risk Officer (full access) and Judge/Stakeholder (read-only demo mode).
  - Portfolio Endpoints (`/api/v1/portfolio`): Aggregated risk exposure by region and sector.
  - Trigger Simulation Endpoints (`/api/v1/triggers`): Test scenario injector for drought, excess rainfall, and heatwave shocks.
  - Risk Analytics Endpoints (`/api/v1/risk`): Detailed anomaly scorecards per borrower/district.
- **Interface**: OpenAPI 3.1 specification, HTTPS JSON payloads.

### Layer 4: Action & Integration Layer (`/integration-layer`)
- **Mission**: Execute downstream loan protection policies and maintain auditability upon trigger activation.
- **Components**:
  - LMS Webhook Dispatcher: Emulates core banking / LMS interactions (initiating EMI moratoriums, restructuring repayment schedules, recovery top-ups).
  - Borrower Alert Service: Formats localized SMS/WhatsApp notifications informing borrowers of proactive climate relief.
  - Immutable Audit Log: Cryptographically hashed, append-only log recording trigger conditions, timestamp, model version, and LMS transaction receipt.
- **Interface**: Webhook emitters with signature validation and asynchronous event queues.

### Layer 5: Presentation Layer (`/frontend`)
- **Mission**: Provide an intuitive, visually distinctive dashboard for operational credit risk monitoring and interactive hackathon demonstration.
- **Components**:
  - Geospatial Portfolio Heatmap: District-level vulnerability overlay with drill-down to MSME cluster nodes.
  - Interactive Trigger Simulator: Sliders and preset scenario cards allowing judges to simulate extreme climate events and observe real-time LMS actions.
  - Live Audit & Action Stream: Real-time feed of generated alerts and LMS moratorium approvals.
  - RBAC Viewport Switcher: Instant toggle between SFL Risk Analyst view and Auditor/Demo view.

---

## 3. Communication Protocols & Contracts

| From Layer | To Layer | Protocol | Description |
| :--- | :--- | :--- | :--- |
| Presentation Layer | API Layer | HTTPS / REST / WS | Client-to-server interaction, JWT bearer authentication. |
| API Layer | Risk Engine | Internal Python Module / RPC | Direct synchronous or queued risk assessment evaluation. |
| API Layer | Data Layer | Internal Service Query / Cache | Portfolio and historical time-series queries. |
| Risk Engine | Integration Layer | Event Bus / Async Webhook | Trigger activation payload emitting automated LMS actions. |
| Integration Layer | External LMS (Simulated) | HTTPS Webhook (HMAC signed) | Emulated core banking loan modification requests. |

---

## 4. Directional Data Flow (The Core Loop - Implemented Architecture)

```
[External Sources]
 NASA POWER API (Precipitation, Temp, Humidity, Wind)
 Sentinel-2 Proxy (Seasonal Vegetation NDVI Index)
           │
           ▼ (HTTP with Exponential Backoff & Sentinel -999 Filter)
┌────────────────────────────────────────────────────────────────────────┐
│                        Layer 1: Data Layer                             │
│ ┌──────────────────────┐  ┌──────────────────────────────────────────┐ │
│ │ Ingestion Providers  │  │ Historical Baseline Store (10-Yr Monthly)│ │
│ │ - NASAPowerProvider  │  │ - Mean Rainfall (μ), Std Dev (σ), P95    │ │
│ │ - IMDProvider (Stub) │  │ - Max Temp Baseline, Average NDVI        │ │
│ │ - SyntheticProvider  │  └──────────────────────────────────────────┘ │
│ └──────────────────────┘  ┌──────────────────────────────────────────┐ │
│                           │ Synthetic MSME Borrower Repository       │ │
│                           │ - SFL Branch Clusters (UP, Bihar, etc.)  │ │
│                           │ - De-identified & Labelled Synthetic PII │ │
│                           └──────────────────────────────────────────┘ │
│                                      │                                 │
│                   PUBLIC FACADE: DataLayerService                     │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       │ Public Methods Only:
                                       │ - get_district_baseline()
                                       │ - get_weather_observations()
                                       │ - list_borrowers()
                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     Layer 2: Risk & Trigger Engine                     │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │ Config Loader (Hot-recalibration without redeploy)                 │ │
│ │ - thresholds.json (Sector-specific trigger thresholds & actions)   │ │
│ │ - model_config.json (Transparent ML weights & explainability)      │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                      │                                 │
│ ┌──────────────────────────────────┐ ┌───────────────────────────────┐ │
│ │ Rule-Based Trigger Evaluator     │ │ Explainable ML Zoning Model   │ │
│ │ - Anomaly % vs Baseline          │ │ - Linear-Logistic Scoring     │ │
│ │ - Sector Sensitivity Breaches    │ │ - Transparent Contributions   │ │
│ │ - Deterministic Relief Proposals │ │ - Continuous 0-100 Risk Score │ │
│ └──────────────────────────────────┘ └───────────────────────────────┘ │
│                                      │                                 │
│                COMBINED OUTPUT: BorrowerRiskOutput                     │
│ { borrower_id, risk_score, trigger_fired, trigger_reason,            │
│   recommended_action, basis_risk_flags, evaluated_at }                │
└──────────────────────────────────────┼─────────────────────────────────┘
                                       │
                                       ▼
                           To Layer 3 (API Gateway)
                        & Layer 4 (Action / LMS Webhook)
```

1. **Monitor**:
   - `DataLayerService` queries `NASAPowerWeatherProvider` (with exponential backoff retries and `-999` sentinel filtering) or `SentinelNDVIProvider`.
   - Incoming coordinates and query date spans undergo strict bounds validation (`-90 <= lat <= 90`, `-180 <= lon <= 180`, `start <= end`).
   - Normalizes raw telemetry into standardized `ClimateObservation` records.

2. **Assess**:
   - `RiskEngineService` consumes observations and queries `DataLayerService.get_district_baseline(district_id, month)` and `list_borrowers(district_id)`.
   - **Rule-Based Trigger Evaluator**: Compares observed rainfall deficit % ($\Delta = \frac{obs - \mu}{\mu} \times 100$) and extreme rainfall against per-sector cutoffs defined in `thresholds.json`.
   - **Explainable ML Zoning Model**: Calculates a continuous 0-100 vulnerability score via calibrated logistic scoring with transparent feature attribution ($w_i x_i$).
   - Formulates a combined `BorrowerRiskOutput` with basis-risk caveat flags.

3. **Act**:
   - Outbound `BorrowerRiskOutput` with `TriggerActionProposal` (e.g. 30-day EMI deferral or recovery top-up) is prepared for dispatch to the LMS webhook simulator and borrower alert service.

4. **Learn**:
   - Threshold configurations (`thresholds.json`) and ML model weights (`model_config.json`) can be hot-recalibrated on disk without requiring service code redeployment.

---

## 5. Architectural Isolation & Basis-Risk Mitigation

### 5.1 Layer Isolation
- **No Raw Storage Access**: `risk-engine` never inspects SQLite databases, files, or internal repositories of `data-layer`. It interfaces exclusively through `DataLayerService`.
- **Decision-Support Guardrails**: Model docstrings, outputs, and log messages explicitly avoid claiming individual borrower default certainty.

### 5.2 Basis-Risk Mitigation Strategy
1. **Multi-Sensor Triangulation**: Atmospheric precipitation is cross-referenced with satellite NDVI vegetative health, preventing single-station measurement error.
2. **Sector Stratification**: Differentiated thresholds prevent agricultural drought triggers from falsely triggering relief for insulated commercial sectors (e.g. urban retail).
3. **Credit Context Integration**: Active debt exposure is factored into the continuous vulnerability index.
4. **Boundary Proximity & Telemetry Flags**: Observations within 3% of trigger thresholds or lacking satellite corroboration are automatically flagged (`BOUNDARY_THRESHOLD_PROXIMITY`, `MISSING_SATELLITE_NDVI_CONFIRMATION`) for human-in-the-loop credit officer review.

