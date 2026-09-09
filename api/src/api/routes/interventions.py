"""Intervention state machine and LMS webhook receiver endpoints."""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Request, status

from climateshield_shared.constants import InterventionStatus
from api.core.dependencies import (
    UserContext,
    get_integration,
    require_role,
)
from api.core.pagination import PaginatedResponse, paginate_items
from integration_layer import (
    IntegrationService,
    LMSCallbackPayload,
    LoanInterventionRecord,
)

logger = logging.getLogger("api.interventions")

router = APIRouter(prefix="/interventions", tags=["Intervention State Machine & LMS"])


@router.get(
    "",
    response_model=PaginatedResponse[LoanInterventionRecord],
    summary="List Loan Interventions (Paginated)",
    description="Returns paginated MSME loan interventions tracking current lifecycle state (TRIGGERED -> NOTIFIED -> APPLIED -> CONFIRMED).",
)
async def list_interventions(
    status_filter: Optional[InterventionStatus] = Query(None, alias="status", description="Filter by lifecycle status"),
    borrower_id: Optional[str] = Query(None, description="Filter by MSME borrower ID"),
    loan_id: Optional[str] = Query(None, description="Filter by LMS loan account ID"),
    correlation_id: Optional[str] = Query(None, description="Filter by originating trigger correlation ID"),
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1 to 100)"),
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    integration: IntegrationService = Depends(get_integration),
) -> PaginatedResponse[LoanInterventionRecord]:
    """Query intervention lifecycle records with multi-attribute filtering."""
    records = integration.list_interventions(
        borrower_id=borrower_id,
        loan_id=loan_id,
        status=status_filter,
        correlation_id=correlation_id,
        limit=1000,
    )
    return paginate_items(records, page=page, page_size=page_size)


@router.get(
    "/{intervention_id}",
    response_model=LoanInterventionRecord,
    summary="Get Intervention Lifecycle Details",
    description="Retrieve full audit history, policy parameters, and current status for a specific loan intervention.",
)
async def get_intervention_detail(
    intervention_id: str = Path(..., pattern=r"^[A-Za-z0-9_-]{3,50}$", description="Unique intervention ID"),
    current_user: UserContext = Depends(require_role("credit_team", "viewer")),
    integration: IntegrationService = Depends(get_integration),
) -> LoanInterventionRecord:
    """Fetch complete lifecycle scorecard for a single intervention."""
    return integration.get_intervention(intervention_id)


# LMS Webhook Receiver Route mounted at /lms/webhook
lms_webhook_router = APIRouter(prefix="/lms", tags=["LMS Webhook Receiver"])


@lms_webhook_router.post(
    "/webhook",
    summary="LMS Inbound Webhook Receiver",
    description="Receives asynchronous status callbacks and disbursement receipts from the core LMS, verifying HMAC-SHA256 signatures before updating intervention state to CONFIRMED or FAILED.",
)
async def receive_lms_webhook(
    request: Request,
    signature: Optional[str] = Header(None, alias="X-ClimateShield-Signature", description="HMAC-SHA256 signature"),
    integration: IntegrationService = Depends(get_integration),
):
    """Process inbound asynchronous LMS webhook with cryptographic verification."""
    raw_body = await request.body()

    if not signature:
        logger.warning("[SECURITY] Inbound LMS webhook rejected: Missing X-ClimateShield-Signature header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required 'X-ClimateShield-Signature' header.",
        )

    try:
        import json
        body_dict = json.loads(raw_body.decode("utf-8"))
        callback_data = LMSCallbackPayload(**body_dict)
    except Exception as exc:
        logger.warning("[SECURITY] Inbound LMS webhook payload parse error: %s", str(exc))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed LMS callback payload: {str(exc)}",
        )

    try:
        updated_record = await integration.handle_incoming_lms_webhook(
            payload_bytes=raw_body,
            signature_header=signature,
            callback_data=callback_data,
            actor="LMS_WEBHOOK_CALLBACK",
        )
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(val_err),
        )

    return {
        "status": "PROCESSED",
        "intervention_id": updated_record.intervention_id,
        "current_status": updated_record.current_status.value,
        "lms_transaction_id": updated_record.lms_transaction_id,
    }
