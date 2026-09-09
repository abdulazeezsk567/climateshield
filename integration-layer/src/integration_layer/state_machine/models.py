"""Domain models for the climate loan intervention lifecycle state machine."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field

from climateshield_shared.constants import InterventionStatus
from climateshield_shared.schemas.trigger import TriggerActionProposal


class InterventionStateTransition(BaseModel):
    """Immutable audit record of a specific lifecycle state transition."""
    transition_id: str = Field(default_factory=lambda: f"TRN-{uuid.uuid4().hex[:8].upper()}")
    from_status: Optional[InterventionStatus] = Field(None, description="Pre-transition status (None if initial)")
    to_status: InterventionStatus = Field(..., description="Post-transition status")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of state transition",
    )
    actor: str = Field(default="SYSTEM", description="Acting user ID, API service, or automated rule engine")
    notes: Optional[str] = Field(None, description="Contextual notes or rationale for the transition")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution payload or response data")


class LoanInterventionRecord(BaseModel):
    """Authoritative lifecycle entity representing a climate relief intervention on an MSME loan."""
    intervention_id: str = Field(..., description="Unique intervention identifier (e.g. INTV-...)")
    correlation_id: str = Field(..., description="Correlation ID tying intervention to originating trigger event")
    borrower_id: str = Field(..., description="Target MSME borrower identifier")
    loan_id: str = Field(..., description="Target LMS loan account number")
    current_status: InterventionStatus = Field(
        default=InterventionStatus.TRIGGERED,
        description="Current lifecycle stage: TRIGGERED -> NOTIFIED -> APPLIED -> CONFIRMED",
    )
    action_proposal: TriggerActionProposal = Field(..., description="Structured parametric loan adjustment proposal")
    lms_transaction_id: Optional[str] = Field(None, description="LMS-issued execution confirmation receipt ID")
    history: List[InterventionStateTransition] = Field(
        default_factory=list,
        description="Chronological audit history of all state transitions",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Initial creation timestamp in UTC",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last status modification timestamp in UTC",
    )
