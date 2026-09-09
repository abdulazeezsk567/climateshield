"""Shared constants, enumerations, and configuration placeholders for ClimateShield.

Note: In accordance with project security and compliance guidelines, financial
values and relief parameters are explicit placeholders intended to be driven
by configuration rather than hardcoded logic.
"""

from enum import Enum


class RiskTier(str, Enum):
    """Categorical risk tiers for climate vulnerability assessment."""
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class ClimateHazardType(str, Enum):
    """Supported climate and meteorological hazard classifications."""
    EXCESS_RAINFALL = "EXCESS_RAINFALL"
    DROUGHT_DEFICIT = "DROUGHT_DEFICIT"
    HEATWAVE_EXTREME = "HEATWAVE_EXTREME"
    CYCLONIC_WIND = "CYCLONIC_WIND"
    VEGETATION_STRESS = "VEGETATION_STRESS"


class TriggerActionType(str, Enum):
    """Supported parametric loan intervention policy actions."""
    EMI_DEFERRAL = "EMI_DEFERRAL"
    RECOVERY_TOPUP = "RECOVERY_TOPUP"
    TENURE_EXTENSION = "TENURE_EXTENSION"
    MANUAL_INSPECTION_HOLD = "MANUAL_INSPECTION_HOLD"


class LMSExecutionStatus(str, Enum):
    """Status flags for simulated LMS webhook executions."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SIMULATED_SUCCESS = "SIMULATED_SUCCESS"


class InterventionStatus(str, Enum):
    """Lifecycle progression states for automated climate-loan interventions."""
    TRIGGERED = "TRIGGERED"
    NOTIFIED = "NOTIFIED"
    APPLIED = "APPLIED"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AlertDeliveryStatus(str, Enum):
    """Delivery verification status for borrower notifications."""
    SIMULATED_DISPATCHED = "SIMULATED_DISPATCHED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


# Clearly labelled placeholders for finance-adjacent parameters:
# These must be configured via environment or LMS policy profiles in production.
DEFAULT_RELIEF_PERIOD_DAYS_PLACEHOLDER: int = 30
DEFAULT_TOPUP_PERCENTAGE_PLACEHOLDER: float = 0.10  # 10% of active principal placeholder
DEFAULT_INTEREST_MORATORIUM_RATE_PLACEHOLDER: float = 0.0  # Zero interest accrued during relief placeholder
