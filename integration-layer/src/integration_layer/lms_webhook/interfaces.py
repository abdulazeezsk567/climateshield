"""Abstract interface for LMS webhook interactions and pluggable adapters."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from climateshield_shared.constants import LMSExecutionStatus, TriggerActionType


class LMSActionPayload(BaseModel):
    """Outbound payload sent to the Loan Management System (LMS)."""
    idempotency_key: str = Field(..., description="Unique idempotency key for this loan adjustment")
    intervention_id: Optional[str] = Field(None, description="ClimateShield intervention identifier reference")
    loan_id: str = Field(..., description="Target LMS loan account number")
    borrower_id: str = Field(..., description="Target borrower ID")
    action_type: TriggerActionType = Field(..., description="Intervention policy action requested")
    relief_period_days: Optional[int] = Field(None, description="Moratorium period in days")
    topup_amount: Optional[float] = Field(None, ge=0.0, description="Approved liquidity amount in INR")
    trigger_event_id: str = Field(..., description="Reference trigger event ID")
    timestamp: datetime = Field(..., description="Dispatch timestamp in UTC")


class LMSActionResponse(BaseModel):
    """Immediate synchronous response from the Loan Management System."""
    transaction_id: str = Field(..., description="LMS-issued transaction confirmation ID")
    status: LMSExecutionStatus = Field(..., description="Execution status: SIMULATED_SUCCESS, ACCEPTED, or REJECTED")
    message: str = Field(..., description="Status description or policy audit notes")
    processed_at: datetime = Field(..., description="Processing timestamp in UTC")
    is_simulated: bool = Field(default=True, description="Explicit flag indicating mock/simulation mode")


class LMSCallbackPayload(BaseModel):
    """Inbound asynchronous webhook confirmation payload received from the LMS."""
    callback_id: str = Field(..., description="Unique callback event identifier")
    intervention_id: str = Field(..., description="ClimateShield intervention identifier")
    loan_id: str = Field(..., description="Target LMS loan account number")
    lms_transaction_id: str = Field(..., description="LMS internal transaction identifier")
    status: LMSExecutionStatus = Field(..., description="Final processing verdict from LMS")
    effective_date: datetime = Field(..., description="Date loan modification takes financial effect")
    notes: Optional[str] = Field(None, description="Underwriting or disbursement notes from LMS")


class LMSAdapter(ABC):
    """Protocol defining outbound and inbound LMS communications.

    Allows seamless swapping between SimulatedLMSAdapter (for demo/testing)
    and HttpLMSAdapter (for production Satin Finnone integration).
    """

    @abstractmethod
    async def dispatch_intervention(
        self,
        payload: LMSActionPayload,
    ) -> LMSActionResponse:
        """Dispatch signed loan relief action payload to LMS.

        Args:
            payload: Standardized LMSActionPayload.

        Returns:
            LMSActionResponse from the core banking platform.
        """
        pass

    @abstractmethod
    def compute_signature(self, payload_bytes: bytes) -> str:
        """Compute cryptographic HMAC-SHA256 signature for payload verification."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        payload_bytes: bytes,
        signature: str,
    ) -> bool:
        """Verify authenticity of an inbound LMS webhook callback.

        Args:
            payload_bytes: Raw HTTP request body bytes.
            signature: Hex-encoded HMAC signature from request header.

        Returns:
            True if signature matches, False otherwise.
        """
        pass


# Backwards-compatible alias for existing imports
LMSWebhookClient = LMSAdapter
