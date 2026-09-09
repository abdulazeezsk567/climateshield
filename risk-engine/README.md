# ClimateShield Risk & Trigger Engine (`/risk-engine`)

The Risk & Trigger Engine evaluates real-time meteorological observations and satellite vegetation indices against 10-year rolling historical baselines. It computes anomaly deviations, executes deterministic sector-specific parametric thresholds, and predicts continuous vulnerability indices via an explainable ML microclimate zoning model.

---

## 1. Key Components

### 1.1 Config-Driven Rule Evaluator (`risk_engine.thresholds.evaluator`)
- **Config-Driven**: Sector-specific trigger thresholds are loaded from `src/risk_engine/config/thresholds.json`.
- **Per-Sector Sensitivity**: Differentiates thresholds across MSME industries (`AGRI_ALLIED`, `DAIRY_LIVESTOCK`, `HANDLOOMS_TEXTILES`, `FOOD_PROCESSING`, `RETAIL_MICRO_ENTERPRISE`, `SERVICES_LIGHT_MANUFACTURING`).
- **Policy Mapping**: Emits structured loan intervention proposals (`EMI_DEFERRAL`, `RECOVERY_TOPUP`).

### 1.2 Explainable ML Zoning Model (`risk_engine.ml_zoning.model`)
- **Transparent Linear-Logistic Scoring**: Computes continuous vulnerability scores ($0 \le \text{score} \le 100$).
- **Inspectable Feature Attribution**: Returns exact mathematical contributions ($w_i x_i$) for:
  - `rainfall_deficit_ratio`
  - `extreme_rain_ratio`
  - `temperature_anomaly_celsius`
  - `vegetation_stress_delta`
  - `sector_vulnerability_weight`
  - `credit_exposure_ratio`
- **Decision-Support Guardrails**: Explicitly positioned as a decision-support heuristic, avoiding assertions of deterministic individual borrower default certainty.

### 1.3 Service Facade (`risk_engine.service.RiskEngineService`)
- **Public Interface**: Consumes `data-layer` strictly through `DataLayerService` without accessing internal raw storage.
- **Combined Output**: Produces `BorrowerRiskOutput` adhering to the unified cross-service schema.
- **Basis-Risk Flags**: Tracks boundary proximity ($\pm 3\%$) and unconfirmed satellite telemetry.

---

## 2. Configuration & Hot-Recalibration
All thresholds and model weights reside in external configuration files:
- `src/risk_engine/config/thresholds.json`: Sector trigger percentages and policy codes.
- `src/risk_engine/config/model_config.json`: Feature coefficients, intercept, and risk tier cutoffs.

These parameters can be modified and reloaded at runtime via `RiskEngineConfig.reload()` without service redeployments.

---

## 3. Running Unit Tests
```bash
# Run the complete test suite
pytest risk-engine/tests -v
```
Covers:
- **Normal Operating Cases**: Deficit, excess rainfall, and normal tolerance conditions.
- **Missing Telemetry Cases**: Graceful degradation when satellite NDVI or humidity is absent.
- **Boundary Precision Cases**: Strict verification at trigger cutoffs ($\pm 0.01\%$).
- **Adversarial Cases**: Rejection of negative/corrupt values and clamping of extreme outliers.
- **Config Recalibration**: Dynamic threshold updates.
- **Explainability**: Verification of feature contribution breakdowns.
