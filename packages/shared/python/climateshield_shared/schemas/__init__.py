"""Pydantic V2 Domain Schemas for ClimateShield."""

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

__all__ = [
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
]
