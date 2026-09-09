"""Pluggable LMS Webhook Adapters: Simulated and Production HTTP."""

from datetime import datetime, timezone
import hashlib
import hmac
import logging
import os
from typing import Optional
import uuid

from climateshield_shared.constants import LMSExecutionStatus
from integration_layer.lms_webhook.interfaces import (
    LMSActionPayload,
    LMSActionResponse,
    LMSAdapter,
)

logger = logging.getLogger("integration.lms")

DEFAULT_DEMO_SECRET = "demo-sfl-lms-hmac-secret-2026"


class SimulatedLMSAdapter(LMSAdapter):
    """Simulates webhook integration with Satin Finserv's Core LMS.

    In development and demonstration modes, emulates instantaneous loan adjustment
    confirmations, generating transaction identifiers and policy audit notes.
    Always explicitly tags actions as simulated to satisfy zero-fabrication constraints.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self._secret_key = secret_key or os.getenv("LMS_WEBHOOK_SECRET", DEFAULT_DEMO_SECRET)

    def compute_signature(self, payload_bytes: bytes) -> str:
        """Generate HMAC-SHA256 signature over payload bytes."""
        return hmac.new(
            self._secret_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        """Constant-time verification of HMAC-SHA256 signature."""
        if not signature:
            return False
        expected = self.compute_signature(payload_bytes)
        return hmac.compare_digest(expected.lower(), signature.strip().lower())

    async def dispatch_intervention(self, payload: LMSActionPayload) -> LMSActionResponse:
        """Emulate dispatching an approved loan intervention to the core LMS."""
        now = datetime.now(timezone.utc)
        tx_id = f"LMS-TXN-{uuid.uuid4().hex[:8].upper()}"

        if payload.relief_period_days:
            msg = (
                f"[SIMULATED_LMS] Scheduled {payload.relief_period_days}-day moratorium for "
                f"loan account '{payload.loan_id}' (Borrower '{payload.borrower_id}')"
            )
        elif payload.topup_amount:
            msg = (
                f"[SIMULATED_LMS] Sanctioned emergency credit top-up of ₹{payload.topup_amount:,.2f} "
                f"for loan account '{payload.loan_id}'"
            )
        else:
            msg = f"[SIMULATED_LMS] Action '{payload.action_type.value}' successfully processed"

        logger.info(
            "[SIMULATED_LMS_DISPATCH] loan_id=%s action=%s tx_id=%s idempotency_key=%s",
            payload.loan_id,
            payload.action_type.value,
            tx_id,
            payload.idempotency_key,
        )

        return LMSActionResponse(
            transaction_id=tx_id,
            status=LMSExecutionStatus.SIMULATED_SUCCESS,
            message=msg,
            processed_at=now,
            is_simulated=True,
        )

    # Backwards-compatible alias for existing tests and call sites
    async def dispatch_action(self, payload: LMSActionPayload) -> LMSActionResponse:
        """Backwards-compatible alias for dispatch_intervention."""
        return await self.dispatch_intervention(payload)


class HttpLMSAdapter(LMSAdapter):
    """Production adapter dispatching real HTTP POST webhooks to Satin's core LMS."""

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        secret_key: Optional[str] = None,
        timeout_seconds: float = 10.0,
    ):
        self._endpoint_url = endpoint_url or os.getenv("LMS_ENDPOINT_URL", "https://lms.satinfinserv.com/api/v1/interventions")
        self._secret_key = secret_key or os.getenv("LMS_WEBHOOK_SECRET", "")
        self._timeout_seconds = timeout_seconds

        if not self._secret_key:
            logger.warning("[SECURITY] HttpLMSAdapter initialized without configured LMS_WEBHOOK_SECRET!")

    def compute_signature(self, payload_bytes: bytes) -> str:
        """Generate HMAC-SHA256 signature."""
        return hmac.new(
            self._secret_key.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()

    def verify_webhook_signature(self, payload_bytes: bytes, signature: str) -> bool:
        """Constant-time HMAC verification."""
        if not signature:
            return False
        expected = self.compute_signature(payload_bytes)
        return hmac.compare_digest(expected.lower(), signature.strip().lower())

    async def dispatch_intervention(self, payload: LMSActionPayload) -> LMSActionResponse:
        """Dispatch real HTTP webhook with cryptographic signature."""
        import httpx

        payload_json = payload.model_dump_json()
        payload_bytes = payload_json.encode("utf-8")
        signature = self.compute_signature(payload_bytes)

        headers = {
            "Content-Type": "application/json",
            "X-ClimateShield-Signature": signature,
            "X-Idempotency-Key": payload.idempotency_key,
        }

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            response = await client.post(
                self._endpoint_url,
                content=payload_bytes,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        return LMSActionResponse(
            transaction_id=data.get("transaction_id", f"LMS-TXN-{uuid.uuid4().hex[:8].upper()}"),
            status=LMSExecutionStatus(data.get("status", "ACCEPTED")),
            message=data.get("message", "Intervention successfully accepted by LMS"),
            processed_at=datetime.now(timezone.utc),
            is_simulated=False,
        )

    async def dispatch_action(self, payload: LMSActionPayload) -> LMSActionResponse:
        """Backwards-compatible alias."""
        return await self.dispatch_intervention(payload)


# Backwards-compatible class alias
SimulatedLMSClient = SimulatedLMSAdapter


def get_lms_adapter() -> LMSAdapter:
    """Factory function resolving configured LMS adapter."""
    adapter_type = os.getenv("LMS_ADAPTER_TYPE", "mock").strip().lower()
    if adapter_type in ("http", "production", "real"):
        return HttpLMSAdapter()
    return SimulatedLMSAdapter()
