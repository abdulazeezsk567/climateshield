"""Prometheus and JSON metrics endpoints for system observability."""

from typing import Any, Dict
from fastapi import APIRouter, Response
from climateshield_shared.telemetry import get_metrics_registry

metrics_router = APIRouter(tags=["System Observability"])


@metrics_router.get(
    "/metrics",
    summary="Prometheus Metrics Exposition",
    description="Exposes system throughput, latencies, HTTP error rates, and climate trigger counts in Prometheus text format.",
    response_class=Response,
)
async def get_prometheus_metrics() -> Response:
    """Standard Prometheus metrics scraper endpoint."""
    registry = get_metrics_registry()
    content = registry.to_prometheus_format()
    return Response(
        content=content,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@metrics_router.get(
    "/api/v1/metrics/summary",
    summary="JSON Metrics Summary",
    description="Returns structured metrics dictionary suitable for administrative dashboard display.",
)
async def get_metrics_summary() -> Dict[str, Any]:
    """JSON structured observability summary."""
    registry = get_metrics_registry()
    return registry.to_dict()
