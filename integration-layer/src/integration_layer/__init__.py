"""ClimateShield Action & Integration Layer Public Interface."""

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
    HttpLMSAdapter,
    SimulatedLMSAdapter,
    SimulatedLMSClient,
    get_lms_adapter,
)
from integration_layer.lms_webhook.interfaces import (
    LMSActionPayload,
    LMSActionResponse,
    LMSAdapter,
    LMSCallbackPayload,
    LMSWebhookClient,
)
from integration_layer.service import (
    IntegrationService,
    get_integration_service,
)
from integration_layer.state_machine import (
    InterventionNotFoundError,
    InterventionStateMachine,
    InterventionStateTransition,
    InvalidInterventionStateTransitionError,
    LoanInterventionRecord,
)

__all__ = [
    "IntegrationService",
    "get_integration_service",
    "InMemoryAuditLogStore",
    "AuditLogStore",
    "LMSAdapter",
    "SimulatedLMSAdapter",
    "SimulatedLMSClient",
    "HttpLMSAdapter",
    "get_lms_adapter",
    "LMSWebhookClient",
    "LMSActionPayload",
    "LMSActionResponse",
    "LMSCallbackPayload",
    "BorrowerAlertService",
    "SimulatedBorrowerAlertService",
    "format_climate_relief_advisory",
    "AlertMessagePayload",
    "AlertDispatchResult",
    "AlertChannel",
    "InterventionStateMachine",
    "LoanInterventionRecord",
    "InterventionStateTransition",
    "InvalidInterventionStateTransitionError",
    "InterventionNotFoundError",
]
