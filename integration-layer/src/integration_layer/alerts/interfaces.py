"""Abstract interface for borrower multi-channel climate relief notifications."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from climateshield_shared.constants import AlertDeliveryStatus


class AlertChannel(str, Enum):
    """Supported communication channels."""
    SMS = "SMS"
    WHATSAPP = "WHATSAPP"
    EMAIL = "EMAIL"
    INTERNAL_NOTIFICATION = "INTERNAL_NOTIFICATION"


class AlertMessagePayload(BaseModel):
    """Notification payload destined for an affected MSME borrower."""
    alert_id: str = Field(..., description="Unique notification identifier")
    borrower_id: str = Field(..., description="Target MSME borrower identifier")
    channel: AlertChannel = Field(default=AlertChannel.SMS, description="Delivery channel")
    localized_message_text: str = Field(..., description="Concise SMS/WhatsApp notification text")
    email_subject: Optional[str] = Field(None, description="Formal subject line for email/app notices")
    email_body_text: Optional[str] = Field(None, description="Detailed text body explaining policy relief terms")
    language_code: str = Field(default="hi", description="ISO 639-1 language code (e.g. 'hi' for Hindi, 'en' for English)")
    dispatched_at: datetime = Field(..., description="Dispatch timestamp in UTC")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Contextual metadata (loan_id, hazard_type, etc.)")


class AlertDispatchResult(BaseModel):
    """Result returned by the notification dispatcher."""
    alert_id: str = Field(..., description="Notification identifier")
    borrower_id: str = Field(..., description="Target borrower identifier")
    delivery_status: AlertDeliveryStatus = Field(
        default=AlertDeliveryStatus.SIMULATED_DISPATCHED,
        description="Delivery verdict: SIMULATED_DISPATCHED, DELIVERED, or FAILED",
    )
    channel: AlertChannel = Field(..., description="Channel utilized")
    is_simulated: bool = Field(default=True, description="Strict indicator that no real external SMS/email was dispatched")
    dispatched_at: datetime = Field(..., description="Timestamp of dispatch attempt in UTC")
    preview_text: str = Field(..., description="Rendered advisory message preview")
    provider_ref: Optional[str] = Field(None, description="Provider transaction reference (if real provider used)")


class BorrowerAlertService(ABC):
    """Protocol for sending proactive climate relief notifications."""

    @abstractmethod
    async def send_alert(
        self,
        payload: AlertMessagePayload,
    ) -> AlertDispatchResult:
        """Send proactive climate relief notification to an impacted borrower.

        Args:
            payload: Standardized AlertMessagePayload.

        Returns:
            AlertDispatchResult containing delivery status and simulation markers.
        """
        pass
