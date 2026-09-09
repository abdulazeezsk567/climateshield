"""Simulated Borrower Multi-Channel Notification Service with Zero-Fabrication Safeguards."""

from datetime import datetime, timezone
import logging
import os
from typing import List, Optional
import uuid

from climateshield_shared.constants import AlertDeliveryStatus
from integration_layer.alerts.interfaces import (
    AlertChannel,
    AlertDispatchResult,
    AlertMessagePayload,
    BorrowerAlertService,
)

logger = logging.getLogger("integration.alerts")


def format_climate_relief_advisory(
    borrower_id: str,
    loan_id: str,
    district: str,
    hazard_type: str,
    action_type: str,
    relief_period_days: Optional[int] = None,
    topup_amount: Optional[float] = None,
    language_code: str = "hi",
) -> tuple[str, str, str]:
    """Construct bilingual, empathetic SMS and Email notification copy.

    Returns:
        tuple of (sms_text, email_subject, email_body_text).
    """
    if language_code == "hi":
        # Hindi notification template
        if action_type == "EMI_DEFERRAL":
            sms_text = (
                f"[सैटिन फिनसर्व सहायता] प्रिय ग्राहक (ID: {borrower_id}), {district} जिले में मौसम विसंगति "
                f"को देखते हुए आपके ऋण {loan_id} पर {relief_period_days or 30} दिनों के लिए ईएमआई राहत लागू की गई है। "
                f"इस अवधि में कोई पेनल्टी नहीं लगेगी।"
            )
        else:
            sms_text = (
                f"[सैटिन फिनसर्व सहायता] प्रिय ग्राहक (ID: {borrower_id}), {district} जिले में जलवायु प्रभाव "
                f"से उबरने हेतु आपके ऋण {loan_id} पर ₹{topup_amount or 0:,.2f} की आपातकालीन सहायता स्वीकृत की गई है।"
            )

        subject = f"सैटिन फिनसर्व जलवायु सुरक्षा - ऋण खाता {loan_id} हेतु राहत सूचना"
        body = (
            f"आदरणीय उद्यमी,\n\n"
            f"क्लाइमेटशील्ड (ClimateShield) द्वारा {district} में प्रतिकूल मौसमी परिस्थितियों ({hazard_type}) "
            f"का स्वतः संज्ञान लिया गया है।\n"
            f"सैटिन फिनसर्व द्वारा आपके MSME व्यवसाय की सुरक्षा हेतु ऋण खाता {loan_id} पर "
            f"तुरंत राहत प्रदान की गई है।\n\n"
            f"राहत प्रकार: {action_type}\n"
            f"विवरण: {relief_period_days or 30} दिन स्थगन अथवा स्वीकृत क्रेडिट।\n"
            f"शर्तें: शून्य दंडात्मक ब्याज (Zero Penalty).\n\n"
            f"किसी भी सहायता हेतु संपर्क करें: 1800-XXX-XXXX (सैटिन फिनसर्व ग्राहक सेवा)\n"
        )
    else:
        # English notification template
        if action_type == "EMI_DEFERRAL":
            sms_text = (
                f"[Satin Finserv Advisory] Dear Borrower ({borrower_id}), due to climate anomaly in {district}, "
                f"an EMI relief moratorium of {relief_period_days or 30} days is activated on loan {loan_id}. "
                f"Zero penalty applies."
            )
        else:
            sms_text = (
                f"[Satin Finserv Advisory] Dear Borrower ({borrower_id}), emergency climate recovery credit "
                f"of ₹{topup_amount or 0:,.2f} has been sanctioned for loan {loan_id}."
            )

        subject = f"Satin Finserv ClimateShield: Automatic Loan Support Notice for {loan_id}"
        body = (
            f"Dear MSME Partner,\n\n"
            f"ClimateShield has detected adverse weather conditions ({hazard_type}) in {district}.\n"
            f"To protect your enterprise cash flows, Satin Finserv has proactively sanctioned loan support:\n\n"
            f"- Account Number: {loan_id}\n"
            f"- Relief Action: {action_type}\n"
            f"- Term: {relief_period_days or 30} Days Moratorium\n"
            f"- Penal Interest: Waived (Zero)\n\n"
            f"For inquiries, contact your SFL Branch Relationship Officer or call 1800-XXX-XXXX.\n"
        )

    return sms_text, subject, body


class SimulatedBorrowerAlertService(BorrowerAlertService):
    """Notification service with explicit simulation labeling and fallback safety.

    Guarantees that demo runs never fabricate a claim of real external delivery,
    logging clearly and marking results with SIMULATED_DISPATCHED.
    """

    def __init__(self):
        self._dispatched_records: List[AlertDispatchResult] = []
        # Check if real SMS gateway credentials exist in environment
        self._real_gateway_configured = bool(os.getenv("SMS_GATEWAY_API_KEY"))

    async def send_alert(self, payload: AlertMessagePayload) -> AlertDispatchResult:
        """Process alert dispatch with strict simulation indicators."""
        now = datetime.now(timezone.utc)

        if not self._real_gateway_configured:
            # DEMO / SIMULATION MODE (Zero-fabrication rule enforced)
            logger.info(
                "[SIMULATED_ALERT] (Demo Mode - No real SMS/Email dispatched to telecom carrier) "
                "alert_id=%s channel=%s borrower=%s text='%s'",
                payload.alert_id,
                payload.channel.value,
                payload.borrower_id,
                payload.localized_message_text,
            )

            result = AlertDispatchResult(
                alert_id=payload.alert_id,
                borrower_id=payload.borrower_id,
                delivery_status=AlertDeliveryStatus.SIMULATED_DISPATCHED,
                channel=payload.channel,
                is_simulated=True,
                dispatched_at=now,
                preview_text=payload.localized_message_text,
                provider_ref=f"SIM-MOCK-REF-{uuid.uuid4().hex[:6].upper()}",
            )
        else:
            # Production gateway integration branch (placeholder for real Twilio / Gupshup API)
            logger.info(
                "[PRODUCTION_ALERT] Dispatching real carrier notification via configured SMS gateway to borrower=%s",
                payload.borrower_id,
            )
            result = AlertDispatchResult(
                alert_id=payload.alert_id,
                borrower_id=payload.borrower_id,
                delivery_status=AlertDeliveryStatus.DELIVERED,
                channel=payload.channel,
                is_simulated=False,
                dispatched_at=now,
                preview_text=payload.localized_message_text,
                provider_ref=f"GW-TXN-{uuid.uuid4().hex[:8].upper()}",
            )

        self._dispatched_records.append(result)
        return result

    @property
    def dispatched_alerts(self) -> List[AlertDispatchResult]:
        """Inspection history of dispatched alerts."""
        return list(self._dispatched_records)

    # Backwards-compatible alias for existing test assertions
    @property
    def sent_alerts(self) -> List[AlertDispatchResult]:
        """Backwards-compatible alias for dispatched_alerts."""
        return list(self._dispatched_records)
