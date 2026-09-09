"""ClimateShield API Gateway Application Factory."""

from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from climateshield_shared.telemetry import configure_logging
from api.core.config import get_settings
from api.core.errors import register_error_handlers
from api.core.middleware import (
    MetricsMiddleware,
    RateLimitingMiddleware,
    SecurityHeadersMiddleware,
)
from api.routes import (
    audit_router,
    auth_router,
    interventions_router,
    lms_webhook_router,
    metrics_router,
    portfolio_router,
    risk_router,
    triggers_router,
)
from data_layer import get_data_layer_service
from integration_layer import get_integration_service
from risk_engine import RiskEngineService


def create_application() -> FastAPI:
    """Instantiate and configure the authoritative ClimateShield API Gateway.

    Acts as the sole externally-facing backend surface, orchestrating calls
    to Data Layer, Risk Engine, and Integration Layer without exposing
    internal subsystems directly to the network.
    """
    settings = get_settings()

    # Configure structured logging subsystem
    configure_logging(
        service_name="climateshield-api",
        log_level=settings.log_level,
        json_format=(settings.log_format.lower() == "json" or settings.environment in ("staging", "production")),
    )

    app = FastAPI(
        title="ClimateShield API Gateway",
        description=(
            "Climate-Risk Intelligence and Parametric Loan-Protection Gateway for Satin Finserv (SFL).\n\n"
            "Orchestrates climate telemetry ingestion, parametric trigger evaluations, automated LMS "
            "loan modifications (EMI relief & recovery top-ups), and immutable cryptographic audit trails."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Attach centralized, sanitized error handlers
    register_error_handlers(app)

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Telemetry and metrics middleware
    app.add_middleware(MetricsMiddleware)

    # Rate limiting middleware (per-IP sliding window)
    app.add_middleware(RateLimitingMiddleware)

    # Defensive HTTP security headers middleware (CSP, X-Frame-Options, HSTS, Cache-Control)
    app.add_middleware(SecurityHeadersMiddleware)

    # Mount metrics router (unauthenticated for Prometheus scrapers, summary for internal dashboard)
    app.include_router(metrics_router)

    # Mount versioned API v1 route blueprints
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(portfolio_router, prefix="/api/v1")
    app.include_router(risk_router, prefix="/api/v1")
    app.include_router(triggers_router, prefix="/api/v1")
    app.include_router(interventions_router, prefix="/api/v1")
    app.include_router(lms_webhook_router, prefix="/api/v1")
    app.include_router(audit_router, prefix="/api/v1")

    @app.get(
        "/health",
        tags=["System Monitoring"],
        summary="Service Health and Deployment Readiness Probe",
        description="Returns runtime service status, environment, version, and internal component probe results for monitoring.",
    )
    async def health_check() -> Dict[str, Any]:
        """Deployment health and readiness probe."""
        # Probe internal services
        try:
            dl = get_data_layer_service()
            summary = await dl.get_portfolio_summary()
            data_layer_ok = summary["total_borrowers"] > 0
        except Exception:
            data_layer_ok = False

        try:
            integ = get_integration_service()
            audit_report = await integ.verify_audit_ledger()
            integration_ok = audit_report["chain_valid"]
        except Exception:
            integration_ok = False

        return {
            "status": "healthy" if (data_layer_ok and integration_ok) else "degraded",
            "service": "climateshield-api",
            "environment": settings.environment,
            "version": "0.1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "subsystems": {
                "data_layer": "UP" if data_layer_ok else "DOWN",
                "risk_engine": "UP",
                "integration_layer": "UP" if integration_ok else "DOWN",
            },
        }

    return app


app = create_application()
