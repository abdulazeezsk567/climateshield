"""API route tests for loan interventions and inbound LMS webhook receiver."""

from datetime import datetime, timezone
import json
import pytest
from fastapi.testclient import TestClient

from api.core.rate_limiter import rate_limiter
from api.core.security import create_access_token
from api.main import app
from integration_layer import get_integration_service
from integration_layer.lms_webhook.interfaces import LMSCallbackPayload
from climateshield_shared.constants import (
    InterventionStatus,
    LMSExecutionStatus,
    TriggerActionType,
)
from climateshield_shared.schemas.trigger import TriggerActionProposal

_AUTH_TOKEN = create_access_token(subject="officer_sfl", role="credit_team")
client = TestClient(app, headers={"Authorization": f"Bearer {_AUTH_TOKEN}"})


@pytest.fixture(autouse=True)
def reset_rate_limiter_fixture():
    """Reset rate limiter state before each test."""
    rate_limiter.reset()
    yield
    rate_limiter.reset()


def test_interventions_api_query_and_detail():
    """Verify listing and detail retrieval of loan interventions via API."""
    integ = get_integration_service()

    # Pre-seed an intervention via service
    proposal = TriggerActionProposal(
        action_type=TriggerActionType.EMI_DEFERRAL,
        relief_period_days=30,
        topup_amount=None,
        reasoning="Test rainfall shock",
        policy_code="POL-CLIMATE-01",
    )
    import asyncio
    record = asyncio.run(
        integ.execute_full_intervention_flow(
            trigger_id="TRIG-API-TEST-01",
            borrower_id="B-001",
            loan_id="LN-TEST-001",
            proposal=proposal,
            actor="user:officer_sfl",
        )
    )

    # 1. Query list
    response = client.get("/api/v1/interventions?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert data["total_items"] >= 1
    found = next((item for item in data["items"] if item["intervention_id"] == record.intervention_id), None)
    assert found is not None
    assert found["current_status"] == InterventionStatus.CONFIRMED.value

    # 2. Query detail
    detail_resp = client.get(f"/api/v1/interventions/{record.intervention_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()

    assert detail["intervention_id"] == record.intervention_id
    assert detail["loan_id"] == "LN-TEST-001"
    assert len(detail["history"]) >= 4


def test_intervention_not_found_returns_404():
    """Verify non-existent intervention ID returns structured 404 error."""
    response = client.get("/api/v1/interventions/INTV-NONEXISTENT")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == "INTERVENTION_NOT_FOUND"


def test_lms_webhook_missing_signature_rejected():
    """Verify LMS webhook endpoint rejects requests missing HMAC signature with 401."""
    payload = {"callback_id": "CB-001"}
    response = client.post("/api/v1/lms/webhook", json=payload)
    assert response.status_code == 401
    assert "Missing required 'X-ClimateShield-Signature'" in response.json()["error"]["message"]


def test_lms_webhook_invalid_signature_rejected():
    """Verify LMS webhook endpoint rejects requests with invalid HMAC signature with 401."""
    callback = LMSCallbackPayload(
        callback_id="CB-002",
        intervention_id="INTV-001",
        loan_id="LN-001",
        lms_transaction_id="LMS-TXN-001",
        status=LMSExecutionStatus.ACCEPTED,
        effective_date=datetime.now(timezone.utc),
        notes="Test note",
    )
    raw_body = callback.model_dump_json()

    response = client.post(
        "/api/v1/lms/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ClimateShield-Signature": "invalid_hmac_hex_000000000000000000000000000000000000000000000000",
        },
    )
    assert response.status_code == 401
    assert "Invalid HMAC-SHA256 signature" in response.json()["error"]["message"]


def test_lms_webhook_valid_signature_success():
    """Verify LMS webhook processes callback when valid HMAC signature is provided."""
    integ = get_integration_service()

    # Create an intervention and advance to APPLIED
    proposal = TriggerActionProposal(
        action_type=TriggerActionType.EMI_DEFERRAL,
        relief_period_days=30,
        topup_amount=None,
        reasoning="Test drought",
        policy_code="POL-CLIMATE-01",
    )
    import asyncio
    record = asyncio.run(
        integ.create_intervention(
            trigger_id="TRIG-WEBHOOK-TEST",
            borrower_id="B-005",
            loan_id="LN-005",
            proposal=proposal,
        )
    )
    asyncio.run(integ.notify_borrower(record.intervention_id))
    asyncio.run(integ.apply_lms_intervention(record.intervention_id))

    # Formulate valid callback payload and sign it
    callback = LMSCallbackPayload(
        callback_id="CB-999",
        intervention_id=record.intervention_id,
        loan_id="LN-005",
        lms_transaction_id="LMS-CONFIRM-9999",
        status=LMSExecutionStatus.ACCEPTED,
        effective_date=datetime.now(timezone.utc),
        notes="All loan terms applied successfully",
    )
    raw_body = callback.model_dump_json().encode("utf-8")
    valid_signature = integ._lms_client.compute_signature(raw_body)

    response = client.post(
        "/api/v1/lms/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-ClimateShield-Signature": valid_signature,
        },
    )
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "PROCESSED"
    assert data["intervention_id"] == record.intervention_id
    assert data["current_status"] == InterventionStatus.CONFIRMED.value
    assert data["lms_transaction_id"] == "LMS-CONFIRM-9999"
