"""Thread-safe state machine managing loan intervention lifecycles."""

from datetime import datetime, timezone
import logging
import threading
from typing import Any, Dict, List, Optional, Set
import uuid

from climateshield_shared.constants import InterventionStatus
from climateshield_shared.schemas.trigger import TriggerActionProposal
from integration_layer.state_machine.exceptions import (
    InvalidInterventionStateTransitionError,
    InterventionNotFoundError,
)
from integration_layer.state_machine.models import (
    InterventionStateTransition,
    LoanInterventionRecord,
)

logger = logging.getLogger("integration.state_machine")

# Directed acyclic graph of permitted lifecycle state transitions
VALID_TRANSITIONS: Dict[InterventionStatus, Set[InterventionStatus]] = {
    InterventionStatus.TRIGGERED: {
        InterventionStatus.NOTIFIED,
        InterventionStatus.APPLIED,
        InterventionStatus.CANCELLED,
        InterventionStatus.FAILED,
    },
    InterventionStatus.NOTIFIED: {
        InterventionStatus.APPLIED,
        InterventionStatus.CANCELLED,
        InterventionStatus.FAILED,
    },
    InterventionStatus.APPLIED: {
        InterventionStatus.CONFIRMED,
        InterventionStatus.FAILED,
    },
    InterventionStatus.FAILED: {
        # Allow retry of failed interventions by credit officer
        InterventionStatus.APPLIED,
        InterventionStatus.CANCELLED,
    },
    InterventionStatus.CONFIRMED: set(),  # Terminal state
    InterventionStatus.CANCELLED: set(),  # Terminal state
}


class InterventionStateMachine:
    """Enforces strict lifecycle rules for MSME climate loan interventions."""

    def __init__(self):
        self._lock = threading.Lock()
        self._interventions: Dict[str, LoanInterventionRecord] = {}

    def create_intervention(
        self,
        correlation_id: str,
        borrower_id: str,
        loan_id: str,
        proposal: TriggerActionProposal,
        actor: str = "RISK_ENGINE",
        notes: Optional[str] = None,
    ) -> LoanInterventionRecord:
        """Instantiate a new loan intervention in TRIGGERED state."""
        now = datetime.now(timezone.utc)
        intervention_id = f"INTV-{uuid.uuid4().hex[:8].upper()}"

        initial_transition = InterventionStateTransition(
            from_status=None,
            to_status=InterventionStatus.TRIGGERED,
            timestamp=now,
            actor=actor,
            notes=notes or f"Parametric trigger breach activated for loan '{loan_id}'.",
            metadata={
                "action_type": proposal.action_type.value,
                "relief_period_days": proposal.relief_period_days,
                "topup_amount": proposal.topup_amount,
                "policy_code": proposal.policy_code,
            },
        )

        record = LoanInterventionRecord(
            intervention_id=intervention_id,
            correlation_id=correlation_id,
            borrower_id=borrower_id,
            loan_id=loan_id,
            current_status=InterventionStatus.TRIGGERED,
            action_proposal=proposal,
            history=[initial_transition],
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._interventions[intervention_id] = record

        logger.info(
            "[INTERVENTION_CREATED] id=%s loan=%s borrower=%s correlation_id=%s",
            intervention_id,
            loan_id,
            borrower_id,
            correlation_id,
        )
        return record

    def transition_status(
        self,
        intervention_id: str,
        target_status: InterventionStatus,
        actor: str = "SYSTEM",
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        lms_transaction_id: Optional[str] = None,
    ) -> LoanInterventionRecord:
        """Advance intervention lifecycle to target status if transition is valid.

        Raises:
            InterventionNotFoundError: If intervention_id does not exist.
            InvalidInterventionStateTransitionError: If the transition is prohibited.
        """
        now = datetime.now(timezone.utc)

        with self._lock:
            record = self._interventions.get(intervention_id)
            if not record:
                raise InterventionNotFoundError(intervention_id)

            current_status = record.current_status
            allowed_next_states = VALID_TRANSITIONS.get(current_status, set())

            if target_status not in allowed_next_states:
                logger.warning(
                    "[ILLEGAL_TRANSITION_ATTEMPT] id=%s current=%s target=%s actor=%s",
                    intervention_id,
                    current_status.value,
                    target_status.value,
                    actor,
                )
                raise InvalidInterventionStateTransitionError(
                    current_status=current_status.value,
                    target_status=target_status.value,
                    intervention_id=intervention_id,
                )

            # Record state transition
            transition = InterventionStateTransition(
                from_status=current_status,
                to_status=target_status,
                timestamp=now,
                actor=actor,
                notes=notes,
                metadata=metadata or {},
            )

            record.current_status = target_status
            record.history.append(transition)
            record.updated_at = now

            if lms_transaction_id:
                record.lms_transaction_id = lms_transaction_id

            logger.info(
                "[INTERVENTION_TRANSITION] id=%s from=%s to=%s actor=%s",
                intervention_id,
                current_status.value,
                target_status.value,
                actor,
            )
            return record

    def get_intervention(self, intervention_id: str) -> LoanInterventionRecord:
        """Retrieve an intervention record by ID."""
        with self._lock:
            record = self._interventions.get(intervention_id)
            if not record:
                raise InterventionNotFoundError(intervention_id)
            return record

    def list_interventions(
        self,
        borrower_id: Optional[str] = None,
        loan_id: Optional[str] = None,
        status: Optional[InterventionStatus] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[LoanInterventionRecord]:
        """Query stored interventions with multi-attribute filtering."""
        with self._lock:
            records = list(self._interventions.values())

        if borrower_id:
            records = [r for r in records if r.borrower_id == borrower_id]
        if loan_id:
            records = [r for r in records if r.loan_id == loan_id]
        if status:
            records = [r for r in records if r.current_status == status]
        if correlation_id:
            records = [r for r in records if r.correlation_id == correlation_id]

        # Newest first
        records.sort(key=lambda r: r.created_at, reverse=True)
        return records[:limit]
