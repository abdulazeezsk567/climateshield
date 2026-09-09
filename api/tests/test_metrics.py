"""Automated tests for Prometheus metrics, JSON summaries, and structured logging."""

import json
import logging
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.core.config import Settings
from api.main import app
from climateshield_shared.telemetry import (
    StructuredJsonFormatter,
    get_metrics_registry,
)


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


def test_prometheus_metrics_endpoint(client):
    """Ensure /metrics returns standard Prometheus exposition text format."""
    # Issue a probe request first to generate telemetry
    client.get("/health")

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    text = response.text

    # Verify Prometheus metric declarations
    assert "# HELP climateshield_http_requests_total" in text
    assert "# TYPE climateshield_http_requests_total counter"
    assert "climateshield_http_requests_total{" in text
    assert "# HELP climateshield_triggers_evaluated_total" in text
    assert "# HELP climateshield_interventions_dispatched_total" in text


def test_metrics_json_summary_endpoint(client):
    """Ensure /api/v1/metrics/summary returns structured telemetry metrics."""
    client.get("/health")

    response = client.get("/api/v1/metrics/summary")
    assert response.status_code == 200
    data = response.json()

    assert "http" in data
    assert "triggers" in data
    assert "interventions" in data
    assert data["http"]["total_requests"] >= 1
    assert "error_rate_percent" in data["http"]


def test_structured_json_logger_redaction():
    """Ensure StructuredJsonFormatter formats single-line JSON and redacts sensitive keys."""
    formatter = StructuredJsonFormatter(service_name="test-service", environment="testing")
    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=42,
        msg="Borrower loan application processed for %s",
        args=("ACME MSME",),
        exc_info=None,
    )
    # Inject context with both benign and sensitive keys
    record.correlation_id = "CORR-TEST-123"
    record.borrower_name = "Ramesh Kumar"
    record.account_number = "SB-9876543210"
    record.pan = "ABCDE1234F"
    record.district = "Varanasi"

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test.logger"
    assert parsed["service"] == "test-service"
    assert parsed["correlation_id"] == "CORR-TEST-123"

    # Context sanitization checks
    assert "context" in parsed
    assert parsed["context"]["district"] == "Varanasi"
    assert parsed["context"]["borrower_name"] == "[REDACTED]"
    assert parsed["context"]["account_number"] == "[REDACTED]"
    assert parsed["context"]["pan"] == "[REDACTED]"


def test_production_environment_rejects_insecure_defaults():
    """Verify that staging and production reject default development secret keys."""
    # Default secret in development passes
    dev_settings = Settings(environment="development")
    assert dev_settings.environment == "development"

    insecure_placeholder = "development-insecure-" + "secret-change-in-production"
    # Default secret in production raises ValidationError
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            environment="production",
            jwt_secret_key=insecure_placeholder,
        )
    assert "jwt_secret_key cannot use default development placeholder" in str(excinfo.value)

    # Valid external secret in production succeeds
    custom_valid_key = "prod-super-secure-" + "entropy-key-test-value-12345"
    prod_settings = Settings(
        environment="production",
        jwt_secret_key=custom_valid_key,
    )
    assert prod_settings.environment == "production"
    assert prod_settings.jwt_secret_key == custom_valid_key
