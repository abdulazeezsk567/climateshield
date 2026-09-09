# ClimateShield Shared Contracts & Telemetry (`climateshield-shared`)

This package provides authoritative domain contracts, entity schemas (Pydantic V2), constants, and telemetry utilities shared across all ClimateShield backend microservices (`data-layer`, `risk-engine`, `api`, `integration-layer`).

---

## 1. Package Modules

- **`climateshield_shared.schemas`**:
  - `borrower`: `Borrower`, `GeoLocation`, `LoanSummary`, `BorrowerSector`
  - `climate`: `ClimateObservation`, `ClimateEvent`, `DataSourceType`
  - `trigger`: `TriggerEvent`, `TriggerActionProposal`, `RiskAssessment`, `BorrowerRiskOutput`
  - `audit`: `AuditLogEntry`, `AuditEventType`
- **`climateshield_shared.constants`**:
  - `RiskTier` (`LOW`, `MODERATE`, `HIGH`, `SEVERE`)
  - `ClimateHazardType` (`EXCESS_RAINFALL`, `AGRICULTURAL_DROUGHT`, `HEATWAVE`, `VEGETATION_STRESS`)
  - `TriggerActionType` (`EMI_DEFERRAL`, `RECOVERY_TOPUP`, `RESTRUCTURE_TENURE`)
  - `InterventionStatus` (`TRIGGERED`, `NOTIFIED`, `APPLIED`, `CONFIRMED`, `FAILED`, `CANCELLED`)
  - `DEFAULT_RELIEF_PERIOD_DAYS_PLACEHOLDER`, `DEFAULT_TOPUP_PERCENTAGE_PLACEHOLDER`
- **`climateshield_shared.telemetry`**:
  - `StructuredJsonFormatter`: Single-line JSON logger with automated PII redaction.
  - `configure_logging()`: Service-level logging bootstrapper.
  - `MetricsRegistry`: Thread-safe Prometheus and JSON operational metrics registry.
  - `get_metrics_registry()`: Global singleton accessor.

---

## 2. Installation (Editable Monorepo Mode)
```bash
pip install -e packages/shared/python
```
