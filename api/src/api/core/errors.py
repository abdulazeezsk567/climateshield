"""Structured error responses and sanitized exception handlers for ClimateShield API."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from data_layer.exceptions import DataLayerError, RecordNotFoundError
from integration_layer import (
    InterventionNotFoundError,
    InvalidInterventionStateTransitionError,
)

logger = logging.getLogger("api.errors")


class ErrorDetail(BaseModel):
    """Normalized error detail representation."""
    code: str = Field(..., description="Machine-readable error classification code")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Any] = Field(None, description="Contextual validation or field error information")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp when error transpired",
    )


class ErrorResponse(BaseModel):
    """Standardized top-level error response envelope."""
    error: ErrorDetail


def register_error_handlers(app: FastAPI) -> None:
    """Attach centralized, sanitized error handlers to the FastAPI application.

    Guarantees that no raw stack traces or internal backend diagnostics
    leak to external API clients.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        error_code = _status_to_error_code(exc.status_code)
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code=error_code,
                message=str(exc.detail),
                details=None,
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_resp.model_dump(mode="json"),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        sanitized_details = []
        for err in exc.errors():
            sanitized_details.append({
                "field": ".".join(str(loc) for loc in err.get("loc", []) if loc != "body"),
                "issue": err.get("msg", "Invalid input"),
            })

        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Request payload or parameters failed input schema validation.",
                details=sanitized_details,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_resp.model_dump(mode="json"),
        )

    @app.exception_handler(RecordNotFoundError)
    async def record_not_found_handler(request: Request, exc: RecordNotFoundError) -> JSONResponse:
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="RESOURCE_NOT_FOUND",
                message=str(exc),
                details=None,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_resp.model_dump(mode="json"),
        )

    @app.exception_handler(DataLayerError)
    async def data_layer_error_handler(request: Request, exc: DataLayerError) -> JSONResponse:
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="DATA_LAYER_ERROR",
                message=str(exc),
                details=None,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_resp.model_dump(mode="json"),
        )

    @app.exception_handler(InterventionNotFoundError)
    async def intervention_not_found_handler(request: Request, exc: InterventionNotFoundError) -> JSONResponse:
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="INTERVENTION_NOT_FOUND",
                message=str(exc),
                details=None,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_resp.model_dump(mode="json"),
        )

    @app.exception_handler(InvalidInterventionStateTransitionError)
    async def invalid_transition_handler(request: Request, exc: InvalidInterventionStateTransitionError) -> JSONResponse:
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="ILLEGAL_STATE_TRANSITION",
                message=str(exc),
                details={"current_status": exc.current_status, "target_status": exc.target_status},
            )
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=error_resp.model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def global_unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Log internal diagnostic details securely on the server
        logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, str(exc))

        # Deliver sanitized non-leaking message to client
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An internal server error occurred. Please contact system support.",
                details=None,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_resp.model_dump(mode="json"),
        )


def _status_to_error_code(status_code: int) -> str:
    """Map numeric HTTP status code to uppercase alphanumeric error code string."""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")
