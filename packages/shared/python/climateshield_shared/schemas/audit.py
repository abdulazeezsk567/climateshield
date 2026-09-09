"""Immutable Audit Trail contracts.

Defines append-only, tamper-evident audit log schemas capturing every
risk assessment, LMS webhook call, and borrower notification.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AuditEventType(str, Enum):
    """Categorization of audit log trail entries."""
    DATA_INGESTION_COMPLETED = "DATA_INGESTION_COMPLETED"
    TRIGGER_FIRED = "TRIGGER_FIRED"
    INTERVENTION_STATE_TRANSITION = "INTERVENTION_STATE_TRANSITION"
    LMS_WEBHOOK_DISPATCHED = "LMS_WEBHOOK_DISPATCHED"
    LMS_WEBHOOK_RECEIVED = "LMS_WEBHOOK_RECEIVED"
    LMS_RESPONSE_RECORDED = "LMS_RESPONSE_RECORDED"
    LMS_CALLBACK_VERIFIED = "LMS_CALLBACK_VERIFIED"
    BORROWER_ALERT_SENT = "BORROWER_ALERT_SENT"
    MANUAL_OVERRIDE_APPLIED = "MANUAL_OVERRIDE_APPLIED"


class AuditLogEntry(BaseModel):
    """Tamper-evident audit log record with cryptographic chaining attributes."""
    audit_id: str = Field(..., description="Unique immutable audit record UUID")
    correlation_id: Optional[str] = Field(None, description="Correlation ID tying action back to originating trigger or workflow")
    timestamp: datetime = Field(..., description="UTC timestamp of the audited operation")
    event_type: AuditEventType = Field(..., description="Action or event classification")
    origin_service: str = Field(..., description="Component responsible for generating the entry")
    actor: str = Field(default="SYSTEM", description="Acting user ID, API service token, or SYSTEM")
    payload_snapshot: Dict[str, Any] = Field(..., description="JSON snapshot of event metadata or transaction payload")
    event_hash: str = Field(..., description="SHA-256 cryptographic digest of record content")
    previous_hash: Optional[str] = Field(None, description="SHA-256 hash of preceding audit entry for ledger chaining")
