"""Public Service Facade for ClimateShield Action & Integration Layer."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from climateshield_shared.constants import (
    AlertDeliveryStatus,
    InterventionStatus,
    LMSExecutionStatus,
)
from climateshield_shared.schemas.audit import AuditEventType, AuditLogEntry
from climateshield_shared.schemas.trigger import TriggerActionProposal, TriggerEvent
from integration_layer.alerts.interfaces import (
    AlertChannel,
    AlertDispatchResult,
    AlertMessagePayload,
    BorrowerAlertService,
)
from integration_layer.alerts.service import (
    SimulatedBorrowerAlertService,
    format_climate_relief_advisory,
)
from integration_layer.audit.interfaces import AuditLogStore
from integration_layer.audit.store import InMemoryAuditLogStore
from integration_layer.lms_webhook.client import (
    SimulatedLMSAdapter,
    get_lms_adapter,
)
from integration_layer.lms_webhook.interfaces import (
    LMSActionPayload,
    LMSActionResponse,
    LMSAdapter,
    LMSCallbackPayload,
)
from integration_layer.state_machine.machine import InterventionStateMachine
from integration_layer.state_machine.models import LoanInterventionRecord

logger = logging.getLogger("integration.service")


class IntegrationService:
    """Authoritative orchestrator for loan interventions, LMS webhooks, borrower alerts, and audit trails."""

    def __init__(
        self,
        audit_store: Optional[AuditLogStore] = None,
        lms_client: Optional[LMSAdapter] = None,
        alert_service: Optional[BorrowerAlertService] = None,
        state_machine: Optional[InterventionStateMachine] = None,
    ):
        self._audit_store = audit_store or InMemoryAuditLogStore()
        self._lms_client = lms_client or get_lms_adapter()
        self._alert_service = alert_service or SimulatedBorrowerAlertService()
        self._state_machine = state_machine or InterventionStateMachine()
        self._active_triggers: Dict[str, TriggerEvent] = {}

    # =========================================================================
    # 1. INTERVENTION LIFECYCLE STATE MACHINE METHODS
    # =========================================================================

    async def create_intervention(
        self,
        trigger_id: str,
        borrower_id: str,
        loan_id: str,
        proposal: TriggerActionProposal,
        actor: str = "RISK_ENGINE",
        notes: Optional[str] = None,
    ) -> LoanInterventionRecord:
        """Create a new loan intervention in TRIGGERED state."""
        record = self._state_machine.create_intervention(
            correlation_id=trigger_id,
            borrower_id=borrower_id,
            loan_id=loan_id,
            proposal=proposal,
            actor=actor,
            notes=notes,
        )

        await self._audit_store.append_entry(
            event_type=AuditEventType.INTERVENTION_STATE_TRANSITION,
            origin_service="integration-layer",
            actor=actor,
            correlation_id=trigger_id,
            payload_snapshot={
                "intervention_id": record.intervention_id,
                "transition": "INITIAL -> TRIGGERED",
                "loan_id": loan_id,
                "borrower_id": borrower_id,
                "action_type": proposal.action_type.value,
                "policy_code": proposal.policy_code,
            },
        )
        return record

    async def notify_borrower(
        self,
        intervention_id: str,
        channel: AlertChannel = AlertChannel.SMS,
        actor: str = "SYSTEM_AUTOMATION",
        district: str = "UNKNOWN",
        hazard_type: str = "CLIMATE_EVENT",
        language_code: str = "hi",
    ) -> AlertDispatchResult:
        """Advance intervention to NOTIFIED and dispatch localized borrower advisory."""
        record = self._state_machine.get_intervention(intervention_id)
        now = datetime.now(timezone.utc)
        alert_id = f"ALT-{uuid.uuid4().hex[:8].upper()}"

        sms_text, subject, body = format_climate_relief_advisory(
            borrower_id=record.borrower_id,
            loan_id=record.loan_id,
            district=district,
            hazard_type=hazard_type,
            action_type=record.action_proposal.action_type.value,
            relief_period_days=record.action_proposal.relief_period_days,
            topup_amount=record.action_proposal.topup_amount,
            language_code=language_code,
        )

        message_payload = AlertMessagePayload(
            alert_id=alert_id,
            borrower_id=record.borrower_id,
            channel=channel,
            localized_message_text=sms_text,
            email_subject=subject,
            email_body_text=body,
            language_code=language_code,
            dispatched_at=now,
            metadata={"intervention_id": intervention_id, "loan_id": record.loan_id},
        )

        dispatch_result = await self._alert_service.send_alert(message_payload)

        # Advance state machine
        self._state_machine.transition_status(
            intervention_id=intervention_id,
            target_status=InterventionStatus.NOTIFIED,
            actor=actor,
            notes=f"Dispatched advisory via {channel.value} (simulated={dispatch_result.is_simulated}).",
            metadata=dispatch_result.model_dump(mode="json"),
        )

        # Record immutable audit entry
        await self._audit_store.append_entry(
            event_type=AuditEventType.BORROWER_ALERT_SENT,
            origin_service="integration-layer",
            actor=actor,
            correlation_id=record.correlation_id,
            payload_snapshot={
                "intervention_id": intervention_id,
                "alert_id": alert_id,
                "channel": channel.value,
                "delivery_status": dispatch_result.delivery_status.value,
                "is_simulated": dispatch_result.is_simulated,
                "preview_text": sms_text,
            },
        )

        return dispatch_result

    async def apply_lms_intervention(
        self,
        intervention_id: str,
        actor: str = "SYSTEM_AUTOMATION",
    ) -> LMSActionResponse:
        """Advance intervention to APPLIED and dispatch signed modification request to LMS."""
        record = self._state_machine.get_intervention(intervention_id)
        now = datetime.now(timezone.utc)
        idempotency_key = f"IDEM-{record.loan_id}-{uuid.uuid4().hex[:8].upper()}"

        lms_payload = LMSActionPayload(
            idempotency_key=idempotency_key,
            intervention_id=intervention_id,
            loan_id=record.loan_id,
            borrower_id=record.borrower_id,
            action_type=record.action_proposal.action_type,
            relief_period_days=record.action_proposal.relief_period_days,
            topup_amount=record.action_proposal.topup_amount,
            trigger_event_id=record.correlation_id,
            timestamp=now,
        )

        response = await self._lms_client.dispatch_intervention(lms_payload)

        # Advance state machine to APPLIED
        self._state_machine.transition_status(
            intervention_id=intervention_id,
            target_status=InterventionStatus.APPLIED,
            actor=actor,
            notes=response.message,
            metadata=response.model_dump(mode="json"),
            lms_transaction_id=response.transaction_id,
        )

        # Record immutable audit entry
        await self._audit_store.append_entry(
            event_type=AuditEventType.LMS_WEBHOOK_DISPATCHED,
            origin_service="integration-layer",
            actor=actor,
            correlation_id=record.correlation_id,
            payload_snapshot={
                "intervention_id": intervention_id,
                "idempotency_key": idempotency_key,
                "loan_id": record.loan_id,
                "action_type": record.action_proposal.action_type.value,
                "lms_transaction_id": response.transaction_id,
                "lms_status": response.status.value,
                "is_simulated": response.is_simulated,
            },
        )

        return response

    async def confirm_lms_intervention(
        self,
        intervention_id: str,
        lms_transaction_id: str,
        notes: Optional[str] = None,
        actor: str = "LMS_CONFIRMATION",
    ) -> LoanInterventionRecord:
        """Advance intervention to terminal CONFIRMED state upon execution verification."""
        record = self._state_machine.transition_status(
            intervention_id=intervention_id,
            target_status=InterventionStatus.CONFIRMED,
            actor=actor,
            notes=notes or "LMS transaction confirmed and verified.",
            lms_transaction_id=lms_transaction_id,
        )

        await self._audit_store.append_entry(
            event_type=AuditEventType.LMS_CALLBACK_VERIFIED,
            origin_service="integration-layer",
            actor=actor,
            correlation_id=record.correlation_id,
            payload_snapshot={
                "intervention_id": intervention_id,
                "lms_transaction_id": lms_transaction_id,
                "final_status": InterventionStatus.CONFIRMED.value,
            },
        )
        return record

    async def execute_full_intervention_flow(
        self,
        trigger_id: str,
        borrower_id: str,
        loan_id: str,
        proposal: TriggerActionProposal,
        actor: str = "SYSTEM_AUTOMATION",
        district: str = "UNKNOWN",
        hazard_type: str = "CLIMATE_ANOMALY",
    ) -> LoanInterventionRecord:
        """Execute complete linear lifecycle: TRIGGERED -> NOTIFIED -> APPLIED -> CONFIRMED."""
        # 1. TRIGGERED
        record = await self.create_intervention(
            trigger_id=trigger_id,
            borrower_id=borrower_id,
            loan_id=loan_id,
            proposal=proposal,
            actor=actor,
        )

        # 2. NOTIFIED
        await self.notify_borrower(
            intervention_id=record.intervention_id,
            channel=AlertChannel.SMS,
            actor=actor,
            district=district,
            hazard_type=hazard_type,
        )

        # 3. APPLIED
        lms_resp = await self.apply_lms_intervention(
            intervention_id=record.intervention_id,
            actor=actor,
        )

        # 4. CONFIRMED (in simulated/mock mode, instantaneous confirmation)
        confirmed_record = await self.confirm_lms_intervention(
            intervention_id=record.intervention_id,
            lms_transaction_id=lms_resp.transaction_id,
            notes=f"Simulated instant confirmation for {record.loan_id}",
            actor=actor,
        )

        return confirmed_record

    # =========================================================================
    # 2. INBOUND LMS WEBHOOK RECEIVER
    # =========================================================================

    async def handle_incoming_lms_webhook(
        self,
        payload_bytes: bytes,
        signature_header: str,
        callback_data: LMSCallbackPayload,
        actor: str = "LMS_WEBHOOK_RECEIVER",
    ) -> LoanInterventionRecord:
        """Validate HMAC signature on incoming callback and advance state machine."""
        is_valid = self._lms_client.verify_webhook_signature(payload_bytes, signature_header)
        if not is_valid:
            logger.warning("[SECURITY] Inbound LMS webhook rejected: Invalid HMAC signature")
            raise ValueError("Invalid HMAC-SHA256 signature on inbound LMS webhook payload.")

        # Log receipt in audit trail
        await self._audit_store.append_entry(
            event_type=AuditEventType.LMS_WEBHOOK_RECEIVED,
            origin_service="lms",
            actor=actor,
            correlation_id=callback_data.intervention_id,
            payload_snapshot=callback_data.model_dump(mode="json"),
        )

        # Advance state machine according to LMS verdict
        if callback_data.status in (LMSExecutionStatus.ACCEPTED, LMSExecutionStatus.SIMULATED_SUCCESS):
            return await self.confirm_lms_intervention(
                intervention_id=callback_data.intervention_id,
                lms_transaction_id=callback_data.lms_transaction_id,
                notes=callback_data.notes,
                actor=actor,
            )
        else:
            record = self._state_machine.transition_status(
                intervention_id=callback_data.intervention_id,
                target_status=InterventionStatus.FAILED,
                actor=actor,
                notes=f"LMS rejected modification: {callback_data.notes}",
                lms_transaction_id=callback_data.lms_transaction_id,
            )
            return record

    # =========================================================================
    # 3. QUERY & BACKWARDS-COMPATIBLE SERVICE METHODS
    # =========================================================================

    def get_intervention(self, intervention_id: str) -> LoanInterventionRecord:
        """Fetch single intervention entity with transition history."""
        return self._state_machine.get_intervention(intervention_id)

    def list_interventions(
        self,
        borrower_id: Optional[str] = None,
        loan_id: Optional[str] = None,
        status: Optional[InterventionStatus] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[LoanInterventionRecord]:
        """List interventions with optional filtering."""
        return self._state_machine.list_interventions(
            borrower_id=borrower_id,
            loan_id=loan_id,
            status=status,
            correlation_id=correlation_id,
            limit=limit,
        )

    async def execute_loan_intervention(
        self,
        borrower_id: str,
        loan_id: str,
        action: TriggerActionProposal,
        trigger_id: str,
        actor: str = "SYSTEM_AUTOMATION",
    ) -> LMSActionResponse:
        """Backwards-compatible wrapper executing full flow and returning LMSActionResponse."""
        record = await self.execute_full_intervention_flow(
            trigger_id=trigger_id,
            borrower_id=borrower_id,
            loan_id=loan_id,
            proposal=action,
            actor=actor,
        )

        return LMSActionResponse(
            transaction_id=record.lms_transaction_id or f"LMS-TXN-{uuid.uuid4().hex[:8].upper()}",
            status=LMSExecutionStatus.SIMULATED_SUCCESS,
            message=f"Intervention '{record.intervention_id}' successfully confirmed for loan '{loan_id}'",
            processed_at=record.updated_at,
            is_simulated=True,
        )

    async def record_trigger_event(
        self,
        trigger: TriggerEvent,
        actor: str = "RISK_ENGINE",
    ) -> AuditLogEntry:
        """Store triggered parametric event in registry and append to audit trail."""
        self._active_triggers[trigger.trigger_id] = trigger

        entry = await self._audit_store.append_entry(
            event_type=AuditEventType.TRIGGER_FIRED,
            origin_service="risk-engine",
            actor=actor,
            correlation_id=trigger.trigger_id,
            payload_snapshot=trigger.model_dump(mode="json"),
        )
        return entry

    async def send_borrower_relief_alert(
        self,
        borrower_id: str,
        message_text: str,
        channel: AlertChannel = AlertChannel.SMS,
        actor: str = "SYSTEM_AUTOMATION",
    ) -> bool:
        """Backwards-compatible wrapper returning boolean for alert dispatch."""
        now = datetime.now(timezone.utc)
        payload = AlertMessagePayload(
            alert_id=f"ALT-{uuid.uuid4().hex[:8].upper()}",
            borrower_id=borrower_id,
            channel=channel,
            localized_message_text=message_text,
            language_code="hi",
            dispatched_at=now,
        )
        result = await self._alert_service.send_alert(payload)

        await self._audit_store.append_entry(
            event_type=AuditEventType.BORROWER_ALERT_SENT,
            origin_service="integration-layer",
            actor=actor,
            correlation_id=None,
            payload_snapshot=result.model_dump(mode="json"),
        )
        return result.delivery_status in (AlertDeliveryStatus.SIMULATED_DISPATCHED, AlertDeliveryStatus.DELIVERED)

    async def list_audit_entries(
        self,
        limit: int = 50,
        event_type: Optional[AuditEventType] = None,
        correlation_id: Optional[str] = None,
    ) -> List[AuditLogEntry]:
        """Fetch audit trail history for compliance and governance review."""
        return await self._audit_store.list_recent_entries(
            limit=limit,
            event_type=event_type,
            correlation_id=correlation_id,
        )

    async def verify_audit_ledger(self) -> Dict[str, Any]:
        """Cryptographically verify the SHA-256 chain of the audit trail."""
        is_valid = await self._audit_store.verify_chain_integrity()
        entries = await self._audit_store.list_recent_entries(limit=1000)

        return {
            "chain_valid": is_valid,
            "total_entries": len(entries),
            "latest_hash": entries[0].event_hash if entries else None,
            "verified_at": datetime.now(timezone.utc).isoformat(),
        }

    async def list_active_triggers(self) -> List[TriggerEvent]:
        """Return all active or simulated parametric triggers."""
        return list(self._active_triggers.values())


_GLOBAL_INTEGRATION_SERVICE: Optional[IntegrationService] = None


def get_integration_service() -> IntegrationService:
    """Singleton provider for IntegrationService."""
    global _GLOBAL_INTEGRATION_SERVICE
    if _GLOBAL_INTEGRATION_SERVICE is None:
        _GLOBAL_INTEGRATION_SERVICE = IntegrationService()
    return _GLOBAL_INTEGRATION_SERVICE
