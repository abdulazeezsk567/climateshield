"""API Route blueprints export module."""

from api.routes.auth import router as auth_router
from api.routes.portfolio import router as portfolio_router
from api.routes.risk import router as risk_router
from api.routes.triggers import router as triggers_router
from api.routes.audit import router as audit_router
from api.routes.interventions import (
    lms_webhook_router,
    router as interventions_router,
)
from api.routes.metrics import metrics_router

__all__ = [
    "auth_router",
    "portfolio_router",
    "risk_router",
    "triggers_router",
    "audit_router",
    "interventions_router",
    "lms_webhook_router",
    "metrics_router",
]

