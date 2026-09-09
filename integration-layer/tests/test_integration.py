"""Unit and integration tests for the ClimateShield Action & Integration Layer."""

import asyncio
from datetime import datetime, timezone
import json
import pytest

from climateshield_shared.constants import (
    AlertDeliveryStatus,
    ClimateHazardType,
    InterventionStatus,
    LMSExecutionStatus,
    TriggerActionType,
)
from climateshield_shared.schemas.audit import AuditEventType
from climateshield_shared.schemas.trigger import TriggerActionProposal, TriggerEvent
from integration_layer.alerts.interfaces import AlertChannel, AlertMessagePayload
from integration_layer.alerts.service import (
    SimulatedBorrowerAlertService,
    format_climate_relief_advisory,
)
from integration_layer.audit.store import InMemoryAuditLogStore
from integration_layer.lms_webhook.client import (
    SimulatedLMSAdapter,
    get_lms_adapter,
)
from integration_layer.lms_webhook.interfaces import (
    LMSActionPayload,
    LMSCallbackPayload,
)
from integration_layer.service import IntegrationService, get_integration_service
from integration_layer.state_machine import (
    InterventionNotFoundError,
    InterventionStateMachine,
    InvalidInterventionStateTransitionError,
)


# =============================================================================
# 1. INTERVENTION LIFECYCLE STATE MACHINE TESTS
# =============================================================================

def test_state_machine_valid_lifecycle_progression():
    """Verify standard happy-path progression: TRIGGERED -> NOTIFIED -> APPLIED -> CONFIRMED."""
    sm = InterventionStateMachine()
    proposal = TriggerActionProposal(
        action_type=TriggerActionType.EMI_DEFERRAL,
        relief_period_days=60,
        topup_amount=None,
        reasoning="Parametric severe drought detected",
        policy_code="POL-CLIMATE-DROUGHT-01",
    )

    # 1. TRIGGERED
    record = sm.create_intervention(
        correlation_id="TRIG-TEST-01",
        borrower_id="B-001",
        loan_id="LN-001",
        proposal=proposal,
        actor="RISK_ENGINE",
    )
    assert record.current_status == InterventionStatus.TRIGGERED
    assert len(record.history) == 1
    assert record.history[0].to_status == InterventionStatus.TRIGGERED

    # 2. NOTIFIED
    record = sm.transition_status(
        intervention_id=record.intervention_id,
        target_status=InterventionStatus.NOTIFIED,
        actor="SYSTEM_AUTOMATION",
        notes="SMS advisory dispatched to borrower",
    )
    assert record.current_status == InterventionStatus.NOTIFIED
    assert len(record.history) == 2

    # 3. APPLIED
    record = sm.transition_status(
        intervention_id=record.intervention_id,
        target_status=InterventionStatus.APPLIED,
        actor="SYSTEM_AUTOMATION",
        lms_transaction_id="LMS-TXN-12345",
        notes="Modification dispatched to LMS",
    )
    assert record.current_status == InterventionStatus.APPLIED
    assert record.lms_transaction_id == "LMS-TXN-12345"
    assert len(record.history) == 3

    # 4. CONFIRMED
    record = sm.transition_status(
        intervention_id=record.intervention_id,
        target_status=InterventionStatus.CONFIRMED,
        actor="LMS_CALLBACK",
        notes="LMS disbursement verified",
    )
    assert record.current_status == InterventionStatus.CONFIRMED
    assert len(record.history) == 4


def test_state_machine_illegal_transition_rejection():
    """Verify that jumping stages or transitioning from terminal state raises error."""
    sm = InterventionStateMachine()
    proposal = TriggerActionProposal(
        action_type=TriggerActionType.EMI_DEFERRAL,
        relief_period_days=30,
        topup_amount=None,
        reasoning="Excess rainfall",
        policy_code="POL-CLIMATE-RAIN-01",
    )

    record = sm.create_intervention(
        correlation_id="TRIG-TEST-02",
        borrower_id="B-002",
        loan_id="LN-002",
        proposal=proposal,
    )

    # Illegal transition: cannot jump directly from TRIGGERED to CONFIRMED
    with pytest.raises(InvalidInterventionStateTransitionError) as exc_info:
        sm.transition_status(
            intervention_id=record.intervention_id,
            target_status=InterventionStatus.CONFIRMED,
        )
    assert "Cannot transition from 'TRIGGERED' to 'CONFIRMED'" in str(exc_info.value)

    # Transition to APPLIED -> CONFIRMED
    sm.transition_status(record.intervention_id, InterventionStatus.APPLIED)
    sm.transition_status(record.intervention_id, InterventionStatus.CONFIRMED)

    # Cannot transition out of terminal state CONFIRMED
    with pytest.raises(InvalidInterventionStateTransitionError):
        sm.transition_status(record.intervention_id, InterventionStatus.TRIGGERED)


