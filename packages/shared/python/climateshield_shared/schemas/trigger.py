"""Trigger and Risk Assessment contracts.

Defines schemas emitted by the Risk Engine and consumed by the API
and Integration layers to drive automated LMS actions.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from climateshield_shared.constants import (
    ClimateHazardType,
    LMSExecutionStatus,
    RiskTier,
    TriggerActionType,
)


class TriggerActionProposal(BaseModel):
    """Structured loan modification proposal emitted upon risk threshold crossing."""
    action_type: TriggerActionType = Field(..., description="Action policy to apply in LMS")
    relief_period_days: Optional[int] = Field(None, description="Proposed moratorium duration in days")
    topup_amount: Optional[float] = Field(None, ge=0.0, description="Proposed emergency liquidity top-up amount")
    reasoning: str = Field(..., description="Explainable rationale behind the policy proposal")
    policy_code: str = Field(..., description="Underlying NBFC credit policy identifier reference")


class RiskAssessment(BaseModel):
    """Comprehensive climate vulnerability evaluation for a borrower or cluster."""
    assessment_id: str = Field(..., description="Unique assessment record identifier")
    subject_id: str = Field(..., description="Target borrower ID or district ID")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Normalized composite risk index (0 to 100)")
    risk_tier: RiskTier = Field(..., description="Categorical risk classification")
    primary_hazard: ClimateHazardType = Field(..., description="Predominant driver of climate vulnerability")
    hazard_scores: Dict[str, float] = Field(default_factory=dict, description="Disaggregated hazard scores")
    ml_zoning_classification: Optional[str] = Field(None, description="ML microclimate zone cluster tag")
    assessed_at: datetime = Field(..., description="Timestamp of evaluation in UTC")
    model_version: str = Field(default="v1.0.0-scaffold", description="Risk model and ruleset version")


class TriggerEvent(BaseModel):
    """Authoritative event record when parametric thresholds are breached."""
    trigger_id: str = Field(..., description="Unique trigger event identifier")
    triggered_at: datetime = Field(..., description="Timestamp when parametric conditions were breached")
    district: str = Field(..., description="Administrative district affected")
    hazard_type: ClimateHazardType = Field(..., description="Active climate anomaly hazard type")
    severity: RiskTier = Field(..., description="Evaluated severity tier")
    affected_borrower_ids: List[str] = Field(default_factory=list, description="IDs of impacted portfolio borrowers")
    recommended_action: TriggerActionProposal = Field(..., description="Structured LMS action proposal")
    execution_status: LMSExecutionStatus = Field(
        default=LMSExecutionStatus.PENDING,
        description="Current execution lifecycle status",
    )
    audit_hash: Optional[str] = Field(None, description="Cryptographic SHA-256 hash linking to audit trail")


class BorrowerRiskOutput(BaseModel):
    """Combined risk evaluation output for an individual MSME borrower.

    Acts as a decision-support record synthesizing deterministic threshold
    evaluations with continuous probabilistic ML vulnerability zoning.
    """
    borrower_id: str = Field(..., description="Anonymized borrower unique identifier")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Estimated vulnerability score on a continuous 0-100 scale")
    trigger_fired: bool = Field(..., description="Whether a parametric policy threshold was crossed")
    trigger_reason: Optional[str] = Field(None, description="Clear explanatory rationale behind the trigger outcome")
    recommended_action: Optional[TriggerActionProposal] = Field(None, description="Proposed loan-support action if triggered")
    basis_risk_flags: List[str] = Field(default_factory=list, description="Quality and basis-risk caveat indicators")
    evaluated_at: datetime = Field(..., description="Timestamp of evaluation in UTC")
