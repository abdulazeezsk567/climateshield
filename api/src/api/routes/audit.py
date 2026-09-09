"""Audit log and tamper-evident ledger governance endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from climateshield_shared.schemas.audit import AuditEventType, AuditLogEntry
from api.core.dependencies import UserContext, get_integration, require_role
from api.core.pagination import PaginatedResponse, paginate_items
from integration_layer import IntegrationService

router = APIRouter(prefix="/audit", tags=["Audit & Governance Ledger"])


class AuditVerificationResponse(BaseModel):
    """Cryptographic hash chain verification report."""
    chain_valid: bool = Field(..., description="Whether all cryptographic SHA-256 links are intact")
    total_entries: int = Field(..., description="Count of evaluated ledger records")
    latest_hash: Optional[str] = Field(None, description="SHA-256 digest of the most recent audit entry")
    verified_at: datetime = Field(..., description="Timestamp of cryptographic verification")


@router.get(
    "/interventions",
    response_model=PaginatedResponse[AuditLogEntry],
    summary="List Intervention & Audit Trail (Paginated)",
    description="Returns chronological, tamper-evident audit ledger entries recording trigger activations, simulated LMS loan modifications, and borrower alerts.",
)
async def list_audit_interventions(
    event_type: Optional[AuditEventType] = Query(None, description="Filter by audit event category"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1 to 100)"),
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    integration: IntegrationService = Depends(get_integration),
) -> PaginatedResponse[AuditLogEntry]:
    """Retrieve paginated audit entries with optional event type filtering."""
    # Fetch recent entries (up to 1000)
    entries = await integration.list_audit_entries(limit=1000, event_type=event_type)
    return paginate_items(entries, page=page, page_size=page_size)


@router.get(
    "/verify",
    response_model=AuditVerificationResponse,
    summary="Verify Audit Ledger Cryptographic Integrity",
    description="Traverses the append-only audit trail and recomputes SHA-256 parent hash links from genesis to ensure zero unauthorized modifications or tampering.",
)
async def verify_audit_ledger_chain(
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    integration: IntegrationService = Depends(get_integration),
) -> AuditVerificationResponse:
    """Perform on-demand cryptographic audit chain verification."""
    result = await integration.verify_audit_ledger()
    return AuditVerificationResponse(
        chain_valid=result["chain_valid"],
        total_entries=result["total_entries"],
        latest_hash=result["latest_hash"],
        verified_at=datetime.fromisoformat(result["verified_at"]),
    )