def test_state_machine_not_found_error():
    """Verify querying non-existent intervention raises InterventionNotFoundError."""
    sm = InterventionStateMachine()
    with pytest.raises(InterventionNotFoundError):
        sm.get_intervention("INTV-DOES-NOT-EXIST")


# =============================================================================
# 2. LMS WEBHOOK ADAPTER & HMAC SIGNATURE TESTS
# =============================================================================

def test_lms_adapter_hmac_signature_verification():
    """Verify cryptographic HMAC-SHA256 signature computation and constant-time verification."""
    adapter = SimulatedLMSAdapter(secret_key="test-secret-key-123")
    payload = b'{"loan_id": "LN-001", "status": "ACCEPTED"}'

    signature = adapter.compute_signature(payload)
    assert len(signature) == 64  # SHA-256 hex digest length

    # Valid signature check
    assert adapter.verify_webhook_signature(payload, signature) is True

    # Tampered signature check
    assert adapter.verify_webhook_signature(payload, "bad_signature_0000000000000000000000000000000000000000000000000000") is False

    # Tampered body check
    assert adapter.verify_webhook_signature(b'{"loan_id": "LN-002"}', signature) is False


def test_simulated_lms_dispatch_zero_fabrication():
    """Verify simulated LMS dispatch explicitly labels action as simulated."""
    adapter = SimulatedLMSAdapter()
    payload = LMSActionPayload(
        idempotency_key="IDEM-LN-001-001",
        loan_id="LN-001",
        borrower_id="B-001",
        action_type=TriggerActionType.EMI_DEFERRAL,
        relief_period_days=45,
        topup_amount=None,
        trigger_event_id="TRIG-001",
        timestamp=datetime.now(timezone.utc),
    )

    async def _run():
        response = await adapter.dispatch_intervention(payload)
        assert response.status == LMSExecutionStatus.SIMULATED_SUCCESS
        assert response.is_simulated is True
        assert "[SIMULATED_LMS]" in response.message
        assert response.transaction_id.startswith("LMS-TXN-")

    asyncio.run(_run())


# =============================================================================
# 3. BORROWER ALERT SERVICE TESTS
# =============================================================================

def test_borrower_alert_bilingual_template_generation():
    """Verify bilingual copy generation for Hindi and English notifications."""
    hindi_sms, hindi_subj, hindi_body = format_climate_relief_advisory(
        borrower_id="B-001",
        loan_id="LN-001",
        district="GORAKHPUR",
        hazard_type="DROUGHT_DEFICIT",
        action_type="EMI_DEFERRAL",
        relief_period_days=60,
        language_code="hi",
    )
    assert "सैटिन फिनसर्व सहायता" in hindi_sms
    assert "गोरखपुर" not in hindi_sms  # English district name maintained for consistency
    assert "60 दिनों के लिए ईएमआई राहत" in hindi_sms
    assert "Zero Penalty" in hindi_body or "शून्य" in hindi_body

    eng_sms, eng_subj, eng_body = format_climate_relief_advisory(
        borrower_id="B-001",
        loan_id="LN-001",
        district="GORAKHPUR",
        hazard_type="DROUGHT_DEFICIT",
        action_type="EMI_DEFERRAL",
        relief_period_days=60,
        language_code="en",
    )
    assert "[Satin Finserv Advisory]" in eng_sms
    assert "moratorium of 60 days" in eng_sms
    assert "Zero penalty applies" in eng_sms


def test_borrower_alert_service_simulated_dispatch():
    """Verify demo mode alert service explicitly marks output as SIMULATED_DISPATCHED."""
    alert_service = SimulatedBorrowerAlertService()
    payload = AlertMessagePayload(
        alert_id="ALT-TEST-01",
        borrower_id="B-001",
        channel=AlertChannel.SMS,
        localized_message_text="Test climate relief alert",
        language_code="hi",
        dispatched_at=datetime.now(timezone.utc),
    )

    async def _run():
        result = await alert_service.send_alert(payload)
        assert result.delivery_status == AlertDeliveryStatus.SIMULATED_DISPATCHED
        assert result.is_simulated is True
        assert result.borrower_id == "B-001"
        assert len(alert_service.dispatched_alerts) == 1

    asyncio.run(_run())


# =============================================================================
# 4. CRYPTOGRAPHIC AUDIT LOG & CORRELATION ID TESTS
# =============================================================================

