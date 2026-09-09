"""ClimateShield Shared Domain Contracts and Schemas.

This package exposes authoritative entity schemas, enums, and constants
utilized across all ClimateShield backend services.
"""

from climateshield_shared.constants import (
    DEFAULT_RELIEF_PERIOD_DAYS_PLACEHOLDER,
    DEFAULT_TOPUP_PERCENTAGE_PLACEHOLDER,
    RiskTier,
    ClimateHazardType,
    TriggerActionType,
    LMSExecutionStatus,
    InterventionStatus,
    AlertDeliveryStatus,
)
from climateshield_shared.schemas.borrower import (
    Borrower,
    BorrowerSector,
    GeoLocation,
    LoanSummary,
)
from climateshield_shared.schemas.climate import (
    ClimateEvent,
    ClimateObservation,
    DataSourceType,
)
from climateshield_shared.schemas.trigger import (
    TriggerEvent,
    TriggerActionProposal,
    RiskAssessment,
    BorrowerRiskOutput,
)
from climateshield_shared.schemas.audit import (
    AuditLogEntry,
    AuditEventType,
)
from climateshield_shared.telemetry import (
    StructuredJsonFormatter,
    configure_logging,
    MetricsRegistry,
    get_metrics_registry,
)

__all__ = [
    "DEFAULT_RELIEF_PERIOD_DAYS_PLACEHOLDER",
    "DEFAULT_TOPUP_PERCENTAGE_PLACEHOLDER",
    "RiskTier",
    "ClimateHazardType",
    "TriggerActionType",
    "LMSExecutionStatus",
    "InterventionStatus",
    "AlertDeliveryStatus",
    "Borrower",
    "BorrowerSector",
    "GeoLocation",
    "LoanSummary",
    "ClimateEvent",
    "ClimateObservation",
    "DataSourceType",
    "TriggerEvent",
    "TriggerActionProposal",
    "RiskAssessment",
    "BorrowerRiskOutput",
    "AuditLogEntry",
    "AuditEventType",
    "StructuredJsonFormatter",
    "configure_logging",
    "MetricsRegistry",
    "get_metrics_registry",
]