def test_audit_store_correlation_id_linking():
    """Verify audit log records carry correlation IDs tying back to the originating trigger."""
    store = InMemoryAuditLogStore()

    async def _run():
        entry1 = await store.append_entry(
            event_type=AuditEventType.TRIGGER_FIRED,
            origin_service="risk-engine",
            actor="SYSTEM",
            correlation_id="TRIG-CORR-100",
            payload_snapshot={"district": "GORAKHPUR"},
        )
        assert entry1.correlation_id == "TRIG-CORR-100"
        assert entry1.previous_hash == "0" * 64

        entry2 = await store.append_entry(
            event_type=AuditEventType.LMS_WEBHOOK_DISPATCHED,
            origin_service="integration-layer",
            actor="user:officer_sfl",
            correlation_id="TRIG-CORR-100",
            payload_snapshot={"loan_id": "LN-001"},
        )
        assert entry2.correlation_id == "TRIG-CORR-100"
        assert entry2.previous_hash == entry1.event_hash

        # Cryptographic chain verification
        is_valid = await store.verify_chain_integrity()
        assert is_valid is True

        # Query by correlation_id
        corr_entries = await store.list_recent_entries(correlation_id="TRIG-CORR-100")
        assert len(corr_entries) == 2

    asyncio.run(_run())


def test_audit_store_tamper_detection_breaks_chain():
    """Verify tampering with a stored payload invalidates cryptographic SHA-256 chain."""
    store = InMemoryAuditLogStore()

    async def _run():
        await store.append_entry(
            event_type=AuditEventType.TRIGGER_FIRED,
            origin_service="risk-engine",
            actor="SYSTEM",
            payload_snapshot={"initial": "data"},
        )
        await store.append_entry(
            event_type=AuditEventType.LMS_WEBHOOK_DISPATCHED,
            origin_service="integration-layer",
            actor="user:officer_sfl",
            payload_snapshot={"loan_id": "LN-001"},
        )

        # Confirm chain initially valid
        assert await store.verify_chain_integrity() is True

        # Maliciously mutate stored payload in memory
        store._entries[0].payload_snapshot["initial"] = "TAMPERED_FRAUDULENT_DATA"

        # Verification must now fail
        assert await store.verify_chain_integrity() is False

    asyncio.run(_run())


# =============================================================================
# 5. INTEGRATION SERVICE FACADE TESTS
# =============================================================================

def test_integration_service_full_intervention_flow():
    """Verify IntegrationService coordinates full 4-stage lifecycle and records audit trail."""
    service = IntegrationService()
    proposal = TriggerActionProposal(
        action_type=TriggerActionType.EMI_DEFERRAL,
        relief_period_days=90,
        topup_amount=None,
        reasoning="Severe heatwave shock",
        policy_code="POL-CLIMATE-HEAT-01",
    )

    async def _run():
        record = await service.execute_full_intervention_flow(
            trigger_id="TRIG-FLOW-01",
            borrower_id="B-001",
            loan_id="LN-001",
            proposal=proposal,
            actor="user:officer_sfl",
            district="GORAKHPUR",
            hazard_type="HEATWAVE_EXTREME",
        )

        assert record.current_status == InterventionStatus.CONFIRMED
        assert record.correlation_id == "TRIG-FLOW-01"
        assert record.lms_transaction_id is not None
        assert len(record.history) == 4

        # Verify audit ledger has all entries chained with correlation ID
        report = await service.verify_audit_ledger()
        assert report["chain_valid"] is True
        assert report["total_entries"] >= 4

        # Query intervention
        fetched = service.get_intervention(record.intervention_id)
        assert fetched.intervention_id == record.intervention_id

        # List interventions
        all_interventions = service.list_interventions(status=InterventionStatus.CONFIRMED)
        assert len(all_interventions) >= 1

    asyncio.run(_run())


def test_inbound_lms_webhook_callback():
    """Verify receiving signed inbound LMS webhook updates intervention state."""
    service = IntegrationService()
    proposal = TriggerActionProposal(
        action_type=TriggerActionType.RECOVERY_TOPUP,
        relief_period_days=None,
        topup_amount=50000.0,
        reasoning="Flood recovery top-up",
        policy_code="POL-CLIMATE-FLOOD-01",
    )

    async def _run():
        # Create intervention and advance to APPLIED
        record = await service.create_intervention(
            trigger_id="TRIG-CALLBACK-01",
            borrower_id="B-002",
            loan_id="LN-002",
            proposal=proposal,
        )
        await service.notify_borrower(record.intervention_id)
        await service.apply_lms_intervention(record.intervention_id)

        # Emulate LMS callback payload
        callback_payload = LMSCallbackPayload(
            callback_id="CB-001",
            intervention_id=record.intervention_id,
            loan_id="LN-002",
            lms_transaction_id="LMS-TXN-REAL-999",
            status=LMSExecutionStatus.ACCEPTED,
            effective_date=datetime.now(timezone.utc),
            notes="Liquidity credit successfully credited to MSME account",
        )
        raw_body = callback_payload.model_dump_json().encode("utf-8")
        signature = service._lms_client.compute_signature(raw_body)

        # Process callback
        updated = await service.handle_incoming_lms_webhook(
            payload_bytes=raw_body,
            signature_header=signature,
            callback_data=callback_payload,
        )

        assert updated.current_status == InterventionStatus.CONFIRMED
        assert updated.lms_transaction_id == "LMS-TXN-REAL-999"

    asyncio.run(_run())
